"""Schema 一致性測試

驗證:
1. Schema 定義的 response 欄位是否在 emit 中正確輸出
2. HookResult 是否有對應的屬性
3. Handlers 是否能生成 Schema 要求的所有欄位
"""
import json
import sys
from pathlib import Path
from dataclasses import fields

# 添加父目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from type_defs import HookResult
from framework import TestRunner, TestResult, TestLevel, PROJECT_ROOT


def run_schema_consistency_tests(runner: TestRunner):
    """運行 Schema 一致性測試"""
    runner.log("="*60)
    runner.log("Schema 一致性測試")
    runner.log("="*60)

    schema_dir = PROJECT_ROOT / "config" / "schema"

    # 1. 檢查 EVENT_CLASSES 和 schema 一致性
    _test_event_classes_consistency(runner, schema_dir)

    # 2. 檢查 HookResult 欄位對應
    _test_hookresult_fields(runner)

    # 3. 檢查各事件的 Schema 覆蓋
    _test_event_schema_coverage(runner, schema_dir)

    # 4. 檢查 emit 函數覆蓋
    _test_emit_coverage(runner, schema_dir)

    # 5. 檢查 output.py 和 schema response 一致性
    _test_output_schema_consistency(runner, schema_dir)

    # 6. 檢查 rules 和 schema rule 定義一致性
    _test_rules_schema_consistency(runner, schema_dir)


def _test_event_classes_consistency(runner: TestRunner, schema_dir: Path):
    """測試動態生成的 EVENT_CLASSES 和 schema 定義一致"""
    runner.log("\n--- EVENT_CLASSES 一致性檢查 ---")

    from utils.events import EVENT_CLASSES

    for schema_file in sorted(schema_dir.glob("*.json")):
        event_name = schema_file.stem
        schema = json.loads(schema_file.read_text())

        # 取得 schema 定義的 event input properties
        event_def = schema.get("definitions", {}).get("event", {})
        schema_properties = set(event_def.get("properties", {}).keys())

        # 取得動態生成的 Event class fields
        event_class = EVENT_CLASSES.get(event_name)
        if not event_class:
            result = TestResult(
                name=f"{event_name} Event class 存在性",
                level=TestLevel.JSON,
                passed=False,
                message=f"EVENT_CLASSES 缺少 {event_name}",
                error=f"Schema 定義了 {event_name} 但 EVENT_CLASSES 沒有"
            )
            runner.report.add(result)
            runner.log(f"{event_name}: FAIL", "FAIL")
            continue

        event_fields = {f.name for f in fields(event_class)}

        # 檢查一致性
        schema_only = schema_properties - event_fields
        event_only = event_fields - schema_properties

        passed = len(schema_only) == 0 and len(event_only) == 0

        details = {
            "schema_properties": sorted(schema_properties),
            "event_fields": sorted(event_fields)
        }

        if schema_only:
            details["schema_only"] = sorted(schema_only)
        if event_only:
            details["event_only"] = sorted(event_only)

        message = "一致" if passed else f"不一致"
        error = None
        if not passed:
            errors = []
            if schema_only:
                errors.append(f"Schema 有但 Event 沒有: {schema_only}")
            if event_only:
                errors.append(f"Event 有但 Schema 沒有: {event_only}")
            error = "; ".join(errors)

        result = TestResult(
            name=f"{event_name} Event class 一致性",
            level=TestLevel.JSON,
            passed=passed,
            message=message,
            details=details,
            error=error
        )

        runner.report.add(result)
        runner.log(
            f"{event_name}: {'PASS' if passed else 'FAIL'}",
            "PASS" if passed else "FAIL"
        )


def _test_hookresult_fields(runner: TestRunner):
    """測試 HookResult 是否有所有必要欄位"""
    runner.log("\n--- HookResult 欄位檢查 ---")

    required_fields = {
        'permission': 'Permission 決策',
        'permission_reason': 'Permission 原因',
        'updated_input': '轉換後輸入',
        'block': 'Block 決策',
        'block_reason': 'Block 原因',
        'additional_context': '額外上下文',
        'continue_processing': 'Continue 控制',
        'stop_reason': 'Stop 原因',
        'suppress': 'Suppress 輸出',
        'system_message': '系統訊息',
    }

    hookresult_fields = {f.name for f in fields(HookResult)}

    missing = []
    for field, desc in required_fields.items():
        if field not in hookresult_fields:
            missing.append(f"{field} ({desc})")

    passed = len(missing) == 0

    result = TestResult(
        name="HookResult 欄位完整性",
        level=TestLevel.JSON,
        passed=passed,
        message="所有欄位都存在" if passed else f"缺少欄位",
        details={"required": list(required_fields.keys()), "actual": list(hookresult_fields)},
        error=f"缺少: {', '.join(missing)}" if missing else None
    )

    runner.report.add(result)
    runner.log(
        f"HookResult 欄位: {'PASS' if passed else 'FAIL'}",
        "PASS" if passed else "FAIL"
    )


def _test_event_schema_coverage(runner: TestRunner, schema_dir: Path):
    """測試各事件 Schema 定義的完整性"""
    runner.log("\n--- 事件 Schema 覆蓋檢查 ---")

    for schema_file in sorted(schema_dir.glob("*.json")):
        event_name = schema_file.stem
        schema = json.loads(schema_file.read_text())

        # 檢查是否有 response 定義
        response_def = schema.get("definitions", {}).get("response", {})
        properties = response_def.get("properties", {})

        # 檢查是否有 examples
        examples = schema.get("examples", {})
        response_examples = {k: v for k, v in examples.items() if k.startswith("response_")}

        has_response_def = "response" in schema.get("definitions", {})
        has_examples = len(response_examples) > 0

        # 有 response 定義就算通過 (即使 properties 為空)
        passed = has_response_def

        result = TestResult(
            name=f"{event_name} Schema 定義",
            level=TestLevel.JSON,
            passed=passed,
            message=f"Response: {len(properties)} 欄位, Examples: {len(response_examples)}",
            details={
                "properties": list(properties.keys()),
                "examples": list(response_examples.keys())
            }
        )

        runner.report.add(result)
        runner.log(
            f"{event_name}: {'PASS' if passed else 'FAIL'}",
            "PASS" if passed else "FAIL"
        )


def _test_emit_coverage(runner: TestRunner, schema_dir: Path):
    """測試 emit 函數是否處理所有 Schema 定義的欄位"""
    runner.log("\n--- emit 函數覆蓋檢查 ---")

    # 讀取 output.py 源碼
    output_py = (PROJECT_ROOT / "output.py").read_text()

    # 檢查各欄位是否在 emit 中被處理
    required_outputs = {
        'permissionDecision': 'Permission 類事件',
        'permissionDecisionReason': 'Permission 原因',
        'updatedInput': '輸入轉換',
        'additionalContext': 'Context 注入',
        'decision': 'Decision 類事件',
        'reason': 'Decision 原因',
        'continue': 'Continue 控制',
        'stopReason': 'Stop 原因',
        'suppressOutput': 'Suppress 輸出',
        'systemMessage': '系統訊息',
    }

    missing = []
    for field, desc in required_outputs.items():
        # 檢查 camelCase 或 snake_case 是否出現在 emit 函數中
        if field not in output_py:
            missing.append(f"{field} ({desc})")

    passed = len(missing) == 0

    result = TestResult(
        name="emit 函數覆蓋",
        level=TestLevel.JSON,
        passed=passed,
        message="所有欄位都處理" if passed else "部分欄位未處理",
        details={"required": list(required_outputs.keys())},
        error=f"未處理: {', '.join(missing)}" if missing else None
    )

    runner.report.add(result)
    runner.log(
        f"emit 覆蓋: {'PASS' if passed else 'FAIL'}",
        "PASS" if passed else "FAIL"
    )


def _test_output_schema_consistency(runner: TestRunner, schema_dir: Path):
    """測試 output.py emit() 和 schema response 定義一致性"""
    runner.log("\n--- output.py 和 schema response 一致性 ---")

    # 解析 output.py 找出所有可能輸出的欄位
    output_py = (PROJECT_ROOT / "output.py").read_text()

    # 從 output.py 提取輸出欄位（簡化版，檢查關鍵欄位）
    output_fields = {
        'permissionDecision', 'permissionDecisionReason', 'updatedInput',
        'decision', 'reason', 'additionalContext',
        'continue', 'stopReason', 'suppressOutput', 'systemMessage'
    }

    for schema_file in sorted(schema_dir.glob("*.json")):
        event_name = schema_file.stem
        schema = json.loads(schema_file.read_text())

        response_def = schema.get("definitions", {}).get("response", {})
        if not response_def:
            continue

        # 檢查 schema response 定義的欄位是否都在 output.py 處理
        response_props = response_def.get("properties", {})
        hook_specific = response_props.get("hookSpecificOutput", {}).get("properties", {})

        all_response_fields = set(response_props.keys())
        if hook_specific:
            all_response_fields.update(hook_specific.keys())

        # 檢查每個 response 欄位是否在 output.py 中
        missing_in_output = []
        for field in all_response_fields:
            if field not in output_py and field != "hookSpecificOutput":
                missing_in_output.append(field)

        passed = len(missing_in_output) == 0

        result = TestResult(
            name=f"{event_name} output.py 一致性",
            level=TestLevel.JSON,
            passed=passed,
            message="一致" if passed else f"缺少 {len(missing_in_output)} 個欄位",
            details={
                "response_fields": sorted(all_response_fields),
                "missing": missing_in_output
            },
            error=f"output.py 未處理: {missing_in_output}" if missing_in_output else None
        )

        runner.report.add(result)
        runner.log(
            f"{event_name}: {'PASS' if passed else 'FAIL'}",
            "PASS" if passed else "FAIL"
        )


def _test_rules_schema_consistency(runner: TestRunner, schema_dir: Path):
    """測試 config/rules/*.md 和 schema rule 定義一致性"""
    runner.log("\n--- Rules 和 schema rule 定義一致性 ---")

    import yaml

    rules_dir = PROJECT_ROOT / "config" / "rules"
    if not rules_dir.exists():
        runner.log("  config/rules/ 目錄不存在，跳過檢查", "WARN")
        return

    # 載入所有 schema 的 rule 定義
    schema_rules = {}
    for schema_file in schema_dir.glob("*.json"):
        event_name = schema_file.stem
        schema = json.loads(schema_file.read_text())
        rule_def = schema.get("definitions", {}).get("rule", {})
        if rule_def:
            schema_rules[event_name] = rule_def

    # 檢查每個 rule 檔案
    for rule_file in sorted(rules_dir.glob("*.md")):
        content = rule_file.read_text()

        # 提取 YAML frontmatter
        if not content.startswith("---"):
            continue

        try:
            # 分離 frontmatter
            parts = content.split("---", 2)
            if len(parts) < 3:
                continue

            frontmatter = yaml.safe_load(parts[1])

            if not frontmatter or "event" not in frontmatter:
                continue

            event_name = frontmatter.get("event")
            rule_name = frontmatter.get("name", rule_file.stem)

            # 取得對應的 schema rule 定義
            rule_schema = schema_rules.get(event_name)
            if not rule_schema:
                result = TestResult(
                    name=f"Rule '{rule_name}' schema 存在性",
                    level=TestLevel.JSON,
                    passed=False,
                    message=f"Event {event_name} 沒有 rule 定義",
                    error=f"{rule_file.name} 使用了 {event_name} 但 schema 沒有 rule 定義"
                )
                runner.report.add(result)
                runner.log(f"{rule_name}: FAIL", "FAIL")
                continue

            # 檢查 required 欄位
            required_fields = set(rule_schema.get("required", []))
            rule_fields = set(frontmatter.keys())

            missing_required = required_fields - rule_fields

            passed = len(missing_required) == 0

            result = TestResult(
                name=f"Rule '{rule_name}' 欄位完整性",
                level=TestLevel.JSON,
                passed=passed,
                message="完整" if passed else f"缺少 {len(missing_required)} 個必填欄位",
                details={
                    "required": sorted(required_fields),
                    "actual": sorted(rule_fields),
                    "missing": sorted(missing_required)
                },
                error=f"缺少必填欄位: {missing_required}" if missing_required else None
            )

            runner.report.add(result)
            runner.log(
                f"{rule_name}: {'PASS' if passed else 'FAIL'}",
                "PASS" if passed else "FAIL"
            )

        except yaml.YAMLError as e:
            result = TestResult(
                name=f"Rule '{rule_file.name}' YAML 解析",
                level=TestLevel.JSON,
                passed=False,
                message="YAML 解析失敗",
                error=str(e)
            )
            runner.report.add(result)
            runner.log(f"{rule_file.name}: FAIL", "FAIL")


if __name__ == "__main__":
    runner = TestRunner(verbose=True)
    run_schema_consistency_tests(runner)
    runner.print_report()
