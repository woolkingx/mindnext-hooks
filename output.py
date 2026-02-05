"""Output Management: merge + emit"""
import json
import sys
import os
from typing import List, Optional
from type_defs import HookResult
from utils.logger import get_logger

logger = get_logger("output")


def merge(results: List[HookResult]) -> Optional[HookResult]:
    """整合多個 HookResult

    優先級：deny > ask > allow > block > context
    permission 類型互斥（只能有一個 deny/ask/allow）
    context 應該合併所有 additional_context
    """
    if not results:
        return None
    if len(results) == 1:
        return results[0]

    def _collect_reasons(results: List[HookResult], permission: str) -> List[str]:
        """收集指定 permission 類型的所有 reasons"""
        reasons = []
        for r in results:
            if getattr(r, 'permission', None) == permission:
                reason = getattr(r, 'permission_reason', None)
                if reason:
                    reasons.append(reason)
        return reasons

    # 優先級 1: deny
    deny_results = [r for r in results if getattr(r, 'permission', None) == 'deny']
    if deny_results:
        reasons = _collect_reasons(results, 'deny')
        return HookResult(
            event_name=deny_results[0].event_name,
            permission='deny',
            permission_reason='\n'.join(reasons) if reasons else deny_results[0].permission_reason,
            interrupt=any(r.interrupt for r in deny_results),
        )

    # 優先級 2: ask
    ask_results = [r for r in results if getattr(r, 'permission', None) == 'ask']
    if ask_results:
        reasons = _collect_reasons(results, 'ask')
        return HookResult(
            event_name=ask_results[0].event_name,
            permission='ask',
            permission_reason='\n'.join(reasons) if reasons else ask_results[0].permission_reason,
        )

    # 優先級 3: allow
    allow_results = [r for r in results if getattr(r, 'permission', None) == 'allow']
    if allow_results:
        reasons = _collect_reasons(results, 'allow')
        # 合併 updated_input - 取第一個有值的
        merged_updated_input = None
        for r in allow_results:
            if getattr(r, 'updated_input', None):
                merged_updated_input = r.updated_input
                break
        return HookResult(
            event_name=allow_results[0].event_name,
            permission='allow',
            permission_reason='\n'.join(reasons) if reasons else allow_results[0].permission_reason,
            updated_input=merged_updated_input,
        )

    # 優先級 4: block
    block_results = [r for r in results if getattr(r, 'block', False)]
    if block_results:
        reasons = [r.block_reason for r in block_results if getattr(r, 'block_reason', None)]
        return HookResult(
            event_name=block_results[0].event_name,
            block=True,
            block_reason='\n'.join(reasons) if reasons else block_results[0].block_reason,
        )

    # 優先級 5: 合併 additional_context
    contexts = [
        r.additional_context for r in results
        if getattr(r, 'additional_context', None)
    ]
    if contexts:
        first = results[0]
        return HookResult(
            event_name=first.event_name,
            additional_context='\n\n'.join(contexts),
        )

    # 沒有任何結果 - 返回第一個
    return results[0]


def emit(result: Optional[HookResult], event_name: str = ''):
    """Output JSON to stdout

    Output fields according to official Schema definitions

    Optional validation: Set HOOKS_VALIDATE_OUTPUT=1 to enable schema validation
    """
    if not result:
        print(json.dumps({}))
        sys.exit(0)

    output = {}
    hook_specific = {}

    logger.debug(f"Emitting output for event: {event_name}")

    # 1. System 控制欄位 (所有事件可用)
    if not result.continue_processing:
        output['continue'] = False
    if result.stop_reason:
        output['stopReason'] = result.stop_reason
    if result.suppress:
        output['suppressOutput'] = True
    if result.system_message:
        output['systemMessage'] = result.system_message

    # 2. Permission 類 (PreToolUse, PermissionRequest)
    if result.permission:
        # PermissionRequest 使用嵌套 decision.behavior 結構
        if event_name == 'PermissionRequest':
            decision_obj = {'behavior': result.permission}
            if result.permission_reason:
                decision_obj['message'] = result.permission_reason
            if result.updated_input:
                decision_obj['updatedInput'] = result.updated_input
            if result.interrupt:
                decision_obj['interrupt'] = result.interrupt
            hook_specific['decision'] = decision_obj
        else:
            # PreToolUse 使用 permissionDecision
            hook_specific['permissionDecision'] = result.permission
            if result.permission_reason:
                hook_specific['permissionDecisionReason'] = result.permission_reason
            if result.updated_input:
                hook_specific['updatedInput'] = result.updated_input

    # 3. Decision 類 (PostToolUse, Stop, SubagentStop)
    if result.block:
        # Stop/SubagentStop 使用 decision+reason
        if event_name in ['Stop', 'SubagentStop']:
            output['decision'] = 'block'
            if result.block_reason:
                output['reason'] = result.block_reason
        else:
            # PostToolUse, UserPromptSubmit 使用 decision+reason
            output['decision'] = 'block'
            if result.block_reason:
                output['reason'] = result.block_reason

    # 4. Context 注入 (所有事件)
    if result.additional_context:
        hook_specific['additionalContext'] = result.additional_context

    # 5. Output hookSpecificOutput
    if hook_specific:
        # CRITICAL: hookEventName 是必填欄位 (官方 API 要求)
        hook_specific['hookEventName'] = event_name or result.event_name
        output['hookSpecificOutput'] = hook_specific

    # 6. Optional: Validate output schema (development/testing)
    if os.getenv('HOOKS_VALIDATE_OUTPUT') == '1':
        _validate_output(output, event_name)

    logger.debug(f"Output keys: {list(output.keys())}")
    print(json.dumps(output, ensure_ascii=False))
    sys.exit(0)


def _validate_output(output: dict, event_name: str):
    """Validate output against schema (optional, for development)

    Only runs if HOOKS_VALIDATE_OUTPUT=1 environment variable is set.
    Logs warnings if validation fails but does not block output.
    """
    try:
        from utils.schema_validator import validate_response
        error = validate_response(event_name, output)
        if error:
            logger.warning(f"Output schema validation failed for {event_name}: {error}")
        else:
            logger.debug(f"Output schema validation passed for {event_name}")
    except ImportError:
        logger.debug("Schema validation skipped (jsonschema not installed)")
    except Exception as e:
        logger.warning(f"Output schema validation error: {e}")
