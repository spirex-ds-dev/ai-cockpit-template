import shutil
from pathlib import Path

from check_docs_metadata import check_repository


ROOT = Path(__file__).resolve().parents[1]


def copy_documentation(target: Path) -> None:
    for name in ("README.md", "README.ja.md", "README.zh-CN.md"):
        shutil.copy2(ROOT / name, target / name)
    shutil.copytree(ROOT / "docs", target / "docs")
    shutil.copytree(ROOT / "examples", target / "examples")
    (target / ".ai").mkdir()
    shutil.copy2(ROOT / ".ai" / "glossary.md", target / ".ai" / "glossary.md")


def test_repository_documentation_metadata_is_consistent():
    assert check_repository(ROOT) == []


def test_check_rejects_supported_stack_drift(tmp_path):
    copy_documentation(tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text(readme.read_text(encoding="utf-8").replace(", android", ""), encoding="utf-8")

    assert "README.md: supported-stack list does not match installer STACKS" in check_repository(tmp_path)


def test_check_rejects_missing_front_matter_field(tmp_path):
    copy_documentation(tmp_path)
    readme = tmp_path / "README.ja.md"
    readme.write_text(readme.read_text(encoding="utf-8").replace("author: Ray\n", ""), encoding="utf-8")

    assert any(error.endswith("README.ja.md: front matter missing author") for error in check_repository(tmp_path))
