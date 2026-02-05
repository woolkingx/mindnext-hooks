"""規則 Frontmatter 驗證器

驗證規則配置的 frontmatter 格式是否正確。
只使用官方欄位名。
"""

from typing import Dict, Any, List, Tuple


# ============================================================
# 事件類型和支援的 action 映射 (12 events from Claude Code CLI)
# ============================================================
EVENT_ACTIONS = {
    'PreToolUse': ['allow', 'deny', 'ask', 'transform'],
    'PostToolUse': ['block'],
    'PostToolUseFailure': [],  # 無輸出控制
    'Notification': [],  # 無輸出控制
    'UserPromptSubmit': ['block'],
    'SessionStart': ['load', 'context'],
    'Stop': ['block'],
    'SubagentStart': ['load', 'context'],
    'SubagentStop': ['block'],
    'PreCompact': ['stdout', 'stderr'],  # 輸出到 stdout/stderr 顯示給用戶
    'SessionEnd': [],  # 無輸出控制
    'PermissionRequest': ['allow', 'deny'],
}

# 必填欄位
REQUIRED_FIELDS = ['name', 'description', 'event']

# 可選欄位（官方名）
OPTIONAL_FIELDS = [
    # 通用
    'enabled', 'priority', 'action',
    # 匹配
    'tool', 'match',
    # 輸出
    'reason', 'additionalContext', 'updatedInput',
    # Bash 結構化匹配
    'cmd', 'args_match', 'flags', 'has_flags', 'any_cmd',
    # load action
    'loaders',
    # 觸發條件
    'source', 'subagent_type', 'notification_type', 'trigger',
    # UserPromptSubmit feature
    'feature',
]

# Bash 專用欄位
BASH_ONLY_FIELDS = ['cmd', 'args_match', 'flags', 'has_flags', 'any_cmd']

# transform action 需要的欄位
TRANSFORM_REQUIRED_FIELDS = ['updatedInput']

# load action 需要的欄位
LOAD_REQUIRED_FIELDS = ['loaders']


def validate_rule(rule: Dict[str, Any], filepath: str = '') -> Tuple[bool, List[str]]:
    """驗證規則配置"""
    errors = []
    prefix = f"[{filepath}] " if filepath else ""

    # 1. 檢查必填欄位
    for field in REQUIRED_FIELDS:
        if field not in rule:
            errors.append(f"{prefix}缺少必填欄位: {field}")
        elif not rule[field]:
            errors.append(f"{prefix}必填欄位不能為空: {field}")

    if 'event' not in rule:
        return (False, errors)

    event = rule['event']
    action = rule.get('action', '')

    # 2. 檢查 event 是否合法
    if event not in EVENT_ACTIONS:
        errors.append(f"{prefix}不支援的 event: {event}")
        return (False, errors)

    # 3. 檢查 action 是否合法（如果有設定）
    valid_actions = EVENT_ACTIONS[event]
    if action and valid_actions and action not in valid_actions:
        errors.append(
            f"{prefix}event={event} 不支援 action={action}。"
            f"支援: {', '.join(valid_actions)}"
        )

    # 4. 無輸出控制事件不應有 action
    if not valid_actions and action:
        errors.append(f"{prefix}event={event} 無輸出控制，不需要 action")

    # 5. Check tool-specific fields
    tool = rule.get('tool', '')
    for field in BASH_ONLY_FIELDS:
        if field in rule and tool != 'Bash':
            errors.append(f"{prefix}{field} 欄位只能用於 tool=Bash")

    # 6. 檢查 action 需要的欄位
    if action == 'transform':
        if 'updatedInput' not in rule:
            errors.append(f"{prefix}action=transform 需要 updatedInput")

    if action == 'load':
        if 'loaders' not in rule:
            errors.append(f"{prefix}action=load 需要 loaders")

    # 7. 檢查欄位類型
    if 'enabled' in rule and not isinstance(rule['enabled'], bool):
        errors.append(f"{prefix}enabled 必須是布林值")

    if 'priority' in rule and not isinstance(rule['priority'], (int, float)):
        errors.append(f"{prefix}priority 必須是數字")

    if 'flags' in rule and not isinstance(rule['flags'], list):
        errors.append(f"{prefix}flags 必須是陣列")

    if 'loaders' in rule and not isinstance(rule['loaders'], list):
        errors.append(f"{prefix}loaders 必須是陣列")

    if 'feature' in rule and not isinstance(rule['feature'], list):
        errors.append(f"{prefix}feature 必須是陣列")

    # 8. 檢查不認識的欄位
    all_valid_fields = set(REQUIRED_FIELDS + OPTIONAL_FIELDS)
    unknown_fields = {
        k for k in rule.keys()
        if not k.startswith('_')
    } - all_valid_fields
    if unknown_fields:
        errors.append(f"{prefix}不認識的欄位: {', '.join(unknown_fields)}")

    return (len(errors) == 0, errors)


def validate_all_rules(rules: List[Dict[str, Any]]) -> Tuple[int, int, List[str]]:
    """驗證所有規則"""
    valid_count = 0
    invalid_count = 0
    all_errors = []

    for rule in rules:
        filepath = rule.get('_filepath', 'unknown')
        is_valid, errors = validate_rule(rule, filepath)

        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1
            all_errors.extend(errors)

    return (valid_count, invalid_count, all_errors)
