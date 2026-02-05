import pytest
from handlers.UserPromptSubmit import process
from type_defs import HookResult

@pytest.mark.asyncio
async def test_process_block_action():
    handle_payload = {
        'rule': {
            'action': 'block',
            'reason': 'test block'
        },
        'claude': {
            'hook_event_name': 'UserPromptSubmit',
            'prompt': 'test'
        }
    }

    result = await process(handle_payload)

    assert isinstance(result, HookResult)
    assert result.block == True
    assert result.block_reason == 'test block'

@pytest.mark.asyncio
async def test_process_additional_context():
    handle_payload = {
        'rule': {
            'additionalContext': 'test context'
        },
        'claude': {
            'hook_event_name': 'UserPromptSubmit',
            'prompt': 'test'
        }
    }

    result = await process(handle_payload)

    assert isinstance(result, HookResult)
    assert result.additional_context == 'test context'
