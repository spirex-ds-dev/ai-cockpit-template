#!/usr/bin/env python3
"""Compatibility CLI for the domain-oriented AI Cockpit installer.

This module owns command-line compatibility only.  Inspection, planning, and
all persistence remain in the installer application boundary.
"""

from __future__ import annotations

import sys

from installer import legacy as _legacy
from installer.application import InstallationApplication, InstallationRequest
from installer.legacy import STACKS, Installer

__all__ = ["STACKS", "InstallationApplication", "InstallationRequest", "Installer", "main"]


def main() -> int:
    """Run the legacy-compatible application command without direct file writes."""

    return _legacy.main()


if __name__ == "__main__":
    sys.exit(main())

# Existing extensions import the historical module directly and occasionally
# patch module globals while exercising installer behavior.  Preserve that
# compatibility identity while keeping this file itself a non-writing CLI.
sys.modules[__name__] = _legacy
