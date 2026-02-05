"""Handler Layer: PreToolUse Event Processing

Responsibilities:
- Handle permission control before tool invocation
- Support deny/ask/allow/transform actions
- Support updatedInput transformation
"""
import re
from typing import Optional, Dict, Any
from type_defs import HookResult
from utils.context import get_event
from utils.logger import get_logger

logger = get_logger("handlers.PreToolUse")


async def process(rule: Dict[str, Any]) -> Optional[HookResult]:
    """Process PreToolUse event

    Workflow:
    1. Get event from global EventContext
    2. Determine permission based on action
    3. Apply updatedInput transformation if present
    4. Return HookResult
    """
    event = get_event()

    # Type narrowing
    if event.hook_event_name != 'PreToolUse':
        logger.warning("Event is not PreToolUse type")
        return None

    action = rule.get('action', 'allow')
    reason = rule.get('reason')
    rule_name = rule.get('name', 'unknown')

    logger.debug(f"Processing PreToolUse: action={action}, tool={event.tool_name}")

    # 1. deny: Reject tool invocation
    if action == 'deny':
        logger.info(f"Rule {rule_name}: Denying tool {event.tool_name}")
        return HookResult(
            event_name='PreToolUse',
            permission='deny',
            permission_reason=reason or 'Denied'
        )

    # 2. ask: Request user confirmation
    if action == 'ask':
        logger.info(f"Rule {rule_name}: Asking for confirmation on {event.tool_name}")
        return HookResult(
            event_name='PreToolUse',
            permission='ask',
            permission_reason=reason or 'Confirm?'
        )

    # 3. transform/allow + updatedInput: Allow and optionally transform
    # Both transform and allow can include updatedInput
    updated_input = None
    if 'updatedInput' in rule:
        logger.debug(f"Rule {rule_name}: Applying updatedInput transformation")
        updated_input = _apply_updated_input(
            rule['updatedInput'],
            event.tool_input
        )
        if updated_input:
            logger.info(f"Rule {rule_name}: Transformed tool input")

    return HookResult(
        event_name='PreToolUse',
        permission='allow',
        permission_reason=reason,
        updated_input=updated_input
    )


def _apply_updated_input(
    config: Dict[str, Any],
    tool_input: Any
) -> Optional[Dict[str, Any]]:
    """應用 updatedInput 轉換

    基於 field 和 pattern/replace 進行字串替換
    支援命令行級別替換（例如 rm → trash-put）

    Args:
        config: updatedInput 設定
            {
                'field': 'command',      # 要轉換的欄位
                'pattern': '^rm$',       # 匹配 pattern
                'replace': 'trash-put'   # 替換為新值
            }
        tool_input: 原始工具輸入

    Returns:
        轉換後的 tool_input，若無需轉換返回 None

    說明：
        - pattern 使用正則表達式
        - 對於命令行，典型用法是 '^cmd(\\b|$)' 匹配命令邊界
        - 不需要 $ 結尾，會自動在字串中替換匹配部分
    """
    field = config.get('field')
    pattern = config.get('pattern')
    replace = config.get('replace')

    # 驗證必要欄位
    if not all([field, pattern, replace]):
        return None

    # object-first input normalization
    if isinstance(tool_input, dict):
        tool_input_dict = dict(tool_input)
    else:
        to_dict = getattr(tool_input, "to_dict", None)
        if callable(to_dict):
            tool_input_dict = to_dict()
        else:
            items = getattr(tool_input, "items", None)
            if callable(items):
                tool_input_dict = dict(items())
            else:
                return None

    # 檢查 field 是否存在
    if field not in tool_input_dict:
        return None

    original = tool_input_dict[field]

    # 執行 pattern 替換
    try:
        # 使用 re.sub 進行替換（會替換所有匹配）
        modified = re.sub(pattern, replace, original)

        # 若沒有改變，返回 None
        if modified == original:
            return None

        # 返回更新後的 tool_input
        return {**tool_input_dict, field: modified}

    except re.error:
        # Pattern 無效，返回 None
        return None
