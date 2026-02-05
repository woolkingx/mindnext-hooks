"""Level 1: 基本測試

驗證 12 個事件的基本流程能運行:
- stdin → main.py → stdout
- 返回碼 0
- 輸出有效 JSON
"""
from framework import TestRunner, TestResult, TestLevel, load_sample_events


def run_basic_tests(runner: TestRunner):
    """運行基本測試"""
    runner.log("="*60)
    runner.log("Level 1: 基本測試 (12 Events Smoke Test)")
    runner.log("="*60)

    samples = load_sample_events()

    # 12 個事件基本測試
    events = [
        "UserPromptSubmit",
        "PreToolUse",
        "PostToolUse",
        "PostToolUseFailure",
        "SessionStart",
        "SessionEnd",
        "Stop",
        "SubagentStart",
        "SubagentStop",
        "Notification",
        "PreCompact",
        "PermissionRequest"
    ]

    for event_name in events:
        # 使用樣本數據或最小數據
        if event_name in samples:
            event_data = samples[event_name]
        else:
            event_data = _minimal_event(event_name)

        # 運行測試
        success, output, stderr = runner.run_main(event_data)

        # 檢查結果
        passed = success and isinstance(output, dict)
        error = None if passed else (stderr or "未返回有效 JSON")

        result = TestResult(
            name=f"{event_name} - 基本流程",
            level=TestLevel.BASIC,
            passed=passed,
            message="成功執行並返回 JSON" if passed else "執行失敗",
            details={"output": output, "stderr": stderr[:200] if stderr else ""},
            error=error
        )

        runner.report.add(result)
        runner.log(
            f"{event_name}: {'PASS' if passed else 'FAIL'}",
            "PASS" if passed else "FAIL"
        )


def _minimal_event(event_name: str) -> dict:
    """生成最小事件數據"""
    base = {
        "hook_event_name": event_name,
        "session_id": "test",
        "transcript_path": "/tmp/test.jsonl",
        "cwd": "/home",
        "permission_mode": "default"
    }

    # 各事件特定欄位
    specific = {
        "UserPromptSubmit": {"prompt": "test"},
        "PreToolUse": {
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
            "tool_use_id": "t1"
        },
        "PostToolUse": {
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
            "tool_response": {
                "stdout": "ok",
                "stderr": "",
                "interrupted": False,
                "isImage": False
            },
            "tool_use_id": "t1"
        },
        "PostToolUseFailure": {
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
            "error": {
                "message": "Error",
                "type": "Error"
            },
            "tool_use_id": "t1"
        },
        "SessionStart": {"source": "startup"},
        "SessionEnd": {"reason": "clear"},
        "Stop": {"stop_hook_active": True},
        "SubagentStart": {
            "task_description": "Task",
            "subagent_type": "general"
        },
        "SubagentStop": {
            "stop_hook_active": True,
            "task_description": "Task",
            "subagent_type": "general"
        },
        "Notification": {
            "message": "Hello",
            "notification_type": "info"
        },
        "PreCompact": {
            "trigger": "auto",
            "custom_instructions": ""
        },
        "PermissionRequest": {
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
            "tool_use_id": "t1"
        }
    }

    return {**base, **specific.get(event_name, {})}


if __name__ == "__main__":
    runner = TestRunner(verbose=True)
    run_basic_tests(runner)
    runner.print_report()
