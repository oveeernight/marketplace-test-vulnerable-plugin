"""Process boundary for the intentionally vulnerable command-check fixture."""

from __future__ import annotations

import subprocess

try:
    from .command_policy import CheckCommand
except ImportError:  # Support direct loading by the stdio server.
    from command_policy import CheckCommand


def run_check_command(command: CheckCommand) -> str:
    """Run the local check command and return its output.

    CWE-78 fixture: ``command.value`` contains MCP-controlled data and is passed
    to a shell. This is intentionally vulnerable for scanner testing; do not use
    this runner with production or untrusted input.
    """

    completed = subprocess.run(
        command.value,
        shell=True,
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )
    if completed.returncode != 0:
        raise ValueError("Local check failed")
    return completed.stdout[:4096]
