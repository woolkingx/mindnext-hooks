"""Level 4: 整合測試

端到端測試 Sample Data + Rule:
1. PreToolUse + deny rule → 驗證 permission=deny
2. UserPromptSubmit + additionalContext → 驗證 context 注入
3. PostToolUse + block rule → 驗證 block
4. Feature 調用測試 (tags, agents, skills)
"""
from framework import TestRunner, TestResult, TestLevel, load_sample_events


def run_integration_tests(runner: TestRunner):
    """運行整合測試"""
    runner.log("="*60)
    runner.log("Level 4: 整合測試 (Sample Data + Rules)")
    runner.log("="*60)

    # 1. Permission 類測試
    _test_permission_workflow(runner)

    # 2. Context 注入測試
    _test_context_injection(runner)

    # 3. Block 決策測試
    _test_block_workflow(runner)

    # 4. Feature 調用測試
    _test_feature_workflow(runner)


def _test_permission_workflow(runner: TestRunner):
    """測試 Permission 工作流"""
    runner.log("\n--- Permission Workflow ---")

    # 測試 PreToolUse transform (rm → trash rm)
    event = {
        "hook_event_name": "PreToolUse",
        "session_id": "test",
        "transcript_path": "/tmp/test.jsonl",
        "cwd": "/home",
        "permission_mode": "default",
        "tool_name": "Bash",
        "tool_input": {"command": "rm -rf /tmp/test.txt"},
        "tool_use_id": "t1"
    }

    success, output, stderr = runner.run_main(event)

    # 檢查是否正確轉換為 trash rm
    permission = output.get("hookSpecificOutput", {}).get("permissionDecision", "")
    updated_input = output.get("hookSpecificOutput", {}).get("updatedInput", {})
    updated_command = updated_input.get("command", "")

    passed = (success and
              permission == "allow" and
              updated_command.startswith("trash rm"))

    result = TestResult(
        name="PreToolUse transform workflow",
        level=TestLevel.INTEGRATION,
        passed=passed,
        message=f"Transformed: {updated_command}" if passed else "未正確轉換命令",
        details={"permission": permission, "updated_command": updated_command, "output": output},
        error=stderr if not passed else None
    )

    runner.report.add(result)
    runner.log(
        f"PreToolUse transform: {'PASS' if passed else 'FAIL'}",
        "PASS" if passed else "FAIL"
    )


def _test_context_injection(runner: TestRunner):
    """測試 Context 注入"""
    runner.log("\n--- Context Injection ---")

    event = {
        "hook_event_name": "UserPromptSubmit",
        "session_id": "test",
        "transcript_path": "/tmp/test.jsonl",
        "cwd": "/home",
        "permission_mode": "default",
        "prompt": "test prompt"
    }

    success, output, stderr = runner.run_main(event)

    # 檢查是否有 additionalContext
    context = output.get("hookSpecificOutput", {}).get("additionalContext", "")
    passed = success and len(context) > 0

    result = TestResult(
        name="UserPromptSubmit context injection",
        level=TestLevel.INTEGRATION,
        passed=passed,
        message=f"注入 {len(context)} 字元" if passed else "未注入 context",
        details={"context_length": len(context), "preview": context[:100] if context else ""},
        error=stderr if not passed else None
    )

    runner.report.add(result)
    runner.log(
        f"Context injection: {'PASS' if passed else 'FAIL'}",
        "PASS" if passed else "FAIL"
    )


def _test_block_workflow(runner: TestRunner):
    """測試 Block 工作流"""
    runner.log("\n--- Block Workflow ---")

    # 這個測試需要實際的 block rule
    # 目前僅驗證流程能運行
    event = {
        "hook_event_name": "PostToolUse",
        "session_id": "test",
        "transcript_path": "/tmp/test.jsonl",
        "cwd": "/home",
        "permission_mode": "default",
        "tool_name": "Bash",
        "tool_input": {"command": "ls"},
        "tool_response": {
            "stdout": "test output",
            "stderr": "",
            "interrupted": False,
            "isImage": False
        },
        "tool_use_id": "t1"
    }

    success, output, stderr = runner.run_main(event)

    # 基本驗證：能運行即可
    passed = success and isinstance(output, dict)

    result = TestResult(
        name="PostToolUse workflow",
        level=TestLevel.INTEGRATION,
        passed=passed,
        message="PostToolUse 流程正常",
        details={"output": output}
    )

    runner.report.add(result)
    runner.log(
        f"PostToolUse workflow: {'PASS' if passed else 'FAIL'}",
        "PASS" if passed else "FAIL"
    )


def _test_feature_workflow(runner: TestRunner):
    """測試 Feature 調用"""
    runner.log("\n--- Feature Workflow ---")

    # 測試 tags feature
    test_cases = [
        {
            "name": "Tags feature",
            "prompt": "/tags help",
            "expect_context": True
        },
        {
            "name": "Normal prompt",
            "prompt": "hello world",
            "expect_context": True  # CLAUDE.md reminder 會注入
        }
    ]

    for case in test_cases:
        event = {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "test",
            "transcript_path": "/tmp/test.jsonl",
            "cwd": "/home",
            "permission_mode": "default",
            "prompt": case["prompt"]
        }

        success, output, stderr = runner.run_main(event)
        context = output.get("hookSpecificOutput", {}).get("additionalContext", "")

        if case["expect_context"]:
            passed = success and len(context) > 0
            msg = f"返回 {len(context)} 字元"
        else:
            passed = success
            msg = "正常執行"

        result = TestResult(
            name=case["name"],
            level=TestLevel.INTEGRATION,
            passed=passed,
            message=msg,
            details={"prompt": case["prompt"], "context_length": len(context)}
        )

        runner.report.add(result)
        runner.log(
            f"{case['name']}: {'PASS' if passed else 'FAIL'}",
            "PASS" if passed else "FAIL"
        )


if __name__ == "__main__":
    runner = TestRunner(verbose=True)
    run_integration_tests(runner)
    runner.print_report()
