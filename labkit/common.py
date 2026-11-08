from __future__ import annotations

import hashlib
import io
import json
import os
import signal
import subprocess
import zipfile
from pathlib import Path, PurePosixPath


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def source_digest(repo: Path) -> str:
    h = hashlib.sha256()
    for path in sorted((repo / "src").rglob("*.py")):
        if path.is_symlink():
            raise ValueError("소스에 심볼릭 링크를 사용할 수 없습니다.")
        h.update(path.relative_to(repo).as_posix().encode())
        h.update(b"\0" + path.read_bytes() + b"\0")
    return h.hexdigest()


def extract_zip(blob: bytes, target: Path, max_bytes: int = 20_000_000) -> None:
    """Extract regular files only, with size and path checks before any writes."""
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        entries = archive.infolist()
        if len(entries) > 2000 or sum(x.file_size for x in entries) > max_bytes:
            raise ValueError("압축 파일의 크기 또는 파일 수가 허용 범위를 넘었습니다.")
        seen = set()
        for item in entries:
            name = PurePosixPath(item.filename)
            mode = item.external_attr >> 16
            if (
                name.is_absolute()
                or ".." in name.parts
                or "\\" in item.filename
                or ":" in item.filename
                or (mode & 0o170000) == 0o120000
                or item.filename in seen
            ):
                raise ValueError("허용하지 않는 압축 경로: " + item.filename)
            seen.add(item.filename)
            if not (target / item.filename).resolve().is_relative_to(target.resolve()):
                raise ValueError("압축 경로가 대상 폴더를 벗어납니다.")
        archive.extractall(target)


def run_process(
    command: list[str],
    cwd: Path,
    stdout: Path,
    stderr: Path,
    timeout: int,
    stdin: str | None = None,
    env: dict | None = None,
) -> int:
    """Stream logs to files; stop the process group on timeout or interruption."""
    with (
        stdout.open("w", encoding="utf-8") as out,
        stderr.open("w", encoding="utf-8") as err,
    ):
        proc = subprocess.Popen(
            command,
            cwd=cwd,
            stdin=subprocess.PIPE if stdin else None,
            stdout=out,
            stderr=err,
            text=True,
            encoding="utf-8",
            env=env,
            start_new_session=os.name != "nt",
        )
        try:
            proc.communicate(stdin, timeout=timeout)
            return proc.returncode
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                    capture_output=True,
                    check=False,
                )
            else:
                os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
            raise
