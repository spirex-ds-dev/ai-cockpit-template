from pathlib import Path

from ai_installer_evidence import summarize_installation_actions
from ai_installer_transaction import TransactionAction


def test_summarize_installation_actions_classifies_add_modify_and_skip(
    tmp_path: Path,
) -> None:
    makefile = tmp_path / "Makefile"
    makefile.write_text("all:\n", encoding="utf-8")

    preview = summarize_installation_actions(
        [
            TransactionAction("write", tmp_path / "Makefile.ai", "new managed file"),
            TransactionAction("append", makefile, "include managed Makefile"),
            TransactionAction("skip", tmp_path / ".gitignore", "rules already present"),
        ],
        target=tmp_path,
        branch="adopt/ai-cockpit",
    )

    assert preview.adds == 1
    assert preview.modifies == 1
    assert preview.skips == 1
    assert preview.source_code_changes is False
    assert preview.branch == "adopt/ai-cockpit"


def test_summarize_installation_actions_flags_unknown_product_source_path(
    tmp_path: Path,
) -> None:
    source = tmp_path / "src" / "application.py"

    preview = summarize_installation_actions(
        [TransactionAction("write", source, "unexpected product write")],
        target=tmp_path,
        branch="main",
    )

    assert preview.source_code_changes is True
