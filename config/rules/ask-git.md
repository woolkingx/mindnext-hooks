---
name: ask-git
description: git checkout/restore 需要確認
enabled: false
event: PreToolUse
tool: Bash
match: "git (checkout|restore)"
action: ask
reason: "確認執行 git checkout/restore？"
---

git checkout 和 restore 會覆蓋本地變更，需要用戶確認。
