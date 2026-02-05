---
name: permission-block-rm
description: 阻擋 rm 權限請求，提示用 trash rm
enabled: false
event: PermissionRequest
tool: Bash
match:
  cmd: [rm, dd, mkfs]
action: deny
reason: "rm command blocked. Use 'trash rm' to move files to trash instead (safer, files are recoverable)"
priority: 100
---

阻擋危險刪除命令的權限請求。
改用 `trash rm` 代替 `rm`，檔案移至 ~/.trash/ 可以恢復。
