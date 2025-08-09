"""
ActionQuality - Quality Check Action Executor with Language-Specific Modules
"""

from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

from .action_base import ActionExecutor, ActionResult
from ..event_layer import HookEvent

# Import quality modules
try:
    from .quality_modules.quality_python import PythonQualityChecker
    from .quality_modules.quality_javascript import JavaScriptQualityChecker
    from .quality_modules.quality_typescript import TypeScriptQualityChecker
    from .quality_modules.quality_golang import GolangQualityChecker
    from .quality_modules.quality_rust import RustQualityChecker
    QUALITY_MODULES_AVAILABLE = True
except ImportError:
    QUALITY_MODULES_AVAILABLE = False

class ActionQuality(ActionExecutor):
    """Quality Check Action Executor with Language-Specific Support"""
    
    def __init__(self):
        super().__init__()
        # Initialize language-specific checkers
        self.checkers = {}
        if QUALITY_MODULES_AVAILABLE:
            self.checkers = {
                'python': PythonQualityChecker(),
                'javascript': JavaScriptQualityChecker(), 
                'typescript': TypeScriptQualityChecker(),
                'golang': GolangQualityChecker(),
                'rust': RustQualityChecker()
            }
    
    def get_action_type(self) -> str:
        return "action.quality"
    
    def execute(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        """ExecuteQuality checkAction"""
        start_time = datetime.now()
        
        try:
            operation = parameters.get('operation', 'check')
            
            if operation == 'check':
                result = self._perform_quality_check(event, parameters)
            elif operation == 'format':
                result = self._format_code(event, parameters)
            elif operation == 'lint':
                result = self._lint_code(event, parameters)
            elif operation == 'security_scan':
                result = self._security_scan(event, parameters)
            elif operation == 'dependency_check':
                result = self._dependency_check(event, parameters)
            elif operation == 'similarity_check':
                result = self._similarity_check(event, parameters)
            else:
                return self._create_result(
                    action_id="action.quality",
                    success=False,
                    execution_time=(datetime.now() - start_time).total_seconds(),
                    error=f"Unknown operation: {operation}"
                )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            return self._create_result(
                action_id="action.quality",
                success=True,
                execution_time=execution_time,
                output=result
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return self._create_result(
                action_id="action.quality",
                success=False,
                execution_time=execution_time,
                error=str(e)
            )
    
    def _perform_quality_check(self, event: HookEvent, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute comprehensive quality check using language-specific modules"""
        results = {
            'summary': {
                'total_files': len(event.file_paths),
                'files_checked': 0,
                'total_issues': 0,
                'total_errors': 0,
                'total_warnings': 0,
                'blocking_issues': False
            },
            'file_results': [],
            'quality_modules_available': QUALITY_MODULES_AVAILABLE
        }
        
        if not QUALITY_MODULES_AVAILABLE:
            # Fallback to basic quality check
            return self._basic_quality_check(event, parameters)
            
        # Check each file with appropriate language-specific checker
        for file_path in event.file_paths:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext in ext_to_checker:
                checker_name = ext_to_checker[file_ext] 
                if checker_name in self.checkers:
                    try:
                        # Use professional quality checker
                        checker = self.checkers[checker_name]
                        check_result = checker.check_file(file_path)
                        
                        file_result = {
                            'file': file_path,
                            'checker': checker.get_checker_name(),
                            'issues': len(check_result.issues),
                            'errors': check_result.error_count,
                            'warnings': check_result.warning_count,
                            'execution_time': check_result.execution_time,
                            'details': [issue.to_dict() for issue in check_result.issues]
                        }
                        
                        results['file_results'].append(file_result)
                        
                        # Update summary statistics
                        results['summary']['files_checked'] += 1
                        results['summary']['total_issues'] += file_result['issues']
                        results['summary']['total_errors'] += file_result['errors']
                        results['summary']['total_warnings'] += file_result['warnings']
                        
                        if file_result['errors'] > 0:
                            results['summary']['blocking_issues'] = True
                            
                    except Exception as e:
                        # Fallback to basic check for this file
                        basic_result = self._check_file_basic(file_path)
                        results['file_results'].append(basic_result)
                        results['summary']['files_checked'] += 1
            else:
                # File type not supported by professional checkers, use basic check
                basic_result = self._check_file_basic(file_path)
                results['file_results'].append(basic_result)
                results['summary']['files_checked'] += 1
                
        # Generate recommendations based on results
        results['recommendations'] = self._generate_quality_recommendations(results['file_results'])
        
        return results
    
    def _check_file_basic(self, file_path: str) -> Dict[str, Any]:
        """Basic file quality check fallback"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
            except Exception:
                return {
                    'file': file_path,
                    'checker': 'basic',
                    'issues': 1,
                    'errors': 1,
                    'warnings': 0,
                    'details': ['Could not read file - encoding issue']
                }
        except Exception as e:
            return {
                'file': file_path,
                'checker': 'basic',
                'issues': 1,
                'errors': 1,
                'warnings': 0,
                'details': [f'Could not read file: {str(e)}']
            }
            
        issues = []
        warnings = 0
        
        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                issues.append(f"Line {i}: Too long ({len(line)} characters)")
                warnings += 1
            
            if line.strip().lower().startswith('todo') or 'fixme' in line.lower():
                issues.append(f"Line {i}: Contains TODO/FIXME")
                warnings += 1
                
            if '\t' in line:
                issues.append(f"Line {i}: Contains tabs, consider using spaces")
                warnings += 1
                
        return {
            'file': file_path,
            'checker': 'basic',
            'issues': len(issues),
            'errors': 0,
            'warnings': warnings,
            'details': issues
        }
    
    def _basic_quality_check(self, event: HookEvent, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback quality check when professional modules are not available"""
        results = {
            'summary': {
                'total_files': len(event.file_paths),
                'files_checked': 0,
                'total_issues': 0,
                'total_errors': 0,
                'total_warnings': 0,
                'blocking_issues': False
            },
            'file_results': [],
            'quality_modules_available': False
        }
        
        for file_path in event.file_paths:
            file_result = self._check_file_basic(file_path)
            results['file_results'].append(file_result)
            
            # Update summary
            results['summary']['files_checked'] += 1
            results['summary']['total_issues'] += file_result['issues']
            results['summary']['total_errors'] += file_result['errors']
            results['summary']['total_warnings'] += file_result['warnings']
            
            if file_result['errors'] > 0:
                results['summary']['blocking_issues'] = True
                
        # Generate basic recommendations
        results['recommendations'] = self._generate_quality_recommendations(results['file_results'])
        
        return results
    
    def _generate_quality_recommendations(self, file_results: List[Dict[str, Any]]) -> List[str]:
        """Generate quality improvement recommendations based on results"""
        recommendations = []
        
        total_errors = sum(result.get('errors', 0) for result in file_results)
        total_warnings = sum(result.get('warnings', 0) for result in file_results)
        
        if total_errors > 0:
            recommendations.append(f"Fix {total_errors} error(s) found - these may prevent compilation or execution")
        
        if total_warnings > 5:
            recommendations.append(f"Address {total_warnings} warning(s) to improve code quality")
        
        # Language-specific recommendations
        python_files = [r for r in file_results if r.get('file', '').endswith('.py')]
        if python_files and any(r.get('issues', 0) > 0 for r in python_files):
            recommendations.append("Consider using Black formatter and flake8 linter for Python files")
            
        js_files = [r for r in file_results if r.get('file', '').endswith(('.js', '.jsx'))]
        if js_files and any(r.get('issues', 0) > 0 for r in js_files):
            recommendations.append("Consider using Prettier formatter and ESLint for JavaScript files")
            
        if not recommendations:
            recommendations.append("Code quality looks good! Consider running regular quality checks")
            
        return recommendations
    
    def _format_code(self, event: HookEvent, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Format化代碼"""
        formatter_map = {
            '.py': 'black',
            '.js': 'prettier',
            '.jsx': 'prettier',
            '.ts': 'prettier',
            '.tsx': 'prettier',
            '.rs': 'rustfmt',
            '.go': 'gofmt'
        }
        
        results = []
        for file_path in event.file_paths:
            file_ext = Path(file_path).suffix.lower()
            formatter = formatter_map.get(file_ext, 'unknown')
            
            results.append({
                'file': file_path,
                'formatter': formatter,
                'status': 'simulated',  # In actual implementation時Execute真正的Format化
                'message': f"將使用 {formatter} Format化File"
            })
        
        return {
            'formatted_files': results,
            'total_formatted': len(results)
        }
    
    def _lint_code(self, event: HookEvent, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """代碼Static check"""
        linter_map = {
            '.py': ['flake8', 'pylint'],
            '.js': ['eslint'],
            '.jsx': ['eslint'],
            '.ts': ['eslint', 'tsc'],
            '.tsx': ['eslint', 'tsc'],
            '.rs': ['clippy'],
            '.go': ['go vet', 'staticcheck']
        }
        
        results = []
        for file_path in event.file_paths:
            file_ext = Path(file_path).suffix.lower()
            linters = linter_map.get(file_ext, ['unknown'])
            
            results.append({
                'file': file_path,
                'linters': linters,
                'status': 'simulated',
                'issues_found': 0  # In actual implementation時Execute真正的 lint
            })
        
        return {
            'lint_results': results,
            'total_files_linted': len(results)
        }
    
    def _security_scan(self, event: HookEvent, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """安全掃描"""
        security_issues = []
        
        for file_path in event.file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except:
                continue
            
            # 基本Security scan
            content_lower = content.lower()
            
            # Check硬編碼密碼
            if 'password' in content_lower and ('=' in content or ':' in content):
                security_issues.append({
                    'file': file_path,
                    'type': 'hardcoded_password',
                    'severity': 'high',
                    'message': '可能包含硬編碼密碼'
                })
            
            # Check API 密鑰
            if 'api_key' in content_lower or 'apikey' in content_lower:
                security_issues.append({
                    'file': file_path,
                    'type': 'api_key',
                    'severity': 'high',
                    'message': '可能包含硬編碼 API 密鑰'
                })
            
            # Check SQL 注入風險
            if 'select' in content_lower and 'where' in content_lower and '+' in content:
                security_issues.append({
                    'file': file_path,
                    'type': 'sql_injection',
                    'severity': 'medium',
                    'message': '可能存在 SQL 注入風險'
                })
        
        return {
            'security_issues': security_issues,
            'total_issues': len(security_issues),
            'severity_summary': self._summarize_security_severity(security_issues)
        }
    
    def _dependency_check(self, event: HookEvent, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Dependency check"""
        dependencies = {
            'package_files': [],
            'outdated_packages': [],
            'vulnerable_packages': [],
            'recommendations': []
        }
        
        # Check包File
        for file_path in event.file_paths:
            file_name = Path(file_path).name
            if file_name in ['package.json', 'requirements.txt', 'Cargo.toml', 'go.mod', 'pom.xml']:
                dependencies['package_files'].append(file_path)
        
        # 模擬依賴Analyze
        if dependencies['package_files']:
            dependencies['recommendations'].append("建議定期Update依賴套件")
            dependencies['recommendations'].append("使用ToolCheck已知安全漏洞")
        
        return dependencies
    
    def _similarity_check(self, event: HookEvent, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Similarity check"""
        similarity_threshold = parameters.get('threshold', 0.8)
        
        # 簡化的Similarity check
        similar_pairs = []
        files_content = {}
        
        # 讀取所有FileContent
        for file_path in event.file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    files_content[file_path] = f.read()
            except:
                continue
        
        # 比較File相似性
        file_paths = list(files_content.keys())
        for i in range(len(file_paths)):
            for j in range(i + 1, len(file_paths)):
                file1, file2 = file_paths[i], file_paths[j]
                similarity = self._calculate_similarity(
                    files_content[file1], 
                    files_content[file2]
                )
                
                if similarity >= similarity_threshold:
                    similar_pairs.append({
                        'file1': file1,
                        'file2': file2,
                        'similarity': similarity,
                        'recommendation': '考慮提取公共邏輯'
                    })
        
        return {
            'similar_pairs': similar_pairs,
            'threshold': similarity_threshold,
            'total_comparisons': len(file_paths) * (len(file_paths) - 1) // 2
        }
    
    def _calculate_similarity(self, content1: str, content2: str) -> float:
        """計算Content相似度"""
        # 簡化的相似度計算
        lines1 = set(line.strip() for line in content1.splitlines() if line.strip())
        lines2 = set(line.strip() for line in content2.splitlines() if line.strip())
        
        if not lines1 and not lines2:
            return 1.0
        if not lines1 or not lines2:
            return 0.0
        
        intersection = len(lines1.intersection(lines2))
        union = len(lines1.union(lines2))
        
        return intersection / union if union > 0 else 0.0
    
    def _generate_quality_recommendations(self, results: List[Dict[str, Any]]) -> List[str]:
        """GenerateQuality建議"""
        recommendations = []
        
        total_errors = sum(r.get('errors', 0) for r in results)
        total_warnings = sum(r.get('warnings', 0) for r in results)
        
        if total_errors > 0:
            recommendations.append(f"優先修復 {total_errors} 個Error")
        
        if total_warnings > 10:
            recommendations.append(f"建議Process {total_warnings} 個Warning")
        
        # 基於Check器Type的建議
        checkers_used = set(r.get('checker', '') for r in results)
        if 'javascript' in checkers_used or 'typescript' in checkers_used:
            recommendations.append("建議啟用 ESLint 自動修復")
        
        if 'python' in checkers_used:
            recommendations.append("建議使用 Black 進行Code formatting")
        
        return recommendations
    
    def _summarize_security_severity(self, security_issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """統計安全問題嚴重程度"""
        severity_count = {'high': 0, 'medium': 0, 'low': 0}
        
        for issue in security_issues:
            severity = issue.get('severity', 'low')
            severity_count[severity] = severity_count.get(severity, 0) + 1
        
        return severity_count