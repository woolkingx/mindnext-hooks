"""Handle 層：Notification 事件處理

職責：
- Notification 事件無執行動作（無輸出控制）
- 只監聽，無策略決定
- 始終返回 None
"""
from typing import Optional, Dict, Any
from type_defs import HookResult
from utils.context import get_event


async def process(rule: Dict[str, Any]) -> Optional[HookResult]:
    """處理 Notification 事件

    Notification 事件是被動通知事件，無需進行任何決策或動作。
    此處理器始終返回 None，表示不對通知進行干涉。

    Args:
        rule: rule 配置 (dict)

    注意: event 從全局 EventContext 取得

    Returns:
        None（不進行任何操作）
    """
    event = get_event()

    if event.hook_event_name != 'Notification':
        return None

    return None
