"""
⚠️ DEPRECATED - V1 遺留代碼

V2 使用 router.py 中的 _matches_rule() 函數進行匹配
此檔案保留僅供參考,不應在新代碼中使用
"""
import re
from typing import Any
from type_defs import HandlePayload


def match(handle_payload: HandlePayload) -> bool:
    """[DEPRECATED] 請使用 router._matches_rule()

    Utility: 條件匹配

    Rule 3: Utility 專注單一功能
    - 只負責條件匹配
    - 不混合其他職責
    """
    rule = handle_payload['rule']
    claude = handle_payload['claude']

    match_config = rule.get('match')

    # 沒有 match 配置 → 默認匹配
    if not match_config:
        return True

    # 字串格式：regex 匹配
    if isinstance(match_config, str):
        return _match_string(match_config, claude)

    # 物件格式：結構化匹配
    if isinstance(match_config, dict):
        return _match_dict(match_config, claude)

    return False


def _match_string(pattern: str, claude: dict) -> bool:
    """字串 regex 匹配"""
    # 優先匹配 tool_input.command
    tool_input = claude.get('tool_input', {})
    command = tool_input.get('command', '')
    if command and re.search(pattern, command):
        return True

    # 其次匹配 prompt
    prompt = claude.get('prompt', '')
    if prompt and re.search(pattern, prompt):
        return True

    return False


def _match_dict(match_config: dict, claude: dict) -> bool:
    """結構化匹配（Bash 專用）"""
    # TODO: 實現 bashlex 解析後的結構化匹配
    return True
