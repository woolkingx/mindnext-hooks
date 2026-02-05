---
name: memory-query
description: 觸發 AI 記憶查詢 (recall, remember, 之前, 上次)
enabled: false  # TODO: UserPromptSubmit memory action 暫緩實作
event: UserPromptSubmit
match: "^ai\\s*:|^ai |記憶|記得|之前|上次|recall|remember|previous"
action: memory
priority: 50
---

當用戶提到記憶相關關鍵詞時，觸發 AI 記憶查詢。
