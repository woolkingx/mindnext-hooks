---
name: find-use-fdfind
description: 當使用 find 命令時，建議改用 fdfind
enabled: true
event: PreToolUse
tool: Bash
match:
  cmd: find
action: deny
reason: "⛔ 請改用 Bash 執行 fdfind\n\n範例：fdfind \"pattern\" /path\n\nfdfind 比 find 快 10-50x，自動忽略 .gitignore"
priority: 50
---

禁止使用 find 命令，建議改用 fdfind：
- 性能提升 10-50x
- 自動忽略 .gitignore
- 多線程並行搜索
- 語法更簡潔

## 參數對比

| 功能 | find | fdfind |
|------|------|--------|
| 文件名搜索 | `find /path -name "*.txt"` | `fdfind "\.txt$" /path` |
| 目錄類型 | `find -type d` | `fdfind --type d` |
| 深度限制 | `find -maxdepth 2` | `fdfind --max-depth 2` |
| 不區分大小寫 | `find -iname` | `fdfind -i` |
| 排除隱藏文件 | `find ! -name ".*"` | `fdfind (預設排除)` |

## 使用建議

✅ 適合用 fdfind：簡單的文件名查找
❌ 不適合 fdfind：權限、修改時間、大小等複雜查詢（find 才支援）
