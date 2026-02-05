import pytest
from handlers.PostToolUseFailure import process
from type_defs import HookResult


@pytest.mark.asyncio
async def test_block_action():
    """Test block action returns block=True (even though PostToolUseFailure doesn't support block officially)"""
    handle_payload = {
        'rule': {
            'action': 'block',
            'reason': 'Tool error detected'
        },
        'claude': {
            'hook_event_name': 'PostToolUseFailure',
            'tool_name': 'Bash',
            'tool_input': {'command': 'curl https://example.com'},
            'error': 'Connection timeout',
            'tool_use_id': 'tool_123'
        }
    }

    result = await process(handle_payload)

    assert isinstance(result, HookResult)
    assert result.block is True
    assert result.block_reason == 'Tool error detected'
    assert result.event_name == 'PostToolUseFailure'


@pytest.mark.asyncio
async def test_allow_action():
    """Test allow action (no block) returns None"""
    handle_payload = {
        'rule': {
            'action': 'allow'
        },
        'claude': {
            'hook_event_name': 'PostToolUseFailure',
            'tool_name': 'Bash',
            'tool_input': {'command': 'ls -la'},
            'error': 'Command failed',
            'tool_use_id': 'tool_123'
        }
    }

    result = await process(handle_payload)

    # allow with no block should return None
    assert result is None


@pytest.mark.asyncio
async def test_additional_context():
    """Test additionalContext is injected"""
    handle_payload = {
        'rule': {
            'additionalContext': 'Error context: timeout during network request'
        },
        'claude': {
            'hook_event_name': 'PostToolUseFailure',
            'tool_name': 'Bash',
            'tool_input': {'command': 'git fetch'},
            'error': 'Network timeout',
            'tool_use_id': 'tool_789'
        }
    }

    result = await process(handle_payload)

    assert result is not None
    assert result.additional_context == 'Error context: timeout during network request'
    assert result.block is False
    assert result.event_name == 'PostToolUseFailure'


@pytest.mark.asyncio
async def test_block_with_reason():
    """Test block action with custom reason"""
    handle_payload = {
        'rule': {
            'action': 'block',
            'reason': 'Permission denied error'
        },
        'claude': {
            'hook_event_name': 'PostToolUseFailure',
            'tool_name': 'Read',
            'tool_input': {'path': '/etc/shadow'},
            'error': 'Permission denied',
            'tool_use_id': 'tool_456'
        }
    }

    result = await process(handle_payload)

    assert result.block is True
    assert result.block_reason == 'Permission denied error'


@pytest.mark.asyncio
async def test_no_action():
    """Test no action returns None"""
    handle_payload = {
        'rule': {},
        'claude': {
            'hook_event_name': 'PostToolUseFailure',
            'tool_name': 'Bash',
            'tool_input': {'command': 'pwd'},
            'error': 'Command not found',
            'tool_use_id': 'tool_000'
        }
    }

    result = await process(handle_payload)

    assert result is None


@pytest.mark.asyncio
async def test_tool_output_available():
    """Test that tool_output (error field) is accessible"""
    handle_payload = {
        'rule': {
            'additionalContext': 'Tool failed with error'
        },
        'claude': {
            'hook_event_name': 'PostToolUseFailure',
            'tool_name': 'Bash',
            'tool_input': {'command': 'apt-get install pkg'},
            'error': 'E: Unable to locate package',
            'tool_use_id': 'tool_555'
        }
    }

    result = await process(handle_payload)

    # Verify we can access the error field
    assert result is not None
    assert result.additional_context == 'Tool failed with error'
    assert result.event_name == 'PostToolUseFailure'


@pytest.mark.asyncio
async def test_block_without_reason():
    """Test block action without explicit reason uses default"""
    handle_payload = {
        'rule': {
            'action': 'block'
        },
        'claude': {
            'hook_event_name': 'PostToolUseFailure',
            'tool_name': 'Bash',
            'tool_input': {'command': 'rm -rf /tmp'},
            'error': 'Operation failed',
            'tool_use_id': 'tool_111'
        }
    }

    result = await process(handle_payload)

    assert result.block is True
    assert result.block_reason == 'Blocked'


@pytest.mark.asyncio
async def test_additional_context_priority():
    """Test additionalContext takes priority over action"""
    handle_payload = {
        'rule': {
            'additionalContext': 'Error handling info',
            'action': 'block'
        },
        'claude': {
            'hook_event_name': 'PostToolUseFailure',
            'tool_name': 'Bash',
            'tool_input': {'command': 'echo hello'},
            'error': 'Unknown error',
            'tool_use_id': 'tool_222'
        }
    }

    result = await process(handle_payload)

    # additionalContext should take priority
    assert result is not None
    assert result.additional_context == 'Error handling info'


@pytest.mark.asyncio
async def test_event_name_always_set():
    """Test event_name is set to PostToolUseFailure in all results"""
    handle_payload = {
        'rule': {
            'action': 'block'
        },
        'claude': {
            'hook_event_name': 'PostToolUseFailure',
            'tool_name': 'Bash'
        }
    }

    result = await process(handle_payload)

    assert result.event_name == 'PostToolUseFailure'
