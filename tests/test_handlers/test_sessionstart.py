import pytest
from pathlib import Path
import tempfile
from handlers.SessionStart import process
from type_defs import HookResult


@pytest.mark.asyncio
async def test_process_with_additional_context():
    """Test SessionStart with additionalContext returns additional_context"""
    handle_payload = {
        'rule': {
            'additionalContext': 'Session context from rule'
        },
        'claude': {
            'hook_event_name': 'SessionStart',
            'source': 'user'
        }
    }

    result = await process(handle_payload)

    assert isinstance(result, HookResult)
    assert result.additional_context == 'Session context from rule'


@pytest.mark.asyncio
async def test_process_no_action():
    """Test SessionStart with no action returns None"""
    handle_payload = {
        'rule': {},
        'claude': {
            'hook_event_name': 'SessionStart',
            'source': 'user'
        }
    }

    result = await process(handle_payload)

    assert result is None


@pytest.mark.asyncio
async def test_process_event_name_set():
    """Test that event_name is set when returning HookResult"""
    handle_payload = {
        'rule': {
            'additionalContext': 'Test context'
        },
        'claude': {
            'hook_event_name': 'SessionStart'
        }
    }

    result = await process(handle_payload)

    assert result is not None
    assert result.event_name == 'SessionStart'


@pytest.mark.asyncio
async def test_process_with_load_single_file():
    """Test SessionStart with load action for a single file"""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / 'test.txt'
        test_file.write_text('Test file content')

        handle_payload = {
            'rule': {
                'action': 'load',
                'loaders': [
                    {
                        'enable': True,
                        'type': 'file',
                        'path': str(test_file),
                        'label': 'Test File'
                    }
                ]
            },
            'claude': {
                'hook_event_name': 'SessionStart'
            }
        }

        result = await process(handle_payload)

        assert isinstance(result, HookResult)
        assert result.additional_context is not None
        assert 'Test File' in result.additional_context
        assert 'Test file content' in result.additional_context


@pytest.mark.asyncio
async def test_process_with_load_multiple_files():
    """Test SessionStart with load action for multiple files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        file1 = Path(tmpdir) / 'file1.txt'
        file2 = Path(tmpdir) / 'file2.txt'
        file1.write_text('Content 1')
        file2.write_text('Content 2')

        handle_payload = {
            'rule': {
                'action': 'load',
                'loaders': [
                    {
                        'enable': True,
                        'type': 'file',
                        'path': str(file1),
                        'label': 'File 1'
                    },
                    {
                        'enable': True,
                        'type': 'file',
                        'path': str(file2),
                        'label': 'File 2'
                    }
                ]
            },
            'claude': {
                'hook_event_name': 'SessionStart'
            }
        }

        result = await process(handle_payload)

        assert isinstance(result, HookResult)
        assert result.additional_context is not None
        assert 'File 1' in result.additional_context
        assert 'Content 1' in result.additional_context
        assert 'File 2' in result.additional_context
        assert 'Content 2' in result.additional_context


@pytest.mark.asyncio
async def test_process_with_load_disabled_loader():
    """Test SessionStart with disabled loader is skipped"""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / 'test.txt'
        test_file.write_text('Test content')

        handle_payload = {
            'rule': {
                'action': 'load',
                'loaders': [
                    {
                        'enable': False,
                        'type': 'file',
                        'path': str(test_file),
                        'label': 'Disabled File'
                    }
                ]
            },
            'claude': {
                'hook_event_name': 'SessionStart'
            }
        }

        result = await process(handle_payload)

        assert result is None


@pytest.mark.asyncio
async def test_process_with_load_nonexistent_file():
    """Test SessionStart with load action for nonexistent file is ignored"""
    handle_payload = {
        'rule': {
            'action': 'load',
            'loaders': [
                {
                    'enable': True,
                    'type': 'file',
                    'path': '/nonexistent/path/file.txt',
                    'label': 'Nonexistent'
                }
            ]
        },
        'claude': {
            'hook_event_name': 'SessionStart'
        }
    }

    result = await process(handle_payload)

    assert result is None


@pytest.mark.asyncio
async def test_process_with_context_action():
    """Test SessionStart with context action"""
    handle_payload = {
        'rule': {
            'action': 'context',
            'additionalContext': 'Direct context text'
        },
        'claude': {
            'hook_event_name': 'SessionStart'
        }
    }

    result = await process(handle_payload)

    assert isinstance(result, HookResult)
    assert result.additional_context == 'Direct context text'
    assert result.event_name == 'SessionStart'


@pytest.mark.asyncio
async def test_process_with_load_empty_loaders():
    """Test SessionStart with load action but empty loaders"""
    handle_payload = {
        'rule': {
            'action': 'load',
            'loaders': []
        },
        'claude': {
            'hook_event_name': 'SessionStart'
        }
    }

    result = await process(handle_payload)

    assert result is None


@pytest.mark.asyncio
async def test_process_with_load_no_loaders():
    """Test SessionStart with load action but no loaders key"""
    handle_payload = {
        'rule': {
            'action': 'load'
        },
        'claude': {
            'hook_event_name': 'SessionStart'
        }
    }

    result = await process(handle_payload)

    assert result is None


@pytest.mark.asyncio
async def test_process_with_load_non_file_type():
    """Test SessionStart with load action for non-file type loader"""
    handle_payload = {
        'rule': {
            'action': 'load',
            'loaders': [
                {
                    'enable': True,
                    'type': 'database',
                    'path': 'db://connection',
                    'label': 'Database'
                }
            ]
        },
        'claude': {
            'hook_event_name': 'SessionStart'
        }
    }

    result = await process(handle_payload)

    assert result is None


@pytest.mark.asyncio
async def test_process_with_load_and_default_label():
    """Test SessionStart with load action uses path as label when label not provided"""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / 'test.txt'
        test_file.write_text('Test content')

        handle_payload = {
            'rule': {
                'action': 'load',
                'loaders': [
                    {
                        'enable': True,
                        'type': 'file',
                        'path': str(test_file)
                    }
                ]
            },
            'claude': {
                'hook_event_name': 'SessionStart'
            }
        }

        result = await process(handle_payload)

        assert isinstance(result, HookResult)
        assert result.additional_context is not None
        assert str(test_file) in result.additional_context
        assert 'Test content' in result.additional_context
