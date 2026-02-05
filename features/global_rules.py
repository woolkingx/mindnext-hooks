"""global_rules 功能 — 全局規則注入

載入並返回全局規則（適用於所有 prompt）
"""

from typing import Optional
from utils.context import get_event

def process() -> Optional[str]:
    """載入全局規則

    Args:
        注意: event 從全局 EventContext.get() 取得

    Returns:
        全局規則或 None
    """
    rules = _load_global_rules()
    if not rules:
        return None

    return _format_rules(rules)

def _load_global_rules() -> list:
    """從知識圖譜載入全局規則"""
    try:
        from utils import db

        aql = """
        FOR rule IN rules
          FILTER rule.scope == 'global' AND rule.enabled == true
          SORT rule.priority DESC
          LIMIT 10
          RETURN {
            key: rule._key,
            name: rule.name,
            content: rule.content
          }
        """

        results = db.query_aql(aql)
        return results if results else []

    except Exception:
        return []

def _format_rules(rules: list) -> Optional[str]:
    """格式化規則"""
    if not rules:
        return None

    lines = ['**Global Rules:**\n']
    for r in rules:
        name = r.get('name', r.get('key', ''))
        content = r.get('content', '')
        lines.append(f"- **{name}**: {content}")

    return '\n'.join(lines)
