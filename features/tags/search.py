"""跨 todo/note 搜尋模組

搜尋 todos 和 notes 集合，使用加權評分排序
"""

import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


def handle(action: str, args: List[str], tags: List[str], flags: Dict[str, Any]) -> str:
    """處理 /tags search 命令"""

    # 搜索詞來自 action 和 args
    search_words = []
    if action:
        search_words.append(action)
    search_words.extend(args)

    query = ' '.join(search_words) if search_words else ''

    if not query and not tags:
        return "請提供搜索關鍵字或標籤"

    # 檢查 DB 連接
    from utils import db as db_module
    db = db_module.get_db()
    if not db:
        error = db_module.get_db_error()
        if error:
            return f"❌ {error}"
        return "❌ 數據庫不可用"

    return search(db, query, tags)


def search(db, query: str, filter_tags: Optional[List[str]] = None) -> str:
    """搜尋 todos 和 notes — 使用加權搜尋"""

    try:
        from utils.db import query_aql

        # 組合搜尋條件
        search_terms = query.split() if query else []
        search_terms.extend(filter_tags or [])

        if not search_terms:
            return "請提供搜索關鍵字或標籤"

        aql = """
        LET results = (
            // 搜尋 notes
            FOR n IN notes
              LET score = LENGTH(
                FOR term IN @terms
                  FILTER CONTAINS(LOWER(n.content), LOWER(term))
                     OR term IN n.tags
                  RETURN 1
              )
              FILTER score > 0
              RETURN {
                type: 'note',
                key: n._key,
                title: n.title,
                tags: n.tags,
                score: score,
                created: n.created_at
              }
        )
        LET todos = (
            // 搜尋 todos
            FOR t IN todos
              LET score = LENGTH(
                FOR term IN @terms
                  FILTER CONTAINS(LOWER(t.content), LOWER(term))
                     OR term IN t.tags
                  RETURN 1
              )
              FILTER score > 0
              RETURN {
                type: 'todo',
                key: t._key,
                title: t.content,
                tags: t.tags,
                score: score,
                status: t.status,
                created: t.created_at
              }
        )
        FOR r IN UNION(results, todos)
          SORT r.score DESC, r.created DESC
          LIMIT 20
          RETURN r
        """

        results = query_aql(aql, bind_vars={'terms': search_terms})

        if not results:
            return f"無結果: {query}"

        lines = [f"**搜尋: {query}**\n"]
        for r in results:
            icon = '📝' if r['type'] == 'note' else ('✅' if r.get('status') == 'done' else '📌')
            tags_str = ' '.join(r.get('tags', []))
            title = r.get('title', '')[:40]
            created = r.get('created', '')[:10]
            lines.append(f"- {icon} [{r['key']}] {created} {title} {tags_str}")

        return '\n'.join(lines)

    except Exception as e:
        logger.error(f"Search error: {e}")
        return f"❌ 搜尋失敗: {e}"
