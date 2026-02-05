---
name: deny-sudo
description: 阻擋 sudo 命令，請用戶協助執行
enabled: true
event: PreToolUse
tool: Bash
match:
  cmd: sudo
action: deny
reason: |
  sudo 命令需要用戶協助執行
  請複製命令到終端機手動執行
priority: 90
---

Claude 無法執行 sudo 命令（無密碼權限）。
