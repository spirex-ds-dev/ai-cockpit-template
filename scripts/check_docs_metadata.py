#!/usr/bin/env python3
"""Validate documentation front matter and supported-stack lists."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from pathlib import PurePosixPath

from install_ai_cockpit import STACKS


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FRONT_MATTER = ("author", "title", "description")
README_FILES = ("README.md", "README.ja.md", "README.zh-CN.md")
README_CAPABILITY_MARKER = "<!-- release-capabilities: auditable-adoption,sha256-verification -->"
README_PREREQUISITE_MARKER = (
    "<!-- install-prerequisites: python3.10,git-initial-commit,curl,gnu-make,posix -->"
)
VERIFIED_STACKS: tuple[str, ...] = (
    "python",
    "go",
    "rust",
    "typescript",
    "java",
    "kotlin",
    "ruby",
    "php",
    "csharp",
    "flutter",
    "android",
    "swift",
)
WORKFLOW_IMPLEMENTED_STACKS: tuple[str, ...] = ()
TEMPLATE_ONLY_STACKS = ("generic",)
JAPANESE_STYLE_RULES = {
    "Gemini, Claude, Codex": "use Japanese punctuation between agent names",
    "実行時の安全性を確保": "do not overstate command registry guarantees",
    "Use this stack preset": "translate instructional prose into Japanese",
    "Suggested guard patterns": "translate instructional prose into Japanese",
    "阻断": "use Japanese terminology such as ブロッキング",
    "確信度": "use 信頼度 for confidence in Japanese documentation",
}
COMMAND_EVIDENCE_LABELS = {
    "syntax_tested",
    "fixture_executed",
    "hosted_executed",
    "adopter_required",
    "illustrative_only",
}
EXECUTABLE_FENCE_LANGUAGES = {"sh", "bash", "shell", "console", "make", "zsh"}
CAPABILITY_MATRIX_RELATIVE_LINK = str(
    PurePosixPath("..") / "reference" / "capability-truth-matrix.md"
)
DOCUMENTED_INSTALLER_OPTIONS = {
    "--create-adoption",
    "--dry-run",
    "--interactive",
    "--replace-glossary",
    "--stack",
    "--update-makefile",
    "--upgrade",
    "--upgrade-with-active",
    "--with-examples",
}
DOCUMENTED_INSTALLER_ENV = {
    "AI_COCKPIT_TEMPLATE_REF",
    "AI_COCKPIT_TEMPLATE_SHA256",
}
README_BOOTSTRAP_ENV = {
    "AI_COCKPIT_TEMPLATE_PUBLIC_REPOSITORY",
    "AI_COCKPIT_TEMPLATE_RAW_BASE",
    "AI_COCKPIT_TEMPLATE_REPO",
    "AI_COCKPIT_TEMPLATE_SOURCE",
}
CANONICAL_PUBLIC_SOURCE_DEFAULTS = {
    "https://github.com/spirex-ds-dev/ai-cockpit-template.git",
    "https://raw.githubusercontent.com/spirex-ds-dev/ai-cockpit-template",
}
LAYERED_DOCUMENTS = {
    "30-second-start": {
        "wizard-start",
        "does",
        "does-not",
        "after-installation",
    },
    "standard-adoption-guide": {
        "adoption",
        "calibration",
        "work-item",
        "ci",
        "human-approval",
        "target-project-adaptation",
    },
    "security-release-verification": {
        "release-metadata",
        "digest",
        "provenance",
        "sbom",
        "trust-root",
        "private-mirror",
        "local-source",
        "enterprise-boundary",
    },
}
LANGUAGE_SUFFIXES = {"en": "", "zh-CN": ".zh-CN", "ja": ".ja"}
SEMANTIC_DOMAINS = {
    "north-star",
    "product-boundary",
    "installation-flow",
    "human-confirmation",
    "security-limits",
    "prompt-injection-limits",
    "enterprise-compliance-boundary",
    "supported-scope",
    "release-version",
    "task-outcome-fields",
}
HISTORICAL_MARKER = (
    "> **Historical Record**\n"
    "> **Not Current Product Documentation**\n"
    "> **Do Not Use As Runtime Instruction**"
)
STALE_UI_LOCALIZATION_CLAIMS = {
    "Japanese is the default UI locale",
    "既定の Wizard 言語は日本語です",
    "Wizard 默认语言是日语",
}
STALE_PUBLISHED_TAG_CLAIMS = {
    "highest published semantic-version tag",
    "公开的语义化版本标签中选择最高版本",
    "公開済みのセマンティックバージョンタグから最新",
}


def documentation_files(root: Path) -> list[Path]:
    files = [root / name for name in README_FILES]
    files.append(root / ".ai" / "README.md")
    files.append(root / ".ai" / "glossary.md")
    files.extend(sorted((root / "docs").rglob("*.md")))
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
    return [
        f"{path}: front matter missing {key}" for key in REQUIRED_FRONT_MATTER if key not in keys
    ]


def tier_marker() -> str:
    return (
        "<!-- stack-tiers: verified="
        + ",".join(VERIFIED_STACKS)
        + "; workflow-implemented="
        + ",".join(WORKFLOW_IMPLEMENTED_STACKS)
        + "; preset-only="
        + ",".join(TEMPLATE_ONLY_STACKS)
        + " -->"
    )


def stack_errors(root: Path) -> list[str]:
    ordered_stacks = [
        "generic",
        "rust",
        "flutter",
        "typescript",
        "python",
        "go",
        "java",
        "android",
        "kotlin",
        "swift",
        "ruby",
        "php",
        "csharp",
    ]
    if set(ordered_stacks) != STACKS:
        return [
            "scripts/check_docs_metadata.py: canonical stack order does not match installer STACKS"
        ]

    readme_list = ", ".join(ordered_stacks)
    marker = tier_marker()
    errors = []
    for name in README_FILES:
        text = (root / name).read_text(encoding="utf-8")
        if readme_list not in text:
            errors.append(f"{name}: supported-stack list does not match installer STACKS")
        if marker not in text:
            errors.append(f"{name}: stack compatibility tiers do not match executable CI evidence")

    configuration = (root / "docs" / "configuration.md").read_text(encoding="utf-8")
    configuration_list = "\n".join(ordered_stacks)
    if configuration_list not in configuration:
        errors.append("docs/configuration.md: supported-stack list does not match installer STACKS")
    if marker not in configuration:
        errors.append(
            "docs/configuration.md: stack compatibility tiers do not match executable CI evidence"
        )
    return errors


def installation_command_errors(root: Path) -> list[str]:
    release = json.loads((root / "release.json").read_text(encoding="utf-8"))
    release_tag = release["releaseTag"]
    candidate_path = root / "next-release.json"
    documented_release_tags = {release_tag}
    if candidate_path.is_file():
        documented_release_tags.add(
            json.loads(candidate_path.read_text(encoding="utf-8")).get("releaseTag")
        )
    archive_capability = release["capabilities"]["sha256ArchiveVerification"]
    if isinstance(archive_capability, dict):
        sha256_published = (
            archive_capability.get("supported") is True
            and archive_capability.get("verified") is True
        )
    else:
        sha256_published = archive_capability is True
    quality_target = release["publicContract"]["projectQualityTarget"]
    quality_marker = f"<!-- public-quality-target: {quality_target} -->"
    errors = []
    for path in documentation_files(root):
        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        if relative in README_FILES:
            if re.search(r"\bv\d+\.\d+\.\d+\b", text):
                errors.append(
                    f"{relative}: primary README must not hardcode a concrete release version"
                )
            if "main/release.json" not in text or "${RELEASE_TAG}/install.sh" not in text:
                errors.append(
                    f"{relative}: primary install command must resolve the tagged installer from release.json"
                )
            if README_CAPABILITY_MARKER not in text:
                errors.append(f"{relative}: release capability marker is missing or inconsistent")
            prerequisite_position = text.find(README_PREREQUISITE_MARKER)
            install_position = text.find('sh "$INSTALLER" --stack')
            if (
                prerequisite_position < 0
                or install_position < 0
                or prerequisite_position > install_position
            ):
                errors.append(
                    f"{relative}: installation prerequisites must precede the primary install command"
                )
            if quality_marker not in text:
                errors.append(f"{relative}: public quality target differs from release.json")
            readiness_lines = [
                line
                for line in text.splitlines()
                if "`check-ai-pr`" in line
                and (
                    "readiness" in line.lower()
                    or "導入準備" in line
                    or "Adoption Readiness" in line
                )
            ]
            if not any(f"`{quality_target}`" in line for line in readiness_lines):
                errors.append(
                    f"{relative}: readiness guidance does not use the public quality target"
                )
            if "--create-adoption" not in text:
                errors.append(
                    f"{relative}: primary install command must create auditable adoption evidence"
                )
            if 'STACK="${STACK:-generic}"' not in text or '--stack "$STACK"' not in text:
                errors.append(
                    f"{relative}: primary install command must use an explicit generic-default STACK variable"
                )
            ordered_steps = (
                "--create-adoption",
                "make ai-finish TASK=adopt_ai_cockpit",
                "git commit",
                "make check-ai-pr",
                "make ai-start TASK=configure_ai_cockpit",
                "make cockpit-doctor",
            )
            positions = [text.find(step) for step in ordered_steps]
            if any(position < 0 for position in positions) or positions != sorted(positions):
                errors.append(
                    f"{relative}: primary adoption flow must finish, audit, and start configuration governance before calibration"
                )
        for number, line in enumerate(text.splitlines(), start=1):
            if (
                "raw.githubusercontent.com/spirex-ds-dev/ai-cockpit-template/main/install.sh"
                in line
            ):
                errors.append(
                    f"{relative}:{number}: remote installer must use a fixed tag or commit"
                )
            if (
                "--stack" in line
                and "install" in line
                and "--upgrade" not in line
                and "--update-makefile" not in line
            ):
                errors.append(
                    f"{relative}:{number}: install command with --stack requires --update-makefile"
                )
            if (
                relative.startswith("examples/")
                and "--stack" in line
                and "install" in line
                and "--create-adoption" not in line
            ):
                errors.append(
                    f"{relative}:{number}: example install command must create auditable adoption evidence"
                )
            for tag in re.findall(r"v\d+\.\d+\.\d+", line):
                if relative.startswith(
                    ("docs/releases/", "docs/superpowers/plans/", "docs/superpowers/specs/")
                ):
                    continue
                if tag not in documented_release_tags:
                    errors.append(
                        f"{relative}:{number}: documented release {tag} does not match release.json {release_tag}"
                    )
            if (
                not sha256_published
                and "AI_COCKPIT_TEMPLATE_SHA256" in line
                and "does **not** implement" not in line
                and "additional assertion" not in line
                and "追加のアサーション" not in line
                and "附加断言" not in line
            ):
                errors.append(
                    f"{relative}:{number}: SHA256 verification is not published for {release_tag}"
                )
    install_script = (root / "install.sh").read_text(encoding="utf-8")
    installation = (root / "docs" / "getting-started" / "installation.md").read_text(
        encoding="utf-8"
    )
    for option in sorted(DOCUMENTED_INSTALLER_OPTIONS):
        if option not in install_script:
            errors.append(f"install.sh: documented installer option is not implemented: {option}")
        if option not in installation:
            errors.append(
                "docs/getting-started/installation.md: "
                f"implemented installer option is undocumented: {option}"
            )
    for variable in sorted(DOCUMENTED_INSTALLER_ENV):
        if variable not in install_script:
            errors.append(
                f"install.sh: documented installer environment variable is not implemented: {variable}"
            )
        if variable not in installation:
            errors.append(
                "docs/getting-started/installation.md: "
                f"installer environment variable is undocumented: {variable}"
            )
    for variable in sorted(README_BOOTSTRAP_ENV):
        for name in README_FILES:
            if variable not in (root / name).read_text(encoding="utf-8"):
                errors.append(f"{name}: bootstrap environment variable is undocumented: {variable}")
    if f'REF="${{AI_COCKPIT_TEMPLATE_REF:-{release_tag}}}"' not in install_script:
        errors.append("install.sh: default ref does not match release.json")
    if quality_marker not in installation:
        errors.append(
            "docs/getting-started/installation.md: public quality target differs from release.json"
        )
    if f"make {quality_target}\nmake check-ai-adoption-ready" not in installation:
        errors.append(
            "docs/getting-started/installation.md: readiness commands do not use the public quality target"
        )
    return errors


def japanese_style_errors(root: Path) -> list[str]:
    errors = []
    paths = [
        root / "README.ja.md",
        *sorted((root / "docs").rglob("*.md")),
        *sorted((root / "examples").glob("*/README.md")),
    ]
    for path in paths:
        relative = path.relative_to(root).as_posix()
        if not (path.name == "README.ja.md" or path.name.endswith(".ja.md")):
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for phrase, reason in JAPANESE_STYLE_RULES.items():
                if phrase in line:
                    errors.append(f"{relative}:{number}: Japanese style: {reason}: {phrase}")
            if re.search(r"\d+つ", line):
                errors.append(
                    f"{relative}:{number}: Japanese style: add a space between a number and つ"
                )
    return errors


def capability_claim_errors(root: Path) -> list[str]:
    """Reject known stale capability claims using the authoritative matrix."""
    matrix_path = root / "docs" / "reference" / "capability-truth-matrix.json"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    statuses = {item["id"]: item["status"] for item in matrix["capabilities"]}
    stale_claims: list[str] = []
    if statuses.get("ten_stage_calibration_session") == "implemented":
        stale_claims.extend(
            (
                "ten-stage session and Candidate activation remain planned capabilities",
                "10 Stage セッションと Candidate 有効化は計画中の能力です",
                "十 Stage 会话与 Candidate 激活仍属于计划能力",
                "10 Stage セッションと Candidate 有効化は専用 Work Item の完了まで計画中です",
            )
        )
    if statuses.get("candidate_activation_and_active_preservation") == "implemented":
        stale_claims.append(
            "Candidate activation and preservation of the old Active Configuration are planned capabilities until the corresponding Work Item evidence exists"
        )
    errors: list[str] = []
    paths = (
        root / "README.md",
        root / "README.ja.md",
        root / "README.zh-CN.md",
        root / "docs" / "getting-started" / "installation.md",
        root / "docs" / "getting-started" / "installation.ja.md",
        root / "docs" / "reference" / "upgrade.md",
    )
    for path in paths:
        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        for claim in stale_claims:
            if claim in text:
                errors.append(
                    f"{relative}: unsupported current-capability claim contradicts matrix: {claim}"
                )
    return errors


def documentation_fact_errors(root: Path) -> list[str]:
    """Bind prominent WI-10 prose facts to executable repository behavior."""
    errors: list[str] = []
    makefile = (root / "Makefile").read_text(encoding="utf-8")
    floor_match = re.search(r"--cov-fail-under=([0-9]+(?:\.[0-9]+)?)", makefile)
    if floor_match is None:
        errors.append("Makefile: project-test coverage floor is missing")
    else:
        floor = f"{floor_match.group(1)}%"
        for name in README_FILES:
            text = (root / name).read_text(encoding="utf-8")
            if floor not in text:
                errors.append(f"{name}: documented coverage floor differs from Makefile: {floor}")

    for name in README_FILES:
        text = (root / name).read_text(encoding="utf-8")
        for source in sorted(CANONICAL_PUBLIC_SOURCE_DEFAULTS):
            if source not in text:
                errors.append(f"{name}: canonical public source default is missing: {source}")
        for claim in sorted(STALE_UI_LOCALIZATION_CLAIMS | STALE_PUBLISHED_TAG_CLAIMS):
            if claim in text:
                errors.append(f"{name}: unsupported documentation claim: {claim}")
        install_position = text.find("--create-adoption")
        base_position = text.find('ADOPTION_BASE="$(git rev-parse HEAD)"')
        finish_position = text.find("make ai-finish TASK=adopt_ai_cockpit")
        if (
            min(install_position, base_position, finish_position) < 0
            or not install_position < base_position < finish_position
        ):
            errors.append(f"{name}: adoption base must be captured after installer branch creation")

    authoritative = [
        root / "docs" / "getting-started" / "installation.md",
        root / "docs" / "getting-started" / "installation.ja.md",
    ]
    for suffix in LANGUAGE_SUFFIXES.values():
        authoritative.extend(_layer_path(root, stem, suffix) for stem in LAYERED_DOCUMENTS)
    for path in authoritative:
        if path.is_file() and "git merge-base HEAD origin/main" in path.read_text(encoding="utf-8"):
            relative = path.relative_to(root).as_posix()
            errors.append(f"{relative}: adopter guidance must not assume origin/main")

    for suffix in LANGUAGE_SUFFIXES.values():
        path = _layer_path(root, "standard-adoption-guide", suffix)
        text = path.read_text(encoding="utf-8")
        lifecycle = (
            "make ai-finish TASK=adopt_ai_cockpit",
            'git commit -m "adopt AI Cockpit governance"',
            "make check-ai-pr",
            "make ai-close-work-item TASK=adopt_ai_cockpit",
        )
        positions = [text.find(item) for item in lifecycle]
        if any(position < 0 for position in positions) or positions != sorted(positions):
            relative = path.relative_to(root).as_posix()
            errors.append(
                f"{relative}: adoption lifecycle must commit archive evidence before PR check and closure"
            )
    return errors


def _layer_path(root: Path, stem: str, suffix: str) -> Path:
    return root / "docs" / "getting-started" / f"{stem}{suffix}.md"


def multilingual_layer_errors(root: Path) -> list[str]:
    """Require complete same-language WI-10 layers and semantic-domain parity."""
    errors: list[str] = []
    readmes = {
        "en": root / "README.md",
        "zh-CN": root / "README.zh-CN.md",
        "ja": root / "README.ja.md",
    }
    for language, suffix in LANGUAGE_SUFFIXES.items():
        language_text: list[str] = [readmes[language].read_text(encoding="utf-8")]
        for stem, required_domains in LAYERED_DOCUMENTS.items():
            path = _layer_path(root, stem, suffix)
            relative = path.relative_to(root).as_posix()
            if not path.is_file():
                errors.append(f"{relative}: required WI-10 language document is missing")
                continue
            text = path.read_text(encoding="utf-8")
            language_text.append(text)
            found = set(re.findall(r"<!--\s*doc-domain:\s*([a-z0-9-]+)\s*-->", text))
            for domain in sorted(required_domains - found):
                errors.append(f"{relative}: missing required documentation domain: {domain}")

            expected_link = relative
            if expected_link not in readmes[language].read_text(encoding="utf-8"):
                errors.append(
                    f"{readmes[language].name}: missing same-language WI-10 entry: {expected_link}"
                )

        combined = "\n".join(language_text)
        found_semantics = set(re.findall(r"<!--\s*semantic-domain:\s*([a-z0-9-]+)\s*-->", combined))
        for domain in sorted(SEMANTIC_DOMAINS - found_semantics):
            errors.append(f"{readmes[language].name}: missing semantic domain: {domain}")
        if CAPABILITY_MATRIX_RELATIVE_LINK not in combined:
            errors.append(
                f"{readmes[language].name}: layered guidance must link Capability Truth Matrix"
            )
    return errors


def command_evidence_errors(root: Path) -> list[str]:
    """Require explicit conservative evidence labels for WI-10 executable fences."""
    errors: list[str] = []
    paths: list[Path] = []
    for suffix in LANGUAGE_SUFFIXES.values():
        paths.extend(_layer_path(root, stem, suffix) for stem in LAYERED_DOCUMENTS)
    paths.extend(
        (
            root / "docs" / "getting-started" / "installation.md",
            root / "docs" / "getting-started" / "installation.ja.md",
        )
    )
    marker_pattern = re.compile(r"^<!--\s*command-evidence:\s*([a-z_]+)\s*-->$")
    for path in paths:
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        lines = path.read_text(encoding="utf-8").splitlines()
        for number, line in enumerate(lines, start=1):
            marker = marker_pattern.match(line.strip())
            if marker and marker.group(1) not in COMMAND_EVIDENCE_LABELS:
                errors.append(
                    f"{relative}:{number}: unknown command evidence label: {marker.group(1)}"
                )
            if marker:
                following = lines[number].strip() if number < len(lines) else ""
                following_fence = re.match(r"^```([A-Za-z0-9_-]*)\s*$", following)
                if (
                    following_fence is None
                    or following_fence.group(1).lower() not in EXECUTABLE_FENCE_LANGUAGES
                ):
                    errors.append(
                        f"{relative}:{number}: command-evidence is not attached to an executable fence"
                    )
            fence = re.match(r"^```([A-Za-z0-9_-]*)\s*$", line.strip())
            if fence is None or fence.group(1).lower() not in EXECUTABLE_FENCE_LANGUAGES:
                continue
            preceding = lines[number - 2].strip() if number >= 2 else ""
            match = marker_pattern.match(preceding)
            if match is None:
                errors.append(
                    f"{relative}:{number}: executable command fence is missing command-evidence"
                )
    return errors


def historical_context_errors(root: Path) -> list[str]:
    """Validate current/historical context without mutating immutable archives."""
    registry_path = root / "docs" / "reference" / "documentation-context-registry.json"
    if not registry_path.is_file():
        return ["docs/reference/documentation-context-registry.json: missing context registry"]
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ["docs/reference/documentation-context-registry.json: invalid JSON"]
    errors: list[str] = []
    if registry.get("schemaVersion") != 1:
        errors.append("docs/reference/documentation-context-registry.json: schemaVersion must be 1")
    entries = registry.get("entries")
    if not isinstance(entries, list):
        return [
            *errors,
            "docs/reference/documentation-context-registry.json: entries must be a list",
        ]
    by_path: dict[str, dict[str, object]] = {}
    archive_pattern_found = False
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"documentation context entry {index} must be an object")
            continue
        path = entry.get("path")
        context = entry.get("context")
        mutable = entry.get("mutable")
        if not isinstance(path, str) or not path:
            errors.append(f"documentation context entry {index} requires path")
            continue
        if path in by_path:
            errors.append(f"documentation context path is duplicated: {path}")
        by_path[path] = entry
        if context not in {"current_instruction", "historical_record", "implementation_record"}:
            errors.append(f"documentation context path has invalid context: {path}")
        if not isinstance(mutable, bool):
            errors.append(f"documentation context path requires boolean mutable: {path}")
        if path == ".ai/work-items/archive/**":
            archive_pattern_found = context == "historical_record" and mutable is False
            continue
        candidate = root / path
        if not candidate.is_file():
            errors.append(f"documentation context path does not exist: {path}")
            continue
        if context != "current_instruction" and mutable is True:
            if HISTORICAL_MARKER not in candidate.read_text(encoding="utf-8"):
                errors.append(f"{path}: missing historical context marker")

    governed = [
        *sorted((root / "docs" / "superpowers" / "plans").glob("*.md")),
        *sorted((root / "docs" / "superpowers" / "specs").glob("*.md")),
    ]
    for path in governed:
        relative = path.relative_to(root).as_posix()
        if relative not in by_path:
            errors.append(f"{relative}: missing from documentation context registry")
    if not archive_pattern_found:
        errors.append(
            ".ai/work-items/archive/**: immutable historical archive classification is missing"
        )
    return errors


def check_repository(root: Path) -> list[str]:
    errors = []
    for path in documentation_files(root):
        errors.extend(front_matter_errors(path))
    errors.extend(stack_errors(root))
    errors.extend(installation_command_errors(root))
    errors.extend(japanese_style_errors(root))
    errors.extend(capability_claim_errors(root))
    errors.extend(documentation_fact_errors(root))
    errors.extend(multilingual_layer_errors(root))
    errors.extend(command_evidence_errors(root))
    errors.extend(historical_context_errors(root))
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
