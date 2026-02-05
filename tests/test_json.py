"""Level 2: JSON Schema 驗證測試

驗證:
1. Event Input - 輸入符合 schema/definitions/event
2. Response Output - 輸出符合 schema/definitions/response
3. Schema 本身格式正確
"""
import json
from pathlib import Path
from framework import TestRunner, TestResult, TestLevel, PROJECT_ROOT, load_sample_events


def run_json_tests(runner: TestRunner):
    """運行 JSON Schema 測試"""
    runner.log("="*60)
    runner.log("Level 2: JSON Schema 驗證")
    runner.log("="*60)

    schema_dir = PROJECT_ROOT / "config" / "schema"

    # 1. Schema 檔案格式檢查
    _test_schema_files(runner, schema_dir)

    # 2. Event Input 驗證
    _test_event_inputs(runner, schema_dir)

    # 3. Response Output 驗證
    _test_response_outputs(runner, schema_dir)


def _test_schema_files(runner: TestRunner, schema_dir: Path):
    """測試 Schema 檔案本身格式"""
    runner.log("\n--- Schema 檔案格式檢查 ---")

    for schema_file in schema_dir.glob("*.json"):
        event_name = schema_file.stem

        try:
            schema = json.loads(schema_file.read_text())

            # 檢查必要欄位
            checks = {
                "有 definitions": "definitions" in schema,
                "有 examples": "examples" in schema,
                "有 event 定義": "definitions" in schema and "event" in schema.get("definitions", {}),
                "有 response 定義": "definitions" in schema and "response" in schema.get("definitions", {}),
                "有 rule 定義": "definitions" in schema and "rule" in schema.get("definitions", {}),
            }

            all_passed = all(checks.values())
            failed_checks = [k for k, v in checks.items() if not v]

            result = TestResult(
                name=f"{event_name}.json 格式",
                level=TestLevel.JSON,
                passed=all_passed,
                message="Schema 格式正確" if all_passed else f"缺少: {', '.join(failed_checks)}",
                details=checks
            )

        except json.JSONDecodeError as e:
            result = TestResult(
                name=f"{event_name}.json 格式",
                level=TestLevel.JSON,
                passed=False,
                message="JSON 解析失敗",
                error=str(e)
            )

        runner.report.add(result)
        runner.log(
            f"{event_name}.json: {'PASS' if result.passed else 'FAIL'}",
            "PASS" if result.passed else "FAIL"
        )


def _test_event_inputs(runner: TestRunner, schema_dir: Path):
    """測試 Event Input 驗證"""
    runner.log("\n--- Event Input Schema 驗證 ---")

    try:
        import jsonschema
    except ImportError:
        runner.log("跳過 (jsonschema 未安裝)", "INFO")
        return

    samples = load_sample_events()

    for event_name, event_data in samples.items():
        schema_file = schema_dir / f"{event_name}.json"
        if not schema_file.exists():
            continue

        try:
            schema = json.loads(schema_file.read_text())
            event_schema = schema.get("definitions", {}).get("event", {})

            # 驗證
            jsonschema.validate(instance=event_data, schema=event_schema)

            result = TestResult(
                name=f"{event_name} Input",
                level=TestLevel.JSON,
                passed=True,
                message="Input 符合 Schema"
            )

        except jsonschema.ValidationError as e:
            result = TestResult(
                name=f"{event_name} Input",
                level=TestLevel.JSON,
                passed=False,
                message="Input 不符合 Schema",
                error=str(e.message)
            )

        runner.report.add(result)
        runner.log(
            f"{event_name} Input: {'PASS' if result.passed else 'FAIL'}",
            "PASS" if result.passed else "FAIL"
        )


def _test_response_outputs(runner: TestRunner, schema_dir: Path):
    """測試 Response Output 驗證"""
    runner.log("\n--- Response Output Schema 驗證 ---")

    try:
        import jsonschema
    except ImportError:
        runner.log("跳過 (jsonschema 未安裝)", "INFO")
        return

    # 從 schema 提取 response examples 驗證
    for schema_file in schema_dir.glob("*.json"):
        event_name = schema_file.stem

        try:
            schema = json.loads(schema_file.read_text())
            response_schema = schema.get("definitions", {}).get("response", {})
            examples = schema.get("examples", {})

            # 查找所有 response_* 的 examples
            response_examples = {
                k: v for k, v in examples.items()
                if k.startswith("response_")
            }

            if not response_examples:
                continue

            all_valid = True
            errors = []

            for ex_name, ex_data in response_examples.items():
                try:
                    jsonschema.validate(instance=ex_data, schema=response_schema)
                except jsonschema.ValidationError as e:
                    all_valid = False
                    errors.append(f"{ex_name}: {e.message}")

            result = TestResult(
                name=f"{event_name} Response",
                level=TestLevel.JSON,
                passed=all_valid,
                message=f"驗證 {len(response_examples)} 個範例" if all_valid else "部分範例不符合",
                details={"examples": list(response_examples.keys())},
                error="; ".join(errors) if errors else None
            )

        except Exception as e:
            result = TestResult(
                name=f"{event_name} Response",
                level=TestLevel.JSON,
                passed=False,
                message="驗證失敗",
                error=str(e)
            )

        runner.report.add(result)
        runner.log(
            f"{event_name} Response: {'PASS' if result.passed else 'FAIL'}",
            "PASS" if result.passed else "FAIL"
        )


if __name__ == "__main__":
    runner = TestRunner(verbose=True)
    run_json_tests(runner)
    runner.print_report()
