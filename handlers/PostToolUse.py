"""Handle 層：PostToolUse 事件處理

職責：
- 處理工具執行後的決策（阻止、允許、注入 context）
- 支援 block action
- 支援 additionalContext 注入
"""
from typing import Optional, Dict, Any
from type_defs import HookResult
from utils.context import get_event


async def process(rule: Dict[str, Any]) -> Optional[HookResult]:
    """處理 PostToolUse 事件

    工作流：
    1. 從全局 EventContext 取得 event
    2. 根據 action 決定是否阻止
    3. 若有 additionalContext，直接注入（優先級最高）
    4. 返回 HookResult 或 None

    PostToolUse 支援的 actions:
    - block: 阻止工具輸出
    - additionalContext: 注入額外 context
    """
    event = get_event()

    if event.hook_event_name != 'PostToolUse':
        return None

    # 1. additionalContext（直接注入，最優先）
    if 'additionalContext' in rule:
        return HookResult(
            event_name='PostToolUse',
            additional_context=rule['additionalContext']
        )

    # 2. action: block
    if rule.get('action') == 'block':
        return HookResult(
            event_name='PostToolUse',
            block=True,
            block_reason=rule.get('reason', 'Blocked')
        )

    # 3. 無 action，返回 None
    return None
