"""
Python 代碼品質檢查器
支援 Black、Flake8、MyPy、PyCodeStyle 等工具
"""

import subprocess
import json
import re
import time
from pathlib import Path
from typing import List, Dict
from .base_checker import BaseQualityChecker, QualityIssue, CheckResult

class PythonQualityChecker(BaseQualityChecker):
    """Python 專用品質檢查器"""
    
    def get_checker_name(self) -> str:
        return "Python"
    
    def get_supported_extensions(self) -> List[str]:
        return ['.py', '.pyi']
    
    def check_file(self, file_path: str) -> CheckResult:
        """檢查 Python 檔案品質"""
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
                file_type="python",
                issues=[QualityIssue("error", str(e))],
                execution_time=time.time() - start_time
            )
        
        # 1. Black 格式化檢查
        if self.config.get("black_enabled", True):
            black_issues, black_fixes = self._check_black(file_path)
            issues.extend(black_issues)
            fixed_issues.extend(black_fixes)
        
        # 2. Flake8 語法檢查
        if self.config.get("flake8_enabled", True):
            flake8_issues = self._check_flake8(file_path)
            issues.extend(flake8_issues)
        
        # 3. MyPy 類型檢查
        if self.config.get("mypy_enabled", False):  # 預設關閉，因為可能很慢
            mypy_issues = self._check_mypy(file_path)
            issues.extend(mypy_issues)
        
        # 4. 自定義規則檢查
        custom_issues = self._check_custom_rules(content, lines, file_path)
        issues.extend(custom_issues)
        
        # 建立結果
        result = CheckResult(
            file_path=file_path,
            file_type="python",
            issues=issues,
            fixed_issues=fixed_issues,
            execution_time=time.time() - start_time
        )
        
        # 儲存快取
        self._save_cache(result)
        
        return result
    
    def _check_black(self, file_path: str) -> tuple[List[QualityIssue], List[str]]:
        """Black 格式化檢查"""
        issues = []
        fixes = []
        
        if not self._tool_available("black"):
            if self.debug:
                print("⚠️ Black 工具不可用")
            return issues, fixes
        
        try:
            # 檢查是否需要格式化
            result = subprocess.run(
                ["black", "--check", "--diff", file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                issues.append(QualityIssue(
                    severity="warning",
                    message="代碼格式不符合 Black 標準",
                    rule="black-formatting",
                    fixable=True
                ))
                
                # 自動修復 (如果啟用)
                if self.config.get("auto_fix", True):
                    fix_result = subprocess.run(
                        ["black", file_path],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if fix_result.returncode == 0:
                        fixes.append("Black 格式化已應用")
                    else:
                        issues.append(QualityIssue(
                            severity="error",
                            message="Black 自動修復失敗",
                            rule="black-autofix"
                        ))
        
        except subprocess.TimeoutExpired:
            issues.append(QualityIssue(
                severity="warning",
                message="Black 檢查逾時",
                rule="black-timeout"
            ))
        except Exception as e:
            if self.debug:
                print(f"Black 檢查失敗: {e}")
        
        return issues, fixes
    
    def _check_flake8(self, file_path: str) -> List[QualityIssue]:
        """Flake8 語法檢查"""
        issues = []
        
        if not self._tool_available("flake8"):
            if self.debug:
                print("⚠️ Flake8 工具不可用")
            return issues
        
        try:
            # 設定忽略的錯誤碼
            ignore_codes = self.config.get("flake8_ignore", ["E203", "W503"])
            ignore_arg = f"--ignore={','.join(ignore_codes)}" if ignore_codes else ""
            
            cmd = ["flake8", "--format=json"]
            if ignore_arg:
                cmd.append(ignore_arg)
            cmd.append(file_path)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.stdout:
                try:
                    # Flake8 JSON 格式輸出需要特殊處理
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if ':' in line:
                            # 解析 flake8 輸出格式: file:line:col: code message
                            parts = line.split(':', 3)
                            if len(parts) >= 4:
                                line_num = int(parts[1]) if parts[1].isdigit() else None
                                col_num = int(parts[2]) if parts[2].isdigit() else None
                                message = parts[3].strip()
                                
                                # 提取錯誤代碼
                                code_match = re.match(r'(\w+)\s+(.+)', message)
                                if code_match:
                                    code, msg = code_match.groups()
                                    severity = "error" if code.startswith('E') else "warning"
                                else:
                                    code = "flake8"
                                    msg = message
                                    severity = "warning"
                                
                                issues.append(QualityIssue(
                                    severity=severity,
                                    message=msg,
                                    line=line_num,
                                    column=col_num,
                                    rule=code
                                ))
                
                except Exception as e:
                    if self.debug:
                        print(f"解析 Flake8 輸出失敗: {e}")
        
        except subprocess.TimeoutExpired:
            issues.append(QualityIssue(
                severity="warning",
                message="Flake8 檢查逾時",
                rule="flake8-timeout"
            ))
        except Exception as e:
            if self.debug:
                print(f"Flake8 檢查失敗: {e}")
        
        return issues
    
    def _check_mypy(self, file_path: str) -> List[QualityIssue]:
        """MyPy 類型檢查"""
        issues = []
        
        if not self._tool_available("mypy"):
            if self.debug:
                print("⚠️ MyPy 工具不可用")
            return issues
        
        try:
            result = subprocess.run(
                ["mypy", "--show-column-numbers", "--show-error-codes", file_path],
                capture_output=True,
                text=True,
                timeout=60  # MyPy 可能較慢
            )
            
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    # 解析 MyPy 輸出: file:line:col: level: message [code]
                    match = re.match(r'^([^:]+):(\d+):(\d+):\s+(\w+):\s+(.+?)(?:\s+\[([^\]]+)\])?$', line)
                    if match:
                        file_name, line_num, col_num, level, message, code = match.groups()
                        
                        severity = {
                            'error': 'error',
                            'warning': 'warning', 
                            'note': 'info'
                        }.get(level.lower(), 'warning')
                        
                        issues.append(QualityIssue(
                            severity=severity,
                            message=message,
                            line=int(line_num),
                            column=int(col_num),
                            rule=code or "mypy"
                        ))
        
        except subprocess.TimeoutExpired:
            issues.append(QualityIssue(
                severity="warning",
                message="MyPy 檢查逾時",
                rule="mypy-timeout"
            ))
        except Exception as e:
            if self.debug:
                print(f"MyPy 檢查失敗: {e}")
        
        return issues
    
    def _check_custom_rules(self, content: str, lines: List[str], file_path: str) -> List[QualityIssue]:
        """自定義規則檢查"""
        issues = []
        
        # 1. print() 語句檢查
        if self.config.get("check_prints", True):
            for i, line in enumerate(lines, 1):
                if re.search(r'\bprint\s*\(', line) and not line.strip().startswith('#'):
                    issues.append(QualityIssue(
                        severity="info",
                        message="考慮使用 logging 而非 print",
                        line=i,
                        rule="no-print"
                    ))
        
        # 2. TODO/FIXME 檢查
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
        
        # 3. 長行檢查
        max_length = self.config.get("max_line_length", 120)
        if self.config.get("check_line_length", True):
            for i, line in enumerate(lines, 1):
                if len(line) > max_length:
                    issues.append(QualityIssue(
                        severity="warning",
                        message=f"行太長 ({len(line)}/{max_length})",
                        line=i,
                        rule="line-too-long"
                    ))
        
        # 4. 未使用的 import 檢查 (簡單版)
        if self.config.get("check_unused_imports", True):
            import_lines = []
            imported_names = set()
            
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if line.startswith('import ') or line.startswith('from '):
                    import_lines.append((i, line))
                    
                    # 提取導入的名稱
                    if line.startswith('import '):
                        # import module [as alias]
                        parts = line[7:].split(' as ')
                        name = parts[1].strip() if len(parts) > 1 else parts[0].strip().split('.')[0]
                        imported_names.add(name)
                    elif ' import ' in line:
                        # from module import name1, name2
                        import_part = line.split(' import ', 1)[1]
                        names = [n.strip().split(' as ')[0] for n in import_part.split(',')]
                        imported_names.update(names)
            
            # 檢查是否有使用
            for line_num, import_line in import_lines:
                for name in imported_names:
                    if name in import_line:
                        # 檢查是否在其他地方使用
                        name_used = any(name in line and line_num != i for i, line in enumerate(lines, 1))
                        if not name_used:
                            issues.append(QualityIssue(
                                severity="info",
                                message=f"可能未使用的導入: {name}",
                                line=line_num,
                                rule="unused-import"
                            ))
        
        # 5. 安全性檢查
        if self.config.get("check_security", True):
            security_patterns = [
                (r'exec\s*\(', "避免使用 exec()"),
                (r'eval\s*\(', "避免使用 eval()"),
                (r'__import__\s*\(', "避免動態導入"),
                (r'input\s*\([^)]*\)', "使用 input() 時要注意安全性")
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