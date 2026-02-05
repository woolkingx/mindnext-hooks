---
name: "precompact-reminder"
description: "Compact 前提醒用戶輸入總結指令"
enabled: false
event: PreCompact
action: stderr
reason: |
  請手動輸入 /compact 加上總結指令，例如：
  /compact 請總結本 session 的經驗教訓、錯誤模式、新發現的 pattern，評估是否需要更新 CLAUDE.md、skills、agents 或知識庫
---

# PreCompact Reminder

提醒用戶使用 `/compact [custom_instructions]` 格式，將總結指令傳入 compact 過程。
