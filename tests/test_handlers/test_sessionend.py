import pytest
from handlers.SessionEnd import process
from type_defs import HookResult


@pytest.mark.asyncio
async def test_additional_context_only():
    """Test SessionEnd with additionalContext returns additional_context"""
    handle_payload = {
        'rule': {
            'additionalContext': 'Session ended context'
        },
        'claude': {
            'hook_event_name': 'SessionEnd',
            'reason': 'logout'
        }
    }

    result = await process(handle_payload)

    assert isinstance(result, HookResult)
    assert result.additional_context == 'Session ended context'


@pytest.mark.asyncio
async def test_context_action():
    """Test SessionEnd with context action"""
    handle_payload = {
        'rule': {
            'action': 'context',
            'additionalContext': 'Cleanup context'
        },
        'claude': {
            'hook_event_name': 'SessionEnd',
            'reason': 'clear'
        }
    }

    result = await process(handle_payload)

    assert isinstance(result, HookResult)
    assert result.additional_context == 'Cleanup context'
    assert result.event_name == 'SessionEnd'


@pytest.mark.asyncio
async def test_no_action():
    """Test SessionEnd with no action returns None"""
    handle_payload = {
        'rule': {},
        'claude': {
            'hook_event_name': 'SessionEnd',
            'reason': 'prompt_input_exit'
        }
    }

    result = await process(handle_payload)

    assert result is None


@pytest.mark.asyncio
async def test_context_priority():
    """Test that additionalContext has priority over action"""
    handle_payload = {
        'rule': {
            'additionalContext': 'Direct context',
            'action': 'context',
            'additionalContext': 'Action context'
        },
        'claude': {
            'hook_event_name': 'SessionEnd',
            'reason': 'logout'
        }
    }

    result = await process(handle_payload)

    assert isinstance(result, HookResult)
    # The direct additionalContext should be used
    assert result.additional_context == 'Action context'


@pytest.mark.asyncio
async def test_event_name_always_set():
    """Test that event_name is always set when returning HookResult"""
    handle_payload = {
        'rule': {
            'additionalContext': 'Test'
        },
        'claude': {
            'hook_event_name': 'SessionEnd',
            'reason': 'other'
        }
    }

    result = await process(handle_payload)

    assert result is not None
    assert result.event_name == 'SessionEnd'


@pytest.mark.asyncio
async def test_empty_additional_context():
    """Test SessionEnd with context action but empty additionalContext"""
    handle_payload = {
        'rule': {
            'action': 'context',
            'additionalContext': ''
        },
        'claude': {
            'hook_event_name': 'SessionEnd',
            'reason': 'clear'
        }
    }

    result = await process(handle_payload)

    assert isinstance(result, HookResult)
    assert result.additional_context == ''
    assert result.event_name == 'SessionEnd'


@pytest.mark.asyncio
async def test_reason_field_present():
    """Test that SessionEnd properly handles different reason values"""
    for reason in ['clear', 'logout', 'prompt_input_exit', 'other']:
        handle_payload = {
            'rule': {
                'additionalContext': f'Context for {reason}'
            },
            'claude': {
                'hook_event_name': 'SessionEnd',
                'reason': reason
            }
        }

        result = await process(handle_payload)

        assert isinstance(result, HookResult)
        assert result.additional_context == f'Context for {reason}'
