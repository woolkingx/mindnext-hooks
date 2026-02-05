"""Handle 層：SessionEnd 事件處理

職責：
- 在 session 結束時注入上下文
- 支援 context action（直接注入）
- 無 loaders（SessionEnd 無檔案載入）
- SessionEnd 無控制權限，只能注入 additionalContext
"""
from typing import Optional, Dict, Any
from type_defs import HookResult
from utils.context import get_event


async def process(rule: Dict[str, Any]) -> Optional[HookResult]:
    """處理 SessionEnd 事件

    工作流：
    1. 提取 rule
    2. 檢查是否有 additionalContext 或 action
    3. 根據 action 處理（僅支援 context）
    4. 返回 HookResult 或 None

    與 SessionStart 的差異：
    - SessionEnd 無 loaders（不需要檔案載入）
    - SessionEnd 無控制權限（無 permission/block/decision）
    - SessionEnd 僅支援 additionalContext 注入

    Args:
        rule: rule 配置 (dict)

    注意: event 從全局 EventContext 取得

    Returns:
        HookResult with additionalContext if applicable, otherwise None
    """
    

    event = get_event()

    if event.hook_event_name != 'SessionEnd':
        return None

    # 直接 additionalContext（優先使用）
    if 'additionalContext' in rule and 'action' not in rule:
        return HookResult(
            event_name='SessionEnd',
            additional_context=rule['additionalContext']
        )

    action = rule.get('action')

    # context action：直接返回 additionalContext
    if action == 'context':
        return HookResult(
            event_name='SessionEnd',
            additional_context=rule.get('additionalContext', '')
        )

    return None
