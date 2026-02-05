# Contributing to MindNext Hooks V2

Thank you for your interest in contributing to MindNext Hooks V2! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Style](#code-style)
- [Testing](#testing)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

- Be respectful and constructive
- Focus on technical merit
- Welcome newcomers and help them learn
- Collaborate in good faith

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- Familiarity with Claude Code Hooks API

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/your-org/mindnext-hooks.git
cd mindnext-hooks/v2

# Install dependencies
pip install -r requirements.txt

# Install optional dev dependencies
pip install jsonschema  # For schema validation

# Verify installation
make test
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/my-feature
# or
git checkout -b fix/bug-description
```

### 2. Make Changes

Follow these principles:

- **Single Responsibility**: Each change should address one concern
- **Read Before Edit**: Always read files before modifying them
- **Test Your Changes**: Write tests for new functionality
- **Document**: Update relevant documentation

### 3. Test Changes

```bash
# Run all tests
make test

# Run specific test level
python3 tests/run_all.py --level basic
python3 tests/run_all.py --level rules

# Validate rules
make validate-rules

# Enable debug logging
HOOKS_DEBUG=1 make run < test_event.json
```

## Code Style

### Python Style Guide

Follow PEP 8 with these specifics:

```python
# Use type hints
def process(rule: Dict[str, Any]) -> Optional[HookResult]:
    """Process rule and return result"""
    pass

# Use meaningful names
event_name = payload.get('hook_event_name')  # Good
e = payload.get('hook_event_name')           # Bad

# Keep functions focused (under 50 lines)
# Add docstrings to public functions
# Use context managers for resources
```

### Naming Conventions

**IMPORTANT**: Use official Claude Code Hooks API names

```yaml
# Rule config - use official camelCase
---
name: "my-rule"
event: PreToolUse
updatedInput:
  field: command
---
```

```python
# Python code - use snake_case
updated_input_config = rule.get('updatedInput')
updated_input = apply_transformation(updated_input_config)

# Output JSON - use official camelCase
return HookResult(
    permission='allow',
    updated_input=updated_input  # Converted to updatedInput in JSON
)
```

### File Organization

```
v2/
├── handlers/           # Event handlers (one per event)
├── features/           # Feature modules (tags, agents, etc.)
├── loaders/            # Config/rule loaders
├── utils/              # Shared utilities
├── config/
│   ├── config.toml     # System configuration
│   ├── rules/          # Rule definitions (*.md)
│   └── schema/         # JSON schemas
└── tests/              # Test suite
```

## Testing

### Test Structure

```python
from framework import TestRunner, TestResult, TestLevel

def run_my_tests(runner: TestRunner):
    """Test description"""
    runner.log("="*60)
    runner.log("My Tests")
    runner.log("="*60)

    # Test case
    result = my_function()
    passed = result == expected

    runner.report.add(TestResult(
        name="test_my_function",
        level=TestLevel.BASIC,
        passed=passed,
        message="Description of what was tested"
    ))
```

### Adding Tests

1. **Unit Tests**: Test individual functions
2. **Integration Tests**: Test handler workflows
3. **Rule Validation Tests**: Test rule loading/validation
4. **Schema Tests**: Test JSON schema compliance

### Test Coverage Goals

- New handlers: 100% coverage
- New features: 90%+ coverage
- Bug fixes: Add regression test

## Commit Guidelines

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test changes
- `refactor`: Code refactoring
- `chore`: Build/config changes

### Examples

```
feat(handlers): add SubagentStop handler

Implement SubagentStop event handler with block action support.
Includes comprehensive tests and logging integration.

Closes #123
```

```
fix(loaders): enable rule validation during load

Rule validation was commented out with TODO. This enables it
and adds proper error logging for invalid rules.

Fixes #456
```

### Commit Best Practices

- Use present tense ("add feature" not "added feature")
- Use imperative mood ("move cursor to..." not "moves cursor to...")
- Limit subject line to 50 characters
- Wrap body at 72 characters
- Reference issues and PRs

## Pull Request Process

### Before Submitting

1. ✅ All tests pass: `make test`
2. ✅ Rule validation passes: `make validate-rules`
3. ✅ Code follows style guide
4. ✅ Documentation updated
5. ✅ Commit messages follow guidelines

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- Describe tests added/modified
- Test results summary

## Checklist
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] Follows code style
```

### Review Process

1. Automated tests run on PR
2. Maintainer reviews code
3. Address feedback
4. Approval and merge

### What Reviewers Look For

- **Correctness**: Does it work as intended?
- **Tests**: Are changes tested?
- **Style**: Follows project conventions?
- **Documentation**: Is it documented?
- **Impact**: Any breaking changes?

## Adding New Features

### Adding a New Handler

1. Create handler file: `handlers/NewEvent.py`
2. Implement `process(rule: dict) -> Optional[HookResult]`
3. Add tests: `tests/test_handlers/test_newevent.py`
4. Update schema: `config/schema/NewEvent.json`
5. Document in `docs/`

Example:

```python
# handlers/NewEvent.py
from typing import Optional, Dict, Any
from type_defs import HookResult
from utils.context import get_event
from utils.events import NewEvent
from utils.logger import get_logger

logger = get_logger("handlers.NewEvent")

async def process(rule: Dict[str, Any]) -> Optional[HookResult]:
    """Process NewEvent"""
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
2. Write YAML frontmatter:

```yaml
---
name: "my-rule"
description: "Rule description"
enabled: true
event: PreToolUse
tool: Bash
match: "dangerous-command"
action: deny
reason: "Safety reason"
priority: 100
---

# Rule Documentation
Additional context and examples
```

3. Test validation: `make validate-rules`
4. Test with actual event: `HOOKS_DEBUG=1 make run < event.json`

## Getting Help

- 📖 Documentation: [docs/](docs/)
- 🐛 Report bugs: [GitHub Issues](https://github.com/your-org/mindnext-hooks/issues)
- 💬 Ask questions: [GitHub Discussions](https://github.com/your-org/mindnext-hooks/discussions)

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).
