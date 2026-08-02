"""Compatibility CLI composition helpers.

The legacy executable owns argument parsing during the staged migration; this
module provides the application seam and intentionally performs no writes.
"""

from installer.application import InstallationApplication, InstallationRequest


def prepare_request(request: InstallationRequest) -> None:
    """Exercise the read-only application boundary before compatibility execution."""

    InstallationApplication().inspect_and_plan(request)
