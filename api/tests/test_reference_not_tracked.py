"""The private reference set must never be committed. These tests fail if the
folder is tracked or not ignored — a committed scan is a content-rule breach."""
import subprocess
from pathlib import Path

_API_DIR = Path(__file__).resolve().parents[1]
_REF = "private_reference"


def test_nothing_under_reference_dir_is_tracked():
    out = subprocess.run(
        ["git", "ls-files", "--", _REF], cwd=_API_DIR, capture_output=True, text=True
    )
    assert out.stdout.strip() == "", f"private reference files are tracked:\n{out.stdout}"


def test_reference_dir_is_gitignored():
    out = subprocess.run(
        ["git", "check-ignore", f"{_REF}/scan.png"], cwd=_API_DIR, capture_output=True, text=True
    )
    # check-ignore prints the path (and exits 0) when it is ignored.
    assert out.stdout.strip() != "", "private_reference/ is not gitignored"
