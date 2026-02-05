---
name: rsync-delete-ask
description: rsync --delete 參數需要確認
enabled: true
event: PreToolUse
tool: Bash
match:
  cmd: rsync
  flags: [delete]
action: ask
reason: "確認執行 rsync --delete？此操作會刪除目標目錄中多餘的檔案"
priority: 60
---

rsync --delete 會刪除目標目錄中不存在於來源的檔案。

危險性：
- 可能誤刪重要檔案
- 無法輕易恢復
- 需要確認同步方向正確

建議：
- 先用 --dry-run 測試
- 確認來源與目標路徑
- 考慮使用 --backup 保留被刪除檔案
