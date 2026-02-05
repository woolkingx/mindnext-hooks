---
name: session-load-claude-md
description: 啟動時載入 CLAUDE.md 和 Skills
enabled: false
event: SessionStart
action: load
loaders:
  - type: file
    path: "~/.claude/CLAUDE.md"
    label: "User CLAUDE.md"
  - type: file
    path: "~/.claude/skills/extends/SKILL.md"
    label: "Skills Index"
    enable: false
priority: 100
---

Session 啟動時自動載入用戶配置。
