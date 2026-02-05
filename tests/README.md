# V2 測試框架

## 四層測試架構

```
Level 1: Basic (基本測試)
  ├─ 12 個事件的 smoke test
  └─ 驗證 stdin → main.py → stdout 流程

Level 2: JSON (Schema 驗證)
  ├─ Schema 檔案格式檢查
  ├─ Event Input 驗證
  └─ Response Output 驗證

Level 3: Rules (規則驗證)
  ├─ Rule 檔案格式檢查
  ├─ Rule 必填欄位驗證
  ├─ Rules Loader 測試
  └─ Rule Validation (12 cases)

Level 4: Integration (整合測試)
  ├─ Permission workflow (PreToolUse deny)
  ├─ Context injection (UserPromptSubmit)
  ├─ Block workflow (PostToolUse)
  └─ Feature workflow (tags, agents, skills)
```

## 使用方式

### 運行所有測試

```bash
cd v2/tests
python3 run_all.py
```

### 運行指定層級

```bash
# 只運行基本測試
python3 run_all.py --level basic

# 只運行 JSON Schema 測試
python3 run_all.py --level json

# 只運行規則驗證
python3 run_all.py --level rules

# 只運行整合測試
python3 run_all.py --level integration
```

### 詳細輸出

```bash
python3 run_all.py --verbose
```

### JSON 格式輸出

```bash
# 輸出到 stdout
python3 run_all.py --json

# 輸出到檔案
python3 run_all.py --json --output report.json
```

### 儲存報告

```bash
# 文字格式
python3 run_all.py --output report.txt

# JSON 格式
python3 run_all.py --json --output report.json
```

## 單獨運行測試

每個測試檔案都可以獨立運行:

```bash
# 基本測試
python3 test_basic.py

# JSON 測試
python3 test_json.py

# Rules 測試
python3 test_rules.py

# Rule validation 測試
python3 test_rule_validation.py

# Logger 測試
python3 test_utils/test_logger.py

# 整合測試
python3 test_integration.py
```

## 測試框架結構

```
tests/
├── framework.py               # 測試框架核心
│   ├── TestRunner            # 測試運行器
│   ├── TestResult            # 測試結果
│   ├── TestReport            # 測試報告
│   └── TestLevel             # 測試層級
│
├── test_basic.py             # Level 1: 基本測試
├── test_json.py              # Level 2: JSON Schema 測試
├── test_rules.py             # Level 3: Rules 測試
├── test_rule_validation.py   # Level 3: Rule 驗證測試 (12 cases)
├── test_schema_consistency.py # Level 2: Schema 一致性測試
├── test_integration.py       # Level 4: 整合測試
│
├── test_utils/               # Utility 測試
│   └── test_logger.py        # Logger 測試 (8 tests)
│
├── run_all.py                # 統一測試運行器
└── README.md                 # 本文件
```

## 測試數據來源

### 1. Event 樣本數據

從 `config/schema/*.json` 的 `examples.event_example` 提取

### 2. Response 樣本數據

從 `config/schema/*.json` 的 `examples.response_*` 提取

### 3. Rule 樣本數據

從 `config/rules/*.md` 的 frontmatter 提取

## 輸出範例

### 文字格式

```
============================================================
測試報告
============================================================

BASIC (12/12):
  ✓ UserPromptSubmit - 基本流程
  ✓ PreToolUse - 基本流程
  ✓ PostToolUse - 基本流程
  ...

JSON (36/36):
  ✓ PreToolUse.json 格式
  ✓ UserPromptSubmit.json 格式
  ...

RULES (22/22):
  ✓ userprompt-tags 格式
  ✓ permission-block-rm 格式
  ...

INTEGRATION (6/6):
  ✓ PreToolUse deny workflow
  ✓ UserPromptSubmit context injection
  ...

------------------------------------------------------------
總計: ✓ 76/76 (100.0%)
============================================================
```

### JSON 格式

```json
{
  "total": 76,
  "passed": 76,
  "failed": 0,
  "pass_rate": "100.0%",
  "results": [
    {
      "name": "UserPromptSubmit - 基本流程",
      "level": "basic",
      "passed": true,
      "message": "成功執行並返回 JSON",
      "details": {...},
      "error": null
    },
    ...
  ]
}
```

## 依賴

### 必需

- Python 3.11+ (tomllib in standard library)
- PyYAML (用於解析 rule frontmatter)

### 可選

- jsonschema (用於 JSON Schema 驗證,Level 2 需要)

安裝依賴:

```bash
pip install -r ../requirements.txt
```

## 返回碼

- `0` - 所有測試通過
- `1` - 有測試失敗

適合用於 CI/CD:

```bash
python3 run_all.py || exit 1
```

## 擴展測試

### 新增測試用例

1. 在對應的 `test_*.py` 加入測試函數
2. 返回 `TestResult` 物件
3. 調用 `runner.report.add(result)`

### 新增測試層級

1. 在 `framework.py` 的 `TestLevel` 加入新層級
2. 建立 `test_<level>.py`
3. 實作 `run_<level>_tests(runner)` 函數
4. 在 `run_all.py` 註冊層級

## 常見問題

### Q: 為什麼 JSON 測試被跳過?

A: 需要安裝 `jsonschema`:

```bash
pip install jsonschema
```

### Q: 如何只測試單一事件?

A: 修改對應測試檔案的事件列表,或直接在 Python 中 import 並調用特定測試函數

### Q: 測試失敗如何除錯?

A: 使用 `--verbose` 參數查看詳細輸出:

```bash
python3 run_all.py --verbose
```

或查看 `details` 和 `error` 欄位:

```bash
python3 run_all.py --json | jq '.results[] | select(.passed == false)'
```
