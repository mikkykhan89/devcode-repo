import subprocess
import sys
from pathlib import Path


def test_user_table_prints_expected_greetings():
    project_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "python_process/user_table.py"],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.splitlines() == ["Hello, World!", "hi same"]
