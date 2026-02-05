"""refer_kwg 功能 — D-Heap 知識圖譜查詢

從 prompt 提取關鍵詞，查詢知識圖譜返回相關內容
"""

from typing import Optional
from utils.context import get_event
from loaders import config

def process() -> Optional[str]:
    """查詢知識圖譜

    Args:
        注意: event 從全局 EventContext.get() 取得

    Returns:
        相關知識或 None
    """
    event = get_event()
    prompt = event.prompt if hasattr(event, 'prompt') else ''

    if not prompt or len(prompt) < 3:
        return None

    # 提取關鍵詞
    keywords = _extract_keywords(prompt)
    if not keywords:
        return None

    # 查詢知識圖譜
    results = _query_kwg(keywords)
    if not results:
        return None

    return _format_results(results)

def _extract_keywords(text: str) -> list:
    """提取關鍵詞"""
    words = text.split()
    return [w.lower() for w in words if len(w) > 3]

def _query_kwg(keywords: list) -> list:
    """查詢知識圖譜"""
    try:
        from utils import db

        cfg = config.get('rules', {})
        limit = cfg.get('refer_kwg_limit', 5)

        aql = """
        FOR doc IN knowledge
          LET score = LENGTH(
            FOR kw IN @keywords
              FILTER CONTAINS(LOWER(doc.content), kw)
              RETURN 1
          )
          FILTER score > 0
          SORT score DESC
          LIMIT @limit
          RETURN {
            key: doc._key,
            title: doc.title,
            content: SUBSTRING(doc.content, 0, 200),
            score: score
          }
        """

        results = db.query_aql(aql, bind_vars={
            'keywords': keywords,
            'limit': limit
        })
        return results if results else []

    except Exception:
        return []

def _format_results(results: list) -> Optional[str]:
    """格式化結果"""
    if not results:
        return None

    lines = ['**Related Knowledge:**\n']
    for r in results:
        title = r.get('title', r.get('key', ''))
        content = r.get('content', '')[:100]
        lines.append(f"- **{title}**: {content}...")

    return '\n'.join(lines)
