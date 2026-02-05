"""Handle 層：Stop 事件處理

職責：
- 在 Stop 事件時進行控制決策
- 支援 block action（阻止停止）
- 無 permission（Stop 無權限控制）
- 支援 additionalContext 注入
"""
from typing import Optional, Dict, Any
from type_defs import HookResult
from utils.context import get_event


async def process(rule: Dict[str, Any]) -> Optional[HookResult]:
    """處理 Stop 事件

    工作流：
    1. 從全局取得 event
    2. 檢查是否有 additionalContext（優先使用）
    3. 根據 action 處理（block/allow）
    4. 返回 HookResult 或 None

    Args:
        rule: Rule 配置字典

    Returns:
        HookResult with block/additional_context if applicable, otherwise None
    """
    event = get_event()

    if event.hook_event_name != 'Stop':
        return None

    # 直接 additionalContext（優先使用）
    if 'additionalContext' in rule and 'action' not in rule:
        return HookResult(
            event_name='Stop',
            additional_context=rule['additionalContext']
        )

    action = rule.get('action')

    # block action：阻止停止
    if action == 'block':
        return HookResult(
            event_name='Stop',
            block=True,
            block_reason=rule.get('reason', 'Blocked'),
            additional_context=rule.get('additionalContext')
        )

    # allow action：允許停止（無輸出）
    if action == 'allow':
        return None

    # 無 action 時返回 HookResult（block=False）
    if not action:
        return HookResult(
            event_name='Stop',
            block=False,
            additional_context=rule.get('additionalContext')
        )

    return None
