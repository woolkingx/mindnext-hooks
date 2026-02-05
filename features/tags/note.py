"""Note 管理 - 快速筆記 CRUD 操作

存儲: ArangoDB notes 集合
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


def handle(action: str, args: List[str], tags: List[str], flags: Dict[str, Any]) -> str:
    """處理 /tags note 命令"""

    # 幫助命令不需要 DB
    if action == 'help':
        return _help()

    # 檢查 DB 連接
    from utils import db as db_module
    db = db_module.get_db()
    if not db:
        error = db_module.get_db_error()
        if error:
            return f"❌ {error}"
        return "❌ 數據庫不可用"

    if action == 'add':
        content = ' '.join(args) if args else ''
        return add(db, content, tags)
    elif action == 'list':
        limit = 10
        return list_notes(db, tags, limit)
    elif action == 'search':
        query = ' '.join(args) if args else ''
        return search_notes(db, query, tags)
    elif action == 'rm' or action == 'remove':
        note_id = args[0] if args else ''
        return remove_note(db, note_id)

    return _help()


def add(db, content: str, tags: Optional[List[str]] = None) -> str:
    """新增筆記"""
    if not content:
        return "請提供筆記內容"

    try:
        from utils.db import insert

        now = datetime.now().isoformat()
        doc = {
            'title': content[:50],  # 前 50 字作為標題
            'content': content,
            'tags': tags or [],
            'created_at': now,
            'updated_at': now
        }

        result = insert('notes', doc)
        if result:
            return f"✅ 新增筆記: {content[:30]}... [{result.get('_key', '?')}]"
        else:
            return f"❌ 新增失敗: DB 操作失敗"

    except Exception as e:
        logger.error(f"Error adding note: {e}")
        return f"❌ 新增失敗: {e}"


def list_notes(db, filter_tags: Optional[List[str]] = None, limit: int = 10) -> str:
    """列出筆記"""
    try:
        from utils.db import query_aql

        if filter_tags:
            query = """
            FOR n IN notes
              FILTER LENGTH(INTERSECTION(n.tags, @tags)) > 0
              SORT n.created_at DESC
              LIMIT @limit
              RETURN n
            """
            results = query_aql(query, bind_vars={
                'tags': filter_tags,
                'limit': limit
            })
        else:
            query = """
            FOR n IN notes
              SORT n.created_at DESC
              LIMIT @limit
              RETURN n
            """
            results = query_aql(query, bind_vars={'limit': limit})

        if not results:
            return "無筆記"

        notes = results

        lines = ["**Notes**\n"]
        for n in notes:
            tags_str = ' '.join(n.get('tags', []))
            title = n.get('title', '')[:40]
            created = n.get('created_at', '')[:10]  # 只顯示日期部分
            lines.append(f"- [{n['_key']}] {created} {title} {tags_str}")

        lines.append("\n💡 Claude: 請在回應中直接引用此 Note 列表回報給用戶")

        return '\n'.join(lines)

    except Exception as e:
        logger.error(f"Error listing notes: {e}")
        return f"❌ 查詢失敗: {e}"


def search_notes(db, query: str, filter_tags: Optional[List[str]] = None) -> str:
    """搜尋筆記"""
    if not query and not filter_tags:
        return "請提供搜索關鍵字或標籤"

    try:
        from utils.db import query_aql

        search_terms = query.split() if query else []
        if filter_tags:
            search_terms.extend(filter_tags)

        aql = """
        FOR n IN notes
          LET score = LENGTH(
            FOR term IN @terms
              FILTER CONTAINS(LOWER(n.content), LOWER(term))
                 OR term IN n.tags
              RETURN 1
          )
          FILTER score > 0
          SORT score DESC, n.created_at DESC
          LIMIT 20
          RETURN {
            key: n._key,
            title: n.title,
            tags: n.tags,
            score: score,
            created: n.created_at
          }
        """

        results = query_aql(aql, bind_vars={'terms': search_terms})

        if not results:
            return f"無結果: {query}"

        lines = [f"**搜尋: {query}**\n"]
        for r in results:
            tags_str = ' '.join(r.get('tags', []))
            title = r.get('title', '')[:40]
            created = r.get('created', '')[:10]
            lines.append(f"- [{r['key']}] {created} {title} {tags_str}")

        return '\n'.join(lines)

    except Exception as e:
        logger.error(f"Error searching notes: {e}")
        return f"❌ 搜尋失敗: {e}"


def remove_note(db, note_id: str) -> str:
    """刪除筆記"""
    if not note_id:
        return "請提供 note ID"

    try:
        from utils.db import find_by_key, delete

        doc = find_by_key('notes', note_id)

        if doc:
            title = doc.get('title', '?')
            if delete('notes', note_id):
                return f"🗑 刪除: {title} ({note_id})"
            else:
                return f"❌ 刪除失敗: {note_id}"
        else:
            return f"❌ 找不到 note: {note_id}"

    except Exception as e:
        logger.error(f"Error deleting note: {e}")
        return f"❌ 刪除失敗: {e}"


def _help() -> str:
    return """**/tags note**

- `add "筆記內容" #tag` - 新增
- `list` - 列出最近筆記
- `list #tag` - 按標籤過濾
- `search <query>` - 搜尋筆記
- `rm <id>` - 刪除筆記
"""
