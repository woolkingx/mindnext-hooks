import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from handlers.SubagentStart import process
from type_defs import HookResult


@pytest.mark.asyncio
async def test_context_action():
    """Test SubagentStart with context action"""
    handle_payload = {
        'rule': {
            'action': 'context',
            'additionalContext': 'Subagent context'
        },
        'claude': {
            'hook_event_name': 'SubagentStart',
            'task_description': 'Data analysis',
            'subagent_type': 'specialized'
        }
    }

    result = await process(handle_payload)

    assert isinstance(result, HookResult)
    assert result.additional_context == 'Subagent context'
    assert result.event_name == 'SubagentStart'


@pytest.mark.asyncio
async def test_load_action_single_file():
    """Test SubagentStart with load action and single file loader"""
    test_content = "File content for test"

    with patch('pathlib.Path.read_text', return_value=test_content):
        handle_payload = {
            'rule': {
                'action': 'load',
                'loaders': [
                    {
                        'type': 'file',
                        'path': '/tmp/test.txt',
                        'label': 'Test File',
                        'enable': True
                    }
                ]
            },
            'claude': {
                'hook_event_name': 'SubagentStart',
                'task_description': 'Read files',
                'subagent_type': 'analyzer'
            }
        }

        result = await process(handle_payload)

        assert result is not None
        assert result.event_name == 'SubagentStart'
        assert 'Test File' in result.additional_context
        assert test_content in result.additional_context


@pytest.mark.asyncio
async def test_load_action_multiple_files():
    """Test SubagentStart with load action and multiple file loaders"""
    content1 = "Content 1"
    content2 = "Content 2"

    with patch('pathlib.Path.read_text', side_effect=[content1, content2]):
        handle_payload = {
            'rule': {
                'action': 'load',
                'loaders': [
                    {
                        'type': 'file',
                        'path': '/tmp/file1.txt',
                        'label': 'File 1',
                        'enable': True
                    },
                    {
                        'type': 'file',
                        'path': '/tmp/file2.txt',
                        'label': 'File 2',
                        'enable': True
                    }
                ]
            },
            'claude': {
                'hook_event_name': 'SubagentStart',
                'task_description': 'Load multiple files',
                'subagent_type': 'processor'
            }
        }

        result = await process(handle_payload)

        assert result is not None
        assert 'File 1' in result.additional_context
        assert 'File 2' in result.additional_context
        assert content1 in result.additional_context
        assert content2 in result.additional_context


@pytest.mark.asyncio
async def test_load_action_disabled_loader():
    """Test SubagentStart skips disabled loaders"""
    with patch('pathlib.Path.read_text') as mock_read:
        handle_payload = {
            'rule': {
                'action': 'load',
                'loaders': [
                    {
                        'type': 'file',
                        'path': '/tmp/enabled.txt',
                        'label': 'Enabled',
                        'enable': True
                    },
                    {
                        'type': 'file',
                        'path': '/tmp/disabled.txt',
                        'label': 'Disabled',
                        'enable': False
                    }
                ]
            },
            'claude': {
                'hook_event_name': 'SubagentStart',
                'task_description': 'Test',
                'subagent_type': 'test'
            }
        }

        mock_read.return_value = "Enabled content"
        result = await process(handle_payload)

        # Only enabled file should be read
        assert mock_read.call_count == 1
        assert 'Enabled' in result.additional_context
        assert 'Disabled' not in result.additional_context


@pytest.mark.asyncio
async def test_load_action_empty_loaders():
    """Test SubagentStart with load action but empty loaders"""
    handle_payload = {
        'rule': {
            'action': 'load',
            'loaders': []
        },
        'claude': {
            'hook_event_name': 'SubagentStart',
            'task_description': 'No files',
            'subagent_type': 'test'
        }
    }

    result = await process(handle_payload)

    assert result is None


@pytest.mark.asyncio
async def test_load_action_missing_path():
    """Test SubagentStart skips loaders without path"""
    handle_payload = {
        'rule': {
            'action': 'load',
            'loaders': [
                {
                    'type': 'file',
                    'label': 'No Path',
                    'enable': True
                }
            ]
        },
        'claude': {
            'hook_event_name': 'SubagentStart',
            'task_description': 'Test',
            'subagent_type': 'test'
        }
    }

    result = await process(handle_payload)

    assert result is None


@pytest.mark.asyncio
async def test_no_action():
    """Test SubagentStart with no action returns None"""
    handle_payload = {
        'rule': {},
        'claude': {
            'hook_event_name': 'SubagentStart',
            'task_description': 'Test',
            'subagent_type': 'generic'
        }
    }

    result = await process(handle_payload)

    assert result is None


@pytest.mark.asyncio
async def test_load_action_file_read_error():
    """Test SubagentStart handles file read errors gracefully"""
    with patch('pathlib.Path.read_text', side_effect=IOError("File not found")):
        handle_payload = {
            'rule': {
                'action': 'load',
                'loaders': [
                    {
                        'type': 'file',
                        'path': '/nonexistent/file.txt',
                        'label': 'Missing',
                        'enable': True
                    }
                ]
            },
            'claude': {
                'hook_event_name': 'SubagentStart',
                'task_description': 'Test error handling',
                'subagent_type': 'test'
            }
        }

        result = await process(handle_payload)

        # Should return None when all files fail
        assert result is None


@pytest.mark.asyncio
async def test_load_action_default_label():
    """Test SubagentStart uses path as label when label not provided"""
    test_content = "Content"

    with patch('pathlib.Path.read_text', return_value=test_content):
        handle_payload = {
            'rule': {
                'action': 'load',
                'loaders': [
                    {
                        'type': 'file',
                        'path': '/tmp/default_label.txt',
                        'enable': True
                    }
                ]
            },
            'claude': {
                'hook_event_name': 'SubagentStart',
                'task_description': 'Test',
                'subagent_type': 'test'
            }
        }

        result = await process(handle_payload)

        assert result is not None
        assert '/tmp/default_label.txt' in result.additional_context


@pytest.mark.asyncio
async def test_context_empty_additional_context():
    """Test SubagentStart context action with empty additionalContext"""
    handle_payload = {
        'rule': {
            'action': 'context',
            'additionalContext': ''
        },
        'claude': {
            'hook_event_name': 'SubagentStart',
            'task_description': 'Empty context',
            'subagent_type': 'test'
        }
    }

    result = await process(handle_payload)

    assert result is not None
    assert result.additional_context == ''
    assert result.event_name == 'SubagentStart'
