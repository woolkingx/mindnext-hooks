# Rules 配置指南

規則檔案位於 `config/rules/*.md`，使用 YAML frontmatter 格式。

---

## 基本結構

```markdown
---
name: rule-name
description: 規則功能說明
enabled: true
event: PreToolUse
priority: 50
# ... 其他配置
---

可選的詳細說明文字（給人看的）
```

### 通用欄位

| 欄位 | 必填 | 說明 |
|------|:----:|------|
| `name` | ✅ | 規則唯一標識 |
| `description` | ✅ | 功能說明 |
| `enabled` | ❌ | 是否啟用 (預設 true) |
| `event` | ✅ | 事件類型 |
| `action` | ✅ | 動作類型 |
| `priority` | ❌ | 優先級，數字越大越先執行 (預設 0) |
| `message` | ❌ | 顯示給 Claude 或用戶的訊息 (支援變數) |

### 變數替換

`message` 欄位支援以下變數：

| 變數 | 說明 | 適用工具 |
|------|------|----------|
| `${command}` | 完整命令 | Bash |
| `${cmd}` | 主命令名 | Bash |
| `${args}` | 參數列表 | Bash |
| `${flags}` | flags 字串 | Bash |
| `${file_path}` | 檔案路徑 | Read, Write, Edit |
| `${tool}` | 工具名稱 | 所有 |

範例：
```yaml
message: |
  ⚠️ 需要手動執行：
  ```
  ${command}
  ```
```

---

## Events (8 個入口)

### 1. PreToolUse

工具執行前攔截，可允許/拒絕/改寫。

```yaml
---
name: example-pretooluse
description: PreToolUse 範例
enabled: true
event: PreToolUse
tool: Bash              # 工具名稱: Bash, Read, Write, Edit, Glob, Grep, WebFetch, Task...
match: "pattern"        # regex 匹配 (二選一)
cmd: rm                 # 結構化匹配 - 命令名 (二選一，僅 Bash)
action: allow|deny|ask|transform
---
```

**支援的 Actions**: `allow`, `deny`, `ask`, `transform`, `context`

**結構化匹配 (僅 Bash)**:
```yaml
cmd: rm                 # 主命令名
args_match: "^/"        # args 匹配 regex
flags: [r, f]           # 必須有這些 flags
has_flags: true         # 必須有任意 flag
any_cmd: [rm, del]      # 複合命令中任一匹配
```

---

### 2. PermissionRequest

權限對話框攔截，自動允許/拒絕。

```yaml
---
name: example-permission
description: PermissionRequest 範例
enabled: true
event: PermissionRequest
tool: Read
match: "\\.md$"
action: allow|deny
suppress: true          # 隱藏輸出 (allow 時)
interrupt: true         # 中斷 Claude (deny 時)
---
```

**支援的 Actions**: `allow`, `deny`

---

### 3. PostToolUse

工具執行後，提供反饋或注入上下文。

```yaml
---
name: example-posttooluse
description: PostToolUse 範例
enabled: true
event: PostToolUse
tool: Write
action: block|context
message: "Please run tests after writing code"
---
```

**支援的 Actions**: `block`, `context`

---

### 4. UserPromptSubmit

用戶輸入提交時，可阻擋或注入上下文。

```yaml
---
name: example-userprompt
description: UserPromptSubmit 範例
enabled: true
event: UserPromptSubmit
match: "記憶|recall|remember"
action: block|context|memory
message: "Context or block reason"
---
```

**支援的 Actions**: `block`, `context`, `memory`

---

### 5. Stop

Claude 準備停止時，可強制繼續。

```yaml
---
name: example-stop
description: Stop 範例
enabled: true
event: Stop
action: block|context
message: "Please run tests before stopping"
---
```

**支援的 Actions**: `block`, `context`

---

### 6. SubagentStop

Subagent 準備停止時，可強制繼續。

```yaml
---
name: example-subagentstop
description: SubagentStop 範例
enabled: true
event: SubagentStop
action: block|context
message: "Please verify results"
---
```

**支援的 Actions**: `block`, `context`

---

### 7. SessionStart

Session 啟動時，載入配置或注入上下文。

```yaml
---
name: example-sessionstart
description: SessionStart 範例
enabled: true
event: SessionStart
action: load|context
loaders:                # load action 用
  - type: file
    path: "~/.claude/CLAUDE.md"
    label: "User Config"
message: "Welcome!"     # context action 用
---
```

**支援的 Actions**: `load`, `context`

**Matcher** (可選):
- `startup` - 正常啟動
- `resume` - 從 --resume 恢復
- `clear` - 從 /clear 清除後
- `compact` - 從 compact 後

---

### 8. SubagentStart

Subagent 啟動時，載入配置或注入上下文。

```yaml
---
name: example-subagentstart
description: SubagentStart 範例
enabled: true
event: SubagentStart
action: load|context
loaders:
  - type: file
    path: "~/.claude/CLAUDE.md"
    label: "User Config"
---
```

**支援的 Actions**: `load`, `context`

---

## Actions (8 種動作)

### allow

自動允許操作，跳過權限確認。

```yaml
---
event: PreToolUse|PermissionRequest
action: allow
message: "Auto allowed"
suppress: true          # 隱藏輸出
---
```

---

### deny

拒絕操作，顯示原因給 Claude。

```yaml
---
event: PreToolUse|PermissionRequest
action: deny
message: "Operation not allowed"
interrupt: true         # 中斷 Claude (僅 PermissionRequest)
---
```

**帶變數的 deny**:
```yaml
---
event: PreToolUse
tool: Bash
cmd: sudo
action: deny
message: |
  ⚠️ sudo 需要用戶協助執行：
  ```
  ${command}
  ```
  請手動執行後告訴我結果。
---
```

---

### ask

詢問用戶確認 (僅 PreToolUse)。

```yaml
---
event: PreToolUse
action: ask
message: "Allow this operation?"
---
```

---

### transform

改寫命令 (僅 PreToolUse + Bash)。

```yaml
---
event: PreToolUse
tool: Bash
cmd: rm
action: transform
transform_cmd: trash-put    # 替換命令
transform_append: ".bak"    # 附加到 args 尾部
transform_prepend: sudo     # 命令前綴
transform_flags: [v]        # 替換 flags
keep_flags: true            # 保留原始 flags
message: "rm → trash-put"
hint: "下次請直接使用 trash-put"  # 教學提示
---
```

**Regex 模式**:
```yaml
---
event: PreToolUse
tool: Bash
match: "^rm\\s+(.+)$"
action: transform
transform: "mv $1 .cleanup/"   # $1 = 捕獲組
message: "rm → mv .cleanup/"
hint: "下次請用 mv 移動到 .cleanup/"
---
```

---

### block

阻止操作並反饋 (Stop, SubagentStop, UserPromptSubmit, PostToolUse)。

```yaml
---
event: Stop|SubagentStop|UserPromptSubmit|PostToolUse
action: block
message: "Reason for blocking"
---
```

---

### context / echo

注入上下文給 Claude (所有 events)。

```yaml
---
event: PreToolUse|PostToolUse|UserPromptSubmit|Stop|SessionStart|...
action: context
message: "Additional context for Claude"
suppress: true          # 隱藏輸出
---
```

---

### load

載入檔案 (SessionStart, SubagentStart)。

```yaml
---
event: SessionStart|SubagentStart
action: load
loaders:
  - type: file
    path: "~/.claude/CLAUDE.md"
    label: "User CLAUDE.md"
  - type: file
    path: "./PROJECT.md"
    label: "Project Config"
---
```

---

### memory

AI 記憶查詢 (UserPromptSubmit)。

```yaml
---
event: UserPromptSubmit
match: "記憶|記得|recall|remember"
action: memory
---
```

---

## Event → Action 對照表

| Event | allow | deny | ask | transform | block | context | load | memory |
|-------|:-----:|:----:|:---:|:---------:|:-----:|:-------:|:----:|:------:|
| PreToolUse | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| PermissionRequest | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| PostToolUse | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ |
| UserPromptSubmit | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ |
| Stop | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ |
| SubagentStop | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ |
| SessionStart | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ |
| SubagentStart | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ |

---

## 完整範例

### 危險命令阻擋

```yaml
---
name: block-dangerous-commands
description: 阻擋危險命令 (sudo rm, mkfs, dd, fork bomb)
enabled: true
event: PreToolUse
tool: Bash
match: "sudo\\s+rm|mkfs|dd\\s+if=|:\\(\\)\\{:\\|:&\\};:"
action: deny
message: "Dangerous command blocked"
priority: 100
---
```

### rm 轉 trash-put

```yaml
---
name: rm-to-trash
description: 將 rm 命令轉換為 trash-put
enabled: true
event: PreToolUse
tool: Bash
cmd: rm
action: transform
transform_cmd: trash-put
message: "rm → trash-put"
hint: "下次請直接使用 trash-put，可用 trash-restore 救回"
priority: 50
---
```

### 自動允許讀取文檔

```yaml
---
name: allow-docs
description: 自動允許讀取 .md 檔案
enabled: true
event: PreToolUse
tool: Read
match: "\\.md$"
action: allow
suppress: true
priority: 10
---
```

### 啟動時載入配置

```yaml
---
name: session-load-config
description: 啟動時載入用戶配置
enabled: true
event: SessionStart
action: load
loaders:
  - type: file
    path: "~/.claude/CLAUDE.md"
    label: "User CLAUDE.md"
  - type: file
    path: "~/.claude/skills/extends/SKILL.md"
    label: "Skills Index"
priority: 100
---
```

### 記憶查詢觸發

```yaml
---
name: memory-query
description: 觸發 AI 記憶查詢
enabled: true
event: UserPromptSubmit
match: "記憶|記得|之前|上次|recall|remember|previous"
action: memory
priority: 50
---
```

### 停止前檢查

```yaml
---
name: require-tests-before-stop
description: 停止前提醒執行測試
enabled: true
event: Stop
action: block
message: "Please run tests before stopping: npm test"
priority: 50
---
```

---

## 管理命令

```bash
# 列出所有規則
python3 -c "from utility.config import list_all_rules; import json; print(json.dumps(list_all_rules(), indent=2))"

# 重新載入規則
python3 -c "from utility.config import reload; reload(); print('Reloaded')"

# 測試規則匹配
python3 -c "from utility.config import get_triggers; print(get_triggers('PreToolUse'))"
```

---

## 檔案命名建議

- `{action}-{target}.md` - 如 `block-dangerous-commands.md`
- `{event}-{action}.md` - 如 `session-load-config.md`
- 使用 kebab-case
- 名稱要能一眼看出功能
