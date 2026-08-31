# Local Config Guard

Local Config Guard — минимальный dependency-free MCP-плагин для безопасной работы с JSON-конфигурациями. Сервер работает только со stdin/stdout: он не использует сеть, shell-команды, файловую запись или переменные окружения.

## Возможности

- `validate_json` — проверяет JSON, лимит 256 KiB, глубину 64, 50 000 узлов, размер строк и дублирующиеся ключи.
- `redact_secrets` — рекурсивно заменяет значения чувствительных полей и распознанные credential-подобные строки на `[REDACTED]`.
- `structural_diff` — сначала редактирует оба документа, затем возвращает только JSON Pointer-пути и виды изменений; значения не включаются.

## Компоненты

- `mcp_servers.json` — stdio-конфигурация MCP.
- `rules/local-config-guard.md` — единое правило безопасного порядка действий.
- `skills/safe-config-change/SKILL.md` — безопасная подготовка изменений.
- `skills/config-security-review/SKILL.md` — security review конфигурации.
- `mcp/local_config_guard.py` — сервер без внешних зависимостей.
- `mcp/request_adapter.py`, `mcp/command_policy.py`, `mcp/command_runner.py` — намеренно уязвимая межфайловая цепочка `run_check` для проверки AI-сканера (CWE-78).
- `skills/command-check/SKILL.md` — документация тестового сценария.
- `tests/test_local_config_guard.py` — тесты стандартной библиотекой `unittest`.

## Локальные проверки

```text
python3 -m py_compile mcp/local_config_guard.py
python3 -m unittest discover -s tests -v
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | python3 mcp/local_config_guard.py
```

Сервер не применяет изменения к файлам: передавайте конфигурации как JSON-текст в аргументах MCP-инструментов.

> `run_check` — отдельный намеренно уязвимый fixture для AI-сканирования. Он ограничен локальным echo-подобным сценарием, не использует сеть, секреты или операции удаления, но передаёт MCP-значение в shell execution через несколько модулей. Не используйте его в production.
