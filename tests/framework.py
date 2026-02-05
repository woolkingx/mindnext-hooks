"""測試框架核心

四層測試架構:
1. BasicTest - 基本流程測試(smoke test)
2. JsonTest - JSON Schema 驗證
3. RulesTest - Rules 配置驗證
4. IntegrationTest - Sample Data + Rule 整合測試
"""
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# 項目根目錄
PROJECT_ROOT = Path(__file__).parent.parent


class TestLevel(Enum):
    """測試層級"""
    BASIC = "basic"
    JSON = "json"
    RULES = "rules"
    INTEGRATION = "integration"


@dataclass
class TestResult:
    """測試結果"""
    name: str
    level: TestLevel
    passed: bool
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class TestReport:
    """測試報告"""
    total: int = 0
    passed: int = 0
    failed: int = 0
    results: List[TestResult] = field(default_factory=list)

    def add(self, result: TestResult):
        self.results.append(result)
        self.total += 1
        if result.passed:
            self.passed += 1
        else:
            self.failed += 1

    def summary(self) -> str:
        """生成摘要"""
        rate = (self.passed / self.total * 100) if self.total > 0 else 0
        return f"✓ {self.passed}/{self.total} ({rate:.1f}%)"

    def to_dict(self) -> Dict[str, Any]:
        """轉為字典"""
        return {
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate": f"{(self.passed/self.total*100):.1f}%" if self.total > 0 else "0%",
            "results": [
                {
                    "name": r.name,
                    "level": r.level.value,
                    "passed": r.passed,
                    "message": r.message,
                    "details": r.details,
                    "error": r.error
                }
                for r in self.results
            ]
        }


class TestRunner:
    """測試運行器"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.report = TestReport()

    def run_main(self, event_json: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], str]:
        """運行 main.py

        Returns:
            (success, output_json, stderr)
        """
        try:
            proc = subprocess.run(
                [sys.executable, str(PROJECT_ROOT / "main.py")],
                input=json.dumps(event_json),
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
                timeout=10
            )

            # 解析 stdout
            output = {}
            if proc.stdout.strip():
                try:
                    output = json.loads(proc.stdout)
                except json.JSONDecodeError:
                    pass

            success = proc.returncode == 0
            return success, output, proc.stderr

        except subprocess.TimeoutExpired:
            return False, {}, "Timeout"
        except Exception as e:
            return False, {}, str(e)

    def validate_json_schema(self, data: Dict[str, Any], schema_file: Path) -> Tuple[bool, str]:
        """驗證 JSON Schema

        Returns:
            (valid, error_message)
        """
        try:
            import jsonschema
            schema = json.loads(schema_file.read_text())
            jsonschema.validate(instance=data, schema=schema)
            return True, ""
        except ImportError:
            return False, "jsonschema 未安裝"
        except jsonschema.ValidationError as e:
            return False, str(e.message)
        except Exception as e:
            return False, str(e)

    def log(self, msg: str, level: str = "INFO"):
        """記錄日誌"""
        if self.verbose or level == "ERROR":
            prefix = "✓" if level == "PASS" else "✗" if level == "FAIL" else "•"
            print(f"{prefix} {msg}")

    def print_report(self):
        """打印報告"""
        print("\n" + "="*60)
        print("測試報告")
        print("="*60)

        # 按層級分組
        by_level = {}
        for result in self.report.results:
            level = result.level.value
            if level not in by_level:
                by_level[level] = []
            by_level[level].append(result)

        # 打印各層級結果
        for level_name in ["basic", "json", "rules", "integration"]:
            if level_name not in by_level:
                continue

            results = by_level[level_name]
            passed = sum(1 for r in results if r.passed)
            total = len(results)

            print(f"\n{level_name.upper()} ({passed}/{total}):")
            for r in results:
                status = "✓" if r.passed else "✗"
                print(f"  {status} {r.name}")
                if not r.passed and r.error:
                    print(f"    錯誤: {r.error}")

        # 總結
        print("\n" + "-"*60)
        print(f"總計: {self.report.summary()}")
        print("="*60)


def load_sample_events() -> Dict[str, Dict[str, Any]]:
    """載入樣本事件數據

    從 config/schema/*.json 提取 event_example
    """
    samples = {}
    schema_dir = PROJECT_ROOT / "config" / "schema"

    for schema_file in schema_dir.glob("*.json"):
        event_name = schema_file.stem
        try:
            schema = json.loads(schema_file.read_text())
            if "examples" in schema and "event_example" in schema["examples"]:
                samples[event_name] = schema["examples"]["event_example"]
        except Exception:
            pass

    return samples


def load_sample_rules() -> List[Dict[str, Any]]:
    """載入樣本規則

    從 config/rules/*.md 解析 frontmatter
    """
    import re
    import yaml

    rules = []
    rules_dir = PROJECT_ROOT / "config" / "rules"
    frontmatter_re = re.compile(r'^---\s*\n(.*?)\n---\s*\n?', re.DOTALL)

    for rule_file in rules_dir.glob("*.md"):
        if rule_file.name == "RULES.md":
            continue

        try:
            content = rule_file.read_text()
            match = frontmatter_re.match(content)
            if match:
                rule = yaml.safe_load(match.group(1))
                if isinstance(rule, dict):
                    rule['_source'] = str(rule_file.name)
                    rules.append(rule)
        except Exception:
            pass

    return rules
