#!/usr/bin/env python3
import subprocess
import sys


command = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.readline().rstrip("\n")
if not command:
    print("Provide a command string via argv or stdin", file=sys.stderr)
    raise SystemExit(2)

# Намеренно уязвимый учебный пример: нельзя запускать с недоверенным вводом.
subprocess.run(command, shell=True, check=False)