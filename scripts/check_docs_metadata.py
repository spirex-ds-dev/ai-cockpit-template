#!/usr/bin/env python3
"""Validate documentation front matter and supported-stack lists."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from install_ai_cockpit import STACKS


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FRONT_MATTER = ("author", "title", "description")
README_FILES = ("README.md", "README.ja.md", "README.zh-CN.md")


def documentation_files(root: Path) -> list[Path]:
    files = [root / name for name in README_FILES]
    files.append(root / ".ai" / "glossary.md")
    files.extend(sorted((root / "docs").glob("*.md")))
    files.extend(sorted((root / "examples").glob("*/README.md")))
    return files


def front_matter_errors(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return [f"{path}: missing YAML front matter"]
    closing = text.find("\n---\n", 4)
    if closing < 0:
        return [f"{path}: unterminated YAML front matter"]
    block = text[4:closing]
    keys = {
        match.group(1)
        for line in block.splitlines()
        if (match := re.match(r"^([A-Za-z][A-Za-z0-9_-]*):", line))
    }
    return [f"{path}: front matter missing {key}" for key in REQUIRED_FRONT_MATTER if key not in keys]


def stack_errors(root: Path) -> list[str]:
    ordered_stacks = [
        "generic", "rust", "flutter", "typescript", "python", "go", "java",
        "android", "kotlin", "swift", "ruby", "php", "csharp",
    ]
    if set(ordered_stacks) != STACKS:
        return ["scripts/check_docs_metadata.py: canonical stack order does not match installer STACKS"]

    readme_list = ", ".join(ordered_stacks)
    errors = []
    for name in README_FILES:
        if readme_list not in (root / name).read_text(encoding="utf-8"):
            errors.append(f"{name}: supported-stack list does not match installer STACKS")

    configuration = (root / "docs" / "configuration.md").read_text(encoding="utf-8")
    configuration_list = "\n".join(ordered_stacks)
    if configuration_list not in configuration:
        errors.append("docs/configuration.md: supported-stack list does not match installer STACKS")
    return errors


def check_repository(root: Path) -> list[str]:
    errors = []
    for path in documentation_files(root):
        errors.extend(front_matter_errors(path))
    errors.extend(stack_errors(root))
    return errors


def main() -> int:
    errors = check_repository(ROOT)
    if errors:
        print("documentation metadata check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("documentation metadata check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
