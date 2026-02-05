"""Handle 層：PostToolUseFailure 事件處理

職責：
- 處理工具執行失敗後的決策（阻止、注入 context）
- 支援 block action（儘管官方 API 僅列出 additionalContext）
- 支援 additionalContext 注入
- 訪問 error 欄位以檢查失敗原因
"""
from typing import Optional, Dict, Any
from type_defs import HookResult
from utils.context import get_event


async def process(rule: Dict[str, Any]) -> Optional[HookResult]:
    """處理 PostToolUseFailure 事件

    工作流：
    1. 從全局 EventContext 取得 event
    2. 根據 action 決定是否阻止
    3. 若有 additionalContext，直接注入（優先級最高）
    4. 返回 HookResult 或 None

    PostToolUseFailure 支援的 actions:
    - block: 阻止/記錄工具失敗
    - additionalContext: 注入額外 context（如失敗原因分析）

    Event 可訪問欄位：
    - tool_name: 工具名稱
    - tool_input: 工具輸入
    - error: 錯誤信息
    - tool_use_id: 工具使用 ID
    """
    event = get_event()

    if event.hook_event_name != 'PostToolUseFailure':
        return None

    # 1. additionalContext（直接注入，最優先）
    if 'additionalContext' in rule:
        return HookResult(
            event_name='PostToolUseFailure',
            additional_context=rule['additionalContext']
        )

    # 2. action: block
    if rule.get('action') == 'block':
        return HookResult(
            event_name='PostToolUseFailure',
            block=True,
            block_reason=rule.get('reason', 'Blocked')
        )

    # 3. 無 action，返回 None
    return None
