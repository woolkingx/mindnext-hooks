#!/usr/bin/env python3
"""按照 hooks-matrix.md 官方 API 完整修正所有 schema"""
import json
from pathlib import Path

SCHEMA_DIR = Path(__file__).parent.parent / "config" / "schema"

# 官方 API 定義（來自 hooks-matrix.md）
TOOL_RESPONSE_SCHEMA = {
    "type": "object",
    "description": "工具執行結果（物件格式）",
    "properties": {
        "stdout": {"type": "string", "description": "標準輸出"},
        "stderr": {"type": "string", "description": "標準錯誤"},
        "interrupted": {"type": "boolean", "description": "是否中斷"},
        "isImage": {"type": "boolean", "description": "是否為圖片"}
    }
}

ERROR_SCHEMA = {
    "type": "object",
    "description": "錯誤訊息（物件格式）",
    "properties": {
        "message": {"type": "string", "description": "錯誤訊息"},
        "type": {"type": "string", "description": "錯誤類型"},
        "stack": {"type": "string", "description": "錯誤堆疊"}
    }
}

def fix_posttooluse():
    """修正 PostToolUse: tool_response 是物件"""
    file = SCHEMA_DIR / "PostToolUse.json"
    schema = json.loads(file.read_text())

    # 修正 tool_response
    props = schema["definitions"]["event"]["properties"]
    if props.get("tool_response", {}).get("type") != "object":
        props["tool_response"] = TOOL_RESPONSE_SCHEMA
        print(f"✓ PostToolUse: tool_response 改為 object")
        file.write_text(json.dumps(schema, ensure_ascii=False, indent=2))
        return True
    return False

def fix_posttoolusefailure():
    """修正 PostToolUseFailure: error 是物件"""
    file = SCHEMA_DIR / "PostToolUseFailure.json"
    schema = json.loads(file.read_text())

    # 修正 error
    props = schema["definitions"]["event"]["properties"]
    if props.get("error", {}).get("type") == "string":
        props["error"] = ERROR_SCHEMA
        print(f"✓ PostToolUseFailure: error 改為 object")

        # 同時需要 tool_input（官方有此欄位）
        if "tool_input" not in props:
            props["tool_input"] = {
                "type": "object",
                "description": "工具輸入參數"
            }
            # 更新 required
            if "tool_input" not in schema["definitions"]["event"]["required"]:
                schema["definitions"]["event"]["required"].append("tool_input")
            print(f"✓ PostToolUseFailure: 加入 tool_input")

        file.write_text(json.dumps(schema, ensure_ascii=False, indent=2))
        return True
    return False

def main():
    print("按照 hooks-matrix.md 修正 schema...\n")

    fixes = [
        ("PostToolUse", fix_posttooluse),
        ("PostToolUseFailure", fix_posttoolusefailure),
    ]

    fixed = 0
    for name, fix_func in fixes:
        try:
            if fix_func():
                fixed += 1
        except Exception as e:
            print(f"✗ {name}: {e}")

    print(f"\n完成: {fixed} 個 schema 已修正")

if __name__ == '__main__':
    main()
