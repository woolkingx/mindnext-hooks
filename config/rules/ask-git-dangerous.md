---
name: ask-git-dangerous
description: git 危險操作需要確認（clean, reset --hard, push -f, rebase -i, branch -D）
enabled: false
event: PreToolUse
tool: Bash
match: "git\\s+(clean|reset\\s+--hard|push\\s+(--force|-f)|rebase\\s+(-i|--interactive)|branch\\s+-D)"
action: ask
reason: "⚠️ 確認執行危險的 git 操作？\n\n此操作可能導致數據丟失：\n- git clean: 刪除未追蹤文件\n- git reset --hard: 丟失所有本地改動\n- git push -f/--force: 覆蓋遠程歷史\n- git rebase -i: 重寫提交歷史\n- git branch -D: 刪除分支\n\n請確認操作無誤後再執行。"
priority: 60
---

## git 危險操作確認

在執行以下 git 命令時需要用戶確認：

### 1. git clean - 刪除未追蹤文件

```bash
git clean -fd      # 刪除未追蹤的文件和目錄
git clean -fdx     # 包括被 .gitignore 忽略的文件
```

**風險**: 永久刪除文件，無法恢復

**安全做法**:
```bash
git clean -fd -n   # 預覽會刪除什麼
git clean -fd      # 確認後執行
```

### 2. git reset --hard - 硬重置

```bash
git reset --hard HEAD       # 重置到 HEAD
git reset --hard origin/main # 重置到遠程主分支
```

**風險**: 丟失所有未提交的本地改動

**安全做法**:
```bash
git status                  # 先看有什麼改動
git stash                   # 保存改動到堆棧
git reset --hard HEAD~1     # 然後重置
```

### 3. git push -f/--force - 強制推送

```bash
git push -f origin branch       # 強制推送，覆蓋遠程歷史
git push --force-with-lease     # 更安全的強制推送
```

**風險**: 覆蓋遠程歷史，影響其他開發者

**安全做法**:
```bash
git log origin/branch..HEAD     # 先看要推送什麼
git push --force-with-lease     # 使用 --force-with-lease 而非 -f
```

### 4. git rebase -i - 交互式變基

```bash
git rebase -i HEAD~3            # 編輯最後 3 個提交
git rebase -i origin/main       # 變基到主分支
```

**風險**: 重寫提交歷史，可能造成衝突

**安全做法**:
```bash
git rebase -i --autostash       # 自動保存工作區改動
git log --oneline -10           # 先看提交歷史
```

### 5. git branch -D - 刪除分支

```bash
git branch -D feature/old        # 強制刪除未合併的分支
```

**風險**: 永久刪除分支（需要從 reflog 恢復）

**安全做法**:
```bash
git branch -d feature/old        # 先用 -d（未合併會拒絕）
git reflog                       # 若誤刪，可從 reflog 恢復
```

## 確認前的檢查清單

執行危險操作前，確認：

- ✅ 當前分支是否正確？
- ✅ 本地有未提交的改動嗎？
- ✅ 遠程有新改動需要拉取嗎？
- ✅ 此操作會影響其他團隊成員嗎？
- ✅ 有備份或備用方案嗎？

## 恢復方法

若誤執行了危險操作：

```bash
# 查看 git 操作歷史
git reflog

# 恢復到特定狀態
git reset --hard HEAD@{N}       # N 是 reflog 中的序號
```

