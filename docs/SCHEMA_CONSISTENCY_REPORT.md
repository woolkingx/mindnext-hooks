# Schema 一致性檢查報告

## 檢查日期
2026-01-31

## 檢查範圍

### 1. Schema 定義檢查
- ✅ 12 個事件的 Schema 定義完整
- ✅ Event Input 定義
- ✅ Response Output 定義
- ✅ Rule Config 定義
- ✅ Examples 提供

### 2. HookResult 欄位對應

| Schema 欄位 | HookResult 屬性 | 狀態 |
|------------|----------------|------|
| `permissionDecision` | `permission` | ✅ |
| `permissionDecisionReason` | `permission_reason` | ✅ |
| `updatedInput` | `updated_input` | ✅ |
| `decision` | `block` | ✅ |
| `reason` | `block_reason` | ✅ |
| `additionalContext` | `additional_context` | ✅ |
| `continue` | `continue_processing` | ✅ |
| `stopReason` | `stop_reason` | ✅ |
| `suppressOutput` | `suppress` | ✅ |
| `systemMessage` | `system_message` | ✅ |

**結論**: 所有 Schema 定義的欄位在 HookResult 中都有對應屬性

### 3. emit 函數輸出檢查

檢查 `output.py` 的 `emit()` 函數是否處理所有欄位:

| 輸出欄位 | 處理狀態 | 對應代碼 |
|---------|---------|----------|
| `permissionDecision` | ✅ | line 123 |
| `permissionDecisionReason` | ✅ | line 125 |
| `updatedInput` | ✅ | line 128 |
| `decision` | ✅ | line 120, 134, 139 |
| `reason` | ✅ | line 136, 141 |
| `additionalContext` | ✅ | line 145 |
| `continue` | ✅ | line 108 |
| `stopReason` | ✅ | line 110 |
| `suppressOutput` | ✅ | line 112 |
| `systemMessage` | ✅ | line 114 |

**結論**: emit 函數正確處理所有 Schema 定義的輸出欄位

### 4. 事件分類與欄位使用

#### Permission 類 (PreToolUse, PermissionRequest)

**Schema 定義**:
- `hookSpecificOutput.permissionDecision`: "allow" | "deny" | "ask"
- `hookSpecificOutput.permissionDecisionReason`: string (optional)
- `hookSpecificOutput.updatedInput`: object (optional)

**HookResult 對應**:
```python
HookResult(
    permission='allow',           # → permissionDecision
    permission_reason='...',      # → permissionDecisionReason
    updated_input={...}           # → updatedInput
)
```

**特殊處理**:
- `PermissionRequest` 使用 `decision` 欄位而非 `permissionDecision`

#### Decision 類 (PostToolUse, Stop, SubagentStop)

**Schema 定義**:
- `decision`: "block" | "allow" (optional)
- `reason`: string (optional)

**HookResult 對應**:
```python
HookResult(
    block=True,                   # → decision='block'
    block_reason='...'            # → reason
)
```

#### Context 類 (所有事件)

**Schema 定義**:
- `hookSpecificOutput.additionalContext`: string (optional)

**HookResult 對應**:
```python
HookResult(
    additional_context='...'      # → additionalContext
)
```

#### System 控制 (所有事件可用)

**Schema 定義**:
- `continue`: boolean (optional, default: true)
- `stopReason`: string (optional)
- `suppressOutput`: boolean (optional)
- `systemMessage`: string (optional)

**HookResult 對應**:
```python
HookResult(
    continue_processing=False,    # → continue=false
    stop_reason='...',            # → stopReason
    suppress=True,                # → suppressOutput=true
    system_message='...'          # → systemMessage
)
```

### 5. 測試覆蓋

新增測試: `tests/test_schema_consistency.py`

測試項目:
- ✅ HookResult 欄位完整性 (1 測試)
- ✅ 各事件 Schema 定義 (12 測試)
- ✅ emit 函數覆蓋 (1 測試)

**總計**: 14/14 測試通過 (100%)

## 發現的問題與修正

### 問題 1: emit 函數欠缺 system 控制欄位

**問題**: emit 函數原本只處理 `additionalContext` 和 `block`,缺少:
- `continue`
- `stopReason`
- `suppressOutput`
- `systemMessage`

**修正**: output.py:107-114 新增 system 控制欄位處理

### 問題 2: PermissionRequest 欄位名稱不一致

**問題**: PermissionRequest 應使用 `decision` 而非 `permissionDecision`

**修正**: output.py:119-120 針對 PermissionRequest 特殊處理

### 問題 3: Decision 類事件輸出格式

**問題**: Stop/SubagentStop 應輸出 `decision` + `reason` 而非 `block`

**修正**: output.py:133-141 根據事件類型選擇輸出格式

## 驗證方法

### 手動測試

```bash
# 測試 PreToolUse transform
echo '{"hook_event_name":"PreToolUse","session_id":"test","transcript_path":"/tmp/t.jsonl","cwd":"/home","permission_mode":"default","tool_name":"Bash","tool_input":{"command":"rm file.txt"},"tool_use_id":"t1"}' | python3 main.py

# 預期輸出
{
  "hookSpecificOutput": {
    "permissionDecision": "allow",
    "permissionDecisionReason": "...",
    "updatedInput": {"command": "trash rm file.txt"}
  }
}
```

### 自動化測試

```bash
# 運行 Schema 一致性測試
python3 tests/test_schema_consistency.py

# 運行完整測試套件
python3 tests/run_all.py
```

## 結論

✅ **Schema 一致性: 100%**

- 所有 Schema 定義的欄位都在 HookResult 中有對應
- emit 函數正確處理所有輸出欄位
- 新增專門測試確保未來一致性
- 發現並修正了 3 個輸出處理問題

## 建議

### 短期
1. ✅ 新增 Schema 一致性測試 - 已完成
2. ✅ 修正 emit 函數欠缺欄位 - 已完成
3. ⚠️ 建議 handlers 開始使用 system 控制欄位

### 中期
1. 新增測試案例驗證所有事件的輸出格式
2. 新增 JSON Schema 自動驗證到 CI/CD
3. 文檔化各事件的標準輸出格式

### 長期
1. 考慮自動從 Schema 生成 TypedDict 定義
2. 考慮使用 Pydantic 進行運行時驗證
3. 建立 Schema 變更的向後兼容性測試
