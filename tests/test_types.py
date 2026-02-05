from type_defs import HookResult


def test_hook_result_creation():
    result = HookResult(
        event_name='PreToolUse',
        permission='deny',
        permission_reason='test reason'
    )
    assert result.event_name == 'PreToolUse'
    assert result.permission == 'deny'
    assert result.permission_reason == 'test reason'
