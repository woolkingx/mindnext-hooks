---
name: userprompt-claude-md-reminder
description: 注入 CLAUDE.md 規範及推理框架的提醒
enabled: false
event: UserPromptSubmit
additionalContext: |
  ⚠️ **對話最後依 CLAUDE.md 及 Bloom Skills 規範輸出完整認知鏈**
  格式：使用的認知鏈：1.2-recognize → 2.6-interpret → 4.1-attribute → ... → 5.1-check
priority: 100
---

每次 UserPromptSubmit 時注入 CLAUDE.md 規範及推理框架的提醒。
