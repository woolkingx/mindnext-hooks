"""Tests for v2/output.py merge() function

Priority-based merging: deny > ask > allow > block > context
"""
import pytest
from type_defs import HookResult
from output import merge


class TestMergeBasics:
    """Basic merge scenarios"""

    def test_merge_empty_list(self):
        """Empty list returns None"""
        result = merge([])
        assert result is None

    def test_merge_single_result(self):
        """Single result returns itself"""
        original = HookResult(
            event_name='PreToolUse',
            permission='deny',
            permission_reason='test reason'
        )
        result = merge([original])
        assert result is original

    def test_merge_preserves_event_name(self):
        """Event name is preserved from highest priority result"""
        results = [
            HookResult(event_name='PreToolUse', permission='allow'),
            HookResult(event_name='PreToolUse', permission='deny', permission_reason='denied'),
        ]
        result = merge(results)
        assert result.event_name == 'PreToolUse'


class TestMergeDenyPriority:
    """deny > ask > allow > block > context"""

    def test_merge_deny_beats_ask(self):
        """deny beats ask"""
        results = [
            HookResult(permission='ask', permission_reason='please confirm'),
            HookResult(permission='deny', permission_reason='blocked'),
        ]
        result = merge(results)
        assert result.permission == 'deny'
        assert 'blocked' in result.permission_reason

    def test_merge_deny_beats_allow(self):
        """deny beats allow"""
        results = [
            HookResult(permission='allow'),
            HookResult(permission='deny', permission_reason='denied'),
        ]
        result = merge(results)
        assert result.permission == 'deny'
        assert result.permission_reason == 'denied'

    def test_merge_multiple_deny_reasons(self):
        """Multiple deny results merge reasons"""
        results = [
            HookResult(permission='deny', permission_reason='reason 1'),
            HookResult(permission='deny', permission_reason='reason 2'),
            HookResult(permission='deny', permission_reason='reason 3'),
        ]
        result = merge(results)
        assert result.permission == 'deny'
        assert 'reason 1' in result.permission_reason
        assert 'reason 2' in result.permission_reason
        assert 'reason 3' in result.permission_reason

    def test_merge_deny_with_block_and_context(self):
        """deny beats block and context"""
        results = [
            HookResult(additional_context='some context'),
            HookResult(block=True, block_reason='blocked'),
            HookResult(permission='deny', permission_reason='denied'),
        ]
        result = merge(results)
        assert result.permission == 'deny'
        assert result.block is False
        assert result.additional_context is None


class TestMergeAskPriority:
    """ask priority tests"""

    def test_merge_ask_beats_allow(self):
        """ask beats allow"""
        results = [
            HookResult(permission='allow'),
            HookResult(permission='ask', permission_reason='confirm'),
        ]
        result = merge(results)
        assert result.permission == 'ask'
        assert result.permission_reason == 'confirm'

    def test_merge_ask_beats_block(self):
        """ask beats block"""
        results = [
            HookResult(block=True, block_reason='blocked'),
            HookResult(permission='ask', permission_reason='confirm'),
        ]
        result = merge(results)
        assert result.permission == 'ask'
        assert result.block is False

    def test_merge_ask_beats_context(self):
        """ask beats context only"""
        results = [
            HookResult(additional_context='context'),
            HookResult(permission='ask', permission_reason='confirm'),
        ]
        result = merge(results)
        assert result.permission == 'ask'
        assert result.additional_context is None

    def test_merge_multiple_ask_reasons(self):
        """Multiple ask results merge reasons"""
        results = [
            HookResult(permission='ask', permission_reason='reason 1'),
            HookResult(permission='ask', permission_reason='reason 2'),
        ]
        result = merge(results)
        assert result.permission == 'ask'
        assert 'reason 1' in result.permission_reason
        assert 'reason 2' in result.permission_reason


class TestMergeAllowPriority:
    """allow priority tests"""

    def test_merge_allow_beats_block(self):
        """allow beats block"""
        results = [
            HookResult(block=True, block_reason='blocked'),
            HookResult(permission='allow'),
        ]
        result = merge(results)
        assert result.permission == 'allow'
        assert result.block is False

    def test_merge_allow_beats_context(self):
        """allow beats context"""
        results = [
            HookResult(additional_context='context'),
            HookResult(permission='allow'),
        ]
        result = merge(results)
        assert result.permission == 'allow'
        assert result.additional_context is None

    def test_merge_allow_with_updated_input(self):
        """allow preserves updated_input"""
        updated = {'command': 'transformed_command'}
        results = [
            HookResult(permission='allow', updated_input=updated),
            HookResult(permission='allow'),
        ]
        result = merge(results)
        assert result.permission == 'allow'
        assert result.updated_input == updated

    def test_merge_allow_multiple_reasons(self):
        """Multiple allow results merge reasons"""
        results = [
            HookResult(permission='allow', permission_reason='reason 1'),
            HookResult(permission='allow', permission_reason='reason 2'),
        ]
        result = merge(results)
        assert result.permission == 'allow'
        assert 'reason 1' in result.permission_reason
        assert 'reason 2' in result.permission_reason


class TestMergeBlockPriority:
    """block priority tests"""

    def test_merge_block_beats_context(self):
        """block beats context only"""
        results = [
            HookResult(additional_context='context'),
            HookResult(block=True, block_reason='blocked'),
        ]
        result = merge(results)
        assert result.block is True
        assert result.additional_context is None

    def test_merge_multiple_block_reasons(self):
        """Multiple block results merge reasons"""
        results = [
            HookResult(block=True, block_reason='reason 1'),
            HookResult(block=True, block_reason='reason 2'),
            HookResult(block=True, block_reason='reason 3'),
        ]
        result = merge(results)
        assert result.block is True
        assert 'reason 1' in result.block_reason
        assert 'reason 2' in result.block_reason
        assert 'reason 3' in result.block_reason

    def test_merge_block_without_reason(self):
        """block without reason handled"""
        results = [
            HookResult(block=True),
            HookResult(block=True, block_reason='reason 1'),
        ]
        result = merge(results)
        assert result.block is True
        assert result.block_reason == 'reason 1'


class TestMergeContextOnly:
    """Context-only merge scenarios"""

    def test_merge_single_context(self):
        """Single context returns as-is"""
        result = merge([HookResult(additional_context='some context')])
        assert result.additional_context == 'some context'

    def test_merge_multiple_contexts(self):
        """Multiple contexts are merged with \\n\\n separator"""
        results = [
            HookResult(additional_context='context 1'),
            HookResult(additional_context='context 2'),
            HookResult(additional_context='context 3'),
        ]
        result = merge(results)
        assert result.additional_context == 'context 1\n\ncontext 2\n\ncontext 3'

    def test_merge_contexts_with_none(self):
        """None contexts are ignored"""
        results = [
            HookResult(additional_context='context 1'),
            HookResult(additional_context=None),
            HookResult(additional_context='context 2'),
        ]
        result = merge(results)
        assert result.additional_context == 'context 1\n\ncontext 2'

    def test_merge_empty_contexts_ignored(self):
        """Empty string contexts are ignored"""
        results = [
            HookResult(additional_context='context 1'),
            HookResult(additional_context=''),
            HookResult(additional_context='context 2'),
        ]
        result = merge(results)
        assert result.additional_context == 'context 1\n\ncontext 2'


class TestMergeComplexScenarios:
    """Complex real-world scenarios"""

    def test_merge_mixed_priority_chain(self):
        """All priority levels mixed - highest wins"""
        results = [
            HookResult(additional_context='context'),
            HookResult(block=True, block_reason='blocked'),
            HookResult(permission='allow'),
            HookResult(permission='ask', permission_reason='confirm'),
            HookResult(permission='deny', permission_reason='denied'),
        ]
        result = merge(results)
        assert result.permission == 'deny'
        assert result.permission_reason == 'denied'
        assert result.block is False
        assert result.additional_context is None

    def test_merge_with_none_results(self):
        """Results with no active fields"""
        results = [
            HookResult(event_name='PreToolUse'),
            HookResult(permission='deny', permission_reason='denied'),
        ]
        result = merge(results)
        assert result.permission == 'deny'

    def test_merge_preserves_first_event_name(self):
        """Event name comes from first result"""
        results = [
            HookResult(event_name='Event1', permission='deny'),
            HookResult(event_name='Event2', permission='allow'),
        ]
        result = merge(results)
        # Event name from deny result (highest priority)
        assert result.event_name == 'Event1'

    def test_merge_permission_with_updated_input_and_allow(self):
        """allow with updated_input is preserved"""
        updated = {'modified': True}
        results = [
            HookResult(permission='allow', updated_input=updated),
        ]
        result = merge(results)
        assert result.permission == 'allow'
        assert result.updated_input == updated

    def test_merge_complex_with_system_fields(self):
        """System fields are preserved appropriately"""
        results = [
            HookResult(
                permission='allow',
                continue_processing=False,
                suppress=True,
            ),
        ]
        result = merge(results)
        assert result.permission == 'allow'
        assert result.continue_processing is False
        assert result.suppress is True


class TestMergeEdgeCases:
    """Edge cases and boundary conditions"""

    def test_merge_only_interrupt_flag(self):
        """interrupt flag preserved from permission results"""
        results = [
            HookResult(permission='deny', interrupt=True),
        ]
        result = merge(results)
        assert result.interrupt is True

    def test_merge_deny_without_reason(self):
        """deny without reason handled"""
        results = [
            HookResult(permission='deny'),
            HookResult(permission='ask', permission_reason='reason'),
        ]
        result = merge(results)
        assert result.permission == 'deny'
        # Should have ask reason merged
        assert result.permission_reason is None or result.permission_reason == ''

    def test_merge_first_updated_input_wins(self):
        """First updated_input in allow results wins"""
        updated1 = {'first': True}
        updated2 = {'second': True}
        results = [
            HookResult(permission='allow', updated_input=updated1),
            HookResult(permission='allow', updated_input=updated2),
        ]
        result = merge(results)
        assert result.updated_input == updated1

    def test_merge_with_false_block_ignored(self):
        """False block values ignored"""
        results = [
            HookResult(block=False),
            HookResult(block=False),
            HookResult(additional_context='context'),
        ]
        result = merge(results)
        assert result.block is False
        assert result.additional_context == 'context'

    def test_merge_very_long_context_chain(self):
        """Many contexts merged correctly"""
        contexts = [f'context {i}' for i in range(100)]
        results = [HookResult(additional_context=ctx) for ctx in contexts]
        result = merge(results)
        assert result.additional_context == '\n\n'.join(contexts)

    def test_merge_multiple_deny_no_reason(self):
        """Multiple deny without reasons"""
        results = [
            HookResult(permission='deny'),
            HookResult(permission='deny'),
        ]
        result = merge(results)
        assert result.permission == 'deny'
        assert result.permission_reason is None or result.permission_reason == ''
