---
name: block-dangerous-paths
description: 阻擋刪除危險路徑 (/, ~, ..) - 可選的額外防護層
enabled: false
event: PreToolUse
tool: Bash
match:
  cmd: rm
  args: "^(/|~|\\.\\.)"
action: deny
reason: "Dangerous path blocked: root/home/parent directory"
priority: 99
---

阻擋 rm 針對以下路徑：
- `/` 開頭 - 根目錄
- `~` 開頭 - 家目錄
- `..` 開頭 - 父目錄
