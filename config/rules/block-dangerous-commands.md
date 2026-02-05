---
name: block-dangerous-commands
description: 阻擋危險命令 (mkfs, dd, fork bomb)
enabled: true
event: PreToolUse
tool: Bash
match: "^(mkfs|dd\\s+if=)"
action: deny
reason: "Dangerous command blocked"
priority: 100
---

阻擋的命令：
- `mkfs*` - 格式化磁碟
- `dd if=` - 低階磁碟寫入
