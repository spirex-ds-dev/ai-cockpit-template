from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from install_ai_cockpit import Installer

ROOT = Path(__file__).resolve().parents[1]


def test_fresh_adopter_receives_and_can_call_knowledge_projection_surface(tmp_path: Path) -> None:
    target = tmp_path / "adopter"
    installer = Installer(
        source=ROOT,
        target=target,
        stack="generic",
        force=False,
        dry_run=False,
        with_examples=False,
        update_makefile=True,
    )
    assert installer.install() == 0

    for relative in (
        "scripts/ai_generate_knowledge_record.py",
        "scripts/ai_check_knowledge_index.py",
        ".ai/schemas/implementation-knowledge-record.schema.json",
        ".ai/schemas/implementation-knowledge-index.schema.json",
    ):
        assert (target / relative).is_file(), relative

    for script in ("ai_generate_knowledge_record.py", "ai_check_knowledge_index.py"):
        result = subprocess.run(
            [sys.executable, str(target / "scripts" / script), "--help"],
            cwd=target,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr

    result = subprocess.run(
        ["make", "-f", "Makefile.ai", "-n", "ai-check-knowledge-index"],
        cwd=target,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_fresh_adopter_does_not_receive_template_repository_knowledge_records(
    tmp_path: Path,
) -> None:
    """Installation delivers the projection runtime, not this template's history."""
    target = tmp_path / "adopter"
    installer = Installer(
        source=ROOT,
        target=target,
        stack="generic",
        force=False,
        dry_run=False,
        with_examples=False,
        update_makefile=True,
    )

    assert installer.install() == 0

    knowledge_root = target / ".ai" / "knowledge"
    assert not (knowledge_root / "index.json").exists()
    if knowledge_root.is_dir():
        assert not list(knowledge_root.rglob("*.json"))
