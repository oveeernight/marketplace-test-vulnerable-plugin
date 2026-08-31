"""Process boundary for local command checks."""

from __future__ import annotations

import subprocess

try:
    from .command_policy import CheckCommand
except ImportError:  # Support direct loading by the stdio server.
    from command_policy import CheckCommand


def run_check_command(command: CheckCommand) -> str:
    """Run the local check command and return its output."""

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
