import pytest
from handlers.PostToolUse import process
from type_defs import HookResult


@pytest.mark.asyncio
async def test_block_action():
    """Test block action returns block=True"""
    handle_payload = {
        'rule': {
            'action': 'block',
            'reason': 'Tool output blocked'
        },
        'claude': {
            'hook_event_name': 'PostToolUse',
            'tool_name': 'Bash',
            'tool_input': {'command': 'curl https://example.com'},
            'tool_response': {
                'stdout': '<!DOCTYPE html>...',
                'stderr': '',
                'interrupted': False,
                'isImage': False
            },
            'tool_use_id': 'tool_123'
        }
    }

    result = await process(handle_payload)

    assert isinstance(result, HookResult)
    assert result.block is True
    assert result.block_reason == 'Tool output blocked'
    assert result.event_name == 'PostToolUse'


@pytest.mark.asyncio
async def test_allow_action():
    """Test allow action (no block) returns None"""
    handle_payload = {
        'rule': {
            'action': 'allow'
        },
        'claude': {
            'hook_event_name': 'PostToolUse',
            'tool_name': 'Bash',
            'tool_input': {'command': 'ls -la'},
            'tool_response': {
                'stdout': 'file1.txt\nfile2.txt',
                'stderr': '',
                'interrupted': False,
                'isImage': False
            },
            'tool_use_id': 'tool_123'
        }
    }

    result = await process(handle_payload)

    # allow with no block should return None
    assert result is None


@pytest.mark.asyncio
async def test_block_with_reason():
    """Test block action with custom reason"""
    handle_payload = {
        'rule': {
            'action': 'block',
            'reason': 'Sensitive data detected'
        },
        'claude': {
            'hook_event_name': 'PostToolUse',
            'tool_name': 'Bash',
            'tool_input': {'command': 'cat /etc/shadow'},
            'tool_response': {
                'stdout': '...',
                'stderr': '',
                'interrupted': False,
                'isImage': False
            },
            'tool_use_id': 'tool_456'
        }
    }

    result = await process(handle_payload)

    assert result.block is True
    assert result.block_reason == 'Sensitive data detected'


@pytest.mark.asyncio
async def test_additional_context():
    """Test additionalContext is injected"""
    handle_payload = {
        'rule': {
            'additionalContext': 'Extra info about the tool output'
        },
        'claude': {
            'hook_event_name': 'PostToolUse',
            'tool_name': 'Bash',
            'tool_input': {'command': 'git status'},
            'tool_response': {
                'stdout': 'On branch main',
                'stderr': '',
                'interrupted': False,
                'isImage': False
            },
            'tool_use_id': 'tool_789'
        }
    }

    result = await process(handle_payload)

    assert result is not None
    assert result.additional_context == 'Extra info about the tool output'
    assert result.block is False
    assert result.event_name == 'PostToolUse'


@pytest.mark.asyncio
async def test_no_action():
    """Test no action returns None"""
    handle_payload = {
        'rule': {},
        'claude': {
            'hook_event_name': 'PostToolUse',
            'tool_name': 'Read',
            'tool_input': {'path': '/tmp/test.txt'},
            'tool_response': {
                'stdout': 'file contents',
                'stderr': '',
                'interrupted': False,
                'isImage': False
            },
            'tool_use_id': 'tool_000'
        }
    }

    result = await process(handle_payload)

    assert result is None


@pytest.mark.asyncio
async def test_block_without_reason():
    """Test block action without explicit reason uses default"""
    handle_payload = {
        'rule': {
            'action': 'block'
        },
        'claude': {
            'hook_event_name': 'PostToolUse',
            'tool_name': 'Bash',
            'tool_input': {'command': 'rm -rf /tmp'},
            'tool_response': {
                'stdout': 'deleted',
                'stderr': '',
                'interrupted': False,
                'isImage': False
            },
            'tool_use_id': 'tool_111'
        }
    }

    result = await process(handle_payload)

    assert result.block is True
    assert result.block_reason == 'Blocked'


@pytest.mark.asyncio
async def test_additional_context_with_block():
    """Test additionalContext takes priority over action"""
    handle_payload = {
        'rule': {
            'additionalContext': 'Tool output info',
            'action': 'block'
        },
        'claude': {
            'hook_event_name': 'PostToolUse',
            'tool_name': 'Bash',
            'tool_input': {'command': 'echo hello'},
            'tool_response': {
                'stdout': 'hello',
                'stderr': '',
                'interrupted': False,
                'isImage': False
            },
            'tool_use_id': 'tool_222'
        }
    }

    result = await process(handle_payload)

    # additionalContext should take priority
    assert result is not None
    assert result.additional_context == 'Tool output info'


@pytest.mark.asyncio
async def test_event_name_always_set():
    """Test event_name is set to PostToolUse in all results"""
    handle_payload = {
        'rule': {
            'action': 'block'
        },
        'claude': {
            'hook_event_name': 'PostToolUse',
            'tool_name': 'Bash'
        }
    }

    result = await process(handle_payload)

    assert result.event_name == 'PostToolUse'


@pytest.mark.asyncio
async def test_block_false_by_default():
    """Test block is False by default"""
    handle_payload = {
        'rule': {
            'action': 'allow'
        },
        'claude': {
            'hook_event_name': 'PostToolUse',
            'tool_name': 'Bash',
            'tool_input': {'command': 'pwd'},
            'tool_response': {
                'stdout': '/home/user',
                'stderr': '',
                'interrupted': False,
                'isImage': False
            }
        }
    }

    result = await process(handle_payload)

    # Should return None for allow with no context
    assert result is None
