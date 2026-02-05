import pytest
from handlers.PreToolUse import process
from type_defs import HookResult


@pytest.mark.asyncio
async def test_process_deny_action():
    """Test deny action returns permission=deny"""
    handle_payload = {
        'rule': {
            'action': 'deny',
            'reason': 'Blocked command'
        },
        'claude': {
            'hook_event_name': 'PreToolUse',
            'tool_name': 'Bash',
            'tool_input': {'command': 'rm -rf /'}
        }
    }

    result = await process(handle_payload)

    assert isinstance(result, HookResult)
    assert result.permission == 'deny'
    assert result.permission_reason == 'Blocked command'


@pytest.mark.asyncio
async def test_process_ask_action():
    """Test ask action returns permission=ask"""
    handle_payload = {
        'rule': {
            'action': 'ask',
            'reason': 'Confirm action'
        },
        'claude': {
            'hook_event_name': 'PreToolUse',
            'tool_name': 'Bash',
            'tool_input': {'command': 'rm file.txt'}
        }
    }

    result = await process(handle_payload)

    assert isinstance(result, HookResult)
    assert result.permission == 'ask'
    assert result.permission_reason == 'Confirm action'


@pytest.mark.asyncio
async def test_process_allow_action():
    """Test allow action returns permission=allow"""
    handle_payload = {
        'rule': {
            'action': 'allow',
            'reason': 'Safe command'
        },
        'claude': {
            'hook_event_name': 'PreToolUse',
            'tool_name': 'Bash',
            'tool_input': {'command': 'ls -la'}
        }
    }

    result = await process(handle_payload)

    assert isinstance(result, HookResult)
    assert result.permission == 'allow'
    assert result.permission_reason == 'Safe command'


@pytest.mark.asyncio
async def test_process_updated_input_simple():
    """Test updatedInput with simple pattern replacement"""
    handle_payload = {
        'rule': {
            'action': 'allow',
            'updatedInput': {
                'field': 'command',
                'pattern': '^rm\\b',
                'replace': 'trash-put'
            }
        },
        'claude': {
            'hook_event_name': 'PreToolUse',
            'tool_name': 'Bash',
            'tool_input': {'command': 'rm file.txt'}
        }
    }

    result = await process(handle_payload)

    assert isinstance(result, HookResult)
    assert result.permission == 'allow'
    assert result.updated_input is not None
    assert result.updated_input['command'] == 'trash-put file.txt'


@pytest.mark.asyncio
async def test_process_updated_input_no_match():
    """Test updatedInput when pattern doesn't match"""
    handle_payload = {
        'rule': {
            'action': 'allow',
            'updatedInput': {
                'field': 'command',
                'pattern': '^rmdir$',
                'replace': 'trash-put'
            }
        },
        'claude': {
            'hook_event_name': 'PreToolUse',
            'tool_name': 'Bash',
            'tool_input': {'command': 'rm file.txt'}
        }
    }

    result = await process(handle_payload)

    assert isinstance(result, HookResult)
    assert result.permission == 'allow'
    assert result.updated_input is None


@pytest.mark.asyncio
async def test_process_updated_input_missing_field():
    """Test updatedInput when specified field is missing in tool_input"""
    handle_payload = {
        'rule': {
            'action': 'allow',
            'updatedInput': {
                'field': 'nonexistent',
                'pattern': '^rm$',
                'replace': 'trash-put'
            }
        },
        'claude': {
            'hook_event_name': 'PreToolUse',
            'tool_name': 'Bash',
            'tool_input': {'command': 'rm file.txt'}
        }
    }

    result = await process(handle_payload)

    assert isinstance(result, HookResult)
    assert result.permission == 'allow'
    assert result.updated_input is None


@pytest.mark.asyncio
async def test_process_default_allow():
    """Test default action is allow"""
    handle_payload = {
        'rule': {},
        'claude': {
            'hook_event_name': 'PreToolUse',
            'tool_name': 'Bash',
            'tool_input': {'command': 'ls'}
        }
    }

    result = await process(handle_payload)

    assert isinstance(result, HookResult)
    assert result.permission == 'allow'


@pytest.mark.asyncio
async def test_process_event_name_set():
    """Test that event_name is always set to PreToolUse"""
    handle_payload = {
        'rule': {
            'action': 'deny'
        },
        'claude': {
            'hook_event_name': 'PreToolUse',
            'tool_name': 'Bash'
        }
    }

    result = await process(handle_payload)

    assert result.event_name == 'PreToolUse'


@pytest.mark.asyncio
async def test_process_updated_input_with_args():
    """Test updatedInput preserves command arguments"""
    handle_payload = {
        'rule': {
            'action': 'allow',
            'updatedInput': {
                'field': 'command',
                'pattern': '^grep\\b',
                'replace': 'rg'
            }
        },
        'claude': {
            'hook_event_name': 'PreToolUse',
            'tool_name': 'Bash',
            'tool_input': {'command': 'grep -i pattern /path/to/file'}
        }
    }

    result = await process(handle_payload)

    assert isinstance(result, HookResult)
    assert result.permission == 'allow'
    assert result.updated_input is not None
    assert result.updated_input['command'] == 'rg -i pattern /path/to/file'


@pytest.mark.asyncio
async def test_process_empty_tool_input():
    """Test handling of empty tool_input"""
    handle_payload = {
        'rule': {
            'action': 'allow'
        },
        'claude': {
            'hook_event_name': 'PreToolUse',
            'tool_name': 'Bash',
            'tool_input': {}
        }
    }

    result = await process(handle_payload)

    assert isinstance(result, HookResult)
    assert result.permission == 'allow'
