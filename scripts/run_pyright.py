"""Run pyright, or skip cleanly while the repo has no Python sources yet.

Pyright exits with an error when it finds no files to check. This wrapper
keeps `make check` green until the first component is written.
"""

import subprocess
import sys
from pathlib import Path

SOURCE_FOLDERS = ("harness", "geo_tools", "serving")


def has_python_sources(repo_root: Path) -> bool:
    """Report whether any source folder contains a Python file.

    Args:
        repo_root: The repository root folder.

    Returns:
        True if at least one `.py` file exists under a source folder.
    """
    for folder_name in SOURCE_FOLDERS:
        folder = repo_root / folder_name
        if not folder.is_dir():
            continue

        first_python_file = next(folder.rglob("*.py"), None)
        if first_python_file is not None:
            return True

    return False


def main() -> int:
    """Run pyright if there is something to check.

    Returns:
        The process exit code: pyright's own, or 0 when skipped.
    """
    repo_root = Path(__file__).resolve().parent.parent

    if not has_python_sources(repo_root):
        sys.stdout.write("pyright: no Python sources yet, skipped\n")
        return 0

    completed = subprocess.run(["pyright"], cwd=repo_root, check=False)
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
