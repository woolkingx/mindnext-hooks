"""Test Rule Validation System

This test verifies that rule validation catches errors before deployment.
It uses test rule files in tests/test_rules/ directory.

Usage:
    python3 tests/test_rule_validation.py              # Run all tests
    python3 tests/test_rule_validation.py --verbose    # Verbose output
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from framework import TestRunner, TestResult, TestLevel
from loaders.validator import validate_rule


# Test rule configurations
VALID_RULES = [
    {
        "name": "valid-pretooluse-deny",
        "rule": {
            "name": "test-deny-dangerous",
            "description": "Deny dangerous commands",
            "enabled": True,
            "event": "PreToolUse",
            "tool": "Bash",
            "action": "deny",
            "reason": "Dangerous command blocked"
        },
        "should_pass": True
    },
    {
        "name": "valid-pretooluse-transform",
        "rule": {
            "name": "test-transform-rm",
            "description": "Transform rm to trash",
            "enabled": True,
            "event": "PreToolUse",
            "tool": "Bash",
            "action": "transform",
            "updatedInput": {
                "field": "command",
                "pattern": "^rm",
                "replace": "trash-put"
            }
        },
        "should_pass": True
    },
    {
        "name": "valid-posttooluse-block",
        "rule": {
            "name": "test-block-on-error",
            "description": "Block on error output",
            "enabled": True,
            "event": "PostToolUse",
            "action": "block",
            "match": "error"
        },
        "should_pass": True
    },
    {
        "name": "valid-userpromptsubmit-feature",
        "rule": {
            "name": "test-tags-feature",
            "description": "Enable tags feature",
            "enabled": True,
            "event": "UserPromptSubmit",
            "feature": ["tags", "memory"]
        },
        "should_pass": True
    }
]

INVALID_RULES = [
    {
        "name": "missing-required-name",
        "rule": {
            "description": "Missing name",
            "enabled": True,
            "event": "PreToolUse",
            "action": "deny"
        },
        "should_pass": False,
        "expected_error": "缺少必填欄位: name"
    },
    {
        "name": "missing-required-description",
        "rule": {
            "name": "test-no-desc",
            "enabled": True,
            "event": "PreToolUse",
            "action": "deny"
        },
        "should_pass": False,
        "expected_error": "缺少必填欄位: description"
    },
    {
        "name": "missing-required-event",
        "rule": {
            "name": "test-no-event",
            "description": "Missing event",
            "enabled": True,
            "action": "deny"
        },
        "should_pass": False,
        "expected_error": "缺少必填欄位: event"
    },
    {
        "name": "invalid-event-name",
        "rule": {
            "name": "test-bad-event",
            "description": "Invalid event",
            "enabled": True,
            "event": "NonExistentEvent",
            "action": "deny"
        },
        "should_pass": False,
        "expected_error": "不支援的 event: NonExistentEvent"
    },
    {
        "name": "invalid-action-for-event",
        "rule": {
            "name": "test-bad-action",
            "description": "PostToolUse doesn't support ask",
            "enabled": True,
            "event": "PostToolUse",
            "action": "ask"  # PostToolUse only supports 'block'
        },
        "should_pass": False,
        "expected_error": "event=PostToolUse 不支援 action=ask"
    },
    {
        "name": "invalid-action-for-userpromptsubmit",
        "rule": {
            "name": "test-wrong-action",
            "description": "UserPromptSubmit doesn't support deny",
            "enabled": True,
            "event": "UserPromptSubmit",
            "action": "deny"  # UserPromptSubmit only supports 'block'
        },
        "should_pass": False,
        "expected_error": "event=UserPromptSubmit 不支援 action=deny"
    },
    {
        "name": "pretooluse-missing-tool-for-cmd",
        "rule": {
            "name": "test-missing-tool",
            "description": "Has cmd but no tool",
            "enabled": True,
            "event": "PreToolUse",
            "action": "deny",
            "cmd": "rm"  # cmd requires tool=Bash
        },
        "should_pass": False,
        "expected_error": "cmd 欄位只能用於 tool=Bash"
    },
    {
        "name": "invalid-tool-for-cmd",
        "rule": {
            "name": "test-wrong-tool",
            "description": "Has cmd with wrong tool",
            "enabled": True,
            "event": "PreToolUse",
            "tool": "Read",
            "action": "deny",
            "cmd": "rm"  # cmd only works with tool=Bash
        },
        "should_pass": False,
        "expected_error": "cmd 欄位只能用於 tool=Bash"
    }
]


def run_rule_validation_tests(runner: TestRunner):
    """Run rule validation tests"""
    runner.log("="*60)
    runner.log("Rule Validation Tests")
    runner.log("="*60)

    # Test valid rules
    runner.log("\n--- Valid Rules ---")
    for test_case in VALID_RULES:
        _test_rule(runner, test_case)

    # Test invalid rules
    runner.log("\n--- Invalid Rules ---")
    for test_case in INVALID_RULES:
        _test_rule(runner, test_case)


def _test_rule(runner: TestRunner, test_case: dict):
    """Test a single rule validation case"""
    name = test_case["name"]
    rule = test_case["rule"]
    should_pass = test_case["should_pass"]
    expected_error = test_case.get("expected_error", "")

    # Run validation
    passed, errors = validate_rule(rule, name)

    # Check result
    if should_pass:
        # Should pass: passed=True, errors=[]
        test_passed = passed and len(errors) == 0
        message = "Validation passed" if test_passed else f"Unexpected errors: {errors}"
    else:
        # Should fail: passed=False, errors contain expected message
        test_passed = not passed and len(errors) > 0
        if test_passed and expected_error:
            # Check if expected error is in the error messages
            error_msg = '; '.join(errors)
            test_passed = expected_error in error_msg
            message = f"Caught expected error: {expected_error[:50]}..." if test_passed else f"Wrong error: {error_msg}"
        else:
            message = f"Caught errors: {errors[0][:50]}..." if errors else "No errors caught"

    result = TestResult(
        name=name,
        level=TestLevel.RULES,
        passed=test_passed,
        message=message,
        details={
            "rule": rule,
            "expected": "pass" if should_pass else "fail",
            "actual_passed": passed,
            "errors": errors
        }
    )

    runner.report.add(result)
    runner.log(
        f"{name}: {'PASS' if test_passed else 'FAIL'}",
        "PASS" if test_passed else "FAIL"
    )


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Rule Validation Tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    runner = TestRunner(verbose=args.verbose)
    run_rule_validation_tests(runner)
    runner.print_report()

    # Exit with error if any tests failed
    sys.exit(0 if runner.report.failed == 0 else 1)
