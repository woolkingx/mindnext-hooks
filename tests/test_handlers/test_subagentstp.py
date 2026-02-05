import pytest
from handlers.SubagentStop import process
from type_defs import HookResult


@pytest.mark.asyncio
async def test_block_action():
    """Test SubagentStop with block action returns block=True"""
    handle_payload = {
        'rule': {
            'action': 'block',
            'reason': 'SubagentStop blocked'
        },
        'claude': {
            'hook_event_name': 'SubagentStop',
            'stop_hook_active': True,
            'task_description': 'Stopped task',
            'subagent_type': 'analyzer'
        }
    }

    result = await process(handle_payload)

    assert isinstance(result, HookResult)
    assert result.block is True
    assert result.block_reason == 'SubagentStop blocked'
    assert result.event_name == 'SubagentStop'


@pytest.mark.asyncio
async def test_block_without_reason():
    """Test SubagentStop with block action uses default reason"""
    handle_payload = {
        'rule': {
            'action': 'block'
        },
        'claude': {
            'hook_event_name': 'SubagentStop',
            'stop_hook_active': True,
            'task_description': 'Task',
            'subagent_type': 'generic'
        }
    }

    result = await process(handle_payload)

    assert result.block is True
    assert result.block_reason == 'Blocked'


@pytest.mark.asyncio
async def test_allow_action():
    """Test SubagentStop with allow action returns None"""
    handle_payload = {
        'rule': {
            'action': 'allow'
        },
        'claude': {
            'hook_event_name': 'SubagentStop',
            'stop_hook_active': True,
            'task_description': 'Task',
            'subagent_type': 'generic'
        }
    }

    result = await process(handle_payload)

    assert result is None


@pytest.mark.asyncio
async def test_no_action():
    """Test SubagentStop with no action returns HookResult with block=False"""
    handle_payload = {
        'rule': {},
        'claude': {
            'hook_event_name': 'SubagentStop',
            'stop_hook_active': True,
            'task_description': 'Task'
        }
    }

    result = await process(handle_payload)

    assert isinstance(result, HookResult)
    assert result.block is False
    assert result.event_name == 'SubagentStop'


@pytest.mark.asyncio
async def test_additional_context():
    """Test SubagentStop with additionalContext"""
    handle_payload = {
        'rule': {
            'additionalContext': 'SubagentStop context'
        },
        'claude': {
            'hook_event_name': 'SubagentStop',
            'stop_hook_active': False,
            'task_description': 'Task'
        }
    }

    result = await process(handle_payload)

    assert result is not None
    assert result.additional_context == 'SubagentStop context'
    assert result.event_name == 'SubagentStop'


@pytest.mark.asyncio
async def test_block_with_context():
    """Test SubagentStop with block action and additionalContext"""
    handle_payload = {
        'rule': {
            'action': 'block',
            'reason': 'Blocked',
            'additionalContext': 'Stop info'
        },
        'claude': {
            'hook_event_name': 'SubagentStop',
            'stop_hook_active': True,
            'task_description': 'Task'
        }
    }

    result = await process(handle_payload)

    assert result.block is True
    assert result.additional_context == 'Stop info'


@pytest.mark.asyncio
async def test_different_stop_hook_values():
    """Test SubagentStop with different stop_hook_active values"""
    for stop_active in [True, False]:
        handle_payload = {
            'rule': {
                'action': 'block',
                'reason': 'Blocked'
            },
            'claude': {
                'hook_event_name': 'SubagentStop',
                'stop_hook_active': stop_active,
                'task_description': 'Task'
            }
        }

        result = await process(handle_payload)

        assert result.block is True
        assert result.block_reason == 'Blocked'


@pytest.mark.asyncio
async def test_different_subagent_types():
    """Test SubagentStop with different subagent types"""
    for subagent_type in ['generic', 'analyzer', 'researcher', 'writer']:
        handle_payload = {
            'rule': {
                'action': 'block',
                'reason': f'Blocked {subagent_type}'
            },
            'claude': {
                'hook_event_name': 'SubagentStop',
                'stop_hook_active': True,
                'task_description': 'Task',
                'subagent_type': subagent_type
            }
        }

        result = await process(handle_payload)

        assert result.block is True
        assert result.block_reason == f'Blocked {subagent_type}'


@pytest.mark.asyncio
async def test_empty_reason():
    """Test SubagentStop with empty reason string"""
    handle_payload = {
        'rule': {
            'action': 'block',
            'reason': ''
        },
        'claude': {
            'hook_event_name': 'SubagentStop',
            'stop_hook_active': True
        }
    }

    result = await process(handle_payload)

    assert result.block is True
    assert result.block_reason == ''
