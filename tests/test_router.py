import pytest
from router import build_handle_payload


def test_build_handle_payload():
    rule = {'name': 'test-rule', 'event': 'PreToolUse'}
    claude = {'hook_event_name': 'PreToolUse', 'tool_name': 'Bash'}

    handle_payload = build_handle_payload(rule, claude)

    assert handle_payload['rule'] == rule
    assert handle_payload['claude'] == claude
