"""
Go 代碼品質檢查器
支援 gofmt、go vet、golint、staticcheck 等工具
"""

import subprocess
import json
import re
import time
from pathlib import Path
from typing import List, Dict
from .base_checker import BaseQualityChecker, QualityIssue, CheckResult

class GolangQualityChecker(BaseQualityChecker):
    """Go 專用品質檢查器"""
    
    def get_checker_name(self) -> str:
        return "Go"
    
    def get_supported_extensions(self) -> List[str]:
        return ['.go']
    
    def check_file(self, file_path: str) -> CheckResult:
        """檢查 Go 檔案品質"""
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
                file_type="golang",
                issues=[QualityIssue("error", str(e))],
                execution_time=time.time() - start_time
            )
        
        # 1. gofmt 格式化檢查
        if self.config.get("gofmt_enabled", True):
            gofmt_issues, gofmt_fixes = self._check_gofmt(file_path)
            issues.extend(gofmt_issues)
            fixed_issues.extend(gofmt_fixes)
        
        # 2. go vet 檢查
        if self.config.get("go_vet_enabled", True):
            vet_issues = self._check_go_vet(file_path)
            issues.extend(vet_issues)
        
        # 3. staticcheck 檢查
        if self.config.get("staticcheck_enabled", True):
            staticcheck_issues = self._check_staticcheck(file_path)
            issues.extend(staticcheck_issues)
        
        # 4. 自定義規則檢查
        custom_issues = self._check_custom_rules(content, lines, file_path)
        issues.extend(custom_issues)
        
        # 建立結果
        result = CheckResult(
            file_path=file_path,
            file_type="golang",
            issues=issues,
            fixed_issues=fixed_issues,
            execution_time=time.time() - start_time
        )
        
        # 儲存快取
        self._save_cache(result)
        
        return result
    
    def _check_gofmt(self, file_path: str) -> tuple[List[QualityIssue], List[str]]:
        """gofmt 格式化檢查"""
        issues = []
        fixes = []
        
        if not self._tool_available("gofmt"):
            if self.debug:
                print("⚠️ gofmt 工具不可用")
            return issues, fixes
        
        try:
            # 檢查格式化
            result = subprocess.run(
                ["gofmt", "-d", file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.stdout.strip():
                issues.append(QualityIssue(
                    severity="warning",
                    message="代碼格式不符合 gofmt 標準",
                    rule="gofmt-formatting",
                    fixable=True
                ))
                
                # 自動修復
                if self.config.get("auto_fix", True):
                    fix_result = subprocess.run(
                        ["gofmt", "-w", file_path],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if fix_result.returncode == 0:
                        fixes.append("gofmt 格式化已應用")
                    else:
                        issues.append(QualityIssue(
                            severity="error",
                            message="gofmt 自動修復失敗",
                            rule="gofmt-autofix"
                        ))
        
        except subprocess.TimeoutExpired:
            issues.append(QualityIssue(
                severity="warning",
                message="gofmt 檢查逾時",
                rule="gofmt-timeout"
            ))
        except Exception as e:
            if self.debug:
                print(f"gofmt 檢查失敗: {e}")
        
        return issues, fixes
    
    def _check_go_vet(self, file_path: str) -> List[QualityIssue]:
        """go vet 檢查"""
        issues = []
        
        if not self._tool_available("go"):
            return issues
        
        try:
            result = subprocess.run(
                ["go", "vet", file_path],
                capture_output=True,
                text=True,
                timeout=45
            )
            
            if result.stderr:
                lines = result.stderr.strip().split('\n')
                for line in lines:
                    # 解析 go vet 輸出格式: file:line:col: message
                    match = re.match(r'^([^:]+):(\d+):(\d+):\s*(.+)$', line)
                    if match:
                        file_name, line_num, col_num, message = match.groups()
                        
                        if Path(file_name).resolve() == Path(file_path).resolve():
                            issues.append(QualityIssue(
                                severity="warning",
                                message=message,
                                line=int(line_num),
                                column=int(col_num),
                                rule="go-vet"
                            ))
        
        except subprocess.TimeoutExpired:
            issues.append(QualityIssue(
                severity="warning",
                message="go vet 檢查逾時",
                rule="go-vet-timeout"
            ))
        except Exception as e:
            if self.debug:
                print(f"go vet 檢查失敗: {e}")
        
        return issues
    
    def _check_staticcheck(self, file_path: str) -> List[QualityIssue]:
        """staticcheck 檢查"""
        issues = []
        
        if not self._tool_available("staticcheck"):
            if self.debug:
                print("⚠️ staticcheck 工具不可用")
            return issues
        
        try:
            result = subprocess.run(
                ["staticcheck", "-f", "json", file_path],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    try:
                        if line.strip():
                            data = json.loads(line)
                            location = data.get('location', {})
                            
                            if location.get('filename') == file_path:
                                severity = "warning"
                                if data.get('severity') == 'error':
                                    severity = "error"
                                
                                issues.append(QualityIssue(
                                    severity=severity,
                                    message=data.get('message', 'staticcheck issue'),
                                    line=location.get('line'),
                                    column=location.get('column'),
                                    rule=data.get('code', 'staticcheck')
                                ))
                    
                    except json.JSONDecodeError:
                        continue
        
        except subprocess.TimeoutExpired:
            issues.append(QualityIssue(
                severity="warning",
                message="staticcheck 檢查逾時",
                rule="staticcheck-timeout"
            ))
        except Exception as e:
            if self.debug:
                print(f"staticcheck 檢查失敗: {e}")
        
        return issues
    
    def _check_custom_rules(self, content: str, lines: List[str], file_path: str) -> List[QualityIssue]:
        """Go 特有的自定義規則檢查"""
        issues = []
        
        # 1. fmt.Println 調試檢查
        if self.config.get("check_fmt_print", True):
            fmt_severity = self.config.get("fmt_print_severity", "info")
            
            for i, line in enumerate(lines, 1):
                if re.search(r'fmt\.Print(ln)?\s*\(', line) and not line.strip().startswith('//'):
                    # 排除測試檔案
                    if not file_path.endswith('_test.go'):
                        issues.append(QualityIssue(
                            severity=fmt_severity,
                            message="考慮使用 log 包而非 fmt.Print* 進行日誌記錄",
                            line=i,
                            rule="no-fmt-print"
                        ))
        
        # 2. panic 使用檢查
        if self.config.get("check_panic", True):
            panic_severity = self.config.get("panic_severity", "warning")
            
            for i, line in enumerate(lines, 1):
                if re.search(r'\bpanic\s*\(', line) and not line.strip().startswith('//'):
                    # 排除測試檔案
                    if not file_path.endswith('_test.go'):
                        issues.append(QualityIssue(
                            severity=panic_severity,
                            message="謹慎使用 panic，考慮返回 error",
                            line=i,
                            rule="no-panic"
                        ))
        
        # 3. TODO/FIXME 檢查
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
        
        # 4. 錯誤處理檢查
        if self.config.get("check_error_handling", True):
            for i, line in enumerate(lines, 1):
                # 檢查是否忽略錯誤
                if re.search(r'_,\s*(?:err\s*:?=|=.*err)', line):
                    issues.append(QualityIssue(
                        severity="warning",
                        message="避免忽略錯誤，應該適當處理",
                        line=i,
                        rule="handle-error"
                    ))
        
        # 5. 命名檢查
        if self.config.get("check_naming", True):
            for i, line in enumerate(lines, 1):
                # 檢查包變數命名 (應該是 MixedCaps)
                if re.search(r'^\s*var\s+([a-z][a-zA-Z0-9_]*)', line):
                    match = re.search(r'^\s*var\s+([a-z][a-zA-Z0-9_]*)', line)
                    if match:
                        var_name = match.group(1)
                        if '_' in var_name:
                            issues.append(QualityIssue(
                                severity="info",
                                message=f"Go 建議使用 mixedCaps 而非 under_scores: {var_name}",
                                line=i,
                                rule="mixed-caps"
                            ))
                
                # 檢查函數命名
                func_match = re.search(r'^\s*func\s+([a-zA-Z][a-zA-Z0-9_]*)', line)
                if func_match:
                    func_name = func_match.group(1)
                    if '_' in func_name:
                        issues.append(QualityIssue(
                            severity="info",
                            message=f"Go 函數建議使用 mixedCaps: {func_name}",
                            line=i,
                            rule="func-naming"
                        ))
        
        # 6. 介面檢查
        if self.config.get("check_interfaces", True):
            for i, line in enumerate(lines, 1):
                # 檢查介面命名 (建議以 -er 結尾)
                interface_match = re.search(r'type\s+([A-Z]\w*)\s+interface', line)
                if interface_match:
                    interface_name = interface_match.group(1)
                    if not interface_name.endswith('er') and len(interface_name) > 5:
                        issues.append(QualityIssue(
                            severity="info",
                            message=f"Go 介面建議以 -er 結尾: {interface_name}",
                            line=i,
                            rule="interface-naming"
                        ))
        
        # 7. 記憶體優化檢查
        if self.config.get("check_memory", True):
            memory_patterns = [
                (r'make\(\[\].*,\s*0\s*,', "避免為空切片分配容量"),
                (r'new\(\[\]', "通常使用 make 而非 new 創建切片"),
                (r'strings\.Split\(.+\)', "大量字串操作考慮使用 strings.Builder")
            ]
            
            for i, line in enumerate(lines, 1):
                for pattern, message in memory_patterns:
                    if re.search(pattern, line):
                        issues.append(QualityIssue(
                            severity="info",
                            message=message,
                            line=i,
                            rule="memory-optimization"
                        ))
        
        # 8. 併發安全檢查
        if self.config.get("check_concurrency", True):
            concurrency_patterns = [
                (r'\bgo\s+func\s*\(', "確保 goroutine 有適當的同步機制"),
                (r'time\.Sleep\s*\(', "避免使用 sleep 進行同步"),
                (r'\bselect\s*\{', "確保 select 語句不會造成死鎖")
            ]
            
            for i, line in enumerate(lines, 1):
                for pattern, message in concurrency_patterns:
                    if re.search(pattern, line):
                        issues.append(QualityIssue(
                            severity="info",
                            message=message,
                            line=i,
                            rule="concurrency-safety"
                        ))
        
        return issues
    
    def _tool_available(self, tool: str) -> bool:
        """檢查工具是否可用"""
        try:
            subprocess.run([tool, "version"], 
                         capture_output=True, 
                         check=True, 
                         timeout=10)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            # 嘗試其他版本檢查方式
            try:
                subprocess.run([tool, "--version"], 
                             capture_output=True, 
                             check=True, 
                             timeout=10)
                return True
            except:
                return False