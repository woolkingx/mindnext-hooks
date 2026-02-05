"""Unified Logging Configuration Module

Priority Order: Environment Variables > config.toml > Defaults

Environment Variables:
- HOOKS_DEBUG=1 → force level=DEBUG
- HOOKS_LOG_LEVEL=INFO → set level
- HOOKS_LOG_FILE=/path/to/log → override file path
- HOOKS_LOG_FORMAT=text → override format (json|text)

Usage:
    # In main.py (initialization)
    from utils.logger import setup_logger
    logger_config = config.get("logging", {})
    logger = setup_logger(logger_config)

    # In other modules
    from utils.logger import get_logger
    logger = get_logger()
    logger.info("Message")
"""
import logging
import logging.handlers
import os
import json
from typing import Optional
from pathlib import Path

# Global logger instance
_logger: Optional[logging.Logger] = None


def _resolve_log_file(raw_path: str) -> Path:
    """Resolve log path relative to app root, not current working directory."""
    app_root = Path(__file__).resolve().parent.parent
    path = Path(raw_path)

    if path.is_absolute():
        return path

    # Backward compatibility: "v2/log/debug.log" from root config
    if path.parts and path.parts[0] == app_root.name:
        path = Path(*path.parts[1:])

    return app_root / path


class JSONFormatter(logging.Formatter):
    """JSON log formatter for machine-parseable logs"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON

        Output format:
        {
            "time": "2026-01-31 10:30:45",
            "level": "WARNING",
            "name": "hooks.router",
            "msg": "Rule validation failed",
            "file": "router.py:42"
        }
        """
        log_data = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "msg": record.getMessage(),
            "file": f"{record.filename}:{record.lineno}",
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


def setup_logger(config: dict) -> logging.Logger:
    """Configure global logger instance

    This should be called ONCE at application startup (in main.py).

    Args:
        config: The [logging] section from config.toml
            - enabled (bool): Whether logging is enabled (default: True)
            - level (str): Log level (DEBUG|INFO|WARNING|ERROR|CRITICAL, default: WARNING)
            - format (str): Log format (json|text, default: json)
            - file (str): Log file path (default: debug.log)
            - max_bytes (int): Max file size before rotation (default: 10MB)
            - backup_count (int): Number of backup files to keep (default: 3)

    Returns:
        Configured logger instance

    Environment Variable Overrides:
        - HOOKS_DEBUG=1 → force level=DEBUG
        - HOOKS_LOG_LEVEL=INFO → override level
        - HOOKS_LOG_FILE=/path/to/log → override file
        - HOOKS_LOG_FORMAT=text → override format
    """
    global _logger

    # Return existing logger if already configured
    if _logger is not None:
        return _logger

    # 1. Parse configuration (env > config > default)
    enabled = config.get("enabled", True)

    # Level priority: HOOKS_DEBUG > HOOKS_LOG_LEVEL > config.level > WARNING
    if os.getenv("HOOKS_DEBUG") == "1":
        level = logging.DEBUG
    elif level_str := os.getenv("HOOKS_LOG_LEVEL"):
        level = getattr(logging, level_str.upper(), logging.WARNING)
    else:
        level_str = config.get("level", "WARNING")
        level = getattr(logging, level_str.upper(), logging.WARNING)

    # Format: env > config > json
    format_type = os.getenv("HOOKS_LOG_FORMAT", config.get("format", "json"))

    # File: env > config > app_root/log/debug.log
    raw_log_file = os.getenv("HOOKS_LOG_FILE", config.get("file", "log/debug.log"))
    log_file = _resolve_log_file(raw_log_file)

    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    max_bytes = config.get("max_bytes", 10485760)  # 10MB
    backup_count = config.get("backup_count", 3)

    # 2. Create logger
    _logger = logging.getLogger("hooks")
    _logger.setLevel(level)
    _logger.propagate = False  # Don't propagate to root logger

    # If disabled, use NullHandler
    if not enabled:
        _logger.addHandler(logging.NullHandler())
        return _logger

    # 3. Create handler (RotatingFileHandler for log rotation)
    handler = logging.handlers.RotatingFileHandler(
        str(log_file),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    handler.setLevel(level)

    # 4. Set formatter
    if format_type == "json":
        formatter = JSONFormatter(datefmt="%Y-%m-%d %H:%M:%S")
    else:
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s: %(message)s (%(name)s @ %(filename)s:%(lineno)d)",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    handler.setFormatter(formatter)
    _logger.addHandler(handler)

    return _logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get logger instance

    Args:
        name: Optional logger name suffix (e.g., "router" -> "hooks.router")
              If None, returns root "hooks" logger

    Returns:
        Logger instance

    Note:
        Must call setup_logger() first in main.py.
        If not initialized, returns a basic logger (fallback).

    Usage:
        from utils.logger import get_logger
        logger = get_logger("router")  # → "hooks.router"
        logger.info("Message")
    """
    if _logger is None:
        # Fallback: return basic logger with warning
        fallback = logging.getLogger("hooks")
        if not fallback.handlers:
            fallback.addHandler(logging.NullHandler())
        return fallback

    if name:
        return _logger.getChild(name)
    return _logger


def reset_logger():
    """Reset global logger (for testing only)

    This removes all handlers and resets the global logger instance.
    Only use in tests to ensure clean state between test cases.
    """
    global _logger
    if _logger:
        for handler in _logger.handlers[:]:
            handler.close()
            _logger.removeHandler(handler)
        _logger = None
