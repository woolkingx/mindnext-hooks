---
name: rm-to-trash
description: 將 rm 命令轉換為 trash rm（Modern Trash），防止誤刪，檔案可恢復
enabled: true
event: PreToolUse
tool: Bash
match:
  cmd: rm
action: transform
updatedInput:
  field: command
  pattern: "^rm\\b"
  replace: "trash rm"
reason: "✓ 已轉換為 trash rm（檔案可恢復）\n提示：trash list 查看 | trash restore 恢復 | trash empty 清空"
priority: 50
---

## 將所有 rm 命令轉換為 trash rm（Modern Trash）

基本原理：
- 檔案移至 `~/.trash/` 而非永久刪除
- 可用 `trash list` 查看垃圾箱
- 可用 `trash restore <pattern>` 救回檔案
- 可用 `trash empty` 清空垃圾箱
- 自動磁盤管理：當系統磁盤 < 10% 時自動刪除最舊的檔案

已安裝：`~/.local/bin/trash`

## 參數相容性

trash rm 支援完整的 rm 參數（基於 bashlex 解析）：

| rm 參數 | trash rm 支援 | 說明 |
|--------|--------------|------|
| `-r, -R` | ✅ 是 | 遞迴刪除目錄 |
| `-i` | ✅ 是 | 交互確認（逐檔案） |
| `-f` | ✅ 接受但無效 | trash 預設安全，無需強制 |
| `-v` | ✅ 接受但無效 | trash 自有詳細輸出 |

hook 轉換原理：
1. **模式匹配**: 匹配命令 `rm`
2. **簡單替換**: `rm` → `trash rm`（保留所有參數和檔案）
3. **bashlex 自動解析**: hook 框架自動解析 bash 語法，確保參數正確傳遞

## 常見用法

```bash
# 基本刪除
rm file.txt            → trash rm file.txt ✓

# 遞迴刪除目錄
rm -r dir/             → trash rm -r dir/ ✓
rm -rf dir/            → trash rm -rf dir/ ✓ (接受 -f，預設安全)

# 交互確認
rm -i file.txt         → trash rm -i file.txt ✓
rm -ri dir/            → trash rm -ri dir/ ✓

# 複合參數
rm -rif /path          → trash rm -rif /path ✓

# 萬用字符
rm *.log               → trash rm *.log ✓
rm *.{tmp,bak}         → trash rm *.{tmp,bak} ✓
```

## 驗證和恢復

```bash
# 查看垃圾箱
trash list                      # 查看全部
trash list -p "pattern"         # 搜索
trash list -s size -r           # 按大小排序

# 恢復檔案
trash restore filename          # 恢復到原位置
trash restore pattern -d /tmp   # 恢復到指定目錄

# 清理垃圾
trash empty -f                  # 強制清空（不確認）
```
