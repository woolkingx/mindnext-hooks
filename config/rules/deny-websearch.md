---
name: deny-websearch
description: 阻擋 WebSearch，提示使用 MCP searxng
enabled: true
event: PreToolUse
tool: WebSearch
action: deny
reason: "Use MCP tool instead: mcp__ddg-search__iask-search"
priority: 10
---

WebSearch 建議使用 MCP iask 替代，支援多種搜尋模式（question/academic/forums/wiki/thinking）和詳細等級調整。
