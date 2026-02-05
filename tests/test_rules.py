"""Level 3: Rules 配置驗證測試

驗證:
1. Rule Frontmatter 格式正確
2. Rule 必填欄位存在
3. Rule action/feature/match 配置有效
4. Rule 能被 loaders.rules 正確載入
"""
import re
import sys
import yaml
from pathlib import Path

# 加入父目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from framework import TestRunner, TestResult, TestLevel, PROJECT_ROOT, load_sample_rules


def run_rules_tests(runner: TestRunner):
    """運行 Rules 測試"""
    runner.log("="*60)
    runner.log("Level 3: Rules 配置驗證")
    runner.log("="*60)

    rules_dir = PROJECT_ROOT / "config" / "rules"

    # 1. Rule 檔案格式檢查
    _test_rule_files(runner, rules_dir)

    # 2. Rule 欄位驗證
    _test_rule_fields(runner)

    # 3. Rule 載入測試
    _test_rule_loading(runner)

    # 4. Rule 實際執行測試（新增）
    _test_rule_execution(runner)


def _test_rule_files(runner: TestRunner, rules_dir: Path):
    """測試 Rule 檔案格式"""
    runner.log("\n--- Rule 檔案格式檢查 ---")

    frontmatter_re = re.compile(r'^---\s*\n(.*?)\n---\s*\n?', re.DOTALL)

    for rule_file in rules_dir.glob("*.md"):
        if rule_file.name == "RULES.md":
            continue

        rule_name = rule_file.stem

        try:
            content = rule_file.read_text()

            # 1. 檢查 frontmatter
            match = frontmatter_re.match(content)
            if not match:
                result = TestResult(
                    name=f"{rule_name} 格式",
                    level=TestLevel.RULES,
                    passed=False,
                    message="缺少 frontmatter",
                    error="Rule 檔案必須以 --- 開頭和結尾"
                )
                runner.report.add(result)
                runner.log(f"{rule_name}: FAIL (無 frontmatter)", "FAIL")
                continue

            # 2. 檢查 YAML 可解析
            try:
                rule = yaml.safe_load(match.group(1))
            except yaml.YAMLError as e:
                result = TestResult(
                    name=f"{rule_name} 格式",
                    level=TestLevel.RULES,
                    passed=False,
                    message="YAML 解析失敗",
                    error=str(e)
                )
                runner.report.add(result)
                runner.log(f"{rule_name}: FAIL (YAML 錯誤)", "FAIL")
                continue

            # 3. 檢查是字典
            if not isinstance(rule, dict):
                result = TestResult(
                    name=f"{rule_name} 格式",
                    level=TestLevel.RULES,
                    passed=False,
                    message="Frontmatter 不是字典格式"
                )
                runner.report.add(result)
                runner.log(f"{rule_name}: FAIL (非字典)", "FAIL")
                continue

            result = TestResult(
                name=f"{rule_name} 格式",
                level=TestLevel.RULES,
                passed=True,
                message="格式正確"
            )

        except Exception as e:
            result = TestResult(
                name=f"{rule_name} 格式",
                level=TestLevel.RULES,
                passed=False,
                message="讀取失敗",
                error=str(e)
            )

        runner.report.add(result)
        runner.log(
            f"{rule_name}: {'PASS' if result.passed else 'FAIL'}",
            "PASS" if result.passed else "FAIL"
        )


def _test_rule_fields(runner: TestRunner):
    """測試 Rule 必填欄位"""
    runner.log("\n--- Rule 欄位驗證 ---")

    rules = load_sample_rules()

    # 12 個事件的必填欄位
    required_fields = {
        "all": ["name", "description", "enabled", "event"],
    }

    for rule in rules:
        rule_name = rule.get("name", rule.get("_source", "unknown"))
        event = rule.get("event", "")

        # 檢查必填欄位
        missing = []
        for field in required_fields["all"]:
            if field not in rule:
                missing.append(field)

        # 檢查 event 值有效
        valid_events = [
            "UserPromptSubmit", "PreToolUse", "PostToolUse", "PostToolUseFailure",
            "SessionStart", "SessionEnd", "Stop", "SubagentStart", "SubagentStop",
            "Notification", "PreCompact", "PermissionRequest"
        ]

        if event and event not in valid_events:
            missing.append(f"event (無效值: {event})")

        # 檢查 action/feature 衝突
        has_action = "action" in rule
        has_feature = "feature" in rule
        has_additional_context = "additionalContext" in rule

        conflicts = []
        if has_additional_context and (has_action or has_feature):
            conflicts.append("additionalContext 與 action/feature 同時存在")

        passed = len(missing) == 0 and len(conflicts) == 0
        error_parts = []
        if missing:
            error_parts.append(f"缺少: {', '.join(missing)}")
        if conflicts:
            error_parts.append(f"衝突: {', '.join(conflicts)}")

        result = TestResult(
            name=f"{rule_name} 欄位",
            level=TestLevel.RULES,
            passed=passed,
            message="欄位完整" if passed else "欄位問題",
            details={"event": event, "has_action": has_action, "has_feature": has_feature},
            error="; ".join(error_parts) if error_parts else None
        )

        runner.report.add(result)
        runner.log(
            f"{rule_name}: {'PASS' if passed else 'FAIL'}",
            "PASS" if passed else "FAIL"
        )


def _test_rule_loading(runner: TestRunner):
    """測試 Rule 載入機制"""
    runner.log("\n--- Rule 載入測試 ---")

    try:
        from loaders import rules as rules_loader

        # 載入規則
        rules = rules_loader.load()

        result = TestResult(
            name="Rules Loader",
            level=TestLevel.RULES,
            passed=True,
            message=f"成功載入 {len(rules)} 個規則",
            details={"count": len(rules), "rules": [r.get("name", "?") for r in rules[:5]]}
        )

    except Exception as e:
        result = TestResult(
            name="Rules Loader",
            level=TestLevel.RULES,
            passed=False,
            message="載入失敗",
            error=str(e)
        )

    runner.report.add(result)
    runner.log(
        f"Rules Loader: {'PASS' if result.passed else 'FAIL'}",
        "PASS" if result.passed else "FAIL"
    )


def _test_rule_execution(runner: TestRunner):
    """測試 Rule 實際執行和 Output"""
    runner.log("\n--- Rule 執行測試 ---")

    # 測試案例：每個 rule 對應的測試 event
    test_cases = [
        {
            "name": "rm-to-trash",
            "event": {
                "hook_event_name": "PreToolUse",
                "session_id": "test",
                "transcript_path": "/tmp/test.jsonl",
                "cwd": "/home",
                "permission_mode": "default",
                "tool_name": "Bash",
                "tool_input": {"command": "rm -rf /tmp/test.txt"},
                "tool_use_id": "t1"
            },
            "expect_output": True,
            "expect_fields": ["permissionDecision", "updatedInput"],
        },
        {
            "name": "ask-git",
            "event": {
                "hook_event_name": "PreToolUse",
                "session_id": "test",
                "transcript_path": "/tmp/test.jsonl",
                "cwd": "/home",
                "permission_mode": "default",
                "tool_name": "Bash",
                "tool_input": {"command": "git checkout main"},
                "tool_use_id": "t2"
            },
            "expect_output": True,
            "expect_fields": ["permissionDecision"],
        },
        {
            "name": "userprompt-tags",
            "event": {
                "hook_event_name": "UserPromptSubmit",
                "session_id": "test",
                "transcript_path": "/tmp/test.jsonl",
                "cwd": "/home",
                "permission_mode": "default",
                "prompt": "/tags help"
            },
            "expect_output": True,
            "expect_fields": ["additionalContext"],
        },
    ]

    for case in test_cases:
        success, output, stderr = runner.run_main(case["event"])

        hook_output = output.get("hookSpecificOutput", {})

        # 檢查是否有輸出
        has_output = len(hook_output) > 0

        # 檢查期望欄位
        missing_fields = []
        for field in case.get("expect_fields", []):
            if field not in hook_output:
                missing_fields.append(field)

        passed = success and has_output and len(missing_fields) == 0

        result = TestResult(
            name=f"{case['name']} 執行",
            level=TestLevel.RULES,
            passed=passed,
            message=f"Output: {len(hook_output)} fields" if passed else "執行失敗或欄位缺失",
            details={
                "output": hook_output,
                "missing_fields": missing_fields
            },
            error=stderr if not success else (f"缺少欄位: {missing_fields}" if missing_fields else None)
        )

        runner.report.add(result)
        runner.log(
            f"{case['name']}: {'PASS' if passed else 'FAIL'}",
            "PASS" if passed else "FAIL"
        )


if __name__ == "__main__":
    runner = TestRunner(verbose=True)
    run_rules_tests(runner)
    runner.print_report()
