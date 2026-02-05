---
name: permission-allow-docs
description: 自動允許讀取文檔檔案的權限請求
enabled: true
event: PermissionRequest
tool: Read
match: "\\.md$|\\.txt$|\\.json$|\\.toml$"
action: allow
priority: 10
---

自動允許讀取配置和文檔檔案，不需確認。
