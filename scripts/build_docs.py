"""Build the local project documentation with MkDocs Material."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Build the complete static documentation into ``docs_build``."""
    project_root = Path(__file__).resolve().parents[1]
    command = [sys.executable, "-m", "mkdocs", "build", "--clean", "--strict"]
    subprocess.run(command, cwd=project_root, check=True)
    print(f"Documentation created in: {project_root / 'docs_build'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
