"""Todo 管理 - 完整 CRUD 操作

存儲: ArangoDB todos 集合
結構: {_key, parent, content, priority, tags, status, project, created_at, updated_at}

專案判斷:
- cwd 是 ~ → project="_user"
- cwd 在專案內 → project="{project_name}"
- -p <name> → 強制指定專案
"""

import os
import hashlib
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


def handle(action: str, args: List[str], tags: List[str], flags: Dict[str, Any]) -> str:
    """處理 /tags todo 命令"""
    # 幫助命令不需要 DB
    if action == 'help':
        return _help()

    # 修正 shlex 的 flag 值問題
    for flag_key in ['p', 'P', 'priority']:
        if flags.get(flag_key) is True and args:
            flags[flag_key] = args.pop(0)

    # 判斷專案
    project = _resolve_project(flags)

    # 優先級
    priority = _parse_priority(flags)

    # 檢查 DB 連接
    from utils import db as db_module
    db = db_module.get_db()
    if not db:
        error = db_module.get_db_error()
        if error:
            return f"❌ {error}"
        return "❌ 數據庫不可用"

    if action == 'add':
        content = args[0] if args else ''
        parent = flags.get('parent')
        if parent is True:
            parent = None
        return add(db, project, content, tags, priority, parent)
    elif action == 'list':
        show_done = flags.get('done', False) or flags.get('d', False)
        show_all = flags.get('all', False) or flags.get('a', False)
        return list_todos(db, project, tags, show_done, show_all)
    elif action == 'done':
        todo_id = args[0] if args else ''
        return done(db, project, todo_id)
    elif action == 'rm' or action == 'remove':
        todo_id = args[0] if args else ''
        return remove(db, project, todo_id)
    elif action == 'update':
        todo_id = args[0] if args else ''
        content = args[1] if len(args) > 1 else None
        return update(db, project, todo_id, content, tags, priority)
    elif action == 'projects':
        return list_projects(db)
    elif action == 'import':
        json_file = args[0] if args else ''
        return import_json(db, '_user', json_file)

    return _help()


def _resolve_project(flags: Dict) -> str:
    """判斷專案名"""
    if flags.get('p'):
        return flags['p']

    if flags.get('g') or flags.get('global'):
        return '_user'

    cwd = os.getcwd()
    home = os.path.expanduser("~")
    if cwd == home or cwd == home + "/":
        return '_user'

    project = cwd.rstrip("/").split("/")[-1]
    project = "".join(c if c.isalnum() or c in '-_.' else '_' for c in project)

    return project or '_user'


def _parse_priority(flags: Dict) -> int:
    """解析優先級"""
    p = flags.get('priority') or flags.get('P')

    if p is None or p is True:
        return 5

    if isinstance(p, int):
        return max(1, min(10, p))

    if isinstance(p, str):
        p_lower = p.lower()
        if p_lower in ('high', 'h'):
            return 8
        elif p_lower in ('mid', 'm', 'medium'):
            return 5
        elif p_lower in ('low', 'l'):
            return 2
        try:
            return max(1, min(10, int(p)))
        except ValueError:
            return 5

    return 5


def _priority_icon(p: int) -> str:
    """優先級圖示"""
    if p >= 8:
        return "🔴"
    elif p >= 4:
        return "🟡"
    else:
        return "🟢"


def _gen_id() -> str:
    """產生短 ID"""
    import time
    raw = f"{time.time()}{os.getpid()}"
    return hashlib.md5(raw.encode()).hexdigest()[:6]


def add(db, project: str, content: str, tags: Optional[List[str]] = None, priority: int = 5, parent: Optional[str] = None) -> str:
    """新增 todo"""
    if not content:
        return "請提供任務內容"

    try:
        now = datetime.now().isoformat()
        todo_key = _gen_id()

        todo_doc = {
            "_key": todo_key,
            "parent": parent,
            "content": content,
            "priority": priority,
            "tags": tags or [],
            "status": "pending",
            "project": project,
            "created_at": now,
            "updated_at": now
        }

        from utils.db import insert
        result = insert('todos', todo_doc)
        if not result:
            return f"❌ 新增失敗: DB 操作失敗"

        icon = _priority_icon(priority)
        tags_str = ' '.join(tags) if tags else ''
        proj_label = '' if project == '_user' else f' [{project}]'

        return f"✅ 新增{proj_label}: {icon} {content} {tags_str} ({todo_key})"

    except Exception as e:
        logger.error(f"Error adding todo: {e}")
        return f"❌ 新增失敗: {e}"


def list_todos(db, project: str, filter_tags: Optional[List[str]] = None, show_done: bool = False, show_all: bool = False) -> str:
    """列出 todos"""
    try:
        from utils.db import query_aql

        # 全局模式 (_user) 返回所有有效的 todo（過濾掉布林型 project）
        # 非全局模式則返回指定專案的 todo
        aql = """
        FOR doc IN todos
          FILTER @is_global ? ((doc.project != null AND doc.project != true) OR doc.project == null) : doc.project == @project
          SORT doc.priority DESC, doc.created_at ASC
          RETURN doc
        """

        results = query_aql(aql, bind_vars={
            'is_global': project == '_user',
            'project': project
        })

        if not results:
            proj_label = '全局' if project == '_user' else project
            return f"無 todo ({proj_label})"

        todos = results

        # 過濾
        filtered = []
        for t in todos:
            if not show_all:
                if show_done and t.get('status') != 'done':
                    continue
                if not show_done and t.get('status') == 'done':
                    continue

            if filter_tags:
                if not any(tag in t.get('tags', []) for tag in filter_tags):
                    continue

            filtered.append(t)

        if not filtered:
            return "無符合條件的 todo"

        # 分組顯示 (parent)
        proj_label = '全局 Todo' if project == '_user' else f'{project} Todo'
        lines = [f"**{proj_label}**\n"]

        root_todos = [t for t in filtered if not t.get('parent')]
        child_map = {}
        for t in filtered:
            if t.get('parent'):
                child_map.setdefault(t['parent'], []).append(t)

        def render_todo(t, indent=0):
            prefix = "  " * indent
            icon = _priority_icon(t.get('priority', 5))
            status = "✅" if t.get('status') == 'done' else "📌"
            tags_str = ' '.join(t.get('tags', []))
            todo_id = t.get('_key', '?')
            lines.append(f"{prefix}- {status} {icon} [{todo_id}] {t.get('content', '?')} {tags_str}")

            for child in child_map.get(t.get('_key', t.get('id')), []):
                render_todo(child, indent + 1)

        for t in root_todos:
            render_todo(t)

        # 統計全局和當前專案
        global_aql = """
        FOR doc IN todos
          FILTER (doc.project != null AND doc.project != true) OR doc.project == null
          COLLECT status = doc.status
          RETURN {status: status, count: LENGTH(1)}
        """
        global_stats_results = query_aql(global_aql)
        global_stats = {s.get('status', 'pending'): s.get('count', 0) for s in (global_stats_results or [])}
        global_total = sum(global_stats.values())
        global_pending = global_stats.get('pending', 0)
        global_done = global_stats.get('done', 0)

        # 當前專案統計（非全局模式時）
        if project != '_user':
            project_aql = """
            FOR doc IN todos
              FILTER doc.project == @project
              COLLECT status = doc.status
              RETURN {status: status, count: LENGTH(1)}
            """
            project_stats_results = query_aql(project_aql, bind_vars={'project': project})
            project_stats = {s.get('status', 'pending'): s.get('count', 0) for s in (project_stats_results or [])}
            project_total = sum(project_stats.values())
            project_pending = project_stats.get('pending', 0)
            project_done = project_stats.get('done', 0)

            stats_line = f"\n**全局** {global_total} 総計, 🔍 觀察 {global_done}, ⏳ 未完成 {global_pending}"
            stats_line += f" | **{project}** {project_total} 総計, 🔍 觀察 {project_done}, ⏳ 未完成 {project_pending}"
        else:
            stats_line = f"\n**全局** {global_total} 総計, 🔍 觀察 {global_done}, ⏳ 未完成 {global_pending}"

        lines.append(stats_line)
        lines.append("\n💡 Claude: 請在回應中直接引用此 TODO 列表回報給用戶")

        return '\n'.join(lines)

    except Exception as e:
        logger.error(f"Error listing todos: {e}")
        return f"❌ 查詢失敗: {e}"


def done(db, project: str, todo_id: str) -> str:
    """完成 todo（有 ID 時跨專案查詢）"""
    if not todo_id:
        return "請提供 todo ID"

    try:
        from utils.db import find_by_key, update

        now = datetime.now().isoformat()
        doc = find_by_key('todos', todo_id)

        if doc:
            result = update('todos', todo_id, {'status': 'done', 'updated_at': now})
            if result:
                return f"✅ 完成: {doc.get('content', '?')} ({todo_id})"
            else:
                return f"❌ 更新失敗: {todo_id}"
        else:
            return f"❌ 找不到 todo: {todo_id}"

    except Exception as e:
        logger.error(f"Error marking todo as done: {e}")
        return f"❌ 操作失敗: {e}"


def remove(db, project: str, todo_id: str) -> str:
    """刪除 todo"""
    if not todo_id:
        return "請提供 todo ID"

    try:
        from utils.db import find_by_key, delete

        doc = find_by_key('todos', todo_id)

        if doc:
            content = doc.get('content', '?')
            if delete('todos', todo_id):
                return f"🗑 刪除: {content} ({todo_id})"
            else:
                return f"❌ 刪除失敗: {todo_id}"
        else:
            return f"❌ 找不到 todo: {todo_id}"

    except Exception as e:
        logger.error(f"Error deleting todo: {e}")
        return f"❌ 刪除失敗: {e}"


def update(db, project: str, todo_id: str, content: Optional[str] = None,
           tags: Optional[List[str]] = None, priority: Optional[int] = None) -> str:
    """更新 todo - 可更新 content, tags, priority"""
    if not todo_id:
        return "請提供 todo ID"

    try:
        from utils.db import find_by_key, update as db_update

        now = datetime.now().isoformat()
        doc = find_by_key('todos', todo_id)

        if doc:
            update_data = {'updated_at': now}

            if content is not None:
                update_data['content'] = content
            if tags is not None:
                update_data['tags'] = tags
            if priority is not None:
                update_data['priority'] = priority

            result = db_update('todos', todo_id, update_data)
            if result:
                updated_fields = []
                if content is not None:
                    updated_fields.append(content)
                if tags is not None and tags:
                    updated_fields.append(' '.join(tags))
                if priority is not None:
                    icon = _priority_icon(priority)
                    updated_fields.append(f"{icon} {priority}")

                fields_str = " | ".join(updated_fields) if updated_fields else "無變更"
                return f"✏️ 已更新 ({todo_id}): {fields_str}"
            else:
                return f"❌ 更新失敗: {todo_id}"
        else:
            return f"❌ 找不到 todo: {todo_id}"

    except Exception as e:
        logger.error(f"Error updating todo: {e}")
        return f"❌ 更新失敗: {e}"


def import_json(db, project: str, json_file: str) -> str:
    """導入 JSON 格式的 todos (固定導入到 _user 全局)

    格式範例 (haiku 產出):
    [
      {"content": "任務內容", "priority": "high", "tags": ["#tag1", "#tag2"]},
      {"content": "任務2", "priority": 5, "tags": ["#urgent"]}
    ]
    """
    if not json_file:
        return "請提供 JSON 檔案路徑"

    import json
    from pathlib import Path

    try:
        json_path = Path(json_file).expanduser()
        if not json_path.exists():
            return f"❌ 檔案不存在: {json_file}"

        with json_path.open('r', encoding='utf-8') as f:
            todos = json.load(f)

        if not isinstance(todos, list):
            return "❌ JSON 格式錯誤，必須是陣列"

        # 批次新增到 _user (全局)
        success_count = 0
        failed_count = 0
        results = []

        from utils.db import insert

        for item in todos:
            if not isinstance(item, dict):
                failed_count += 1
                continue

            content = item.get('content', '')
            if not content:
                failed_count += 1
                continue

            # 解析 priority
            priority_raw = item.get('priority', 5)
            if isinstance(priority_raw, str):
                priority = _parse_priority({'P': priority_raw})
            elif isinstance(priority_raw, int):
                priority = max(1, min(10, priority_raw))
            else:
                priority = 5

            # 解析 tags
            tags = item.get('tags', [])
            if not isinstance(tags, list):
                tags = []

            # 新增到 _user
            try:
                now = datetime.now().isoformat()
                todo_key = _gen_id()

                todo_doc = {
                    "_key": todo_key,
                    "parent": None,
                    "content": content,
                    "priority": priority,
                    "tags": tags,
                    "status": "pending",
                    "project": "_user",
                    "created_at": now,
                    "updated_at": now
                }

                result = insert('todos', todo_doc)
                if result:
                    success_count += 1
                    icon = _priority_icon(priority)
                    tags_str = ' '.join(tags) if tags else ''
                    results.append(f"  ✅ {icon} {content[:30]}... {tags_str}")
                else:
                    failed_count += 1

            except Exception as e:
                failed_count += 1
                logger.error(f"Import error for item: {e}")

        # 摘要
        summary = f"📥 導入完成 [全局]: {success_count} 成功"
        if failed_count > 0:
            summary += f", {failed_count} 失敗"

        # 只顯示前 10 筆結果
        result_lines = results[:10]
        if len(results) > 10:
            result_lines.append(f"  ... 還有 {len(results) - 10} 筆")

        return summary + "\n" + "\n".join(result_lines)

    except json.JSONDecodeError as e:
        return f"❌ JSON 解析失敗: {e}"
    except Exception as e:
        logger.error(f"Import error: {e}")
        return f"❌ 導入失敗: {e}"


def list_projects(db) -> str:
    """列出所有專案"""
    try:
        from utils.db import query_aql

        aql = """
        FOR doc IN todos
          COLLECT project = doc.project
          LET pending = LENGTH(
            FOR t IN todos
              FILTER t.project == project AND t.status == 'pending'
              RETURN t
          )
          LET done_count = LENGTH(
            FOR t IN todos
              FILTER t.project == project AND t.status == 'done'
              RETURN t
          )
          RETURN {project: project, pending: pending, done: done_count}
        """
        results = query_aql(aql)

        if not results:
            return "無任何 todo 專案"

        projects = results

        lines = ["**Todo 專案**\n"]
        for p in projects:
            name = p.get('project', '?')
            label = "全局" if name == "_user" else name
            pending = p.get('pending', 0)
            done = p.get('done', 0)
            lines.append(f"- {label}: {pending} pending, {done} done")

        return '\n'.join(lines)

    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        return f"❌ 查詢失敗: {e}"


def _help() -> str:
    return """**/tags todo**

**新增**
- `add "任務" #tag` - 新增 (當前專案)
- `add "任務" -P high` - 高優先 (8)
- `add "任務" -P 10` - 指定優先級
- `add "子任務" --parent <id>` - 子任務

**列出**
- `list` - 當前專案 pending
- `list #tag` - 按標籤過濾
- `list -d` - 已完成
- `list -a` - 全部
- `list -g` - 全局 todo

**操作**
- `done <id>` - 完成
- `rm <id>` - 刪除
- `update <id> "新內容" #新標籤 -P 優先級` - 更新
- `import <json-file>` - 批次導入 (固定導入到全局)

**專案**
- `-p <name>` - 指定專案
- `-g` - 全局 (等同 -p _user)
- `projects` - 列出所有專案

**優先級**: 1-10 或 high(8)/mid(5)/low(2)
"""
