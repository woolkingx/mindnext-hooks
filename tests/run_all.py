#!/usr/bin/env python3
"""統一測試運行器

四層測試架構:
Level 1 - Basic: 基本流程測試 (12 events smoke test + logger)
Level 2 - Schema: Schema 一致性測試 (event/response/rule)
Level 3 - Rules: 規則驗證測試
Level 4 - Integration: 整合測試 (sample data + rules)

使用方式:
    python3 run_all.py              # 運行所有測試
    python3 run_all.py --level basic  # 只運行指定層級
    python3 run_all.py --verbose      # 詳細輸出
    python3 run_all.py --json         # JSON 格式輸出
"""
import sys
import json
import argparse
from pathlib import Path

# 加入父目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from framework import TestRunner, TestLevel


def main():
    parser = argparse.ArgumentParser(description="V2 測試框架")
    parser.add_argument(
        "--level",
        choices=["basic", "schema", "rules", "integration", "all"],
        default="all",
        help="指定測試層級 (預設: all)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="詳細輸出"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式輸出結果"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="輸出報告到檔案"
    )

    args = parser.parse_args()

    # 建立 runner
    runner = TestRunner(verbose=args.verbose or not args.json)

    # Level 1: Basic Tests
    if args.level in ["basic", "all"]:
        from test_basic import run_basic_tests
        from test_utils.test_logger import run_logger_tests

        run_basic_tests(runner)
        run_logger_tests(runner)

    # Level 2: Schema Tests
    if args.level in ["schema", "all"]:
        from test_schema_consistency import run_schema_consistency_tests
        from test_output_format import run_all_tests as run_output_format_tests

        run_schema_consistency_tests(runner)

        # Output format tests (返回 bool)
        runner.log("\n" + "=" * 60)
        runner.log("Output Format Tests (官方 API 格式驗證)")
        runner.log("=" * 60)
        if run_output_format_tests():
            runner.log("Output format tests: PASS", "PASS")
        else:
            runner.log("Output format tests: FAIL", "FAIL")

    # Level 3: Rules Tests
    if args.level in ["rules", "all"]:
        from test_rules import run_rules_tests
        from test_rule_validation import run_rule_validation_tests

        run_rules_tests(runner)
        run_rule_validation_tests(runner)

    # Level 4: Integration Tests
    if args.level in ["integration", "all"]:
        from test_integration import run_integration_tests

        run_integration_tests(runner)

    # 輸出報告
    if args.json:
        report_data = runner.report.to_dict()
        output = json.dumps(report_data, indent=2, ensure_ascii=False)

        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
            print(f"報告已儲存至: {args.output}")
        else:
            print(output)
    else:
        # 文字報告
        runner.print_report()

        if args.output:
            report_text = _generate_text_report(runner)
            Path(args.output).write_text(report_text, encoding="utf-8")
            print(f"\n報告已儲存至: {args.output}")

    # 返回碼
    sys.exit(0 if runner.report.failed == 0 else 1)


def _generate_text_report(runner: TestRunner) -> str:
    """生成文字格式報告"""
    lines = []
    lines.append("="*60)
    lines.append("V2 測試總報告")
    lines.append("="*60)

    # 按層級分組
    by_level = {}
    for result in runner.report.results:
        level = result.level.value
        if level not in by_level:
            by_level[level] = []
        by_level[level].append(result)

    # 各層級結果
    level_order = ["basic", "json", "rules", "integration"]
    level_names = {
        "basic": "Level 1: Basic Tests",
        "json": "Level 2: Schema Tests",
        "rules": "Level 3: Rules Tests",
        "integration": "Level 4: Integration Tests"
    }

    for level_key in level_order:
        if level_key not in by_level:
            continue

        results = by_level[level_key]
        passed = sum(1 for r in results if r.passed)
        total = len(results)
        percentage = (passed / total * 100) if total > 0 else 0

        lines.append(f"\n{level_names.get(level_key, level_key.upper())} ({passed}/{total} = {percentage:.1f}%):")

        for r in results:
            status = "✓" if r.passed else "✗"
            lines.append(f"  {status} {r.name}")
            if r.message and not r.passed:
                lines.append(f"    {r.message}")
            if not r.passed and r.error:
                lines.append(f"    錯誤: {r.error}")

    # 總結
    lines.append("\n" + "-"*60)
    summary = runner.report.summary()
    lines.append(f"總計: {summary}")
    lines.append("="*60)

    return "\n".join(lines)


if __name__ == "__main__":
    main()
