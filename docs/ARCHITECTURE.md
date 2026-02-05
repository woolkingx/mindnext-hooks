# V2 架構設計

**核心理念**: Schema-Driven + 全局物件化 + 零傳遞

---

## 設計原則

### 1. Schema 即契約

```
config/schema/PreToolUse.json
├── definitions.event      ← Input 型別定義
├── definitions.response   ← Output 型別定義
├── definitions.rule       ← Rule 配置定義
└── examples               ← 完整範例
```

**單一真相源**: 所有型別、文檔、範例、驗證規則來自 schema

### 2. 物件化 Payload

**Before (V1)**:
```python
payload.get('prompt')              # 💀 字典地獄
payload.get('tool_input', {}).get('command')  # 💀💀
```

**After (V2)**:
```python
event.prompt                       # ✅ 物件訪問
event.tool_input.command           # ✅ IDE 自動補全
```

### 3. 全局 Event Context

**Before (層層傳遞)**:
```python
main(payload) → route(payload) → handler(payload) → feature(payload)
```

**After (全局訪問)**:
```python
EventContext.set(event)  # main.py 設置一次
get_event()              # 任何地方直接取用
```

**理由**: Event 是**只讀環境**,不是**可變狀態**

---

## 架構圖

```
┌─────────────────────────────────────────────────────────┐
│ main.py                                                 │
├─────────────────────────────────────────────────────────┤
│ 1. stdin → JSON                                         │
│ 2. Schema 驗證 (validate_event)                         │
│ 3. JSON → Event 物件 (from_dict)                        │
│ 4. 設置全局 EventContext.set(event)  ← 唯一設置點       │
│ 5. 載入 rules                                           │
│ 6. 路由 route(rules)                                    │
│ 7. 整合輸出 merge → emit                                │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ router.py                                               │
├─────────────────────────────────────────────────────────┤
│ 1. event = get_event()  ← 從全局取得                    │
│ 2. 篩選 matched_rules                                   │
│ 3. 並發調用 handlers (傳 rule,不傳 event)               │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ handlers/*.py                                           │
├─────────────────────────────────────────────────────────┤
│ async def process(rule):  ← 只接收 rule                 │
│   event = get_event()     ← 從全局取得                  │
│   if isinstance(event, UserPromptSubmit):  ← 型別窄化   │
│       # event.prompt                                    │
│       # event.session_id                                │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ features/*.py                                           │
├─────────────────────────────────────────────────────────┤
│ def process():            ← 無參數                      │
│   event = get_event()     ← 從全局取得                  │
│   return context_string                                 │
└─────────────────────────────────────────────────────────┘
```

---

## 數據流

### Input (stdin → Event)

```python
# 1. 原始 JSON
raw = {"hook_event_name": "PreToolUse", "tool_name": "Bash", ...}

# 2. Schema 驗證
validate_event(raw)  # 基於 config/schema/PreToolUse.json

# 3. 轉換為物件
event = from_dict(raw)  # → PreToolUse(tool_name='Bash', ...)

# 4. 設置全局
EventContext.set(event)
```

### Processing (全局訪問)

```python
# 任何層級都可直接取用
event = get_event()

# 型別窄化
if isinstance(event, PreToolUse):
    print(event.tool_name)      # IDE 自動補全
    print(event.tool_input)     # 型別安全
```

### Output (Event → JSON)

```python
# 1. Handler 返回 HookResult
result = HookResult(
    permission='deny',
    permission_reason='危險操作'
)

# 2. 轉換為官方 JSON 格式
output = {
    'hookSpecificOutput': {
        'permissionDecision': 'deny',
        'permissionDecisionReason': '危險操作'
    }
}

# 3. 驗證 (可選)
validate_response('PreToolUse', output)

# 4. stdout
print(json.dumps(output))
```

---

## 目錄結構

```
v2/
├── main.py                    # 入口 (唯一設置 EventContext)
├── router.py                  # 路由 (取 event,分發 rules)
│
├── config/
│   └── schema/                # Schema 定義 (三段式)
│       ├── PreToolUse.json
│       └── UserPromptSubmit.json
│
├── utils/
│   ├── events.py              # Event 型別定義 (12 個 dataclass)
│   ├── responses.py           # Response 型別定義
│   ├── context.py             # EventContext (全局單例)
│   └── schema_validator.py    # Schema 驗證器
│
├── handlers/                  # 事件處理器
│   └── UserPromptSubmit.py    # async def process(rule)
│
├── features/                  # 功能模組
│   └── tags.py                # def process() → str
│
└── loaders/                   # 載入器
    └── rules.py               # 載入 rule 配置
```

---

## 核心組件

### EventContext (utils/context.py)

```python
class EventContext:
    _event: Optional[BaseEvent] = None

    @classmethod
    def set(cls, event: BaseEvent):
        """main.py 啟動時調用一次"""
        cls._event = event

    @classmethod
    def get(cls) -> BaseEvent:
        """任何地方取用"""
        return cls._event
```

**設計理由**:
- Event 是**只讀環境** (如 `os.environ`, `sys.argv`)
- 不需要層層傳遞
- 全局訪問無副作用

### Event 型別 (utils/events.py)

```python
@dataclass
class PreToolUse(BaseEvent):
    tool_name: str
    tool_input: Dict[str, Any]
    tool_use_id: str

@dataclass
class UserPromptSubmit(BaseEvent):
    prompt: str

# ... 共 12 個事件類型
```

**從 JSON 轉換**:
```python
event = from_dict({"hook_event_name": "PreToolUse", ...})
# → PreToolUse(tool_name=..., tool_input=...)
```

### Handler 介面 (handlers/*.py)

```python
async def process(rule: Dict[str, Any]) -> Optional[HookResult]:
    """
    Args:
        rule: rule 配置 (dict)

    Returns:
        HookResult 或 None

    注意: event 從 EventContext.get() 取得
    """
    event = get_event()

    if isinstance(event, UserPromptSubmit):
        # 型別窄化,IDE 知道有 .prompt
        print(event.prompt)
```

### Feature 介面 (features/*.py)

```python
def process() -> Optional[str]:
    """
    無參數 - 從 EventContext 取 event

    Returns:
        context 字串或 None
    """
    event = get_event()

    if isinstance(event, UserPromptSubmit):
        return f"User said: {event.prompt}"
```

---

## 對比 V1

| 項目 | V1 | V2 |
|------|----|----|
| Payload 型別 | `dict` | `BaseEvent` (dataclass) |
| 訪問方式 | `.get('key')` | `.attribute` |
| IDE 支援 | ❌ | ✅ 自動補全 |
| 型別檢查 | ❌ | ✅ mypy/pyright |
| 傳遞方式 | 層層傳遞 | 全局訪問 |
| Schema | 無 | ✅ JSON Schema |
| 驗證 | 手動 | ✅ 自動驗證 |
| 文檔 | 分散 | ✅ Schema 即文檔 |

---

## 使用範例

### 新增事件處理

1. **定義 Schema** (若新事件)
   ```bash
   cp config/schema/PreToolUse.json config/schema/NewEvent.json
   # 修改 definitions + examples
   ```

2. **更新 utils/events.py** (若新事件)
   ```python
   @dataclass
   class NewEvent(BaseEvent):
       custom_field: str
   ```

3. **建立 Handler**
   ```python
   # handlers/NewEvent.py
   async def process(rule):
       event = get_event()
       if isinstance(event, NewEvent):
           print(event.custom_field)  # ✅ 自動補全
   ```

### 測試

```python
# tests/test_newevent.py
from v2.utils.events import from_dict
from v2.utils.context import EventContext

def test_newevent():
    # 從 schema 載入範例
    event = from_dict({
        "hook_event_name": "NewEvent",
        "custom_field": "test"
    })

    EventContext.set(event)

    # 測試 handler
    from v2.handlers.NewEvent import process
    result = await process({'action': 'test'})
```

---

## 優勢總結

### ✅ 開發體驗

- 減少 50% 的 `.get()` 調用
- IDE 自動補全所有欄位
- 重構時不會漏改

### ✅ 型別安全

- 編譯期檢查 (mypy)
- 執行期驗證 (jsonschema)
- 打錯字立即發現

### ✅ 維護性

- Schema 是單一真相源
- 修改 schema → 自動更新所有下游
- 版本控制清晰

### ✅ 性能

- 無重複傳遞開銷
- 無重複解析
- 並發安全 (只讀)

---

## 遷移指南 (V1 → V2)

### Handler 遷移

**Before (V1)**:
```python
def process(trigger, payload):
    prompt = payload.get('prompt')
    tool_name = payload.get('tool_name')
```

**After (V2)**:
```python
async def process(rule):
    event = get_event()

    if isinstance(event, UserPromptSubmit):
        prompt = event.prompt  # ✅

    if isinstance(event, PreToolUse):
        tool_name = event.tool_name  # ✅
```

### Feature 遷移

**Before (V1)**:
```python
def process(prompt: str) -> str:
    return f"Context: {prompt}"
```

**After (V2)**:
```python
def process() -> str:
    event = get_event()

    if isinstance(event, UserPromptSubmit):
        return f"Context: {event.prompt}"
```

---

## FAQ

### Q: 為何不傳遞 event?

**A**: Event 是只讀環境,全局訪問更符合語義。類比 `os.environ`, `sys.argv` 都是全局的,無人會寫 `def main(argv)` 傳來傳去。

### Q: 並發安全嗎?

**A**: 安全。一個進程只處理一個 event,設置一次後只讀。若未來需處理多 event,改用 `contextvars.ContextVar`。

### Q: 測試怎麼辦?

**A**: `EventContext.set(mock_event)`,每個測試獨立設置。

### Q: Rule 為何還是 dict?

**A**: Rule 結構動態 (不同事件有不同欄位),用 dict 更靈活。Event 結構固定,用 dataclass。

---

## 未來擴展

- [ ] 從 schema 自動生成 dataclass
- [ ] 從 schema 生成 TypeScript 型別
- [ ] 從 schema 生成測試 fixture
- [ ] 支援 `contextvars` (若需多 event 並發)
