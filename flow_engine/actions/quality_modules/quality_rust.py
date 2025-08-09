"""
Rust 代碼品質檢查器
支援 rustfmt、clippy、cargo check 等工具
"""

import subprocess
import json
import re
import time
from pathlib import Path
from typing import List, Dict
from .base_checker import BaseQualityChecker, QualityIssue, CheckResult

class RustQualityChecker(BaseQualityChecker):
    """Rust 專用品質檢查器"""
    
    def get_checker_name(self) -> str:
        return "Rust"
    
    def get_supported_extensions(self) -> List[str]:
        return ['.rs']
    
    def check_file(self, file_path: str) -> CheckResult:
        """檢查 Rust 檔案品質"""
        start_time = time.time()
        
        # 檢查快取
        cached_result = self._load_cache(file_path)
        if cached_result:
            return cached_result
        
        issues = []
        fixed_issues = []
        
        try:
            content, lines = self._read_file_content(file_path)
        except Exception as e:
            return CheckResult(
                file_path=file_path,
                file_type="rust",
                issues=[QualityIssue("error", str(e))],
                execution_time=time.time() - start_time
            )
        
        # 1. rustfmt 格式化檢查
        if self.config.get("rustfmt_enabled", True):
            rustfmt_issues, rustfmt_fixes = self._check_rustfmt(file_path)
            issues.extend(rustfmt_issues)
            fixed_issues.extend(rustfmt_fixes)
        
        # 2. clippy 檢查
        if self.config.get("clippy_enabled", True):
            clippy_issues = self._check_clippy(file_path)
            issues.extend(clippy_issues)
        
        # 3. cargo check
        if self.config.get("cargo_check_enabled", True):
            cargo_issues = self._check_cargo(file_path)
            issues.extend(cargo_issues)
        
        # 4. 自定義規則檢查
        custom_issues = self._check_custom_rules(content, lines, file_path)
        issues.extend(custom_issues)
        
        # 建立結果
        result = CheckResult(
            file_path=file_path,
            file_type="rust",
            issues=issues,
            fixed_issues=fixed_issues,
            execution_time=time.time() - start_time
        )
        
        # 儲存快取
        self._save_cache(result)
        
        return result
    
    def _check_rustfmt(self, file_path: str) -> tuple[List[QualityIssue], List[str]]:
        """rustfmt 格式化檢查"""
        issues = []
        fixes = []
        
        if not self._tool_available("rustfmt"):
            if self.debug:
                print("⚠️ rustfmt 工具不可用")
            return issues, fixes
        
        try:
            # 檢查格式化
            result = subprocess.run(
                ["rustfmt", "--check", file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                issues.append(QualityIssue(
                    severity="warning",
                    message="代碼格式不符合 rustfmt 標準",
                    rule="rustfmt-formatting",
                    fixable=True
                ))
                
                # 自動修復
                if self.config.get("auto_fix", True):
                    fix_result = subprocess.run(
                        ["rustfmt", file_path],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if fix_result.returncode == 0:
                        fixes.append("rustfmt 格式化已應用")
                    else:
                        issues.append(QualityIssue(
                            severity="error",
                            message="rustfmt 自動修復失敗",
                            rule="rustfmt-autofix"
                        ))
        
        except subprocess.TimeoutExpired:
            issues.append(QualityIssue(
                severity="warning",
                message="rustfmt 檢查逾時",
                rule="rustfmt-timeout"
            ))
        except Exception as e:
            if self.debug:
                print(f"rustfmt 檢查失敗: {e}")
        
        return issues, fixes
    
    def _check_clippy(self, file_path: str) -> List[QualityIssue]:
        """clippy 檢查"""
        issues = []
        
        if not self._tool_available("cargo"):
            return issues
        
        try:
            # 嘗試找到 Cargo.toml 來確定專案根目錄
            project_root = self._find_cargo_root(file_path)
            if not project_root:
                if self.debug:
                    print("⚠️ 無法找到 Cargo.toml，跳過 clippy 檢查")
                return issues
            
            # 執行 clippy
            result = subprocess.run(
                ["cargo", "clippy", "--message-format=json", "--", "-D", "warnings"],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    try:
                        if line.strip():
                            message = json.loads(line)
                            if message.get('reason') == 'compiler-message':
                                diag = message.get('message', {})
                                spans = diag.get('spans', [])
                                
                                for span in spans:
                                    span_file = Path(span.get('file_name', ''))
                                    if span_file.resolve() == Path(file_path).resolve():
                                        severity = {
                                            'error': 'error',
                                            'warning': 'warning',
                                            'note': 'info',
                                            'help': 'info'
                                        }.get(diag.get('level', 'warning'), 'warning')
                                        
                                        issues.append(QualityIssue(
                                            severity=severity,
                                            message=diag.get('message', 'Clippy issue'),
                                            line=span.get('line_start'),
                                            column=span.get('column_start'),
                                            rule='clippy'
                                        ))
                    
                    except json.JSONDecodeError:
                        continue
        
        except subprocess.TimeoutExpired:
            issues.append(QualityIssue(
                severity="warning",
                message="Clippy 檢查逾時",
                rule="clippy-timeout"
            ))
        except Exception as e:
            if self.debug:
                print(f"Clippy 檢查失敗: {e}")
        
        return issues
    
    def _check_cargo(self, file_path: str) -> List[QualityIssue]:
        """cargo check 檢查"""
        issues = []
        
        if not self._tool_available("cargo"):
            return issues
        
        try:
            project_root = self._find_cargo_root(file_path)
            if not project_root:
                return issues
            
            result = subprocess.run(
                ["cargo", "check", "--message-format=json"],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    try:
                        if line.strip():
                            message = json.loads(line)
                            if message.get('reason') == 'compiler-message':
                                diag = message.get('message', {})
                                spans = diag.get('spans', [])
                                
                                for span in spans:
                                    span_file = Path(span.get('file_name', ''))
                                    if span_file.resolve() == Path(file_path).resolve():
                                        severity = {
                                            'error': 'error',
                                            'warning': 'warning'
                                        }.get(diag.get('level', 'warning'), 'warning')
                                        
                                        issues.append(QualityIssue(
                                            severity=severity,
                                            message=diag.get('message', 'Compiler issue'),
                                            line=span.get('line_start'),
                                            column=span.get('column_start'),
                                            rule='rustc'
                                        ))
                    
                    except json.JSONDecodeError:
                        continue
        
        except subprocess.TimeoutExpired:
            issues.append(QualityIssue(
                severity="warning",
                message="Cargo check 逾時",
                rule="cargo-timeout"
            ))
        except Exception as e:
            if self.debug:
                print(f"Cargo check 失敗: {e}")
        
        return issues
    
    def _find_cargo_root(self, file_path: str) -> str:
        """找到 Cargo.toml 所在的專案根目錄"""
        current = Path(file_path).parent
        for _ in range(10):  # 最多向上找10層
            if (current / "Cargo.toml").exists():
                return str(current)
            if current.parent == current:  # 到達根目錄
                break
            current = current.parent
        return None
    
    def _check_custom_rules(self, content: str, lines: List[str], file_path: str) -> List[QualityIssue]:
        """Rust 特有的自定義規則檢查"""
        issues = []
        
        # 1. unwrap() 使用檢查
        if self.config.get("check_unwrap", True):
            unwrap_severity = self.config.get("unwrap_severity", "warning")
            
            for i, line in enumerate(lines, 1):
                if '.unwrap()' in line and not line.strip().startswith('//'):
                    # 排除測試代碼
                    if not any(test_pattern in file_path for test_pattern in ['/test', '/tests', 'test.rs']):
                        issues.append(QualityIssue(
                            severity=unwrap_severity,
                            message="避免在生產代碼中使用 unwrap()，考慮使用 ? 或 match",
                            line=i,
                            rule="no-unwrap"
                        ))
        
        # 2. expect() 使用檢查
        if self.config.get("check_expect", True):
            for i, line in enumerate(lines, 1):
                if '.expect(' in line and not line.strip().startswith('//'):
                    # 檢查是否有意義的錯誤訊息
                    expect_match = re.search(r'\.expect\s*\(\s*"([^"]*)"', line)
                    if expect_match:
                        message = expect_match.group(1)
                        if len(message.strip()) < 10:
                            issues.append(QualityIssue(
                                severity="info",
                                message="expect() 應該提供更詳細的錯誤訊息",
                                line=i,
                                rule="expect-message"
                            ))
        
        # 3. println! 調試檢查
        if self.config.get("check_println", True):
            println_severity = self.config.get("println_severity", "info")
            
            for i, line in enumerate(lines, 1):
                if re.search(r'\bprintln!\s*\(', line) and not line.strip().startswith('//'):
                    # 排除測試代碼和範例代碼
                    if not any(pattern in file_path for pattern in ['/test', '/tests', '/examples', 'test.rs']):
                        issues.append(QualityIssue(
                            severity=println_severity,
                            message="考慮使用 log crate 而非 println! 進行日誌記錄",
                            line=i,
                            rule="no-println"
                        ))
        
        # 4. TODO/FIXME 檢查
        if self.config.get("check_todos", True):
            todo_patterns = ['TODO', 'FIXME', 'HACK', 'XXX']
            for i, line in enumerate(lines, 1):
                for pattern in todo_patterns:
                    if pattern in line.upper():
                        issues.append(QualityIssue(
                            severity="info",
                            message=f"發現 {pattern} 註解",
                            line=i,
                            rule="todo-comment"
                        ))
                        break
        
        # 5. 命名檢查
        if self.config.get("check_naming", True):
            # 檢查 snake_case
            for i, line in enumerate(lines, 1):
                # 變數和函數命名
                var_match = re.search(r'\b(?:let|fn)\s+([a-zA-Z_][a-zA-Z0-9_]*)', line)
                if var_match:
                    name = var_match.group(1)
                    if not name.islower() and '_' not in name and not name.startswith('_'):
                        if any(c.isupper() for c in name):
                            issues.append(QualityIssue(
                                severity="info",
                                message=f"建議使用 snake_case 命名: {name}",
                                line=i,
                                rule="snake-case"
                            ))
                
                # 結構體和枚舉命名 (PascalCase)
                struct_match = re.search(r'\b(?:struct|enum)\s+([a-zA-Z_][a-zA-Z0-9_]*)', line)
                if struct_match:
                    name = struct_match.group(1)
                    if not (name[0].isupper() and '_' not in name):
                        issues.append(QualityIssue(
                            severity="info",
                            message=f"結構體/枚舉應使用 PascalCase: {name}",
                            line=i,
                            rule="pascal-case"
                        ))
        
        # 6. 效能檢查
        if self.config.get("check_performance", True):
            perf_patterns = [
                (r'\.clone\(\)', "考慮是否真的需要 clone()"),
                (r'String::from\(', "對於字面量，考慮使用 &str 而非 String"),
                (r'vec!\[\]', "考慮使用 Vec::new() 代替空的 vec![]")
            ]
            
            for i, line in enumerate(lines, 1):
                for pattern, message in perf_patterns:
                    if re.search(pattern, line):
                        issues.append(QualityIssue(
                            severity="info",
                            message=message,
                            line=i,
                            rule="performance"
                        ))
        
        # 7. 安全性檢查
        if self.config.get("check_security", True):
            security_patterns = [
                (r'\bunsafe\s*\{', "謹慎使用 unsafe 代碼"),
                (r'std::mem::transmute', "transmute 是危險的，考慮其他方案"),
                (r'std::ptr::', "使用裸指針時要小心")
            ]
            
            for i, line in enumerate(lines, 1):
                for pattern, message in security_patterns:
                    if re.search(pattern, line):
                        issues.append(QualityIssue(
                            severity="warning",
                            message=message,
                            line=i,
                            rule="security-check"
                        ))
        
        return issues
    
    def _tool_available(self, tool: str) -> bool:
        """檢查工具是否可用"""
        try:
            subprocess.run([tool, "--version"], 
                         capture_output=True, 
                         check=True, 
                         timeout=10)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False