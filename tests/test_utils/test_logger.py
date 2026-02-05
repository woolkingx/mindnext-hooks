"""Test logger configuration and functionality"""
import os
import sys
import json
import tempfile
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from framework import TestRunner, TestResult, TestLevel
from utils.logger import setup_logger, get_logger, reset_logger, JSONFormatter


def run_logger_tests(runner: TestRunner):
    """Run logger tests"""
    runner.log("="*60)
    runner.log("Logger Tests")
    runner.log("="*60)

    # Test 1: Default configuration
    _test_default_config(runner)

    # Test 2: Environment variable override - DEBUG
    _test_env_debug(runner)

    # Test 3: Environment variable override - LOG_LEVEL
    _test_env_log_level(runner)

    # Test 4: JSON formatter
    _test_json_formatter(runner)

    # Test 5: Text formatter
    _test_text_formatter(runner)

    # Test 6: File output
    _test_file_output(runner)

    # Test 7: get_logger with name
    _test_get_logger_with_name(runner)

    # Test 8: Disabled logging
    _test_disabled_logging(runner)


def _test_default_config(runner: TestRunner):
    """Test default configuration"""
    runner.log("\n--- Default Configuration ---")

    # Reset logger
    reset_logger()

    # Setup with default config
    config = {}
    logger = setup_logger(config)

    # Check level (should be WARNING)
    passed = (
        logger.level == logging.WARNING and
        len(logger.handlers) == 1 and
        isinstance(logger.handlers[0].formatter, JSONFormatter)
    )

    result = TestResult(
        name="Default configuration",
        level=TestLevel.BASIC,
        passed=passed,
        message=f"Level: {logging.getLevelName(logger.level)}, Handlers: {len(logger.handlers)}",
        details={"level": logger.level, "handler_count": len(logger.handlers)}
    )

    runner.report.add(result)
    runner.log(
        f"Default config: {'PASS' if passed else 'FAIL'}",
        "PASS" if passed else "FAIL"
    )


def _test_env_debug(runner: TestRunner):
    """Test HOOKS_DEBUG environment variable"""
    runner.log("\n--- Environment Variable: HOOKS_DEBUG ---")

    # Reset logger
    reset_logger()

    # Set environment variable
    os.environ["HOOKS_DEBUG"] = "1"

    try:
        config = {}
        logger = setup_logger(config)

        # Check level (should be DEBUG)
        passed = logger.level == logging.DEBUG

        result = TestResult(
            name="HOOKS_DEBUG=1 sets DEBUG level",
            level=TestLevel.BASIC,
            passed=passed,
            message=f"Level: {logging.getLevelName(logger.level)}",
            details={"level": logger.level}
        )

        runner.report.add(result)
        runner.log(
            f"HOOKS_DEBUG: {'PASS' if passed else 'FAIL'}",
            "PASS" if passed else "FAIL"
        )

    finally:
        # Clean up
        del os.environ["HOOKS_DEBUG"]
        reset_logger()


def _test_env_log_level(runner: TestRunner):
    """Test HOOKS_LOG_LEVEL environment variable"""
    runner.log("\n--- Environment Variable: HOOKS_LOG_LEVEL ---")

    # Reset logger
    reset_logger()

    # Set environment variable
    os.environ["HOOKS_LOG_LEVEL"] = "ERROR"

    try:
        config = {"level": "INFO"}  # Should be overridden
        logger = setup_logger(config)

        # Check level (should be ERROR, not INFO)
        passed = logger.level == logging.ERROR

        result = TestResult(
            name="HOOKS_LOG_LEVEL overrides config",
            level=TestLevel.BASIC,
            passed=passed,
            message=f"Level: {logging.getLevelName(logger.level)}",
            details={"level": logger.level, "expected": logging.ERROR}
        )

        runner.report.add(result)
        runner.log(
            f"HOOKS_LOG_LEVEL: {'PASS' if passed else 'FAIL'}",
            "PASS" if passed else "FAIL"
        )

    finally:
        # Clean up
        del os.environ["HOOKS_LOG_LEVEL"]
        reset_logger()


def _test_json_formatter(runner: TestRunner):
    """Test JSON formatter"""
    runner.log("\n--- JSON Formatter ---")

    # Reset logger
    reset_logger()

    config = {"format": "json"}
    logger = setup_logger(config)

    # Check formatter type
    passed = isinstance(logger.handlers[0].formatter, JSONFormatter)

    result = TestResult(
        name="JSON formatter configured",
        level=TestLevel.BASIC,
        passed=passed,
        message="Formatter is JSONFormatter" if passed else "Formatter is not JSONFormatter",
        details={"formatter_type": type(logger.handlers[0].formatter).__name__}
    )

    runner.report.add(result)
    runner.log(
        f"JSON formatter: {'PASS' if passed else 'FAIL'}",
        "PASS" if passed else "FAIL"
    )

    # Clean up
    reset_logger()


def _test_text_formatter(runner: TestRunner):
    """Test text formatter"""
    runner.log("\n--- Text Formatter ---")

    # Reset logger
    reset_logger()

    # Set environment variable
    os.environ["HOOKS_LOG_FORMAT"] = "text"

    try:
        config = {"format": "json"}  # Should be overridden
        logger = setup_logger(config)

        # Check formatter type (should NOT be JSONFormatter)
        passed = not isinstance(logger.handlers[0].formatter, JSONFormatter)

        result = TestResult(
            name="Text formatter via env var",
            level=TestLevel.BASIC,
            passed=passed,
            message="Formatter is text" if passed else "Formatter is JSON",
            details={"formatter_type": type(logger.handlers[0].formatter).__name__}
        )

        runner.report.add(result)
        runner.log(
            f"Text formatter: {'PASS' if passed else 'FAIL'}",
            "PASS" if passed else "FAIL"
        )

    finally:
        # Clean up
        del os.environ["HOOKS_LOG_FORMAT"]
        reset_logger()


def _test_file_output(runner: TestRunner):
    """Test file output"""
    runner.log("\n--- File Output ---")

    # Reset logger
    reset_logger()

    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        temp_log = f.name

    try:
        config = {"file": temp_log, "format": "json"}
        logger = setup_logger(config)

        # Write a log message
        test_logger = get_logger("test")
        test_logger.warning("Test message")

        # Force flush
        for handler in logger.handlers:
            handler.flush()

        # Check file exists and has content
        log_path = Path(temp_log)
        content = log_path.read_text()

        # Parse JSON
        log_entry = json.loads(content.strip())

        passed = (
            log_path.exists() and
            log_entry.get("level") == "WARNING" and
            log_entry.get("msg") == "Test message" and
            log_entry.get("name") == "hooks.test"
        )

        result = TestResult(
            name="File output and JSON format",
            level=TestLevel.INTEGRATION,
            passed=passed,
            message=f"Log written to {temp_log}",
            details={"log_entry": log_entry}
        )

        runner.report.add(result)
        runner.log(
            f"File output: {'PASS' if passed else 'FAIL'}",
            "PASS" if passed else "FAIL"
        )

    finally:
        # Clean up
        reset_logger()
        if Path(temp_log).exists():
            Path(temp_log).unlink()


def _test_get_logger_with_name(runner: TestRunner):
    """Test get_logger with name parameter"""
    runner.log("\n--- get_logger with name ---")

    # Reset logger
    reset_logger()

    config = {}
    setup_logger(config)

    # Get logger with name
    logger = get_logger("test.module")

    # Check logger name
    passed = logger.name == "hooks.test.module"

    result = TestResult(
        name="get_logger creates child logger",
        level=TestLevel.BASIC,
        passed=passed,
        message=f"Logger name: {logger.name}",
        details={"logger_name": logger.name}
    )

    runner.report.add(result)
    runner.log(
        f"get_logger with name: {'PASS' if passed else 'FAIL'}",
        "PASS" if passed else "FAIL"
    )

    # Clean up
    reset_logger()


def _test_disabled_logging(runner: TestRunner):
    """Test disabled logging"""
    runner.log("\n--- Disabled Logging ---")

    # Reset logger
    reset_logger()

    config = {"enabled": False}
    logger = setup_logger(config)

    # Check handler type (should be NullHandler)
    passed = (
        len(logger.handlers) == 1 and
        isinstance(logger.handlers[0], logging.NullHandler)
    )

    result = TestResult(
        name="Disabled logging uses NullHandler",
        level=TestLevel.BASIC,
        passed=passed,
        message="NullHandler configured" if passed else "Wrong handler type",
        details={"handler_type": type(logger.handlers[0]).__name__}
    )

    runner.report.add(result)
    runner.log(
        f"Disabled logging: {'PASS' if passed else 'FAIL'}",
        "PASS" if passed else "FAIL"
    )

    # Clean up
    reset_logger()


if __name__ == "__main__":
    runner = TestRunner(verbose=True)
    run_logger_tests(runner)
    runner.print_report()
