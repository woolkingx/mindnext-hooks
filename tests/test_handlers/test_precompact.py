import pytest
import sys
from io import StringIO
from unittest.mock import patch
from handlers.PreCompact import process
from type_defs import HookResult


@pytest.mark.asyncio
async def test_stderr_action_exits_2():
    """Test PreCompact with stderr action prints to stderr and exits with code 2"""
    handle_payload = {
        'rule': {
            'action': 'stderr',
            'reason': 'Error message'
        },
        'claude': {
            'hook_event_name': 'PreCompact',
            'trigger': 'before_compact'
        }
    }

    with patch('sys.exit') as mock_exit:
        with patch('builtins.print') as mock_print:
            result = await process(handle_payload)

            # Should print to stderr
            mock_print.assert_called_once_with('Error message', file=sys.stderr)
            # Should exit with code 2
            mock_exit.assert_called_once_with(2)
            # Should return None
            assert result is None


@pytest.mark.asyncio
async def test_stdout_action_exits_0():
    """Test PreCompact with stdout action prints to stdout and exits with code 0"""
    handle_payload = {
        'rule': {
            'action': 'stdout',
            'reason': 'Success message'
        },
        'claude': {
            'hook_event_name': 'PreCompact',
            'trigger': 'before_compact'
        }
    }

    with patch('sys.exit') as mock_exit:
        with patch('builtins.print') as mock_print:
            result = await process(handle_payload)

            # Should print to stdout
            mock_print.assert_called_once_with('Success message')
            # Should exit with code 0
            mock_exit.assert_called_once_with(0)
            # Should return None
            assert result is None


@pytest.mark.asyncio
async def test_no_action():
    """Test PreCompact with no action returns None"""
    handle_payload = {
        'rule': {},
        'claude': {
            'hook_event_name': 'PreCompact',
            'trigger': 'before_compact'
        }
    }

    result = await process(handle_payload)

    assert result is None


@pytest.mark.asyncio
async def test_no_reason():
    """Test PreCompact with action but no reason returns None"""
    handle_payload = {
        'rule': {
            'action': 'stderr'
        },
        'claude': {
            'hook_event_name': 'PreCompact',
            'trigger': 'before_compact'
        }
    }

    result = await process(handle_payload)

    assert result is None


@pytest.mark.asyncio
async def test_empty_reason():
    """Test PreCompact with empty reason returns None"""
    handle_payload = {
        'rule': {
            'action': 'stderr',
            'reason': ''
        },
        'claude': {
            'hook_event_name': 'PreCompact'
        }
    }

    result = await process(handle_payload)

    assert result is None


@pytest.mark.asyncio
async def test_reason_with_whitespace():
    """Test PreCompact strips whitespace from reason"""
    handle_payload = {
        'rule': {
            'action': 'stdout',
            'reason': '  \n  Message with whitespace  \n  '
        },
        'claude': {
            'hook_event_name': 'PreCompact'
        }
    }

    with patch('sys.exit') as mock_exit:
        with patch('builtins.print') as mock_print:
            result = await process(handle_payload)

            # Should strip whitespace
            mock_print.assert_called_once_with('Message with whitespace')
            mock_exit.assert_called_once_with(0)


@pytest.mark.asyncio
async def test_unknown_action():
    """Test PreCompact with unknown action returns None"""
    handle_payload = {
        'rule': {
            'action': 'unknown_action',
            'reason': 'Some message'
        },
        'claude': {
            'hook_event_name': 'PreCompact'
        }
    }

    result = await process(handle_payload)

    assert result is None


@pytest.mark.asyncio
async def test_multiline_reason_stderr():
    """Test PreCompact with multiline reason for stderr"""
    multiline_reason = "Line 1\nLine 2\nLine 3"
    handle_payload = {
        'rule': {
            'action': 'stderr',
            'reason': multiline_reason
        },
        'claude': {
            'hook_event_name': 'PreCompact'
        }
    }

    with patch('sys.exit') as mock_exit:
        with patch('builtins.print') as mock_print:
            result = await process(handle_payload)

            mock_print.assert_called_once_with(multiline_reason, file=sys.stderr)
            mock_exit.assert_called_once_with(2)


@pytest.mark.asyncio
async def test_multiline_reason_stdout():
    """Test PreCompact with multiline reason for stdout"""
    multiline_reason = "Output 1\nOutput 2"
    handle_payload = {
        'rule': {
            'action': 'stdout',
            'reason': multiline_reason
        },
        'claude': {
            'hook_event_name': 'PreCompact'
        }
    }

    with patch('sys.exit') as mock_exit:
        with patch('builtins.print') as mock_print:
            result = await process(handle_payload)

            mock_print.assert_called_once_with(multiline_reason)
            mock_exit.assert_called_once_with(0)


@pytest.mark.asyncio
async def test_unicode_reason():
    """Test PreCompact with unicode characters in reason"""
    unicode_reason = "錯誤 🔴 Error occurred"
    handle_payload = {
        'rule': {
            'action': 'stderr',
            'reason': unicode_reason
        },
        'claude': {
            'hook_event_name': 'PreCompact'
        }
    }

    with patch('sys.exit') as mock_exit:
        with patch('builtins.print') as mock_print:
            result = await process(handle_payload)

            mock_print.assert_called_once_with(unicode_reason, file=sys.stderr)
            mock_exit.assert_called_once_with(2)
