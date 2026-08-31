"""Policy layer for the intentionally vulnerable command-check fixture."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CheckCommand:
    """A local echo-style command assembled for the demonstration fixture."""

    value: str


def build_check_command(value: str) -> CheckCommand:
    """Build a local echo command from the untrusted check value.

    This deliberately does not shell-escape ``value``. The resulting data flow is
    used by the fixture to exercise cross-file CWE-78 detection.
    """

    return CheckCommand(value=f'echo config-check: "{value}"')
