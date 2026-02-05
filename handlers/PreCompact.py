"""Handle 層：PreCompact 事件處理

職責：
- 在 PreCompact 事件時進行終止操作
- 支援 stdout/stderr action
- 直接調用 sys.exit() 進行進程終止
"""
import sys
from typing import Optional, Dict, Any
from type_defs import HookResult
from utils.context import get_event


async def process(rule: Dict[str, Any]) -> Optional[HookResult]:
    """處理 PreCompact 事件

    工作流：
    1. 提取 rule
    2. 檢查 action 和 reason 是否存在
    3. 根據 action 處理（stdout/stderr）
    4. 調用 sys.exit() 進行進程終止
    5. 不返回結果（因為已退出）

    Args:
        rule: rule 配置 (dict)

    注意: event 從全局 EventContext 取得

    Returns:
        None（進程會終止，不會返回）
    """
    
    event = get_event()

    if event.hook_event_name != 'PreCompact':
        return None

    action = rule.get('action')
    reason = rule.get('reason', '')

    if not action or not reason:
        return None

    # 移除 reason 前後的空白字符（包含 \n）
    reason_stripped = reason.strip()

    if action == 'stderr':
        print(reason_stripped, file=sys.stderr)
        sys.exit(2)
    elif action == 'stdout':
        print(reason_stripped)
        sys.exit(0)

    return None
