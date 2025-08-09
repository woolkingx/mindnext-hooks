"""
TypeScript 代碼品質檢查器
支援 tsc、ESLint、Prettier 等工具
"""

import subprocess
import json
import re
import time
from pathlib import Path
from typing import List, Dict
from .base_checker import BaseQualityChecker, QualityIssue, CheckResult

class TypeScriptQualityChecker(BaseQualityChecker):
    """TypeScript 專用品質檢查器"""
    
    def get_checker_name(self) -> str:
        return "TypeScript"
    
    def get_supported_extensions(self) -> List[str]:
        return ['.ts', '.tsx', '.d.ts']
    
    def check_file(self, file_path: str) -> CheckResult:
        """檢查 TypeScript 檔案品質"""
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
                file_type="typescript",
                issues=[QualityIssue("error", str(e))],
                execution_time=time.time() - start_time
            )
        
        # 1. TypeScript 編譯檢查
        if self.config.get("tsc_enabled", True):
            tsc_issues = self._check_typescript(file_path)
            issues.extend(tsc_issues)
        
        # 2. ESLint 檢查
        if self.config.get("eslint_enabled", True):
            eslint_issues, eslint_fixes = self._check_eslint(file_path)
            issues.extend(eslint_issues)
            fixed_issues.extend(eslint_fixes)
        
        # 3. Prettier 格式化檢查
        if self.config.get("prettier_enabled", True):
            prettier_issues, prettier_fixes = self._check_prettier(file_path)
            issues.extend(prettier_issues)
            fixed_issues.extend(prettier_fixes)
        
        # 4. 自定義規則檢查
        custom_issues = self._check_custom_rules(content, lines, file_path)
        issues.extend(custom_issues)
        
        # 建立結果
        result = CheckResult(
            file_path=file_path,
            file_type="typescript",
            issues=issues,
            fixed_issues=fixed_issues,
            execution_time=time.time() - start_time
        )
        
        # 儲存快取
        self._save_cache(result)
        
        return result
    
    def _check_typescript(self, file_path: str) -> List[QualityIssue]:
        """TypeScript 編譯檢查"""
        issues = []
        
        if not self._tool_available("npx"):
            return issues
        
        try:
            result = subprocess.run(
                ["npx", "tsc", "--noEmit", "--pretty", "false", file_path],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.stderr:
                lines = result.stderr.strip().split('\n')
                for line in lines:
                    # 解析 TypeScript 錯誤格式
                    match = re.match(r'^([^(]+)\((\d+),(\d+)\):\s*(error|warning)\s*TS(\d+):\s*(.+)$', line)
                    if match:
                        file_name, line_num, col_num, level, ts_code, message = match.groups()
                        
                        if Path(file_name).resolve() == Path(file_path).resolve():
                            severity = "error" if level == "error" else "warning"
                            
                            issues.append(QualityIssue(
                                severity=severity,
                                message=message,
                                line=int(line_num),
                                column=int(col_num),
                                rule=f"TS{ts_code}"
                            ))
        
        except subprocess.TimeoutExpired:
            issues.append(QualityIssue(
                severity="warning",
                message="TypeScript 編譯檢查逾時",
                rule="tsc-timeout"
            ))
        except Exception as e:
            if self.debug:
                print(f"TypeScript 檢查失敗: {e}")
        
        return issues
    
    def _check_eslint(self, file_path: str) -> tuple[List[QualityIssue], List[str]]:
        """ESLint 檢查 (複用 JavaScript 的邏輯)"""
        issues = []
        fixes = []
        
        if not self._tool_available("npx"):
            return issues, fixes
        
        try:
            result = subprocess.run(
                ["npx", "eslint", "--format=json", file_path],
                capture_output=True,
                text=True,
                timeout=45
            )
            
            if result.stdout:
                try:
                    eslint_results = json.loads(result.stdout)
                    
                    for file_result in eslint_results:
                        for message in file_result.get("messages", []):
                            severity = "error" if message["severity"] == 2 else "warning"
                            
                            issues.append(QualityIssue(
                                severity=severity,
                                message=message["message"],
                                line=message.get("line"),
                                column=message.get("column"),
                                rule=message.get("ruleId", "eslint"),
                                fixable=message.get("fix") is not None
                            ))
                
                except json.JSONDecodeError:
                    pass
            
            # 自動修復
            if self.config.get("auto_fix", True) and issues:
                fix_result = subprocess.run(
                    ["npx", "eslint", "--fix", file_path],
                    capture_output=True,
                    text=True,
                    timeout=45
                )
                
                if fix_result.returncode == 0:
                    fixes.append("ESLint 自動修復已應用")
        
        except subprocess.TimeoutExpired:
            issues.append(QualityIssue(
                severity="warning",
                message="ESLint 檢查逾時",
                rule="eslint-timeout"
            ))
        except Exception as e:
            if self.debug:
                print(f"ESLint 檢查失敗: {e}")
        
        return issues, fixes
    
    def _check_prettier(self, file_path: str) -> tuple[List[QualityIssue], List[str]]:
        """Prettier 格式化檢查"""
        issues = []
        fixes = []
        
        if not self._tool_available("npx"):
            return issues, fixes
        
        try:
            result = subprocess.run(
                ["npx", "prettier", "--check", file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                issues.append(QualityIssue(
                    severity="warning",
                    message="代碼格式不符合 Prettier 標準",
                    rule="prettier-formatting",
                    fixable=True
                ))
                
                if self.config.get("auto_fix", True):
                    fix_result = subprocess.run(
                        ["npx", "prettier", "--write", file_path],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if fix_result.returncode == 0:
                        fixes.append("Prettier 格式化已應用")
        
        except subprocess.TimeoutExpired:
            issues.append(QualityIssue(
                severity="warning",
                message="Prettier 檢查逾時",
                rule="prettier-timeout"
            ))
        except Exception as e:
            if self.debug:
                print(f"Prettier 檢查失敗: {e}")
        
        return issues, fixes
    
    def _check_custom_rules(self, content: str, lines: List[str], file_path: str) -> List[QualityIssue]:
        """TypeScript 特有的自定義規則檢查"""
        issues = []
        
        # 1. any 類型檢查
        if self.config.get("check_any_type", True):
            any_severity = self.config.get("any_type_severity", "warning")
            any_pattern = re.compile(r':\s*any\b|<any>|as\s+any\b')
            
            for i, line in enumerate(lines, 1):
                if any_pattern.search(line) and not line.strip().startswith('//'):
                    issues.append(QualityIssue(
                        severity=any_severity,
                        message="避免使用 'any' 類型，使用具體類型",
                        line=i,
                        rule="no-any"
                    ))
        
        # 2. console 檢查 (TypeScript 專案通常更嚴格)
        if self.config.get("check_console", True):
            console_severity = self.config.get("console_severity", "warning")  # TS 更嚴格
            console_pattern = re.compile(r'console\.\w+\s*\(')
            
            # 檢查是否在測試檔案中
            is_test_file = any(test_pattern in file_path.lower() 
                             for test_pattern in ['.test.', '.spec.', '/test/', '/tests/'])
            
            if not is_test_file:
                for i, line in enumerate(lines, 1):
                    if console_pattern.search(line) and not line.strip().startswith('//'):
                        issues.append(QualityIssue(
                            severity=console_severity,
                            message="在 TypeScript 中避免使用 console，使用 logger",
                            line=i,
                            rule="no-console"
                        ))
        
        # 3. 非空斷言檢查
        if self.config.get("check_non_null_assertion", True):
            for i, line in enumerate(lines, 1):
                if '!' in line and not line.strip().startswith('//'):
                    # 檢查是否為非空斷言操作符
                    if re.search(r'\w+!(?:\.|$|\s)', line):
                        issues.append(QualityIssue(
                            severity="warning",
                            message="謹慎使用非空斷言操作符 (!)",
                            line=i,
                            rule="no-non-null-assertion"
                        ))
        
        # 4. 接口命名檢查
        if self.config.get("check_interface_naming", True):
            interface_pattern = re.compile(r'interface\s+([A-Z]\w*)')
            
            for i, line in enumerate(lines, 1):
                match = interface_pattern.search(line)
                if match:
                    interface_name = match.group(1)
                    if interface_name.startswith('I') and len(interface_name) > 1 and interface_name[1].isupper():
                        issues.append(QualityIssue(
                            severity="info",
                            message=f"建議不要使用 'I' 前綴命名接口: {interface_name}",
                            line=i,
                            rule="interface-naming"
                        ))
        
        # 5. 導入檢查
        if self.config.get("check_imports", True):
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if line.startswith('import '):
                    # 檢查預設導入和命名導入混用
                    if ' from ' in line and '{' in line and not line.startswith('import {'):
                        # import default, { named } from 'module'
                        if line.count(',') > 0 and '{' in line:
                            issues.append(QualityIssue(
                                severity="info",
                                message="考慮分離預設導入和命名導入",
                                line=i,
                                rule="import-style"
                            ))
                    
                    # 檢查相對路徑導入
                    if '../' in line:
                        depth = line.count('../')
                        if depth > 2:
                            issues.append(QualityIssue(
                                severity="warning",
                                message=f"相對導入層級過深 ({depth} 層)",
                                line=i,
                                rule="import-depth"
                            ))
        
        # 6. 類型註解檢查
        if self.config.get("check_type_annotations", True):
            # 檢查函數參數是否有類型註解
            function_patterns = [
                re.compile(r'function\s+\w+\s*\(([^)]+)\)'),
                re.compile(r'const\s+\w+\s*=\s*\(([^)]+)\)\s*=>'),
                re.compile(r'\w+\s*:\s*\(([^)]+)\)\s*=>')
            ]
            
            for i, line in enumerate(lines, 1):
                for pattern in function_patterns:
                    match = pattern.search(line)
                    if match:
                        params = match.group(1)
                        if params and ':' not in params and '...' not in params:
                            issues.append(QualityIssue(
                                severity="info",
                                message="考慮為函數參數添加類型註解",
                                line=i,
                                rule="type-annotation"
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