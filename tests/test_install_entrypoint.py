from __future__ import annotations

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_no_argument_non_tty_fails_closed_without_target_mutation(tmp_path: Path) -> None:
    result = subprocess.run(
        [str(ROOT / "install.sh")],
        cwd=tmp_path,
        env={**os.environ, "AI_COCKPIT_TEMPLATE_SOURCE": str(ROOT)},
        text=True,
        input="",
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "requires a TTY" in result.stderr
    assert list(tmp_path.iterdir()) == []


def test_interactive_flag_routes_to_wizard_and_non_tty_does_not_write(tmp_path: Path) -> None:
    result = subprocess.run(
        [str(ROOT / "install.sh"), "--interactive"],
        cwd=tmp_path,
        env={**os.environ, "AI_COCKPIT_TEMPLATE_SOURCE": str(ROOT)},
        text=True,
        input="",
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert list(tmp_path.iterdir()) == []
