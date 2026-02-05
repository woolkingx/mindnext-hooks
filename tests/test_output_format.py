#!/usr/bin/env python3
"""測試最終 JSON 輸出格式符合官方 API"""
import json
import sys
from pathlib import Path
from io import StringIO

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from type_defs import HookResult
from output import emit


def capture_output(result: HookResult, event_name: str) -> dict:
    """捕獲 emit() 的 stdout 輸出"""
    old_stdout = sys.stdout
    old_exit = sys.exit

    sys.stdout = StringIO()

    def mock_exit(code):
        pass

    sys.exit = mock_exit

    try:
        emit(result, event_name)
        output = sys.stdout.getvalue()
        return json.loads(output)
    finally:
        sys.stdout = old_stdout
        sys.exit = old_exit


def test_userpromptsubmit_has_hookEventName():
    """UserPromptSubmit 輸出必須包含 hookEventName"""
    result = HookResult(
        event_name='UserPromptSubmit',
        additional_context='test context'
    )

    output = capture_output(result, 'UserPromptSubmit')

    assert 'hookSpecificOutput' in output
    assert output['hookSpecificOutput']['hookEventName'] == 'UserPromptSubmit'
    assert output['hookSpecificOutput']['additionalContext'] == 'test context'


def test_pretooluse_has_hookEventName():
    """PreToolUse 輸出必須包含 hookEventName"""
    result = HookResult(
        event_name='PreToolUse',
        permission='deny',
        permission_reason='Blocked'
    )

    output = capture_output(result, 'PreToolUse')

    assert 'hookSpecificOutput' in output
    assert output['hookSpecificOutput']['hookEventName'] == 'PreToolUse'
    assert output['hookSpecificOutput']['permissionDecision'] == 'deny'
    assert output['hookSpecificOutput']['permissionDecisionReason'] == 'Blocked'


def test_permissionrequest_nested_decision():
    """PermissionRequest 使用嵌套 decision.behavior 結構"""
    result = HookResult(
        event_name='PermissionRequest',
        permission='deny',
        permission_reason='Not allowed'
    )

    output = capture_output(result, 'PermissionRequest')

    assert 'hookSpecificOutput' in output
    assert output['hookSpecificOutput']['hookEventName'] == 'PermissionRequest'

    # 檢查嵌套結構
    assert 'decision' in output['hookSpecificOutput']
    decision = output['hookSpecificOutput']['decision']
    assert decision['behavior'] == 'deny'
    assert decision['message'] == 'Not allowed'


def test_permissionrequest_with_updated_input():
    """PermissionRequest 的 updatedInput 在 decision 內"""
    result = HookResult(
        event_name='PermissionRequest',
        permission='allow',
        updated_input={'command': 'safe command'}
    )

    output = capture_output(result, 'PermissionRequest')

    decision = output['hookSpecificOutput']['decision']
    assert decision['behavior'] == 'allow'
    assert decision['updatedInput'] == {'command': 'safe command'}


def test_stop_no_hookSpecificOutput():
    """Stop 事件使用頂層 decision，無 hookSpecificOutput"""
    result = HookResult(
        event_name='Stop',
        block=True,
        block_reason='Not finished'
    )

    output = capture_output(result, 'Stop')

    # Stop 使用頂層 decision
    assert output['decision'] == 'block'
    assert output['reason'] == 'Not finished'

    # Stop 不應該有 hookSpecificOutput (因為沒有 additionalContext)
    assert 'hookSpecificOutput' not in output


def test_posttooluse_has_hookEventName():
    """PostToolUse 輸出必須包含 hookEventName"""
    result = HookResult(
        event_name='PostToolUse',
        additional_context='Tool completed'
    )

    output = capture_output(result, 'PostToolUse')

    assert 'hookSpecificOutput' in output
    assert output['hookSpecificOutput']['hookEventName'] == 'PostToolUse'
    assert output['hookSpecificOutput']['additionalContext'] == 'Tool completed'


def test_sessionstart_has_hookEventName():
    """SessionStart 輸出必須包含 hookEventName"""
    result = HookResult(
        event_name='SessionStart',
        additional_context='Loaded context'
    )

    output = capture_output(result, 'SessionStart')

    assert 'hookSpecificOutput' in output
    assert output['hookSpecificOutput']['hookEventName'] == 'SessionStart'


def run_all_tests():
    """執行所有測試"""
    tests = [
        ('UserPromptSubmit hookEventName', test_userpromptsubmit_has_hookEventName),
        ('PreToolUse hookEventName', test_pretooluse_has_hookEventName),
        ('PermissionRequest nested decision', test_permissionrequest_nested_decision),
        ('PermissionRequest updatedInput', test_permissionrequest_with_updated_input),
        ('Stop 無 hookSpecificOutput', test_stop_no_hookSpecificOutput),
        ('PostToolUse hookEventName', test_posttooluse_has_hookEventName),
        ('SessionStart hookEventName', test_sessionstart_has_hookEventName),
    ]

    passed = 0
    failed = 0

    print("=" * 60)
    print("測試輸出格式符合官方 API")
    print("=" * 60)

    for name, test_func in tests:
        try:
            test_func()
            print(f"✓ {name}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {name}: ERROR - {e}")
            failed += 1

    print("=" * 60)
    print(f"結果: {passed} 通過, {failed} 失敗")
    print("=" * 60)

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
