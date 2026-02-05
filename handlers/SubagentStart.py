"""Handle 層：SubagentStart 事件處理

職責：
- 在 SubagentStart 事件時注入上下文
- 支援 context action（直接注入）
- 支援 load action（從檔案載入）
- 支援 loaders 配置（file type）
"""
from pathlib import Path
from typing import Optional, Dict, Any
from type_defs import HookResult
from utils.context import get_event


async def process(rule: Dict[str, Any]) -> Optional[HookResult]:
    """處理 SubagentStart 事件

    工作流：
    1. 提取 rule
    2. 檢查是否有 additionalContext（優先使用）
    3. 根據 action 處理（context/load）
    4. 返回 HookResult 或 None

    Args:
        rule: rule 配置 (dict)

    注意: event 從全局 EventContext 取得

    Returns:
        HookResult with additional_context if applicable, otherwise None
    """
    

    event = get_event()

    if event.hook_event_name != 'SubagentStart':
        return None

    # 直接 additionalContext（優先使用）
    if 'additionalContext' in rule and 'action' not in rule:
        return HookResult(
            event_name='SubagentStart',
            additional_context=rule['additionalContext']
        )

    action = rule.get('action')

    # context action：直接返回 additionalContext
    if action == 'context':
        return HookResult(
            event_name='SubagentStart',
            additional_context=rule.get('additionalContext', '')
        )

    # load action：從檔案載入內容
    if action == 'load':
        return await _load_files(rule)

    return None


async def _load_files(rule: dict) -> Optional[HookResult]:
    """載入檔案到 additionalContext

    Args:
        rule: rule 配置

    Returns:
        HookResult with additional_context if files loaded, otherwise None
    """
    loaders = rule.get('loaders', [])
    contents = []

    for loader in loaders:
        if not isinstance(loader, dict):
            continue
        if not loader.get('enable', True):
            continue
        if loader.get('type') != 'file':
            continue

        path = loader.get('path', '')
        if not path:
            continue

        try:
            expanded = Path(path).expanduser()
            content = expanded.read_text(encoding='utf-8')
            label = loader.get('label', path)
            contents.append(f"## {label}\n\n{content}")
        except Exception:
            pass

    if contents:
        return HookResult(
            event_name='SubagentStart',
            additional_context='\n\n'.join(contents)
        )

    return None
