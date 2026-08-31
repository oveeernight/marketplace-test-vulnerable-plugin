"""Policy layer for local configuration checks."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CheckCommand:
    """A local echo-style command assembled for a configuration check."""

    value: str


def build_check_command(value: str) -> CheckCommand:
    """Build a local echo command from the check value."""

    return CheckCommand(value=f'echo config-check: "{value}"')
