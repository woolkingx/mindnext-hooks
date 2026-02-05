"""Handle 層：PermissionRequest 事件處理

職責：
- 處理一般權限請求（非工具調用）
- 支援 deny/ask/allow action
- 返回 permission 決策
"""
from typing import Optional, Dict, Any
from type_defs import HookResult
from utils.context import get_event


async def process(rule: Dict[str, Any]) -> Optional[HookResult]:
    """處理 PermissionRequest 事件

    工作流：
    1. 提取 rule 和 claude payload
    2. 根據 action 決定權限
    3. 返回 HookResult

    Args:
        rule: rule 配置 (dict)

    注意: event 從全局 EventContext 取得

    Returns:
        HookResult with permission decision
    """
    

    event = get_event()

    if event.hook_event_name != 'PermissionRequest':
        return None

    action = rule.get('action', 'allow')
    reason = rule.get('reason')

    # 1. deny: 拒絕權限請求
    if action == 'deny':
        return HookResult(
            event_name='PermissionRequest',
            permission='deny',
            permission_reason=reason or 'Denied'
        )

    # 2. ask: 詢問使用者確認
    if action == 'ask':
        return HookResult(
            event_name='PermissionRequest',
            permission='ask',
            permission_reason=reason or 'Confirm?'
        )

    # 3. allow: 允許權限請求
    return HookResult(
        event_name='PermissionRequest',
        permission='allow',
        permission_reason=reason
    )
