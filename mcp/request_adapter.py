"""MCP request adaptation for command checks."""

from __future__ import annotations

from typing import Any

try:
    from .command_policy import CheckCommand, build_check_command
except ImportError:  # Support direct loading by the stdio server.
    from command_policy import CheckCommand, build_check_command

MAX_CHECK_VALUE_LENGTH = 512


def adapt_check_arguments(arguments: dict[str, Any]) -> CheckCommand:
    """Convert MCP arguments into the policy-layer command object."""

    value = arguments.get("value")
    if not isinstance(value, str) or not value:
        raise ValueError("The 'value' argument must be a non-empty string")
    if len(value) > MAX_CHECK_VALUE_LENGTH:
        raise ValueError("The 'value' argument is too long")
    return build_check_command(value)
