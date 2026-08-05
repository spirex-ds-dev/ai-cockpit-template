#!/usr/bin/env python3
"""Fail closed for raw Dependabot pull requests in hosted CI."""

from __future__ import annotations

import argparse
import json


def decision(event_name: str, author: str, pull_request_url: str, head: str) -> dict[str, object]:
    if event_name != "pull_request" or author != "dependabot[bot]":
        return {"state": "not_applicable", "automaticMergeAuthorized": False}
    return {
        "state": "blocked",
        "reason": "raw_dependabot_candidate_requires_current_main_successor",
        "pullRequestUrl": pull_request_url,
        "head": head,
        "automaticMergeAuthorized": False,
        "requiredAction": "preserve source facts and create a current-main Work Item with Start Receipt",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-name", required=True)
    parser.add_argument("--author", required=True)
    parser.add_argument("--pull-request-url", default="")
    parser.add_argument("--head", default="")
    args = parser.parse_args()
    result = decision(args.event_name, args.author, args.pull_request_url, args.head)
    print(json.dumps(result, sort_keys=True))
    return 1 if result["state"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
