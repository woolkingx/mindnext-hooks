---
name: deny-webfetch
description: 阻擋 WebFetch，提示使用 MCP fetcher
enabled: true
event: PreToolUse
tool: WebFetch
action: deny
reason: "WebFetch is unstable. Use MCP tool instead: mcp__fetcher__fetch_url"
priority: 10
---

WebFetch 有時不穩定，建議使用 MCP fetcher 替代。
