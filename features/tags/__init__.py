"""Process 層：tags 業務邏輯

#tags 命令路由器：
- #tags todo ... - todo 管理（add, list, done, rm, update, projects, import）
- #tags note ... - note 筆記（add, list, search）
- #tags search ... - 跨 todo/note 搜尋

支援前綴:
- #tags (推薦)
- /tags (向後兼容，自動轉換為 #tags)
"""
from typing import Optional
from utils.context import get_event


def process() -> Optional[str]:
    """處理 tags 命令"""
    event = get_event()
    prompt = event.prompt if hasattr(event, 'prompt') else ''

    # 檢查前綴（同時支援 #tags 與 /tags）
    if prompt.startswith("#tags"):
        # shlex parser 以 /command 為 command 型態判斷
        prompt = "/" + prompt[1:]
    elif not prompt.startswith("/tags"):
        return None

    # 使用 shlex 解析器保留引號
    from utils.parsers.shlex_parser import parse as shlex_parse
    parsed = shlex_parse(prompt)

    if parsed.get('type') != 'command':
        return None

    cmd = parsed.get('cmd', '')
    if cmd != 'tags':
        return None

    sub = parsed.get('sub', '')
    action = parsed.get('action', '')
    args = parsed.get('args', [])
    tags = parsed.get('tags', [])
    flags = parsed.get('flags', {})

    # 路由到子模組
    if sub == 'todo':
        from features.tags import todo
        return todo.handle(action, args, tags, flags)
    elif sub == 'note':
        from features.tags import note
        return note.handle(action, args, tags, flags)
    elif sub == 'search':
        from features.tags import search
        return search.handle(action, args, tags, flags)
    elif sub == 'help':
        return _help()

    return _help()


def _help() -> str:
    return """**#tags 命令**

跨 session 管理 todo 和筆記，支援標籤、優先級、專案分組（ArangoDB 驅動）。

**子命令**
- `#tags todo <action>` - Todo 管理
- `#tags note <action>` - Note 筆記
- `#tags search <query>` - 跨 todo/note 搜尋

**查看詳細說明**
- `#tags todo help` - Todo 完整命令列表
- `#tags note help` - Note 完整命令列表

**專案管理**
- `-g` - 全局（所有專案）
- `-p <name>` - 指定專案
"""
