from __future__ import annotations

import os
import subprocess
import sys


def main() -> int:
    cmd = [sys.executable, "-m", "pytest"]
    cmd.extend(sys.argv[1:])

    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")

    return subprocess.call(cmd, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
