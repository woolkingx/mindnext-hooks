---
name: ask-git-all
description: git 寫入操作需要確認（add, commit, push, checkout, merge, rebase 等）
enabled: true
event: PreToolUse
tool: Bash
match:
  cmd: git
  args: "^(add|commit|push|checkout|switch|merge|rebase|reset|branch|tag|stash|cherry-pick|revert|rm|mv)"
action: ask
reason: "確認執行 git 寫入操作？"
priority: 65
---

## Git 寫入操作確認

此規則針對**寫入操作**才詢問，只讀操作（status, log, diff, show 等）不受影響。

### 需要確認的命令

- **提交操作**: `git add`, `git commit`, `git push`
- **分支操作**: `git checkout`, `git switch`, `git branch`, `git merge`, `git rebase`
- **遠程操作**: `git pull`, `git fetch`, `git merge`
- **歷史操作**: `git reset`, `git rebase`, `git revert`
- **維護操作**: `git clean`, `git gc`, `git fsck`
- **其他操作**: `git stash`, `git tag`, `git config`

### 為什麼需要確認所有 git 操作？

1. **防止誤操作**: 用戶可能一時不察執行了不想要的命令
2. **提高意識**: 明確每一步 git 操作，有助於形成良好習慣
3. **協作安全**: 特別是在多人協作項目中，避免覆蓋他人改動
4. **版本控制**: 確保所有變更都是有意而為

### 風險提示

請特別注意以下高風險操作：

- `git push -f` / `git push --force`: 覆蓋遠程歷史
- `git reset --hard`: 丟失所有本地改動
- `git clean -f`: 永久刪除未追蹤文件
- `git branch -D`: 強制刪除分支
- `git rebase -i`: 重寫提交歷史

### 安全實踐

執行 git 操作前，檢查：

- ✅ 當前分支是否正確？`git status`
- ✅ 有未提交的改動嗎？`git diff`
- ✅ 遠程有新改動嗎？`git fetch` 後 `git log`
- ✅ 操作會影響團隊嗎？

### 若需要跳過此確認

如果覺得確認太頻繁，可以：
1. 禁用此規則: 編輯 `enabled: false`
2. 或修改 match 條件更精確地篩選
