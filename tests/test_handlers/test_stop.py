import pytest
from handlers.Stop import process
from type_defs import HookResult


@pytest.mark.asyncio
async def test_block_action():
    """Test Stop with block action returns block=True"""
    handle_payload = {
        'rule': {
            'action': 'block',
            'reason': 'Stop blocked'
        },
        'claude': {
            'hook_event_name': 'Stop',
            'stop_reason': 'user_requested'
        }
    }

    result = await process(handle_payload)

    assert isinstance(result, HookResult)
    assert result.block is True
    assert result.block_reason == 'Stop blocked'
    assert result.event_name == 'Stop'


@pytest.mark.asyncio
async def test_block_without_reason():
    """Test Stop with block action uses default reason"""
    handle_payload = {
        'rule': {
            'action': 'block'
        },
        'claude': {
            'hook_event_name': 'Stop',
            'stop_reason': 'user_requested'
        }
    }

    result = await process(handle_payload)

    assert result.block is True
    assert result.block_reason == 'Blocked'


@pytest.mark.asyncio
async def test_allow_action():
    """Test Stop with allow action returns None"""
    handle_payload = {
        'rule': {
            'action': 'allow'
        },
        'claude': {
            'hook_event_name': 'Stop',
            'stop_reason': 'user_requested'
        }
    }

    result = await process(handle_payload)

    assert result is None


@pytest.mark.asyncio
async def test_no_action():
    """Test Stop with no action returns HookResult with block=False"""
    handle_payload = {
        'rule': {},
        'claude': {
            'hook_event_name': 'Stop',
            'stop_reason': 'user_requested'
        }
    }

    result = await process(handle_payload)

    assert isinstance(result, HookResult)
    assert result.block is False
    assert result.event_name == 'Stop'


@pytest.mark.asyncio
async def test_additional_context():
    """Test Stop with additionalContext"""
    handle_payload = {
        'rule': {
            'additionalContext': 'Stop context info'
        },
        'claude': {
            'hook_event_name': 'Stop',
            'stop_reason': 'user_requested'
        }
    }

    result = await process(handle_payload)

    assert result is not None
    assert result.additional_context == 'Stop context info'
    assert result.event_name == 'Stop'


@pytest.mark.asyncio
async def test_block_with_context():
    """Test Stop with block action and additionalContext"""
    handle_payload = {
        'rule': {
            'action': 'block',
            'reason': 'Stop blocked',
            'additionalContext': 'Additional stop info'
        },
        'claude': {
            'hook_event_name': 'Stop',
            'stop_reason': 'user_requested'
        }
    }

    result = await process(handle_payload)

    assert result.block is True
    assert result.additional_context == 'Additional stop info'


@pytest.mark.asyncio
async def test_different_stop_reasons():
    """Test Stop with different stop_reason values"""
    for reason in ['user_requested', 'max_iterations', 'error', 'other']:
        handle_payload = {
            'rule': {
                'action': 'block',
                'reason': f'Stopped: {reason}'
            },
            'claude': {
                'hook_event_name': 'Stop',
                'stop_reason': reason
            }
        }

        result = await process(handle_payload)

        assert result.block is True
        assert result.block_reason == f'Stopped: {reason}'


@pytest.mark.asyncio
async def test_empty_reason():
    """Test Stop with empty reason string"""
    handle_payload = {
        'rule': {
            'action': 'block',
            'reason': ''
        },
        'claude': {
            'hook_event_name': 'Stop'
        }
    }

    result = await process(handle_payload)

    assert result.block is True
    assert result.block_reason == ''
