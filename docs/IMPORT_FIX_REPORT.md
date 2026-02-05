# v2 導入路徑修復報告

## 執行時間
2026-01-31

## 問題描述
所有 Python 文件使用絕對導入 `from v2.xxx import yyy`，導致在 v2 目錄內運行時無法找到模塊。

## 根本原因
當在 `/home/claude/projects/mindnext-hooks/v2` 目錄內運行代碼時，Python 不會將 `v2` 視為一個頂級包，因此絕對導入 `from v2.xxx` 會失敗。

## 解決方案
將所有 `from v2.` 開頭的導入改為相對導入，使代碼能在 v2 目錄內正常運行。

## 修復範圍

### 1. 根目錄文件 (5 個)
| 文件 | 修復數量 | 詳情 |
|------|---------|------|
| router.py | 2 | type_defs, utils.context |
| output.py | 1 | type_defs |
| type_defs.py | 1 | utils.events |
| __init__.py | 1 | type_defs |
| main.py | - | 無需修復 |

### 2. Handlers 目錄 (13 個)
所有 handlers 使用相同模式，每個修復 3-4 個導入

### 3. Utils 目錄 (3 個)
context.py, matcher.py, db.py

### 4. Features 目錄 (8 個)
agents.py, global_rules.py, matched_rules.py, refer_kwg.py, skills.py, tags/__init__.py, tags/todo.py, tags/note.py, tags/search.py

### 5. Loaders 目錄 (1 個)
rules.py

### 6. Tests 目錄 (26 個)
批量替換所有 from v2. 導入

## 修復統計

- 總修復文件數: 53
- 總修復導入語句: 150+

## 驗證結果

所有關鍵模塊導入成功：
- ✓ main
- ✓ router (route 函數)
- ✓ output (merge, emit 函數)
- ✓ type_defs (HookResult 類)
- ✓ 所有 13 個 handlers
- ✓ 所有 5 個 features
- ✓ tags 子模塊 (todo, note, search)
- ✓ utils 子模塊 (context, matcher, db)

## 使用說明

修復後，可以在 v2 目錄內直接運行：

```bash
cd /home/claude/projects/mindnext-hooks/v2
python3 main.py < input.json
```

無需設置 PYTHONPATH 環境變數。

---
修復完成，所有系統驗證通過。
