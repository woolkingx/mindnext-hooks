"""Handle 層：SessionStart 事件處理

職責：
- 在 session 開始時注入上下文
- 支援 context action（直接注入）
- 支援 load action（載入檔案）
"""
from pathlib import Path
from typing import Optional, Dict, Any
from type_defs import HookResult
from utils.context import get_event


async def process(rule: Dict[str, Any]) -> Optional[HookResult]:
    """處理 SessionStart 事件

    工作流：
    1. 從全局取得 event
    2. 檢查是否有 action
    3. 根據 action 處理（context 或 load）
    4. 返回 HookResult 或 None

    Args:
        rule: Rule 配置字典

    Returns:
        HookResult with additionalContext if applicable, otherwise None
    """
    event = get_event()

    if event.hook_event_name != 'SessionStart':
        return None

    # 直接 additionalContext（優先使用）
    if 'additionalContext' in rule and 'action' not in rule:
        return HookResult(
            event_name='SessionStart',
            additional_context=rule['additionalContext']
        )

    action = rule.get('action')

    # context action：直接返回 additionalContext
    if action == 'context':
        return HookResult(
            event_name='SessionStart',
            additional_context=rule.get('additionalContext', '')
        )

    # load action：載入檔案
    if action == 'load':
        return _load_files(rule)

    return None


def _load_files(rule: Dict[str, Any]) -> Optional[HookResult]:
    """載入檔案到 additionalContext

    規則設定格式：
    ```yaml
    action: load
    loaders:
      - enable: true
        type: file
        path: /path/to/file
        label: Optional label
    ```

    Args:
        rule: Rule 配置字典

    Returns:
        HookResult with additionalContext if files loaded successfully, otherwise None
    """
    loaders = rule.get('loaders', [])
    contents = []

    for loader in loaders:
        if not isinstance(loader, dict):
            continue

        # 檢查是否啟用
        if not loader.get('enable', True):
            continue

        # 只處理 file type
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
            # 忽略讀取失敗的檔案
            pass

    if contents:
        return HookResult(
            event_name='SessionStart',
            additional_context='\n\n'.join(contents)
        )

    return None
