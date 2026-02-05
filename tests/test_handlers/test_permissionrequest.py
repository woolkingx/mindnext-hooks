import pytest
from handlers.PermissionRequest import process
from type_defs import HookResult


@pytest.mark.asyncio
async def test_process_deny_action():
    """Test deny action returns permission=deny"""
    handle_payload = {
        'rule': {
            'action': 'deny',
            'reason': 'Permission not granted'
        },
        'claude': {
            'hook_event_name': 'PermissionRequest',
            'tool_name': 'Python',
            'tool_use_id': 'tool-123'
        }
    }

    result = await process(handle_payload)

    assert isinstance(result, HookResult)
    assert result.permission == 'deny'
    assert result.permission_reason == 'Permission not granted'


@pytest.mark.asyncio
async def test_process_ask_action():
    """Test ask action returns permission=ask"""
    handle_payload = {
        'rule': {
            'action': 'ask',
            'reason': 'Confirm permission'
        },
        'claude': {
            'hook_event_name': 'PermissionRequest',
            'tool_name': 'Python'
        }
    }

    result = await process(handle_payload)

    assert isinstance(result, HookResult)
    assert result.permission == 'ask'
    assert result.permission_reason == 'Confirm permission'


@pytest.mark.asyncio
async def test_process_allow_action():
    """Test allow action returns permission=allow"""
    handle_payload = {
        'rule': {
            'action': 'allow',
            'reason': 'Permission granted'
        },
        'claude': {
            'hook_event_name': 'PermissionRequest',
            'tool_name': 'Python'
        }
    }

    result = await process(handle_payload)

    assert isinstance(result, HookResult)
    assert result.permission == 'allow'
    assert result.permission_reason == 'Permission granted'


@pytest.mark.asyncio
async def test_process_default_allow():
    """Test default action is allow"""
    handle_payload = {
        'rule': {},
        'claude': {
            'hook_event_name': 'PermissionRequest',
            'tool_name': 'Python'
        }
    }

    result = await process(handle_payload)

    assert isinstance(result, HookResult)
    assert result.permission == 'allow'


@pytest.mark.asyncio
async def test_process_event_name_set():
    """Test that event_name is always set to PermissionRequest"""
    handle_payload = {
        'rule': {
            'action': 'deny',
            'reason': 'Not allowed'
        },
        'claude': {
            'hook_event_name': 'PermissionRequest'
        }
    }

    result = await process(handle_payload)

    assert result.event_name == 'PermissionRequest'


@pytest.mark.asyncio
async def test_process_deny_with_no_reason():
    """Test deny action with no reason provided"""
    handle_payload = {
        'rule': {
            'action': 'deny'
        },
        'claude': {
            'hook_event_name': 'PermissionRequest'
        }
    }

    result = await process(handle_payload)

    assert isinstance(result, HookResult)
    assert result.permission == 'deny'
    assert result.permission_reason == 'Denied'


@pytest.mark.asyncio
async def test_process_ask_with_no_reason():
    """Test ask action with no reason provided"""
    handle_payload = {
        'rule': {
            'action': 'ask'
        },
        'claude': {
            'hook_event_name': 'PermissionRequest'
        }
    }

    result = await process(handle_payload)

    assert isinstance(result, HookResult)
    assert result.permission == 'ask'
    assert result.permission_reason == 'Confirm?'
