"""전체 테스트와 상세 로그를 보존하고 짧은 결과만 출력한다."""

from __future__ import annotations
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    folder = root / ".practice-test-logs"
    folder.mkdir(exist_ok=True)
    log = folder / (datetime.now().strftime("%Y%m%d-%H%M%S-%f") + ".log")
    env = dict(os.environ)
    env.pop("PYTEST_ADDOPTS", None)
    with log.open("w", encoding="utf-8") as output:
        run = subprocess.run(
            [sys.executable, "-m", "pytest", "-v", "-s", "--log-cli-level=DEBUG"],
            cwd=root,
            env=env,
            stdout=output,
            stderr=subprocess.STDOUT,
            check=False,
        )
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    print("전체 테스트:", "통과" if run.returncode == 0 else "확인 필요")
    print(next((line for line in reversed(lines) if line.strip()), "출력 없음"))
    print("상세 로그:", log.relative_to(root))
    return run.returncode


if __name__ == "__main__":
    sys.exit(main())
