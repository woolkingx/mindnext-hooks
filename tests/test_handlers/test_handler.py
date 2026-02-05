import pytest
from handlers import Handler
from type_defs import HookResult

@pytest.mark.asyncio
async def test_handler_basic():
    rule = {'name': 'test', 'event': 'PreToolUse', 'enabled': True}
    handler = Handler(rule)

    assert handler.name == 'test'
    assert handler.event == 'PreToolUse'
    assert handler.enabled == True

@pytest.mark.asyncio
async def test_handler_event_mismatch():
    rule = {'name': 'test', 'event': 'PreToolUse'}
    handler = Handler(rule)

    handle_payload = {
        'rule': rule,
        'claude': {'hook_event_name': 'PostToolUse'}
    }

    result = await handler.on_event(handle_payload)
    assert result is None  # 事件不匹配
