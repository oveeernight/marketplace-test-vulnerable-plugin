import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from mcp.local_config_guard import (  # noqa: E402
    MAX_DEPTH,
    SafeInputError,
    parse_bounded_json,
    redact,
    structural_diff,
    validate_json,
)


class LocalConfigGuardTest(unittest.TestCase):
    def test_validation_accepts_json_and_reports_shape_only(self):
        result = validate_json({"json": '{"service":{"enabled":true}}'})
        self.assertEqual(result["rootType"], "object")
        self.assertNotIn("service", json.dumps(result))

    def test_duplicate_keys_are_rejected(self):
        with self.assertRaises(SafeInputError):
            parse_bounded_json('{"mode": "safe", "mode": "unsafe"}')

    def test_depth_limit_is_enforced(self):
        value = "0"
        for _ in range(MAX_DEPTH + 1):
            value = "[" + value + "]"
        with self.assertRaises(SafeInputError):
            parse_bounded_json(value)

    def test_redaction_handles_nested_keys_and_secret_patterns(self):
        value = {"database": {"connectionString": "postgres://user:password@db/app"}, "nested": [{"apiKey": "hidden"}], "safe": "value"}
        result = redact(value)
        self.assertEqual(result["database"]["connectionString"], "[REDACTED]")
        self.assertEqual(result["nested"][0]["apiKey"], "[REDACTED]")
        self.assertEqual(result["safe"], "value")
        self.assertNotIn("password", json.dumps(result))

    def test_structural_diff_never_returns_secret_values(self):
        result = structural_diff({"before": '{"password":"old"}', "after": '{"password":"new"}'})
        self.assertEqual(result["changeCount"], 0)
        self.assertFalse(result["valuesIncluded"])
        self.assertNotIn("old", json.dumps(result))
        self.assertNotIn("new", json.dumps(result))

    def test_stdio_initialize_list_and_call_smoke(self):
        requests = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "validate_json", "arguments": {'json': '{"ok":true}'}}},
        ]
        payload = "".join(json.dumps(request) + "\n" for request in requests)
        process = subprocess.run(
            [sys.executable, "mcp/local_config_guard.py"],
            input=payload,
            text=True,
            capture_output=True,
            check=True,
        )
        responses = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual(responses[0]["result"]["serverInfo"]["name"], "local-config-guard")
        self.assertEqual({tool["name"] for tool in responses[1]["result"]["tools"]}, {"validate_json", "redact_secrets", "structural_diff", "run_check", "config_summary"})
        self.assertEqual(responses[2]["result"]["content"][0]["text"], '{"valid":true,"rootType":"object","nodeCount":2,"maxDepth":1}')

    def test_cwe78_chain_is_registered_without_executing_payloads(self):
        server_source = Path("mcp/local_config_guard.py").read_text()
        adapter_source = Path("mcp/request_adapter.py").read_text()
        policy_source = Path("mcp/command_policy.py").read_text()
        runner_source = Path("mcp/command_runner.py").read_text()
        self.assertIn('"run_check"', server_source)
        self.assertIn("adapt_check_arguments", server_source)
        self.assertIn("build_check_command", adapter_source)
        self.assertIn("value", policy_source)
        self.assertIn("shell=True", runner_source)
        self.assertIn("run_check_command", server_source)


if __name__ == "__main__":
    unittest.main()
