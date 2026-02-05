# Payload API

## Handle Payload 結構

```python
handle_payload = {
    'rule': {
        'name': str,
        'event': str,
        'match': dict | str | None,
        'action': str | None,
        'feature': list[str] | None,
        'params': dict | None,
    },
    'claude': {
        'hook_event_name': str,
        'tool_name': str | None,
        'tool_input': dict | None,
        'prompt': str | None,
        'tool_output': dict | None,
    }
}
```

## 提取範例

```python
rule = handle_payload['rule']
claude = handle_payload['claude']

event = rule['event']
prompt = claude.get('prompt', '')
tool_name = claude.get('tool_name', '')
```

## Rule Payload 欄位

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| name | str | ✓ | Rule 名稱 |
| event | str | ✓ | 事件類型 |
| match | dict\|str | | 匹配條件 |
| action | str | | 動作（deny/ask/allow） |
| feature | list[str] | | 特性列表 |
| params | dict | | 參數 |

## Claude Payload 欄位

| 欄位 | 類型 | 說明 |
|------|------|------|
| hook_event_name | str | 事件名稱 |
| tool_name | str | 工具名稱（PreToolUse） |
| tool_input | dict | 工具輸入 |
| prompt | str | 用戶提示（UserPromptSubmit） |
| tool_output | dict | 工具輸出（PostToolUse） |
