---
name: grep-use-rg
description: 禁止 Grep，改用 Bash(rg)
enabled: true
event: PreToolUse
tool: Grep
action: deny
reason: "⛔ 請改用 Bash 執行 rg（ripgrep）\n\n範例：rg 'pattern' --type py\n\nrg 比 Grep 快 5-10x，自動忽略 .gitignore"
priority: 50
---

禁止使用內建 Grep，引導使用 ripgrep：
- 速度快 5-10x
- 自動忽略 .gitignore
- 彩色輸出
