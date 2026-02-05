#!/usr/bin/env python3
"""修復所有 schema examples 加入 hookEventName"""
import json
from pathlib import Path

SCHEMA_DIR = Path(__file__).parent.parent / "config" / "schema"

def fix_examples(event_name: str):
    """修復單個 schema 的 examples"""
    schema_file = SCHEMA_DIR / f"{event_name}.json"
    if not schema_file.exists():
        return False

    with open(schema_file, 'r', encoding='utf-8') as f:
        schema = json.load(f)

    examples = schema.get("examples", {})
    modified = False

    # 找所有 response_* examples
    for key, value in examples.items():
        if not key.startswith('response_'):
            continue

        # 檢查是否有 hookSpecificOutput
        if 'hookSpecificOutput' not in value:
            continue

        hook_spec = value['hookSpecificOutput']

        # 已有 hookEventName？
        if 'hookEventName' in hook_spec:
            continue

        # 加入 hookEventName（在最前面）
        new_hook_spec = {'hookEventName': event_name}
        new_hook_spec.update(hook_spec)
        value['hookSpecificOutput'] = new_hook_spec
        modified = True
        print(f"  ✓ {event_name}: {key}")

    if modified:
        with open(schema_file, 'w', encoding='utf-8') as f:
            json.dump(schema, f, ensure_ascii=False, indent=2)
        return True

    return False

def main():
    events = [
        'UserPromptSubmit',
        'PreToolUse',
        'PostToolUse',
        'PostToolUseFailure',
        'SessionStart',
        'SubagentStart',
        'PermissionRequest',
        'Notification',
        'PreCompact',
        'SessionEnd',
    ]

    print("修復 schema examples...\n")

    fixed = 0
    for event in events:
        if fix_examples(event):
            fixed += 1

    print(f"\n完成: {fixed} 個 schema 已更新")

if __name__ == '__main__':
    main()
