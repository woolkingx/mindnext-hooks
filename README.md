# MindNext Hooks V2

[![Tests](https://img.shields.io/badge/tests-125%2F125-brightgreen)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-93.5%25-brightgreen)](tests/test_report.json)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
![License](https://img.shields.io/badge/license-MIT-blue)

Production-ready hook system for [Claude Code CLI](https://github.com/anthropics/claude-code) with comprehensive logging, validation, and testing infrastructure.

v2 is a fully self-contained version. It does not depend on sibling versions (`v1`, `v1-5`) at runtime.

## Features

- ✅ **12 Event Handlers** - Full Claude Code Hooks API coverage
- ✅ **Unified Logging** - JSON/text formats with rotation and env control
- ✅ **Schema Validation** - Runtime input/output validation
- ✅ **Rule Validation** - Pre-deployment error detection
- ✅ **125 Tests** - Comprehensive test coverage (93.5%)
- ✅ **Type-Safe** - Full type hints with dataclass events
- ✅ **Async Support** - Concurrent rule processing
- ✅ **Production Ready** - Error handling, logging, monitoring

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/woolkingx/mindnext-hooks.git
cd mindnext-hooks

# Install dependencies
pip install -r requirements.txt

# Configure (v2-local)
cp config/config.toml.example config/config.toml
# Edit config.toml with your settings
```

### Basic Usage

```bash
# Single-run (stdin -> stdout)
make run

# Enable debug logging
HOOKS_DEBUG=1 make run < event.json

# Validate output schema (development)
HOOKS_VALIDATE_OUTPUT=1 make run < event.json

# Smoke test
make smoke
```

### Testing

```bash
# Run all tests
make test

# Run specific test level (advanced)
python3 tests/run_all.py --level basic
python3 tests/run_all.py --level rules

# Generate JSON report
make test-json

# Validate rules before deployment
make validate-rules
```

## Architecture

```
.
├── main.py              # Entry point: stdin → router → output → stdout
├── router.py            # Event routing with concurrent rule processing
├── output.py            # Response merging and JSON output
├── type_defs.py         # Type definitions (HookResult, etc.)
│
├── handlers/            # Event handlers (12 events)
│   ├── PreToolUse.py
│   ├── PostToolUse.py
│   ├── UserPromptSubmit.py
│   └── ...
│
├── features/            # Feature modules
│   ├── tags/           # Tag management (todo, note, search)
│   ├── agents.py       # Agent suggestions
│   ├── skills.py       # Skill recommendations
│   └── ...
│
├── loaders/            # Configuration loaders
│   ├── config.py       # config.toml loader
│   ├── rules.py        # Rule file loader with validation
│   └── validator.py    # Rule validation logic
│
├── utils/              # Utilities
│   ├── logger.py       # Unified logging system
│   ├── events.py       # Type-safe event classes
│   ├── schema_validator.py  # JSON Schema validation
│   ├── db.py           # ArangoDB interface
│   └── ...
│
├── config/
│   ├── config.toml     # System configuration
│   ├── rules/          # Rule definitions (*.md)
│   └── schema/         # JSON schemas (12 events)
│
├── tests/              # Test suite (125 tests)
│   ├── run_all.py      # Unified test runner
│   ├── test_*.py       # Test modules
│   └── framework.py    # Test framework
│
└── docs/               # Documentation
    ├── ARCHITECTURE.md
    ├── LOGGING_IMPLEMENTATION.md
    ├── PHASE6_PHASE7_REPORT.md
    └── ...
```

## Configuration

### Logging

Configure in `config/config.toml`:

```toml
[logging]
enabled = true
level = "INFO"         # default runtime level; use DEBUG for development
format = "json"        # json|text
file = "log/debug.log" # Default inside v2/
max_bytes = 10485760   # 10MB rotation
backup_count = 3       # Keep 3 backups
```

Override with environment variables:

```bash
HOOKS_DEBUG=1              # Force DEBUG level
HOOKS_LOG_LEVEL=INFO       # Set specific level
HOOKS_LOG_FILE=/tmp/hooks.log  # Custom log file
HOOKS_LOG_FORMAT=text      # Text format instead of JSON
```

### Rules

Rules are defined in `config/rules/*.md` with YAML frontmatter:

```yaml
---
name: "deny-dangerous-commands"
description: "Block dangerous system commands"
enabled: true
event: PreToolUse
tool: Bash
match: "rm -rf|mkfs|dd"
action: deny
reason: "Dangerous command blocked for safety"
priority: 100
---

# Rule Documentation
Additional context and examples...
```

See [config/rules/RULES.md](config/rules/RULES.md) for full documentation.

## Development

### Running Tests

```bash
# All tests
make test

# Specific levels
python3 tests/run_all.py --level basic     # Basic smoke tests
python3 tests/run_all.py --level json      # Schema validation tests
python3 tests/run_all.py --level rules     # Rule loading tests
python3 tests/run_all.py --level integration  # End-to-end tests

# Verbose output
python3 tests/run_all.py --verbose

# JSON report
make test-json
```

### Adding a New Handler

1. Create handler file: `handlers/NewEvent.py`
2. Implement `process(rule: dict) -> Optional[HookResult]`
3. Add tests: `tests/test_handlers/test_newevent.py`
4. Update schema: `config/schema/NewEvent.json`

Example:

```python
# handlers/NewEvent.py
from type_defs import HookResult
from utils.context import get_event
from utils.logger import get_logger

logger = get_logger("handlers.NewEvent")

async def process(rule: dict) -> Optional[HookResult]:
    event = get_event()
    logger.debug(f"Processing NewEvent: {rule.get('name')}")

    # Your logic here

    return HookResult(
        event_name='NewEvent',
        additional_context="Generated context"
    )
```

### Adding a New Rule

1. Create rule file: `config/rules/my-rule.md`
2. Write YAML frontmatter with required fields
3. Test validation: `make validate-rules`
4. Test with actual event: `HOOKS_DEBUG=1 make run < event.json`

### Pre-Deployment Validation

```bash
# Validate all rules
make validate-rules

# Check specific rule loads correctly
HOOKS_LOG_LEVEL=DEBUG make run < event.json | grep "my-rule"

# Validate schema compliance
HOOKS_VALIDATE_OUTPUT=1 make run < event.json
```

## Testing

### Test Structure

```
tests/
├── Level 1: Basic       - 19 smoke tests (12 events + utilities)
├── Level 2: JSON        - 14 schema validation tests
├── Level 3: Rules       - 74 rule loading/validation tests
├── Level 4: Integration - End-to-end workflow tests
└── Utils                - 8 logger tests, 12 validation tests
```

### Test Coverage

| Component | Tests | Coverage |
|-----------|-------|----------|
| Event Handlers | 12 | 100% |
| Schema Validation | 14 | 100% |
| Rule Loading | 62 | 95.9% |
| Rule Validation | 12 | 100% |
| Logger | 8 | 100% |
| Integration | 4 | 100% |
| **Total** | **125** | **93.5%** |

### CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python3 v2/tests/run_all.py --json
      - name: Validate rules
        run: python3 v2/tests/test_rule_validation.py
```

## Documentation

- [Architecture Guide](docs/ARCHITECTURE.md) - System design and data flow
- [Logging Implementation](docs/LOGGING_IMPLEMENTATION.md) - Logging system details
- [Phase 6 & 7 Report](docs/PHASE6_PHASE7_REPORT.md) - Schema & rule validation
- [Test Summary](docs/TEST_SUMMARY.md) - Test framework overview
- [Rule Writing Guide](config/rules/RULES.md) - How to write rules

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'jsonschema'`
```bash
# Install optional dependency
pip install jsonschema
```

**Issue**: Rules not loading
```bash
# Check validation errors
HOOKS_LOG_LEVEL=WARNING python3 main.py < event.json
grep "Rule validation failed" log/debug.log
```

**Issue**: No output from hooks
```bash
# Enable debug logging
HOOKS_DEBUG=1 make run < event.json
# Check: Event received? Rules matched? Handler called?
```

**Issue**: Output validation failing
```bash
# This is optional - disable in production
unset HOOKS_VALIDATE_OUTPUT
# Or fix schema mismatch in handler
```

### Debug Checklist

1. ✅ Check log file exists and has content: `ls -lh log/debug.log`
2. ✅ Verify event JSON is valid: `cat event.json | jq .`
3. ✅ Check rules loaded: `grep "Successfully loaded" log/debug.log`
4. ✅ Verify rule matched: `grep "Rule.*matched" log/debug.log`
5. ✅ Check handler output: `grep "emit" log/debug.log`

## Performance

- **Rule Loading**: ~50ms for 20 rules (one-time cost)
- **Event Processing**: <10ms per event (concurrent handlers)
- **Logging Overhead**: <1ms per log entry (async I/O)
- **Memory Usage**: ~50MB baseline + ~2MB per concurrent handler

### Optimization Tips

1. **Production**: Set `level = "WARNING"` in config.toml
2. **Development**: Use `HOOKS_DEBUG=1` only when needed
3. **Testing**: Disable logging with `enabled = false`
4. **Large Logs**: Adjust `max_bytes` and `backup_count`

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Write tests for new functionality
4. Ensure all tests pass: `make test`
5. Validate rules if changed: `make validate-rules`
6. Commit with conventional commits: `feat: add new feature`
7. Push and create Pull Request

### Code Style

- Follow PEP 8
- Use type hints
- Add docstrings to public functions
- Write tests for new code (aim for 90%+ coverage)
- Use meaningful variable names
- Keep functions under 50 lines

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`

Example:
```
feat(handlers): add SubagentStop handler

Implement SubagentStop event handler with block action support.
Includes comprehensive tests and logging integration.

Closes #123
```

## License

MIT License - see [LICENSE](../LICENSE) file for details

## Acknowledgments

- [Claude Code CLI](https://github.com/anthropics/claude-code) - Hook system API
- [ArangoDB](https://www.arangodb.com/) - Graph database backend
- Contributors and testers

## Support

- 📖 Documentation: [docs/](docs/)
- 🐛 Issues: [GitHub Issues](https://github.com/your-org/mindnext-hooks/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/your-org/mindnext-hooks/discussions)

---

**Status**: Production Ready | **Version**: 2.0.0 | **Last Updated**: 2026-01-31
