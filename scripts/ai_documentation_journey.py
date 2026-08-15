"""Validate reader-criticality topics and localized documentation journeys."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

CRITICALITIES = {"P0", "P1", "P2"}
LOCALES = {"en", "ja", "zh-CN"}
STATUSES = {"planned", "active"}
LOCALIZATION_POLICIES = {"english-fallback-labelled", "not-required-by-default"}


def topic_index(registry: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    topics = registry.get("topics", [])
    if not isinstance(topics, list):
        return {}
    return {
        item["topic"]: item
        for item in topics
        if isinstance(item, Mapping) and isinstance(item.get("topic"), str)
    }


def _topic_paths(topic: Mapping[str, Any]) -> Mapping[str, Any]:
    paths = topic.get("localizedPaths")
    return paths if isinstance(paths, Mapping) else {}


def planned_gaps(registry: Mapping[str, Any], root: Path) -> list[dict[str, str]]:
    gaps: list[dict[str, str]] = []
    for topic_id, topic in sorted(topic_index(registry).items()):
        if topic.get("enforcementStatus") != "planned":
            continue
        paths = _topic_paths(topic)
        locales = sorted(
            set(paths) | ({"en", "ja", "zh-CN"} if topic.get("criticality") == "P0" else set())
        )
        for locale in locales:
            path = paths.get(locale)
            if not isinstance(path, str) or not path:
                gaps.append(
                    {"topic": topic_id, "locale": locale, "path": "", "reason": "path is missing"}
                )
            elif not (root / path).is_file():
                gaps.append(
                    {
                        "topic": topic_id,
                        "locale": locale,
                        "path": path,
                        "reason": "path does not exist",
                    }
                )
    return gaps


def validate_topics(registry: Mapping[str, Any], root: Path) -> list[str]:
    topics = registry.get("topics")
    if not isinstance(topics, list):
        return ["registry topics must be a list"]
    errors: list[str] = []
    seen: set[str] = set()
    owners: dict[str, str] = {}
    for index, raw in enumerate(topics):
        if not isinstance(raw, Mapping):
            errors.append(f"topic {index} must be an object")
            continue
        topic_id = raw.get("topic")
        prefix = str(topic_id) if isinstance(topic_id, str) and topic_id else f"topic {index}"
        if not isinstance(topic_id, str) or not topic_id:
            errors.append(f"{prefix}: topic is required")
        elif topic_id in seen:
            errors.append(f"{prefix}: duplicate topic")
        else:
            seen.add(topic_id)
        criticality = raw.get("criticality")
        if criticality not in CRITICALITIES:
            errors.append(f"{prefix}: invalid criticality")
        canonical = raw.get("canonicalPath")
        if not isinstance(canonical, str) or not canonical:
            errors.append(f"{prefix}: canonicalPath is required")
        elif canonical in owners:
            errors.append(f"{prefix}: canonicalPath already owned by {owners[canonical]}")
        else:
            owners[canonical] = prefix
        paths = raw.get("localizedPaths")
        if not isinstance(paths, Mapping):
            errors.append(f"{prefix}: localizedPaths must be an object")
            paths = {}
        for locale in sorted(paths):
            if locale not in LOCALES:
                errors.append(f"{prefix}: invalid locale: {locale}")
        if criticality == "P0":
            for locale in sorted(LOCALES):
                if not isinstance(paths.get(locale), str) or not paths.get(locale):
                    errors.append(f"{prefix}: missing P0 locale: {locale}")
        status = raw.get("enforcementStatus")
        if status not in STATUSES:
            errors.append(f"{prefix}: invalid enforcementStatus")
        policy = raw.get("localizationPolicy")
        if criticality in {"P1", "P2"} and policy not in LOCALIZATION_POLICIES:
            errors.append(f"{prefix}: localizationPolicy is required for {criticality}")
        if criticality == "P1" and policy == "english-fallback-labelled":
            fallback_label = raw.get("fallbackLabel")
            missing_locales = any(locale not in paths for locale in ("ja", "zh-CN"))
            if missing_locales and (
                not isinstance(fallback_label, str) or not fallback_label.strip()
            ):
                errors.append(f"{prefix}: P1 English fallback requires fallbackLabel")
        if criticality == "P2" and policy == "english-fallback-labelled":
            errors.append(f"{prefix}: P2 cannot use the P1 English fallback policy")
        if raw.get("previousEnforcementStatus") == "active" and status == "planned":
            errors.append(f"{prefix}: active topics cannot be downgraded to planned")
        if status == "active":
            for locale, path in sorted(paths.items()):
                if isinstance(path, str) and path and not (root / path).is_file():
                    errors.append(f"{prefix}: {locale} path does not exist: {path}")
    return sorted(errors)


def validate_journeys(registry: Mapping[str, Any], root: Path) -> list[str]:
    del root
    errors: list[str] = []
    topics = topic_index(registry)
    for topic_id, topic in sorted(topics.items()):
        next_topics = topic.get("nextTopics", [])
        if not isinstance(next_topics, list):
            errors.append(f"{topic_id}: nextTopics must be a list")
            continue
        for target in sorted(next_topics):
            if target not in topics:
                errors.append(f"{topic_id}: next topic does not exist: {target}")
    return sorted(errors)


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        registry = json.loads(args.registry.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2
    errors = [*validate_topics(registry, args.root), *validate_journeys(registry, args.root)]
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2))
        return 1
    print(f"documentation journey check passed: {args.registry}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
