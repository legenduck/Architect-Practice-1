"""로컬 bare 저장소로 검증한다. GitHub나 LLM을 호출하지 않는다."""

from pathlib import Path
import json
import subprocess
import tempfile
import unittest

from labkit.github_flow import (
    enroll,
    fetch_results,
    participant,
    push_submission,
    receipt_for,
)


def git(folder, *args, check=True):
    return subprocess.run(
        ["git", *args], cwd=folder, text=True, capture_output=True, check=check
    )


class GitWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.remote = self.root / "remote.git"
        git(self.root, "init", "--bare", "--initial-branch=main", str(self.remote))
        self.teacher = self.root / "teacher"
        git(self.root, "clone", str(self.remote), str(self.teacher))
        self.identity(self.teacher)
        (self.teacher / "README.md").write_text("Course materials\n")
        (self.teacher / ".gitignore").write_text("config.json\nruns/\n")
        git(self.teacher, "add", ".")
        git(self.teacher, "commit", "-m", "Course baseline")
        git(self.teacher, "push", "origin", "main")
        self.student = self.root / "student"
        git(self.root, "clone", str(self.remote), str(self.student))
        self.identity(self.student)
        self.cfg = {"repository": str(self.remote), "participant": "p01"}

    def identity(self, folder):
        git(folder, "config", "user.name", "Fixture")
        git(folder, "config", "user.email", "fixture@example.invalid")
        git(folder, "config", "commit.gpgsign", "false")

    def tearDown(self):
        self.tmp.cleanup()

    def artifact(self):
        folder = self.student / "runs/20261109-000000-abcd"
        folder.mkdir(parents=True, exist_ok=True)
        path = self.student / "submissions" / (folder.name + ".zip")
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(b"fixture submission")
        return folder, path

    def test_enrollment_selects_only_assigned_branch(self):
        self.assertEqual(enroll(self.student, self.cfg, "P01"), "students/p01")
        self.assertEqual(
            git(self.student, "branch", "--show-current").stdout.strip(), "students/p01"
        )
        self.assertEqual(
            json.loads((self.student / "config.json").read_text())["participant"], "p01"
        )

    def test_unsafe_participant_name_is_rejected(self):
        for name in ["../../main", "p01/a", "-x", ""]:
            with self.assertRaises(ValueError):
                participant(name)

    def test_main_cannot_be_used_for_submission(self):
        folder, path = self.artifact()
        with self.assertRaises(ValueError):
            push_submission(self.student, folder, path, self.cfg)
        self.assertEqual(
            git(self.student, "branch", "--show-current").stdout.strip(), "main"
        )

    def test_only_generated_artifact_is_committed(self):
        enroll(self.student, self.cfg, "p01")
        folder, path = self.artifact()
        (self.student / "local-notes.txt").write_text("Do not publish")
        result = push_submission(self.student, folder, path, self.cfg)
        files = git(
            self.remote, "ls-tree", "-r", "--name-only", "refs/heads/students/p01"
        ).stdout
        self.assertIn("submissions/" + folder.name + ".zip", files)
        self.assertNotIn("local-notes.txt", files)
        self.assertNotIn("config.json", files)
        self.assertEqual(result["branch"], "students/p01")

    def test_other_staged_files_stop_submission(self):
        enroll(self.student, self.cfg, "p01")
        folder, path = self.artifact()
        (self.student / "other.txt").write_text("unrelated")
        git(self.student, "add", "other.txt")
        with self.assertRaises(ValueError):
            push_submission(self.student, folder, path, self.cfg)

    def test_result_is_bound_to_exact_submitted_git_blob(self):
        enroll(self.student, self.cfg, "p01")
        folder, path = self.artifact()
        submitted = push_submission(self.student, folder, path, self.cfg)
        git(self.teacher, "checkout", "--orphan", "results")
        grade = self.teacher / "grades/p01" / f"{folder.name}.json"
        grade.parent.mkdir(parents=True)
        grade.write_text(
            json.dumps(
                {
                    "run_id": folder.name,
                    "artifact_blob": submitted["artifact_blob"],
                    "status": "passed",
                }
            )
        )
        git(self.teacher, "add", "grades")
        git(self.teacher, "commit", "-m", "Fixture receipt")
        git(self.teacher, "push", "origin", "results")
        fetch_results(self.student, self.cfg)
        self.assertEqual(
            receipt_for(self.student, folder, self.cfg)["status"], "passed"
        )
        path.write_bytes(b"new submission")
        push_submission(self.student, folder, path, self.cfg)
        self.assertIsNone(receipt_for(self.student, folder, self.cfg))

    def test_origin_must_match_the_course_repository(self):
        with self.assertRaises(ValueError):
            enroll(
                self.student,
                {**self.cfg, "repository": "https://github.com/other/course.git"},
                "p01",
            )


if __name__ == "__main__":
    unittest.main()
