"""
JavaScript 代碼品質檢查器
支援 ESLint、Prettier、JSHint 等工具
"""

import subprocess
import json
import re
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from .base_checker import BaseQualityChecker, QualityIssue, CheckResult

class JavaScriptQualityChecker(BaseQualityChecker):
    """JavaScript 專用品質檢查器"""
    
    def get_checker_name(self) -> str:
        return "JavaScript"
    
    def get_supported_extensions(self) -> List[str]:
        return ['.js', '.mjs', '.jsx']
    
    def check_file(self, file_path: str) -> CheckResult:
        """檢查 JavaScript 檔案品質"""
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
                file_type="javascript",
                issues=[QualityIssue("error", str(e))],
                execution_time=time.time() - start_time
            )
        
        # 1. Prettier 格式化檢查
        if self.config.get("prettier_enabled", True):
            prettier_issues, prettier_fixes = self._check_prettier(file_path)
            issues.extend(prettier_issues)
            fixed_issues.extend(prettier_fixes)
        
        # 2. ESLint 語法檢查
        if self.config.get("eslint_enabled", True):
            eslint_issues, eslint_fixes = self._check_eslint(file_path)
            issues.extend(eslint_issues)
            fixed_issues.extend(eslint_fixes)
        
        # 3. 自定義規則檢查
        custom_issues = self._check_custom_rules(content, lines, file_path)
        issues.extend(custom_issues)
        
        # 建立結果
        result = CheckResult(
            file_path=file_path,
            file_type="javascript",
            issues=issues,
            fixed_issues=fixed_issues,
            execution_time=time.time() - start_time
        )
        
        # 儲存快取
        self._save_cache(result)
        
        return result
    
    def _check_prettier(self, file_path: str) -> tuple[List[QualityIssue], List[str]]:
        """Prettier 格式化檢查"""
        issues = []
        fixes = []
        
        if not self._tool_available("npx"):
            if self.debug:
                print("⚠️ npx 工具不可用")
            return issues, fixes
        
        try:
            # 檢查格式化
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
                
                # 自動修復
                if self.config.get("auto_fix", True):
                    fix_result = subprocess.run(
                        ["npx", "prettier", "--write", file_path],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if fix_result.returncode == 0:
                        fixes.append("Prettier 格式化已應用")
                    else:
                        issues.append(QualityIssue(
                            severity="error",
                            message="Prettier 自動修復失敗",
                            rule="prettier-autofix"
                        ))
        
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
    
    def _check_eslint(self, file_path: str) -> tuple[List[QualityIssue], List[str]]:
        """ESLint 語法檢查"""
        issues = []
        fixes = []
        
        if not self._tool_available("npx"):
            if self.debug:
                print("⚠️ npx 工具不可用")
            return issues, fixes
        
        try:
            # ESLint 檢查
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
                
                except json.JSONDecodeError as e:
                    if self.debug:
                        print(f"ESLint JSON 解析失敗: {e}")
            
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
    
    def _check_custom_rules(self, content: str, lines: List[str], file_path: str) -> List[QualityIssue]:
        """自定義規則檢查"""
        issues = []
        
        # 1. ES Module 檢查
        if self.config.get("check_esmodule", True):
            esmodule_issues = self._check_esmodule_usage(lines, file_path)
            issues.extend(esmodule_issues)
        
        # 2. 建議使用現成庫檢查
        if self.config.get("check_library_suggestions", True):
            library_issues = self._check_library_suggestions(content, lines, file_path)
            issues.extend(library_issues)
        
        # 3. 相似函數檢測
        if self.config.get("check_similar_functions", True):
            similar_issues = self._check_similar_functions(content, lines, file_path)
            issues.extend(similar_issues)
        
        # 3. console 語句檢查
        console_severity = self.config.get("console_severity", "info")
        if self.config.get("check_console", True):
            console_patterns = [
                (r'console\.log\s*\(', 'console.log'),
                (r'console\.warn\s*\(', 'console.warn'),
                (r'console\.error\s*\(', 'console.error'),
                (r'console\.debug\s*\(', 'console.debug'),
                (r'console\.info\s*\(', 'console.info')
            ]
            
            # 檢查是否在允許的路徑中
            allowed_paths = self.config.get("console_allowed_paths", ["test/", "spec/", "debug/"])
            is_allowed = any(path in file_path for path in allowed_paths)
            
            if not is_allowed:
                for i, line in enumerate(lines, 1):
                    for pattern, method in console_patterns:
                        if re.search(pattern, line) and not line.strip().startswith('//'):
                            issues.append(QualityIssue(
                                severity=console_severity,
                                message=f"避免在生產代碼中使用 {method}",
                                line=i,
                                rule="no-console"
                            ))
        
        # 2. debugger 語句檢查
        if self.config.get("check_debugger", True):
            for i, line in enumerate(lines, 1):
                if 'debugger' in line and not line.strip().startswith('//'):
                    issues.append(QualityIssue(
                        severity="error",
                        message="移除 debugger 語句",
                        line=i,
                        rule="no-debugger",
                        fixable=True
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
        
        # 4. 變數命名檢查
        if self.config.get("check_naming", True):
            # 檢查 camelCase
            var_pattern = re.compile(r'\b(?:var|let|const)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)')
            for i, line in enumerate(lines, 1):
                matches = var_pattern.findall(line)
                for var_name in matches:
                    if '_' in var_name and not var_name.isupper():
                        issues.append(QualityIssue(
                            severity="info",
                            message=f"建議使用 camelCase 命名: {var_name}",
                            line=i,
                            rule="camel-case"
                        ))
        
        # 5. 函數複雜度檢查 (簡單版)
        if self.config.get("check_complexity", True):
            max_complexity = self.config.get("max_complexity", 10)
            function_pattern = re.compile(r'^\s*(?:function\s+\w+|const\s+\w+\s*=\s*(?:\([^)]*\)\s*=>|function))')
            
            current_function_start = None
            brace_count = 0
            complexity = 0
            
            for i, line in enumerate(lines, 1):
                if function_pattern.match(line):
                    current_function_start = i
                    brace_count = 0
                    complexity = 1  # 基礎複雜度
                
                if current_function_start:
                    # 計算複雜度
                    complexity += len(re.findall(r'\b(if|else if|while|for|switch|catch|&&|\|\|)\b', line))
                    
                    # 追蹤大括號
                    brace_count += line.count('{') - line.count('}')
                    
                    # 函數結束
                    if brace_count == 0 and '{' in lines[current_function_start - 1]:
                        if complexity > max_complexity:
                            issues.append(QualityIssue(
                                severity="warning",
                                message=f"函數複雜度過高 ({complexity}/{max_complexity})",
                                line=current_function_start,
                                rule="complexity"
                            ))
                        current_function_start = None
                        complexity = 0
        
        # 6. 安全性檢查
        if self.config.get("check_security", True):
            security_patterns = [
                (r'eval\s*\(', "避免使用 eval()"),
                (r'innerHTML\s*=', "注意 XSS 風險，考慮使用 textContent"),
                (r'document\.write\s*\(', "避免使用 document.write()"),
                (r'setTimeout\s*\(\s*["\']', "避免在 setTimeout 中使用字串")
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
        
        # 7. 效能檢查
        if self.config.get("check_performance", True):
            perf_patterns = [
                (r'document\.getElementById\s*\(.*\)\s*\.', "考慮快取 DOM 元素"),
                (r'for\s*\([^)]*\.length[^)]*\)', "將 length 快取到變數中"),
                (r'\+\s*["\'].*["\']', "考慮使用模板字串而非字串連接")
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
        
        return issues
    
    def _check_esmodule_usage(self, lines: List[str], file_path: str) -> List[QualityIssue]:
        """檢查 ES Module 使用情況"""
        issues = []
        has_import = False
        has_require = False
        has_module_exports = False
        has_exports = False
        
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # 檢查導入方式
            if re.search(r'^import\s+', line_stripped):
                has_import = True
            elif re.search(r'require\s*\(', line_stripped):
                has_require = True
            
            # 檢查導出方式
            if re.search(r'^export\s+', line_stripped) or re.search(r'export\s*{', line_stripped):
                has_exports = True
            elif re.search(r'module\.exports\s*=', line_stripped):
                has_module_exports = True
        
        # 混用檢查
        if has_import and has_require:
            issues.append(QualityIssue(
                severity="warning",
                message="混用 ES Module (import) 和 CommonJS (require)，建議統一使用 ES Module",
                rule="mixed-modules"
            ))
        
        if has_exports and has_module_exports:
            issues.append(QualityIssue(
                severity="warning", 
                message="混用 ES Module (export) 和 CommonJS (module.exports)，建議統一使用 ES Module",
                rule="mixed-exports"
            ))
        
        # 建議使用 ES Module
        if has_require and not has_import and self.config.get("prefer_esmodule", True):
            issues.append(QualityIssue(
                severity="info",
                message="建議使用 ES Module (import/export) 而非 CommonJS (require/module.exports)",
                rule="prefer-esmodule"
            ))
        
        return issues
    
    def _check_library_suggestions(self, content: str, lines: List[str], file_path: str) -> List[QualityIssue]:
        """檢查是否可以使用現成庫，避免重複造輪子"""
        issues = []
        
        # 常見功能模式和對應建議的庫
        library_suggestions = {
            # 工具函數
            r'function\s+cloneDeep|\.cloneDeep|function\s+clone\s*\(': {
                'library': 'lodash.clonedeep 或 structuredClone()',
                'message': '深拷貝功能建議使用 lodash.clonedeep 或原生 structuredClone()'
            },
            r'function\s+debounce|\.debounce': {
                'library': 'lodash.debounce',
                'message': '防抖功能建議使用 lodash.debounce'
            },
            r'function\s+throttle|\.throttle': {
                'library': 'lodash.throttle',
                'message': '節流功能建議使用 lodash.throttle'
            },
            r'function\s+isEmpty|\.isEmpty.*Object\.keys.*length': {
                'library': 'lodash.isempty',
                'message': '空值檢查建議使用 lodash.isempty'
            },
            
            # 日期處理
            r'new\s+Date\(.*\)\.(?:getFullYear|getMonth|getDate)': {
                'library': 'dayjs 或 date-fns',
                'message': '日期處理建議使用 dayjs 或 date-fns，避免原生 Date 的陷阱'
            },
            r'Date\.parse|Date\.now.*格式化': {
                'library': 'dayjs 或 date-fns',
                'message': '日期解析和格式化建議使用專業庫'
            },
            
            # HTTP 請求
            r'new\s+XMLHttpRequest|\.open\(.*GET|POST': {
                'library': 'fetch API 或 axios',
                'message': 'HTTP 請求建議使用 fetch API 或 axios'
            },
            r'fetch\(.*\)\.then.*\.json\(\)\.then': {
                'library': 'axios',
                'message': '複雜 HTTP 請求建議使用 axios，提供更好的錯誤處理'
            },
            
            # 字串處理
            r'function\s+capitalize|\.charAt\(0\)\.toUpperCase': {
                'library': 'lodash.capitalize',
                'message': '字串首字母大寫建議使用 lodash.capitalize'
            },
            r'function\s+camelCase|\.replace.*[_-]': {
                'library': 'lodash.camelcase',
                'message': '駝峰命名轉換建議使用 lodash.camelcase'
            },
            
            # DOM 操作
            r'document\.getElementById.*addEventListener': {
                'library': 'jQuery 或現代框架',
                'message': '複雜 DOM 操作建議使用 jQuery 或考慮使用現代框架'
            },
            r'document\.createElement.*appendChild': {
                'library': 'React/Vue/Svelte',
                'message': '動態 DOM 創建建議使用現代框架（React/Vue/Svelte）'
            },
            
            # 表單驗證
            r'function\s+validateEmail.*@.*\.': {
                'library': 'validator.js 或 yup',
                'message': '表單驗證建議使用 validator.js 或 yup'
            },
            r'function\s+validate.*required.*pattern': {
                'library': 'yup, joi, 或 zod',
                'message': '複雜表單驗證建議使用 yup, joi, 或 zod'
            },
            
            # UUID 生成
            r'function\s+generateId.*Math\.random': {
                'library': 'uuid',
                'message': 'UUID 生成建議使用 uuid 庫，避免衝突'
            },
            
            # 陣列處理
            r'for\s*\(.*\.length.*\).*push': {
                'library': 'lodash 或原生陣列方法',
                'message': '陣列處理建議使用 lodash 或原生方法（map, filter, reduce）'
            },
            
            # 格式化
            r'function\s+formatNumber.*toFixed': {
                'library': 'numeral.js',
                'message': '數字格式化建議使用 numeral.js'
            },
            r'function\s+formatCurrency': {
                'library': 'Intl.NumberFormat',
                'message': '貨幣格式化建議使用原生 Intl.NumberFormat'
            },
            
            # 顏色處理
            r'function\s+hexToRgb|rgbToHex': {
                'library': 'chroma.js 或 color',
                'message': '顏色轉換建議使用 chroma.js 或 color'
            },
            
            # 加密/哈希
            r'function\s+hash.*Math\.random|btoa': {
                'library': 'crypto-js',
                'message': '加密和哈希功能建議使用 crypto-js'
            },
            
            # 文件處理
            r'FileReader.*readAsText|readAsDataURL': {
                'library': '考慮使用 file-saver 或現代 File System API',
                'message': '文件處理建議使用專門庫或現代 API'
            },
            
            # 動畫
            r'setInterval.*animate|setTimeout.*animate': {
                'library': 'requestAnimationFrame 或動畫庫',
                'message': '動畫建議使用 requestAnimationFrame 或專門的動畫庫（如 GSAP）'
            },
            
            # 模板引擎
            r'function\s+template.*replace.*\{\{|\$\{': {
                'library': 'handlebars, mustache, 或模板字串',
                'message': '模板功能建議使用專門的模板引擎或 ES6 模板字串'
            }
        }
        
        # 檢查每個模式
        for i, line in enumerate(lines, 1):
            for pattern, suggestion in library_suggestions.items():
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(QualityIssue(
                        severity="info",
                        message=f"{suggestion['message']} ({suggestion['library']})",
                        line=i,
                        rule="use-library"
                    ))
        
        # 檢查重複實現的常見工具函數
        common_utils = [
            (r'function\s+isArray.*instanceof\s+Array', 'Array.isArray()'),
            (r'function\s+isObject.*typeof.*object', 'lodash.isobject'),
            (r'function\s+merge.*Object\.assign', 'lodash.merge 或 spread operator'),
            (r'function\s+pick.*keys.*reduce', 'lodash.pick'),
            (r'function\s+omit.*keys.*filter', 'lodash.omit'),
            (r'function\s+groupBy.*reduce.*push', 'lodash.groupby'),
            (r'function\s+sortBy.*sort.*\(a.*b\)', 'lodash.sortby'),
            (r'function\s+uniq.*filter.*indexOf', 'lodash.uniq 或 new Set()'),
            (r'function\s+flatten.*reduce.*concat', 'lodash.flatten 或 array.flat()'),
            (r'function\s+chunk.*for.*slice', 'lodash.chunk')
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, suggestion in common_utils:
                if re.search(pattern, line):
                    issues.append(QualityIssue(
                        severity="info",
                        message=f"避免重複實現，建議使用 {suggestion}",
                        line=i,
                        rule="avoid-reinvention"
                    ))
        
        return issues
    
    def _check_similar_functions(self, content: str, lines: List[str], file_path: str) -> List[QualityIssue]:
        """檢測相似的自定義函數，避免重複實現"""
        issues = []
        
        # 提取當前檔案中的函數
        current_functions = self._extract_functions(content, lines)
        if len(current_functions) < 2:
            return issues
        
        # 檢查當前檔案內的相似函數
        similar_pairs = self._find_similar_function_pairs(current_functions)
        for func1, func2, similarity in similar_pairs:
            issues.append(QualityIssue(
                severity="info",
                message=f"發現相似函數：{func1['name']} 和 {func2['name']} (相似度: {similarity:.1%})，考慮合併或重構",
                line=func1['line'],
                rule="similar-functions"
            ))
        
        # 檢查專案中其他檔案的相似函數
        if self.config.get("check_project_wide_similarity", True):
            project_similar_issues = self._check_project_wide_similarity(current_functions, file_path)
            issues.extend(project_similar_issues)
        
        return issues
    
    def _extract_functions(self, content: str, lines: List[str]) -> List[Dict]:
        """提取函數定義和特徵"""
        functions = []
        
        # 函數定義模式
        function_patterns = [
            # function declaration: function name() {}
            r'^\s*function\s+(\w+)\s*\([^)]*\)\s*\{',
            # function expression: const name = function() {}
            r'^\s*(?:const|let|var)\s+(\w+)\s*=\s*function\s*\([^)]*\)\s*\{',
            # arrow function: const name = () => {}
            r'^\s*(?:const|let|var)\s+(\w+)\s*=\s*\([^)]*\)\s*=>\s*\{',
            # arrow function single param: const name = param => {}
            r'^\s*(?:const|let|var)\s+(\w+)\s*=\s*\w+\s*=>\s*\{',
            # method definition: methodName() {}
            r'^\s*(\w+)\s*\([^)]*\)\s*\{',
            # object method: name: function() {}
            r'^\s*(\w+):\s*function\s*\([^)]*\)\s*\{',
            # object method shorthand: name() {}
            r'^\s*(\w+)\s*\([^)]*\)\s*\{',
        ]
        
        i = 0
        while i < len(lines):
            line = lines[i]
            for pattern in function_patterns:
                match = re.search(pattern, line)
                if match:
                    func_name = match.group(1)
                    func_start = i + 1
                    
                    # 提取函數體
                    func_body, func_end = self._extract_function_body(lines, i)
                    
                    if func_body:
                        # 分析函數特徵
                        features = self._analyze_function_features(func_name, func_body)
                        
                        functions.append({
                            'name': func_name,
                            'line': func_start,
                            'body': func_body,
                            'features': features,
                            'end_line': func_end
                        })
                    
                    i = func_end if func_end else i + 1
                    break
            else:
                i += 1
        
        return functions
    
    def _extract_function_body(self, lines: List[str], start_line: int) -> Tuple[str, int]:
        """提取函數體內容"""
        brace_count = 0
        func_lines = []
        found_opening = False
        
        for i in range(start_line, len(lines)):
            line = lines[i]
            
            # 計算大括號
            for char in line:
                if char == '{':
                    brace_count += 1
                    found_opening = True
                elif char == '}':
                    brace_count -= 1
            
            func_lines.append(line)
            
            # 函數結束
            if found_opening and brace_count == 0:
                return '\n'.join(func_lines), i + 1
        
        return '\n'.join(func_lines), len(lines)
    
    def _analyze_function_features(self, name: str, body: str) -> Dict:
        """分析函數特徵"""
        features = {
            'name': name,
            'length': len(body),
            'line_count': len(body.split('\n')),
            'keywords': set(),
            'patterns': set(),
            'api_calls': set(),
            'variables': set(),
            'control_structures': set()
        }
        
        # 清理函數體（移除註解和字串）
        cleaned_body = self._clean_function_body(body)
        
        # JavaScript 關鍵字
        js_keywords = ['if', 'else', 'for', 'while', 'return', 'try', 'catch', 'throw', 'switch', 'case']
        for keyword in js_keywords:
            if re.search(rf'\b{keyword}\b', cleaned_body):
                features['keywords'].add(keyword)
        
        # 常見模式
        patterns = {
            'array_iteration': r'\.(?:forEach|map|filter|reduce|find|some|every)',
            'promise_usage': r'\.then\(|\.catch\(|await\s+',
            'dom_manipulation': r'document\.|querySelector|getElementById',
            'event_handling': r'addEventListener|on\w+\s*=',
            'async_operations': r'setTimeout|setInterval|fetch\(',
            'object_operations': r'Object\.|JSON\.',
            'string_operations': r'\.(?:split|join|replace|match|trim)',
            'math_operations': r'Math\.|parseInt|parseFloat',
            'validation': r'if\s*\(.*(?:!|===|!==|<|>)',
            'loop_operations': r'for\s*\(|while\s*\(',
            'error_handling': r'try\s*\{|catch\s*\(',
            'type_checking': r'typeof\s+|instanceof\s+'
        }
        
        for pattern_name, pattern in patterns.items():
            if re.search(pattern, cleaned_body):
                features['patterns'].add(pattern_name)
        
        # API 調用
        api_matches = re.findall(r'\.(\w+)\(', cleaned_body)
        features['api_calls'] = set(api_matches[:10])  # 限制數量
        
        # 變數使用 (簡化版)
        var_matches = re.findall(r'\b(?:const|let|var)\s+(\w+)', cleaned_body)
        features['variables'] = set(var_matches[:10])  # 限制數量
        
        # 控制結構
        control_patterns = {
            'if_else': r'if\s*\(.*\)\s*\{.*\}\s*else',
            'switch_case': r'switch\s*\(.*\)\s*\{.*case',
            'for_loop': r'for\s*\(',
            'while_loop': r'while\s*\(',
            'try_catch': r'try\s*\{.*\}\s*catch'
        }
        
        for control_name, control_pattern in control_patterns.items():
            if re.search(control_pattern, cleaned_body, re.DOTALL):
                features['control_structures'].add(control_name)
        
        return features
    
    def _clean_function_body(self, body: str) -> str:
        """清理函數體，移除註解和字串常量"""
        # 移除單行註解
        body = re.sub(r'//.*$', '', body, flags=re.MULTILINE)
        # 移除多行註解
        body = re.sub(r'/\*.*?\*/', '', body, flags=re.DOTALL)
        # 移除字串常量（簡化版）
        body = re.sub(r'"[^"]*"', '""', body)
        body = re.sub(r"'[^']*'", "''", body)
        body = re.sub(r'`[^`]*`', '``', body)
        
        return body
    
    def _find_similar_function_pairs(self, functions: List[Dict]) -> List[Tuple]:
        """找到相似的函數對"""
        similar_pairs = []
        similarity_threshold = self.config.get("similarity_threshold", 0.7)
        
        for i, func1 in enumerate(functions):
            for func2 in functions[i+1:]:
                similarity = self._calculate_function_similarity(func1['features'], func2['features'])
                
                if similarity >= similarity_threshold:
                    similar_pairs.append((func1, func2, similarity))
        
        return similar_pairs
    
    def _calculate_function_similarity(self, features1: Dict, features2: Dict) -> float:
        """計算兩個函數的相似度"""
        weights = {
            'keywords': 0.2,
            'patterns': 0.3,
            'api_calls': 0.2,
            'control_structures': 0.2,
            'length_ratio': 0.1
        }
        
        similarity = 0.0
        
        # 關鍵字相似度
        keywords1 = features1['keywords']
        keywords2 = features2['keywords']
        if keywords1 or keywords2:
            keyword_sim = len(keywords1 & keywords2) / len(keywords1 | keywords2)
            similarity += weights['keywords'] * keyword_sim
        
        # 模式相似度
        patterns1 = features1['patterns']
        patterns2 = features2['patterns']
        if patterns1 or patterns2:
            pattern_sim = len(patterns1 & patterns2) / len(patterns1 | patterns2)
            similarity += weights['patterns'] * pattern_sim
        
        # API 調用相似度
        apis1 = features1['api_calls']
        apis2 = features2['api_calls']
        if apis1 or apis2:
            api_sim = len(apis1 & apis2) / len(apis1 | apis2)
            similarity += weights['api_calls'] * api_sim
        
        # 控制結構相似度
        controls1 = features1['control_structures']
        controls2 = features2['control_structures']
        if controls1 or controls2:
            control_sim = len(controls1 & controls2) / len(controls1 | controls2)
            similarity += weights['control_structures'] * control_sim
        
        # 長度比例相似度
        len1, len2 = features1['length'], features2['length']
        if len1 and len2:
            length_ratio = min(len1, len2) / max(len1, len2)
            similarity += weights['length_ratio'] * length_ratio
        
        return similarity
    
    def _check_project_wide_similarity(self, current_functions: List[Dict], current_file: str) -> List[QualityIssue]:
        """檢查專案範圍內的相似函數"""
        issues = []
        
        try:
            # 找到專案根目錄
            project_root = self._find_project_root(current_file)
            if not project_root:
                return issues
            
            # 掃描專案中的 JS/TS 檔案
            js_files = self._find_js_files(project_root, current_file)
            
            # 限制檢查檔案數量，避免效能問題
            max_files = self.config.get("max_similarity_check_files", 20)
            js_files = js_files[:max_files]
            
            for other_file in js_files:
                try:
                    with open(other_file, 'r', encoding='utf-8') as f:
                        other_content = f.read()
                        other_lines = other_content.splitlines()
                    
                    other_functions = self._extract_functions(other_content, other_lines)
                    
                    # 比較函數
                    for current_func in current_functions:
                        for other_func in other_functions:
                            similarity = self._calculate_function_similarity(
                                current_func['features'], 
                                other_func['features']
                            )
                            
                            threshold = self.config.get("project_similarity_threshold", 0.8)
                            if similarity >= threshold:
                                relative_path = Path(other_file).relative_to(Path(project_root))
                                issues.append(QualityIssue(
                                    severity="info",
                                    message=f"發現相似函數：{current_func['name']} 與 {relative_path}:{other_func['line']} 的 {other_func['name']} 相似 ({similarity:.1%})，考慮提取共用函數",
                                    line=current_func['line'],
                                    rule="project-similar-functions"
                                ))
                
                except Exception as e:
                    if self.debug:
                        print(f"檢查檔案 {other_file} 失敗: {e}")
                    continue
        
        except Exception as e:
            if self.debug:
                print(f"專案相似性檢查失敗: {e}")
        
        return issues
    
    def _find_project_root(self, file_path: str) -> Optional[str]:
        """找到專案根目錄"""
        current = Path(file_path).parent
        
        # 常見專案根目錄標識
        root_indicators = ['package.json', '.git', 'yarn.lock', 'pnpm-lock.yaml', 'node_modules']
        
        for _ in range(10):  # 最多向上找10層
            for indicator in root_indicators:
                if (current / indicator).exists():
                    return str(current)
            
            if current.parent == current:  # 到達根目錄
                break
            current = current.parent
        
        return None
    
    def _find_js_files(self, project_root: str, exclude_file: str) -> List[str]:
        """找到專案中的 JS/TS 檔案"""
        js_files = []
        project_path = Path(project_root)
        exclude_path = Path(exclude_file).resolve()
        
        # 忽略的目錄
        ignore_dirs = {'node_modules', '.git', 'dist', 'build', '.cache', 'coverage', '.next'}
        
        for ext in ['.js', '.ts', '.jsx', '.tsx']:
            for js_file in project_path.rglob(f'*{ext}'):
                if js_file.resolve() != exclude_path and not any(ignore_dir in js_file.parts for ignore_dir in ignore_dirs):
                    js_files.append(str(js_file))
        
        return js_files[:50]  # 限制檔案數量
    
    def _tool_available(self, tool: str) -> bool:
        """檢查工具是否可用"""
        try:
            if tool == "npx":
                subprocess.run([tool, "--version"], 
                             capture_output=True, 
                             check=True, 
                             timeout=10)
            else:
                subprocess.run([tool, "--version"], 
                             capture_output=True, 
                             check=True, 
                             timeout=10)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False