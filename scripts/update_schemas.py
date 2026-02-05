#!/usr/bin/env python3
"""批次更新所有 schema 加入 hookEventName 必填欄位"""
import json
from pathlib import Path

SCHEMA_DIR = Path(__file__).parent.parent / "config" / "schema"

# 定義每個事件的 hookSpecificOutput 結構
EVENTS = {
    # Group 1: 只有 additionalContext
    "SessionStart": ["additionalContext"],
    "SubagentStart": ["additionalContext"],
    "PostToolUseFailure": ["additionalContext"],
    "Notification": ["additionalContext"],
    "PreCompact": [],  # 沒有 hookSpecificOutput
    "SessionEnd": [],  # 沒有 hookSpecificOutput

    # Group 2: additionalContext + 其他
    "UserPromptSubmit": ["additionalContext"],
    "PostToolUse": ["additionalContext", "updatedMCPToolOutput"],

    # Group 3: PreToolUse (permissionDecision)
    "PreToolUse": ["permissionDecision", "permissionDecisionReason", "updatedInput", "additionalContext"],

    # Group 4: PermissionRequest (decision 嵌套)
    "PermissionRequest": ["decision"],

    # Group 5: Stop 類 (無 hookSpecificOutput，用頂層 decision)
    "Stop": None,
    "SubagentStop": None,
}

def update_schema(event_name: str):
    """更新單個 schema"""
    schema_file = SCHEMA_DIR / f"{event_name}.json"
    if not schema_file.exists():
        print(f"❌ {event_name}.json not found")
        return False

    with open(schema_file, 'r', encoding='utf-8') as f:
        schema = json.load(f)

    # 找到 response.properties.hookSpecificOutput
    response_def = schema.get("definitions", {}).get("response", {})
    hook_specific = response_def.get("properties", {}).get("hookSpecificOutput")

    if not hook_specific:
        # Stop/SubagentStop 沒有 hookSpecificOutput
        if EVENTS[event_name] is None:
            print(f"✓ {event_name}: 無 hookSpecificOutput (正確)")
            return True
        else:
            print(f"⚠ {event_name}: 缺少 hookSpecificOutput 定義")
            return False

    # 已有 hookEventName？
    if "hookEventName" in hook_specific.get("properties", {}):
        print(f"✓ {event_name}: 已有 hookEventName")
        return True

    # 加入 hookEventName
    if "properties" not in hook_specific:
        hook_specific["properties"] = {}

    # 在最前面插入 hookEventName
    new_props = {
        "hookEventName": {
            "type": "string",
            "const": event_name,
            "description": "事件名稱 (必填)"
        }
    }
    new_props.update(hook_specific["properties"])
    hook_specific["properties"] = new_props

    # 設置 required
    if "required" not in hook_specific:
        hook_specific["required"] = []
    if "hookEventName" not in hook_specific["required"]:
        hook_specific["required"].insert(0, "hookEventName")

    # 寫回文件
    with open(schema_file, 'w', encoding='utf-8') as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)

    print(f"✅ {event_name}: 已加入 hookEventName")
    return True

def main():
    print("開始更新 schema 文件...\n")

    success = 0
    failed = 0

    for event_name in EVENTS.keys():
        if update_schema(event_name):
            success += 1
        else:
            failed += 1

    print(f"\n完成: {success} 成功, {failed} 失敗")

if __name__ == "__main__":
    main()
