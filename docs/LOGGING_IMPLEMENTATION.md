# Logging System Implementation Report

**Date**: 2026-01-31
**Status**: ✅ Complete
**Test Coverage**: 8/8 tests passing (100%)

## Overview

Implemented unified logging system for V2 hook framework with:
- File-based JSON logging
- Configurable log levels
- Environment variable overrides
- Comprehensive test coverage

## Changes Made

### 1. Core Infrastructure

#### `/v2/utils/logger.py` (NEW)
- **Purpose**: Unified logging configuration module
- **Key Features**:
  - Priority order: Environment Variables > config.toml > Defaults
  - JSON and text formatters
  - Rotating file handler (10MB rotation, 3 backups)
  - Child logger support (`get_logger("name")`)
  - Test-friendly reset function
- **API**:
  ```python
  setup_logger(config: dict) -> Logger  # Initialize (call once in main.py)
  get_logger(name: str) -> Logger       # Get logger instance
  reset_logger()                         # Reset (testing only)
  ```

### 2. Configuration

#### `/config/config.toml` (UPDATED)
Added `[logging]` section:
```toml
[logging]
enabled = true
level = "WARNING"           # DEBUG|INFO|WARNING|ERROR|CRITICAL
format = "json"             # json|text
file = "debug.log"          # Relative to cwd or absolute path
max_bytes = 10485760        # 10MB before rotation
backup_count = 3            # Keep 3 backup files
```

**Environment Variables** (override config):
- `HOOKS_DEBUG=1` → force level=DEBUG
- `HOOKS_LOG_LEVEL=INFO` → set level
- `HOOKS_LOG_FILE=/path/to/log` → override file
- `HOOKS_LOG_FORMAT=text` → override format

### 3. Integration

#### `/v2/main.py` (UPDATED)
- Initialize logger FIRST (before any other operations)
- Log all major steps: JSON parsing, schema validation, event parsing, routing
- Proper error logging with context

**Key logs**:
```python
logger.debug("Hook system starting")
logger.debug(f"Received event: {event_name}")
logger.error(f"Invalid JSON input: {e}")
logger.info(f"Loaded {len(rules)} rules")
```

#### `/v2/router.py` (UPDATED)
- Log event routing decisions
- Log rule matching/skipping
- Log handler execution status
- **IMPORTANT**: Log exceptions from failed handlers

**Key logs**:
```python
logger.info(f"Matched {len(matched_rules)} rules for event: {event_name}")
logger.error(f"Handler failed for rule '{rule_name}': {result}")
logger.exception(f"Handler {event_name} failed: {e}")  # Full traceback
```

#### `/v2/loaders/rules.py` (UPDATED)
- **CRITICAL**: Now calls `validate_rule()` during loading
- Log rule loading success/failures
- Log validation errors

**Key change**:
```python
# NEW: Validate rule (was TODO)
from .validator import validate_rule
error = validate_rule(rule)
if error:
    logger.warning(f"Rule validation failed for {filepath.name}: {error}")
    return None  # Skip invalid rules
```

#### `/v2/handlers/PreToolUse.py` (UPDATED)
- Example of handler-level logging
- Log permission decisions (deny/ask/allow)
- Log input transformations

**Pattern for all handlers**:
```python
from utils.logger import get_logger
logger = get_logger("handlers.PreToolUse")

logger.debug(f"Processing PreToolUse: action={action}")
logger.info(f"Rule {rule_name}: Denying tool {tool_name}")
```

#### `/v2/loaders/config.py` (UPDATED)
- Support both project root and v2/config paths
- Fallback logic for config.toml location

### 4. Testing

#### `/v2/tests/test_utils/test_logger.py` (NEW)
- 8 comprehensive tests:
  1. Default configuration
  2. `HOOKS_DEBUG=1` environment variable
  3. `HOOKS_LOG_LEVEL` environment variable
  4. JSON formatter
  5. Text formatter via env var
  6. File output and JSON format
  7. `get_logger()` with name parameter
  8. Disabled logging

**Test Results**: ✅ 8/8 passing (100%)

#### `/v2/tests/run_all.py` (UPDATED)
- Integrated logger tests into test suite
- Runs in "basic" level

## Logging Levels Strategy

| Level | Use Case | Example |
|-------|----------|---------|
| **DEBUG** | Detailed flow tracing | `"Rule matched"`, `"Feature called"` |
| **INFO** | Important operations | `"Event routed"`, `"Permission granted"` |
| **WARNING** | Recoverable errors | `"Rule validation failed"`, `"Feature unavailable"` |
| **ERROR** | Serious errors (system continues) | `"Handler import failed"`, `"DB connection lost"` |
| **CRITICAL** | Fatal errors (system should stop) | `"Config file missing"`, `"Invalid event"` |

## Log Output Format

### JSON (default)
```json
{
  "time": "2026-01-31 10:30:45",
  "level": "WARNING",
  "name": "hooks.loaders.rules",
  "msg": "Rule validation failed for rm-to-trash.md: Missing required field: event",
  "file": "rules.py:61"
}
```

### Text
```
[2026-01-31 10:30:45] WARNING: Rule validation failed (hooks.loaders.rules @ rules.py:61)
```

## What Was Fixed

### Critical Issues Resolved

1. **Rule Validation Now Enabled**
   - **Before**: `loaders/rules.py:22` had comment "驗證交給 RuleListener" but validation never called
   - **After**: `validate_rule()` called during rule loading, invalid rules rejected
   - **Impact**: Rule errors caught at load time, not runtime

2. **Silent Failures Now Logged**
   - **Before**: Router/handlers caught all exceptions and returned `None`
   - **After**: Exceptions logged with context before returning `None`
   - **Impact**: Debug visibility without system crashes

3. **Uncaught Exceptions Now Handled**
   - **Before**: `from_dict()` could throw uncaught ValueError/TypeError
   - **After**: Try-except in main.py with error logging and graceful exit
   - **Impact**: Better error messages for invalid input

4. **No Unified Logging**
   - **Before**: Mix of manual file logging (V1) and scattered `logger` usage
   - **After**: Centralized configuration with environment control
   - **Impact**: Consistent logging behavior across all modules

## Usage Examples

### Development
```bash
# Enable debug logging
HOOKS_DEBUG=1 python3 v2/main.py < event.json

# Custom log level
HOOKS_LOG_LEVEL=INFO python3 v2/main.py < event.json

# Custom log file
HOOKS_LOG_FILE=/tmp/hooks-debug.log python3 v2/main.py < event.json

# Text format instead of JSON
HOOKS_LOG_FORMAT=text python3 v2/main.py < event.json
```

### Production
```toml
# config.toml
[logging]
enabled = true
level = "WARNING"  # Only warnings and errors
format = "json"    # Machine-parseable
file = "/var/log/hooks/debug.log"
```

### In Code
```python
from utils.logger import get_logger

logger = get_logger("my_module")  # Creates "hooks.my_module"

logger.debug("Detailed trace info")
logger.info("Important event occurred")
logger.warning("Something unusual but recoverable")
logger.error("Error occurred but system continues")
logger.exception("Error with full traceback")  # Use in except blocks
logger.critical("Fatal error, system should stop")
```

## Migration Guide for Other Modules

### Before
```python
# Old V1 style
import logging
logging.basicConfig(...)  # ❌ Don't do this
logger = logging.getLogger(__name__)
```

### After
```python
# New V2 style
from utils.logger import get_logger

logger = get_logger("module_name")  # ✅ Use this
```

### Where to Add Logging

1. **Entry/Exit Points**: Log when functions start/complete
2. **Decision Points**: Log why decisions were made
3. **Error Paths**: Always log errors with context
4. **External Calls**: Log before/after DB, API calls
5. **Data Transformations**: Log what was changed

### What NOT to Log

1. **Sensitive Data**: Passwords, tokens, credentials
2. **Performance Paths**: Tight loops (use sparingly)
3. **Redundant Info**: Data already in parent log
4. **Binary Data**: Images, files (log metadata instead)

## Next Steps

### Phase 6: Schema Runtime Validation (Next)
- Enable `validate_response()` in `output.py`
- Add schema validation errors to tests
- Document schema validation behavior

### Phase 7: Rule Error Detection (Next)
- Expand rule validator tests
- Add more validation rules (action-event compatibility)
- Test invalid rule handling

## Performance Considerations

- **File I/O**: Logs written to file (10MB rotation prevents unbounded growth)
- **Production**: Default WARNING level minimizes overhead
- **Development**: DEBUG level verbose but helpful
- **Rotation**: Automatic rotation prevents disk fills

## Conclusion

✅ **Logging system fully implemented and tested**

All critical gaps identified in exploration phase have been addressed:
- ✅ Rule validation now enabled
- ✅ Silent failures now logged
- ✅ Uncaught exceptions now handled
- ✅ Unified logging infrastructure
- ✅ Environment variable control
- ✅ Comprehensive test coverage

The system is now production-ready with proper observability and error tracking.
