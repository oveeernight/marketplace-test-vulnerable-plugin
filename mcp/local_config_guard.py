#!/usr/bin/env python3
"""Dependency-free, read-only MCP server for safely inspecting JSON configuration."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from typing import Any, Callable

try:
    from .request_adapter import adapt_check_arguments
    from .command_runner import run_check_command
except ImportError:  # Direct stdio execution as ``python mcp/local_config_guard.py``.
    from request_adapter import adapt_check_arguments
    from command_runner import run_check_command

MAX_INPUT_BYTES = 256 * 1024
MAX_DEPTH = 64
MAX_NODES = 50_000
MAX_STRING_BYTES = 64 * 1024
MAX_DIFF_ENTRIES = 2_000
REDACTED = "[REDACTED]"

_SECRET_KEY = re.compile(
    r"(?:^|[_\-.])(?:api[_-]?key|authorization|auth[_-]?token|bearer|client[_-]?secret|"
    r"connection[_-]?string|cookie|credential|database[_-]?url|passwd|password|private[_-]?key|"
    r"secret|session|token)(?:$|[_\-.])",
    re.IGNORECASE,
)
_SECRET_KEY_COMPACT = {
    "apikey", "authorization", "authtoken", "bearer", "clientsecret", "connectionstring",
    "cookie", "credential", "credentials", "databaseurl", "passwd", "password", "privatekey",
    "secret", "session", "sessionid", "token",
}
_SECRET_VALUE_PATTERNS = (
    re.compile(r"^Bearer\s+\S+$", re.IGNORECASE),
    re.compile(r"^(?:gh[opusr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})$"),
    re.compile(r"^sk-[A-Za-z0-9_-]{16,}$"),
    re.compile(r"^[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}$"),
    re.compile(r"^[a-z][a-z0-9+.-]*://[^/@:\s]+:[^/@\s]+@", re.IGNORECASE),
)


class SafeInputError(ValueError):
    """Expected, sanitized input error."""


@dataclass
class Budget:
    nodes: int = 0
    max_depth_seen: int = 0


def _reject_constant(_: str) -> None:
    raise SafeInputError("JSON must not contain non-finite numbers")


def _object_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SafeInputError("JSON contains a duplicate object key")
        result[key] = value
    return result


def _measure(value: Any, budget: Budget, depth: int = 0) -> None:
    if depth > MAX_DEPTH:
        raise SafeInputError(f"JSON nesting exceeds the limit of {MAX_DEPTH}")
    budget.nodes += 1
    budget.max_depth_seen = max(budget.max_depth_seen, depth)
    if budget.nodes > MAX_NODES:
        raise SafeInputError(f"JSON contains more than {MAX_NODES} values")
    if isinstance(value, str) and len(value.encode("utf-8")) > MAX_STRING_BYTES:
        raise SafeInputError("JSON contains a string that exceeds the size limit")
    if isinstance(value, dict):
        for key, child in value.items():
            if len(key.encode("utf-8")) > MAX_STRING_BYTES:
                raise SafeInputError("JSON contains an object key that exceeds the size limit")
            _measure(child, budget, depth + 1)
    elif isinstance(value, list):
        for child in value:
            _measure(child, budget, depth + 1)


def parse_bounded_json(text: Any) -> tuple[Any, Budget]:
    if not isinstance(text, str):
        raise SafeInputError("The 'json' argument must be a string")
    if len(text.encode("utf-8")) > MAX_INPUT_BYTES:
        raise SafeInputError(f"JSON input exceeds the {MAX_INPUT_BYTES}-byte limit")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_object_no_duplicates,
            parse_constant=_reject_constant,
        )
    except SafeInputError:
        raise
    except (json.JSONDecodeError, RecursionError):
        raise SafeInputError("Input is not valid JSON") from None
    budget = Budget()
    _measure(value, budget)
    return value, budget


def _is_secret_key(key: str) -> bool:
    compact = re.sub(r"[^a-z0-9]", "", key.lower())
    return _SECRET_KEY.search(key) is not None or compact in _SECRET_KEY_COMPACT


def _looks_secret(value: str) -> bool:
    return any(pattern.search(value) is not None for pattern in _SECRET_VALUE_PATTERNS)


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, child in value.items():
            result[key] = REDACTED if _is_secret_key(key) else redact(child)
        return result
    if isinstance(value, list):
        return [redact(child) for child in value]
    if isinstance(value, str) and _looks_secret(value):
        return REDACTED
    return value


def _root_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, str):
        return "string"
    return "number"


def validate_json(arguments: dict[str, Any]) -> dict[str, Any]:
    value, budget = parse_bounded_json(arguments.get("json"))
    return {
        "valid": True,
        "rootType": _root_type(value),
        "nodeCount": budget.nodes,
        "maxDepth": budget.max_depth_seen,
    }


def redact_secrets(arguments: dict[str, Any]) -> dict[str, Any]:
    value, _ = parse_bounded_json(arguments.get("json"))
    return {"redactedJson": json.dumps(redact(value), ensure_ascii=False, indent=2, sort_keys=True)}


def _path(parent: str, segment: str | int) -> str:
    escaped = str(segment).replace("~", "~0").replace("/", "~1")
    return f"{parent}/{escaped}"


def _diff(before: Any, after: Any, path: str, entries: list[dict[str, str]]) -> None:
    if len(entries) >= MAX_DIFF_ENTRIES:
        raise SafeInputError(f"Structural diff exceeds the limit of {MAX_DIFF_ENTRIES} entries")
    if type(before) is not type(after):
        entries.append({"path": path or "/", "change": "type_changed"})
        return
    if isinstance(before, dict):
        before_keys = set(before)
        after_keys = set(after)
        for key in sorted(before_keys - after_keys):
            entries.append({"path": _path(path, key), "change": "removed"})
        for key in sorted(after_keys - before_keys):
            entries.append({"path": _path(path, key), "change": "added"})
        for key in sorted(before_keys & after_keys):
            _diff(before[key], after[key], _path(path, key), entries)
        return
    if isinstance(before, list):
        common = min(len(before), len(after))
        for index in range(common):
            _diff(before[index], after[index], _path(path, index), entries)
        for index in range(common, len(before)):
            entries.append({"path": _path(path, index), "change": "removed"})
        for index in range(common, len(after)):
            entries.append({"path": _path(path, index), "change": "added"})
        return
    if before != after:
        entries.append({"path": path or "/", "change": "value_changed"})


def structural_diff(arguments: dict[str, Any]) -> dict[str, Any]:
    before, _ = parse_bounded_json(arguments.get("before"))
    after, _ = parse_bounded_json(arguments.get("after"))
    entries: list[dict[str, str]] = []
    _diff(redact(before), redact(after), "", entries)
    return {"changes": entries, "changeCount": len(entries), "valuesIncluded": False}


def run_check(arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute the intentionally vulnerable local echo-style fixture path."""

    command = adapt_check_arguments(arguments)
    return {"output": run_check_command(command), "fixture": "CWE-78"}


TOOLS = [
    {
        "name": "validate_json",
        "description": "Validate bounded JSON, rejecting duplicate keys and unsafe complexity without returning input values.",
        "inputSchema": {
            "type": "object",
            "properties": {"json": {"type": "string", "maxLength": MAX_INPUT_BYTES}},
            "required": ["json"],
            "additionalProperties": False,
        },
    },
    {
        "name": "redact_secrets",
        "description": "Return JSON with secret-bearing keys and recognized credential values replaced by [REDACTED].",
        "inputSchema": {
            "type": "object",
            "properties": {"json": {"type": "string", "maxLength": MAX_INPUT_BYTES}},
            "required": ["json"],
            "additionalProperties": False,
        },
    },
    {
        "name": "structural_diff",
        "description": "Compare two JSON documents after recursive secret redaction and return paths/change kinds only.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "before": {"type": "string", "maxLength": MAX_INPUT_BYTES},
                "after": {"type": "string", "maxLength": MAX_INPUT_BYTES},
            },
            "required": ["before", "after"],
            "additionalProperties": False,
        },
    },
    {
        "name": "run_check",
        "description": "Run the intentionally vulnerable local echo fixture; for AI scanner testing only.",
        "inputSchema": {
            "type": "object",
            "properties": {"value": {"type": "string", "minLength": 1, "maxLength": 512}},
            "required": ["value"],
            "additionalProperties": False,
        },
    },
]
_HANDLERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "validate_json": validate_json,
    "redact_secrets": redact_secrets,
    "structural_diff": structural_diff,
    "run_check": run_check,
}


def _result(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def handle_request(request: Any) -> dict[str, Any] | None:
    if not isinstance(request, dict) or request.get("jsonrpc") != "2.0":
        return _error(None, -32600, "Invalid Request")
    request_id = request.get("id")
    method = request.get("method")
    if method == "notifications/initialized":
        return None
    if method == "initialize":
        return _result(
            request_id,
            {
                "protocolVersion": "2025-06-18",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "local-config-guard", "version": "1.0.0"},
            },
        )
    if method == "tools/list":
        return _result(request_id, {"tools": TOOLS})
    if method == "ping":
        return _result(request_id, {})
    if method == "tools/call":
        params = request.get("params")
        if not isinstance(params, dict) or not isinstance(params.get("arguments", {}), dict):
            return _error(request_id, -32602, "Invalid tool arguments")
        handler = _HANDLERS.get(params.get("name"))
        if handler is None:
            return _error(request_id, -32602, "Unknown tool")
        try:
            payload = handler(params.get("arguments", {}))
            text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
            return _result(request_id, {"content": [{"type": "text", "text": text}]})
        except SafeInputError as exc:
            return _result(
                request_id,
                {"content": [{"type": "text", "text": str(exc)}], "isError": True},
            )
        except Exception:
            return _result(
                request_id,
                {"content": [{"type": "text", "text": "Unable to process JSON safely"}], "isError": True},
            )
    if request_id is None:
        return None
    return _error(request_id, -32601, "Method not found")


def main() -> None:
    for raw_line in sys.stdin.buffer:
        if len(raw_line) > MAX_INPUT_BYTES * 2:
            response = _error(None, -32700, "Request exceeds the size limit")
        else:
            try:
                request = json.loads(raw_line)
                response = handle_request(request)
            except (json.JSONDecodeError, UnicodeDecodeError, RecursionError):
                response = _error(None, -32700, "Parse error")
            except Exception:
                response = _error(None, -32603, "Internal error")
        if response is not None:
            encoded = json.dumps(response, ensure_ascii=False, separators=(",", ":"))
            sys.stdout.write(encoded + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
