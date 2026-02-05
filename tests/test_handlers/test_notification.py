import pytest
from handlers.Notification import process
from type_defs import HookResult


@pytest.mark.asyncio
async def test_notification_returns_none():
    """Test Notification handler always returns None"""
    handle_payload = {
        'rule': {
            'action': 'block'
        },
        'claude': {
            'hook_event_name': 'Notification',
            'message': 'Test notification',
            'notification_type': 'info'
        }
    }

    result = await process(handle_payload)

    assert result is None


@pytest.mark.asyncio
async def test_notification_with_additional_context():
    """Test Notification with additionalContext still returns None"""
    handle_payload = {
        'rule': {
            'additionalContext': 'Some context'
        },
        'claude': {
            'hook_event_name': 'Notification',
            'message': 'Another notification',
            'notification_type': 'warning'
        }
    }

    result = await process(handle_payload)

    assert result is None


@pytest.mark.asyncio
async def test_notification_empty_rule():
    """Test Notification with empty rule"""
    handle_payload = {
        'rule': {},
        'claude': {
            'hook_event_name': 'Notification',
            'message': 'Message',
            'notification_type': 'error'
        }
    }

    result = await process(handle_payload)

    assert result is None


@pytest.mark.asyncio
async def test_notification_with_all_fields():
    """Test Notification with all possible payload fields"""
    handle_payload = {
        'rule': {
            'name': 'notification-rule',
            'enabled': True,
            'action': 'notify',
            'reason': 'Test reason'
        },
        'claude': {
            'hook_event_name': 'Notification',
            'message': 'Complex notification',
            'notification_type': 'info',
            'timestamp': '2024-01-01T00:00:00Z',
            'source': 'system'
        }
    }

    result = await process(handle_payload)

    assert result is None


@pytest.mark.asyncio
async def test_different_notification_types():
    """Test Notification with different notification types"""
    for notif_type in ['info', 'warning', 'error', 'debug', 'success']:
        handle_payload = {
            'rule': {},
            'claude': {
                'hook_event_name': 'Notification',
                'message': f'{notif_type} message',
                'notification_type': notif_type
            }
        }

        result = await process(handle_payload)

        assert result is None


@pytest.mark.asyncio
async def test_notification_long_message():
    """Test Notification with long message"""
    long_message = "x" * 10000
    handle_payload = {
        'rule': {},
        'claude': {
            'hook_event_name': 'Notification',
            'message': long_message,
            'notification_type': 'info'
        }
    }

    result = await process(handle_payload)

    assert result is None


@pytest.mark.asyncio
async def test_notification_unicode_message():
    """Test Notification with unicode characters"""
    handle_payload = {
        'rule': {},
        'claude': {
            'hook_event_name': 'Notification',
            'message': '通知訊息 🔔 message ñoño',
            'notification_type': 'info'
        }
    }

    result = await process(handle_payload)

    assert result is None


@pytest.mark.asyncio
async def test_notification_empty_message():
    """Test Notification with empty message"""
    handle_payload = {
        'rule': {},
        'claude': {
            'hook_event_name': 'Notification',
            'message': '',
            'notification_type': 'info'
        }
    }

    result = await process(handle_payload)

    assert result is None
