# V2 Schema 完整定義

**狀態**: ✅ 12/12 完成 (100%)
**最後更新**: 2026-01-31

---

## 概述

本目錄包含 Claude Code Hooks 所有 12 個事件的完整 JSON Schema 定義,作為整個系統的**單一真相源**。

### 三位一體設計

每個 schema 文件包含三個核心定義:

```json
{
  "definitions": {
    "event": {/* Input 驗證 - 從 stdin 接收 */},
    "response": {/* Output 驗證 - 到 stdout 輸出 */},
    "rule": {/* Rule 驗證 - YAML frontmatter */}
  },
  "examples": {/* 實際可用的範例 */}
}
```

---

## Schema 清單

### 可阻止事件 (6/12)

| # | Event | 用途 | Examples | Schema |
|---|-------|------|----------|--------|
| 1 | **PreToolUse** | 工具執行前權限控制 | 6 | 7.5 KB |
| 2 | **PostToolUse** | 工具執行後驗證 | 4 | 5.6 KB |
| 3 | **UserPromptSubmit** | 用戶提交前處理 | 5 | 5.8 KB |
| 4 | **Stop** | Claude 響應結束前 | 2 | 3.1 KB |
| 5 | **SubagentStop** | 子代理結束前 | 2 | 3.4 KB |
| 6 | **PermissionRequest** | 權限對話框 | 3 | 4.4 KB |

### 上下文事件 (4/12)

| # | Event | 用途 | Examples | Schema |
|---|-------|------|----------|--------|
| 7 | **SessionStart** | 會話初始化 | 2 | 3.5 KB |
| 8 | **SubagentStart** | 子代理啟動 | 1 | 3.3 KB |
| 9 | **PostToolUseFailure** | 工具執行失敗 | 2 | 3.9 KB |
| 10 | **Notification** | 通知發送 | 2 | 3.5 KB |

### 被動事件 (2/12)

| # | Event | 用途 | Examples | Schema |
|---|-------|------|----------|--------|
| 11 | **PreCompact** | 對話壓縮前 | 1 | 3.2 KB |
| 12 | **SessionEnd** | 會話結束 | 1 | 3.1 KB |

---

## 統計數據

```
總檔案數:        12
總大小:          50.8 KB
平均大小:        4.2 KB

總範例數:        31
平均範例/檔案:   2.6

可阻止事件:      6 (50%)
上下文事件:      4 (33%)
被動事件:        2 (17%)

必填欄位:
  最少:          5 (SessionEnd)
  最多:          9 (PostToolUse, PostToolUseFailure)
  平均:          7.0
```

---

## Schema 結構

### Event Definition (輸入層)

**通用欄位** (所有事件):
```json
{
  "hook_event_name": "EventName",
  "session_id": "string",
  "transcript_path": "string",
  "cwd": "string",
  "permission_mode": "default|plan|acceptEdits|dontAsk|bypassPermissions"
}
```

**擴展元數據**:
- `x-usage`: 事件用途說明
- `x-canBlock`: 是否可阻止執行

**事件專用欄位** (依事件類型):

| Event | 專用欄位 |
|-------|---------|
| PreToolUse | `tool_name`, `tool_input`, `tool_use_id` |
| PostToolUse | `tool_name`, `tool_input`, `tool_response`, `tool_use_id` |
| PostToolUseFailure | `tool_name`, `tool_input`, `error`, `tool_use_id` |
| UserPromptSubmit | `prompt` |
| Stop | `stop_hook_active` |
| SubagentStart | `task_description`, `subagent_type` |
| SubagentStop | `stop_hook_active`, `task_description`, `subagent_type` |
| SessionStart | `source` |
| SessionEnd | `reason` |
| Notification | `message`, `notification_type` |
| PreCompact | `trigger`, `custom_instructions` |
| PermissionRequest | `tool_name`, `tool_input`, `tool_use_id` |

### Response Definition (輸出層)

**通用欄位**:
```json
{
  "continue": false,
  "stopReason": "string",
  "suppressOutput": false,
  "systemMessage": "string"
}
```

**事件專用輸出**:

| Event | 專用輸出 |
|-------|---------|
| PreToolUse | `hookSpecificOutput.permissionDecision` (allow/deny/ask) |
| | `hookSpecificOutput.permissionDecisionReason` |
| | `hookSpecificOutput.updatedInput` |
| PostToolUse | `decision` (block) |
| | `reason` |
| | `hookSpecificOutput.additionalContext` |
| UserPromptSubmit | `decision` (block) |
| | `reason` |
| | `hookSpecificOutput.additionalContext` |
| Stop | `decision` (block) |
| | `reason` |
| SubagentStop | `decision` (block) |
| | `reason` |
| PermissionRequest | `hookSpecificOutput.decision.behavior` (allow/deny) |
| | `hookSpecificOutput.decision.updatedInput` |
| | `hookSpecificOutput.decision.message` |
| | `hookSpecificOutput.decision.interrupt` |
| 其他 | `hookSpecificOutput.additionalContext` |

### Rule Definition (配置層)

**基礎欄位** (所有 rule):
```yaml
name: "rule-name"           # 必填
description: "說明"          # 必填
enabled: true               # 必填
event: EventName            # 必填
priority: 50                # 可選 (0-100, 預設 50)
match: "pattern"            # 可選
action: "action_type"       # 可選
reason: "原因"              # 可選
```

**事件專用欄位**:

| Event | 專用欄位 |
|-------|---------|
| PreToolUse | `tool`, `updatedInput` |
| PostToolUse | `tool` |
| UserPromptSubmit | `feature: [tags, memory, ...]` |
| 其他 | 無特殊欄位 |

---

## Examples (範例)

每個 schema 包含實際可用的範例:

### Event Example
真實的 stdin payload,可直接用於測試:
```bash
echo '$(cat schema/PreToolUse.json | jq .examples.event_example)' | python3 v2/main.py
```

### Response Examples
多個輸出場景:
- 成功響應
- 阻止響應
- 轉換響應
- 上下文注入

### Rule Examples
多個配置場景:
- 基本匹配
- 結構化匹配
- 優先級設置
- 轉換規則

---

## 使用方式

### 1. 驗證 Event

```python
from v2.utils.schema_validator import validate_event

raw_payload = json.loads(sys.stdin.read())
error = validate_event(raw_payload)
if error:
    print(f"Invalid event: {error}")
```

### 2. 驗證 Response

```python
from v2.utils.schema_validator import validate_response

error = validate_response('PreToolUse', response_data)
if error:
    print(f"Invalid response: {error}")
```

### 3. 驗證 Rule

```python
from v2.utils.schema_validator import validate_rule

error = validate_rule(rule_config)
if error:
    print(f"Invalid rule: {error}")
```

### 4. 生成測試數據

```bash
# 提取 event example
jq '.examples.event_example' schema/PreToolUse.json

# 提取所有 response examples
jq '.examples | to_entries | map(select(.key | startswith("response_")))' schema/PreToolUse.json
```

---

## 開發工作流

### 新增事件 (若未來擴展)

1. **建立 Schema**
   ```bash
   cp schema/PreToolUse.json schema/NewEvent.json
   ```

2. **修改定義**
   - 更新 `$id`, `title`, `description`
   - 修改 `definitions.event` (input 欄位)
   - 修改 `definitions.response` (output 欄位)
   - 修改 `definitions.rule` (配置欄位)
   - 更新 `examples` (至少 3 個)

3. **更新型別**
   ```python
   # v2/utils/events.py
   @dataclass
   class NewEvent(BaseEvent):
       custom_field: str
   ```

4. **建立 Handler**
   ```python
   # v2/handlers/NewEvent.py
   async def process(rule):
       event = get_event()
       if isinstance(event, NewEvent):
           ...
   ```

### 修改現有 Schema

**重要**: Schema 是 API 契約,修改需謹慎

**向後兼容變更** (安全):
- ✅ 新增可選欄位
- ✅ 放寬型別限制
- ✅ 新增 enum 值
- ✅ 新增 examples

**破壞性變更** (需版本升級):
- ❌ 刪除欄位
- ❌ 重命名欄位
- ❌ 改變必填/可選
- ❌ 收緊型別限制
- ❌ 移除 enum 值

---

## Schema 驗證

### 本地驗證

```bash
# 安裝 jsonschema (可選)
pip install jsonschema

# Python 驗證
python3 -c "
import json
from pathlib import Path
from jsonschema import validate, Draft7Validator

for f in Path('schema').glob('*.json'):
    schema = json.loads(f.read_text())
    Draft7Validator.check_schema(schema)
    print(f'✅ {f.name}')
"
```

### CI 驗證

```yaml
# .github/workflows/schema-validation.yml
- name: Validate Schemas
  run: |
    python3 -m pip install jsonschema
    python3 scripts/validate_schemas.py
```

---

## 參考資料

- **官方 API**: `/docs/hooks-matrix.md`
- **JSON Schema 規範**: https://json-schema.org/
- **驗證器實作**: `/v2/utils/schema_validator.py`
- **型別定義**: `/v2/utils/events.py`

---

## FAQ

### Q: 為何用 JSON Schema?

**A**:
- ✅ 標準化驗證
- ✅ 自動生成文檔
- ✅ IDE 整合支援
- ✅ 語言無關

### Q: 為何三段式 (event + response + rule)?

**A**:
- ✅ 一個檔案看完整 API
- ✅ 修改不會漏
- ✅ 就近原則 (locality of reference)

### Q: Examples 是必須的嗎?

**A**:
- ✅ 強烈建議,但不強制
- ✅ 用於測試和文檔
- ✅ 新開發者參考

### Q: 如何生成 TypeScript 型別?

**A**:
```bash
npm install -g json-schema-to-typescript
json2ts schema/PreToolUse.json > types/PreToolUse.d.ts
```

---

**維護者**: mindnext-hooks 開發團隊
**版本**: v2.0
**最後更新**: 2026-01-31
