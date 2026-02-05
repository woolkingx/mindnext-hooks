"""matched_rules 功能 — 匹配規則查詢

從 prompt 匹配相關規則
"""

from typing import Optional
from utils.context import get_event
from loaders import config

def process() -> Optional[str]:
    """匹配規則

    Args:
        注意: event 從全局 EventContext.get() 取得

    Returns:
        匹配的規則或 None
    """
    event = get_event()
    prompt = event.prompt if hasattr(event, 'prompt') else ''

    if not prompt:
        return None

    # 提取關鍵詞
    keywords = _extract_keywords(prompt)
    if not keywords:
        return None

    # 查詢匹配規則
    rules = _match_rules(keywords)
    if not rules:
        return None

    return _format_rules(rules)

def _extract_keywords(text: str) -> list:
    """提取關鍵詞"""
    words = text.split()
    return [w.lower() for w in words if len(w) > 2]

def _match_rules(keywords: list) -> list:
    """匹配規則"""
    try:
        from utils import db

        cfg = config.get('rules', {})
        max_matched = cfg.get('max_matched', 10)

        aql = """
        FOR rule IN rules
          FILTER rule.enabled == true
          LET score = LENGTH(
            FOR kw IN @keywords
              FILTER kw IN rule.keywords OR CONTAINS(LOWER(rule.content), kw)
              RETURN 1
          )
          FILTER score > 0
          SORT score DESC, rule.priority DESC
          LIMIT @limit
          RETURN {
            key: rule._key,
            name: rule.name,
            content: rule.content,
            score: score
          }
        """

        results = db.query_aql(aql, bind_vars={
            'keywords': keywords,
            'limit': max_matched
        })
        return results if results else []

    except Exception:
        return []

def _format_rules(rules: list) -> Optional[str]:
    """格式化規則"""
    if not rules:
        return None

    lines = ['**Matched Rules:**\n']
    for r in rules:
        name = r.get('name', r.get('key', ''))
        content = r.get('content', '')
        lines.append(f"- **{name}**: {content}")

    return '\n'.join(lines)
