---
name: allow-docs
description: 自動允許讀取文檔檔案
enabled: true
event: PreToolUse
tool: Read
match: "/docs/|/README|\\.md$"
action: allow
priority: 10
---

自動允許讀取：
- `/docs/` 目錄下的檔案
- README 相關檔案
- 所有 .md 檔案
