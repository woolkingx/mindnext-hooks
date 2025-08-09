"""
ActionAI - AI 相關動作執行器
"""

from typing import Dict, Any, List
from datetime import datetime
import json
from pathlib import Path

from .action_base import ActionExecutor, ActionResult
from ..event_layer import HookEvent

class ActionAI(ActionExecutor):
    """AI 相關動作執行器"""
    
    def get_action_type(self) -> str:
        return "action.ai"
    
    def execute(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        """執行 AI 動作"""
        start_time = datetime.now()
        
        try:
            operation = parameters.get('operation', 'analyze')
            
            if operation == 'analyze_code':
                result = self._analyze_code(event, parameters)
            elif operation == 'generate_suggestions':
                result = self._generate_suggestions(event, parameters)
            elif operation == 'detect_patterns':
                result = self._detect_patterns(event, parameters)
            elif operation == 'estimate_effort':
                result = self._estimate_effort(event, parameters)
            elif operation == 'generate_tests':
                result = self._generate_tests(event, parameters)
            elif operation == 'code_review':
                result = self._code_review(event, parameters)
            else:
                return self._create_result(
                    action_id="action.ai",
                    success=False,
                    execution_time=(datetime.now() - start_time).total_seconds(),
                    error=f"未知操作: {operation}"
                )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            return self._create_result(
                action_id="action.ai",
                success=True,
                execution_time=execution_time,
                output=result
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return self._create_result(
                action_id="action.ai",
                success=False,
                execution_time=execution_time,
                error=str(e)
            )
    
    def _analyze_code(self, event: HookEvent, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """分析代碼"""
        analysis = {
            'files_analyzed': [],
            'summary': {},
            'insights': [],
            'recommendations': []
        }
        
        for file_path in event.file_paths:
            file_analysis = self._analyze_single_file(file_path)
            analysis['files_analyzed'].append(file_analysis)
        
        # 生成總結
        analysis['summary'] = self._generate_code_summary(analysis['files_analyzed'])
        
        # 生成洞察
        analysis['insights'] = self._generate_code_insights(analysis['files_analyzed'])
        
        # 生成建議
        analysis['recommendations'] = self._generate_code_recommendations(analysis['files_analyzed'])
        
        return analysis
    
    def _analyze_single_file(self, file_path: str) -> Dict[str, Any]:
        """分析單個文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
            except:
                return {'file': file_path, 'error': '無法讀取文件'}
        
        file_ext = Path(file_path).suffix.lower()
        
        analysis = {
            'file': file_path,
            'extension': file_ext,
            'size': len(content),
            'lines': len(content.splitlines()),
            'language': self._detect_language(file_ext),
            'complexity': self._estimate_code_complexity(content, file_ext),
            'patterns': self._detect_code_patterns(content, file_ext),
            'issues': self._detect_code_issues(content, file_ext),
            'structure': self._analyze_code_structure(content, file_ext)
        }
        
        return analysis
    
    def _detect_language(self, file_ext: str) -> str:
        """檢測程式語言"""
        language_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.jsx': 'JavaScript',
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript',
            '.rs': 'Rust',
            '.go': 'Go',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.swift': 'Swift',
            '.kt': 'Kotlin'
        }
        return language_map.get(file_ext, 'Unknown')
    
    def _estimate_code_complexity(self, content: str, file_ext: str) -> Dict[str, Any]:
        """估計代碼複雜度"""
        lines = content.splitlines()
        non_empty_lines = [line for line in lines if line.strip()]
        
        complexity = {
            'total_lines': len(lines),
            'code_lines': len(non_empty_lines),
            'comment_lines': 0,
            'blank_lines': len(lines) - len(non_empty_lines),
            'cyclomatic_complexity': 1,
            'nesting_depth': 0,
            'function_count': 0,
            'class_count': 0
        }
        
        # 計算註解行數
        comment_patterns = {
            '.py': ['#'],
            '.js': ['//', '/*'],
            '.jsx': ['//', '/*'],
            '.ts': ['//', '/*'],
            '.tsx': ['//', '/*'],
            '.rs': ['//'],
            '.go': ['//'],
            '.java': ['//', '/*'],
            '.cpp': ['//', '/*'],
            '.c': ['//', '/*']
        }
        
        patterns = comment_patterns.get(file_ext, ['#', '//'])
        for line in lines:
            stripped = line.strip()
            if any(stripped.startswith(pattern) for pattern in patterns):
                complexity['comment_lines'] += 1
        
        # 計算循環複雜度和嵌套深度
        for line in non_empty_lines:
            stripped = line.strip().lower()
            
            # 分支語句增加複雜度
            if any(keyword in stripped for keyword in ['if', 'while', 'for', 'case', 'catch']):
                complexity['cyclomatic_complexity'] += 1
            
            # 計算嵌套深度
            indent_level = len(line) - len(line.lstrip())
            if indent_level > complexity['nesting_depth']:
                complexity['nesting_depth'] = indent_level
            
            # 計算函數和類數量
            if 'def ' in stripped or 'function ' in stripped:
                complexity['function_count'] += 1
            if 'class ' in stripped:
                complexity['class_count'] += 1
        
        return complexity
    
    def _detect_code_patterns(self, content: str, file_ext: str) -> List[str]:
        """檢測代碼模式"""
        patterns = []
        content_lower = content.lower()
        
        # 通用模式
        if 'singleton' in content_lower:
            patterns.append('Singleton Pattern')
        if 'factory' in content_lower:
            patterns.append('Factory Pattern')
        if 'observer' in content_lower:
            patterns.append('Observer Pattern')
        if 'decorator' in content_lower:
            patterns.append('Decorator Pattern')
        
        # 架構模式
        if 'mvc' in content_lower or ('model' in content_lower and 'view' in content_lower):
            patterns.append('MVC Pattern')
        if 'middleware' in content_lower:
            patterns.append('Middleware Pattern')
        if 'repository' in content_lower:
            patterns.append('Repository Pattern')
        
        # 並發模式
        if 'async' in content_lower or 'await' in content_lower:
            patterns.append('Async/Await Pattern')
        if 'promise' in content_lower:
            patterns.append('Promise Pattern')
        if 'thread' in content_lower or 'mutex' in content_lower:
            patterns.append('Threading Pattern')
        
        return patterns
    
    def _detect_code_issues(self, content: str, file_ext: str) -> List[Dict[str, str]]:
        """檢測代碼問題"""
        issues = []
        lines = content.splitlines()
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip().lower()
            
            # 通用問題
            if 'todo' in stripped or 'fixme' in stripped:
                issues.append({
                    'line': i,
                    'type': 'todo',
                    'message': 'TODO 或 FIXME 註解',
                    'severity': 'info'
                })
            
            if len(line) > 120:
                issues.append({
                    'line': i,
                    'type': 'line_length',
                    'message': '行過長 (>120 字符)',
                    'severity': 'warning'
                })
            
            # 語言特定問題
            if file_ext in ['.py']:
                if 'print(' in stripped:
                    issues.append({
                        'line': i,
                        'type': 'debug_code',
                        'message': 'Debug print 語句',
                        'severity': 'info'
                    })
            
            if file_ext in ['.js', '.jsx', '.ts', '.tsx']:
                if 'console.log(' in stripped:
                    issues.append({
                        'line': i,
                        'type': 'debug_code',
                        'message': 'Console.log 語句',
                        'severity': 'info'
                    })
                if 'debugger' in stripped:
                    issues.append({
                        'line': i,
                        'type': 'debug_code',
                        'message': 'Debugger 語句',
                        'severity': 'warning'
                    })
        
        return issues
    
    def _analyze_code_structure(self, content: str, file_ext: str) -> Dict[str, Any]:
        """分析代碼結構"""
        structure = {
            'imports': [],
            'functions': [],
            'classes': [],
            'exports': [],
            'dependencies': []
        }
        
        lines = content.splitlines()
        
        for line in lines:
            stripped = line.strip()
            
            # 分析導入語句
            if stripped.startswith('import ') or stripped.startswith('from '):
                structure['imports'].append(stripped)
            elif stripped.startswith('const ') and 'require(' in stripped:
                structure['imports'].append(stripped)
            
            # 分析函數定義
            if stripped.startswith('def ') or stripped.startswith('function '):
                structure['functions'].append(stripped)
            elif 'function(' in stripped or '=>' in stripped:
                structure['functions'].append(stripped)
            
            # 分析類定義
            if stripped.startswith('class '):
                structure['classes'].append(stripped)
            
            # 分析導出語句
            if stripped.startswith('export ') or stripped.startswith('module.exports'):
                structure['exports'].append(stripped)
        
        return structure
    
    def _generate_code_summary(self, files_analyzed: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成代碼總結"""
        total_lines = sum(f.get('lines', 0) for f in files_analyzed if 'lines' in f)
        total_files = len(files_analyzed)
        
        languages = {}
        for file_analysis in files_analyzed:
            lang = file_analysis.get('language', 'Unknown')
            languages[lang] = languages.get(lang, 0) + 1
        
        return {
            'total_files': total_files,
            'total_lines': total_lines,
            'languages': languages,
            'average_lines_per_file': total_lines / total_files if total_files > 0 else 0
        }
    
    def _generate_code_insights(self, files_analyzed: List[Dict[str, Any]]) -> List[str]:
        """生成代碼洞察"""
        insights = []
        
        # 複雜度洞察
        high_complexity_files = [f for f in files_analyzed 
                               if f.get('complexity', {}).get('cyclomatic_complexity', 0) > 10]
        if high_complexity_files:
            insights.append(f"發現 {len(high_complexity_files)} 個高複雜度文件，建議重構")
        
        # 模式洞察
        all_patterns = []
        for f in files_analyzed:
            all_patterns.extend(f.get('patterns', []))
        
        if 'Async/Await Pattern' in all_patterns:
            insights.append("代碼使用現代異步模式，結構良好")
        
        # 問題洞察
        all_issues = []
        for f in files_analyzed:
            all_issues.extend(f.get('issues', []))
        
        todo_count = len([i for i in all_issues if i.get('type') == 'todo'])
        if todo_count > 5:
            insights.append(f"發現 {todo_count} 個 TODO 項目，建議優先處理")
        
        return insights
    
    def _generate_code_recommendations(self, files_analyzed: List[Dict[str, Any]]) -> List[str]:
        """生成代碼建議"""
        recommendations = []
        
        # 基於複雜度的建議
        for f in files_analyzed:
            complexity = f.get('complexity', {})
            if complexity.get('function_count', 0) == 0 and complexity.get('lines', 0) > 50:
                recommendations.append(f"文件 {f.get('file')} 缺少函數結構，建議模組化")
        
        # 基於問題的建議
        for f in files_analyzed:
            issues = f.get('issues', [])
            debug_issues = [i for i in issues if i.get('type') == 'debug_code']
            if debug_issues:
                recommendations.append(f"文件 {f.get('file')} 包含調試代碼，建議清理")
        
        return recommendations
    
    def _generate_suggestions(self, event: HookEvent, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """生成改進建議"""
        suggestion_type = parameters.get('type', 'general')
        
        suggestions = {
            'type': suggestion_type,
            'suggestions': [],
            'priority': 'medium'
        }
        
        if suggestion_type == 'performance':
            suggestions['suggestions'] = [
                "考慮使用緩存機制提升性能",
                "檢查是否有不必要的循環或遞歸",
                "優化數據結構的使用"
            ]
        elif suggestion_type == 'security':
            suggestions['suggestions'] = [
                "驗證所有用戶輸入",
                "使用參數化查詢防止 SQL 注入",
                "實施適當的身份驗證和授權"
            ]
        elif suggestion_type == 'maintainability':
            suggestions['suggestions'] = [
                "增加代碼註解和文檔",
                "提取重複代碼到公共函數",
                "使用一致的命名約定"
            ]
        
        return suggestions
    
    def _detect_patterns(self, event: HookEvent, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """檢測模式"""
        return {
            'detected_patterns': [],
            'anti_patterns': [],
            'recommendations': []
        }
    
    def _estimate_effort(self, event: HookEvent, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """估計工作量"""
        total_lines = 0
        for file_path in event.file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    total_lines += len(f.readlines())
            except:
                continue
        
        # 簡單的工作量估計
        estimated_hours = max(1, total_lines / 100)  # 假設每100行需要1小時
        
        return {
            'total_lines': total_lines,
            'estimated_hours': estimated_hours,
            'confidence': 'medium',
            'factors': ['代碼複雜度', '需求明確度', '技術難度']
        }
    
    def _generate_tests(self, event: HookEvent, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """生成測試建議"""
        return {
            'test_suggestions': [
                "為核心業務邏輯編寫單元測試",
                "添加集成測試驗證組件交互",
                "實施端到端測試覆蓋用戶流程"
            ],
            'coverage_recommendations': "建議達到 80% 以上的代碼覆蓋率",
            'testing_framework': "根據項目選擇合適的測試框架"
        }
    
    def _code_review(self, event: HookEvent, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """代碼審查"""
        review = {
            'overall_rating': 'good',
            'strengths': [],
            'weaknesses': [],
            'action_items': []
        }
        
        # 基於代碼分析結果進行審查
        code_analysis = self._analyze_code(event, parameters)
        
        # 評估優點
        if code_analysis['summary'].get('total_files', 0) > 0:
            review['strengths'].append("代碼結構組織合理")
        
        # 評估缺點
        total_issues = sum(len(f.get('issues', [])) for f in code_analysis['files_analyzed'])
        if total_issues > 10:
            review['weaknesses'].append(f"發現 {total_issues} 個代碼問題")
        
        # 行動項目
        if review['weaknesses']:
            review['action_items'].append("優先處理發現的代碼問題")
        
        return review