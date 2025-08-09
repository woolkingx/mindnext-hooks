"""
ActionPrompt - Prompt Processing Action Executor
"""

from typing import Dict, Any
from datetime import datetime
from .action_base import ActionExecutor, ActionResult
from ..event_layer import HookEvent

class ActionPrompt(ActionExecutor):
    """Prompt Processing Action Executor"""
    
    def get_action_type(self) -> str:
        return "action.prompt"
    
    def execute(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        """ExecutePrompt processingAction"""
        start_time = datetime.now()
        
        try:
            operation = parameters.get('operation', 'analyze')
            
            if operation == 'analyze':
                result = self._analyze_prompt(event, parameters)
            elif operation == 'enhance':
                result = self._enhance_prompt(event, parameters)
            elif operation == 'validate':
                result = self._validate_prompt(event, parameters)
            elif operation == 'extract_intent':
                result = self._extract_intent(event, parameters)
            else:
                return self._create_result(
                    action_id="action.prompt",
                    success=False,
                    execution_time=(datetime.now() - start_time).total_seconds(),
                    error=f"Unknown operation: {operation}"
                )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            return self._create_result(
                action_id="action.prompt",
                success=True,
                execution_time=execution_time,
                output=result
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return self._create_result(
                action_id="action.prompt",
                success=False,
                execution_time=execution_time,
                error=str(e)
            )
    
    def _analyze_prompt(self, event: HookEvent, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze prompt content"""
        prompt = event.user_prompt or ""
        
        analysis = {
            'length': len(prompt),
            'word_count': len(prompt.split()),
            'contains_code': self._contains_code_patterns(prompt),
            'complexity': self._estimate_prompt_complexity(prompt),
            'keywords': self._extract_technical_keywords(prompt),
            'intent': self._estimate_intent(prompt),
            'urgency': self._estimate_urgency(prompt),
            'scope': self._estimate_scope(prompt)
        }
        
        return analysis
    
    def _enhance_prompt(self, event: HookEvent, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """增強提示"""
        prompt = event.user_prompt or ""
        enhancement_type = parameters.get('type', 'clarity')
        
        enhancements = {
            'original_prompt': prompt,
            'enhancement_type': enhancement_type,
            'suggestions': []
        }
        
        if enhancement_type == 'clarity':
            enhancements['suggestions'] = self._generate_clarity_suggestions(prompt)
        elif enhancement_type == 'completeness':
            enhancements['suggestions'] = self._generate_completeness_suggestions(prompt)
        elif enhancement_type == 'technical':
            enhancements['suggestions'] = self._generate_technical_suggestions(prompt)
        
        return enhancements
    
    def _validate_prompt(self, event: HookEvent, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate提示"""
        prompt = event.user_prompt or ""
        
        validation = {
            'is_valid': True,
            'issues': [],
            'warnings': [],
            'score': 0
        }
        
        # Check基本問題
        if len(prompt) < 10:
            validation['issues'].append("提示過短，可能不夠具體")
            validation['is_valid'] = False
        
        if len(prompt) > 1000:
            validation['warnings'].append("提示過長，建議簡化")
        
        # Check模糊用詞
        vague_words = ['這個', '那個', '某些', '一些', '改一下', '修一下']
        if any(word in prompt for word in vague_words):
            validation['warnings'].append("包含模糊用詞，建議更具體")
        
        # 計算分數
        validation['score'] = self._calculate_prompt_score(prompt, validation)
        
        return validation
    
    def _extract_intent(self, event: HookEvent, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """提取意圖"""
        prompt = event.user_prompt or ""
        
        intent_analysis = {
            'primary_intent': self._estimate_intent(prompt),
            'secondary_intents': self._extract_secondary_intents(prompt),
            'confidence': self._calculate_intent_confidence(prompt),
            'action_verbs': self._extract_action_verbs(prompt),
            'target_objects': self._extract_target_objects(prompt)
        }
        
        return intent_analysis
    
    def _contains_code_patterns(self, prompt: str) -> bool:
        """Check是否包含代碼模式"""
        code_patterns = [
            '```', '`', 'function', 'class', 'def ', 'import ', 'const ', 'let ', 'var ',
            '{', '}', '()', '=>', 'return', 'if', 'for', 'while'
        ]
        return any(pattern in prompt.lower() for pattern in code_patterns)
    
    def _estimate_prompt_complexity(self, prompt: str) -> str:
        """估計提示複雜度"""
        word_count = len(prompt.split())
        technical_terms = len(self._extract_technical_keywords(prompt))
        
        if word_count < 10 and technical_terms < 2:
            return 'simple'
        elif word_count < 50 and technical_terms < 5:
            return 'medium'
        else:
            return 'complex'
    
    def _extract_technical_keywords(self, prompt: str) -> list:
        """提取技術關鍵字"""
        technical_terms = [
            'api', 'database', 'server', 'client', 'frontend', 'backend',
            'function', 'class', 'method', 'variable', 'array', 'object',
            'json', 'xml', 'http', 'https', 'rest', 'graphql',
            'react', 'vue', 'angular', 'node', 'python', 'javascript',
            'typescript', 'rust', 'go', 'java', 'c++', 'docker',
            'kubernetes', 'aws', 'azure', 'gcp', 'git', 'github'
        ]
        
        prompt_lower = prompt.lower()
        found_terms = [term for term in technical_terms if term in prompt_lower]
        return found_terms
    
    def _estimate_intent(self, prompt: str) -> str:
        """估計主要意圖"""
        prompt_lower = prompt.lower()
        
        intent_patterns = {
            'create': ['Create', 'create', '新增', 'add', '寫', 'write', '製作', 'make'],
            'modify': ['修改', 'modify', 'Update', 'update', '編輯', 'edit', '改', 'change'],
            'delete': ['Delete', 'delete', '移除', 'remove', '清除', 'clear'],
            'query': ['Query', 'query', '搜索', 'search', '找', 'find', '獲取', 'get'],
            'analyze': ['Analyze', 'analyze', 'Check', 'check', 'Validate', 'validate', 'Test', 'test'],
            'explain': ['解釋', 'explain', '說明', 'describe', '介紹', 'introduce'],
            'fix': ['修復', 'fix', '解決', 'solve', '調試', 'debug', '除錯'],
            'optimize': ['Optimize', 'optimize', '改善', 'improve', '提升', 'enhance']
        }
        
        for intent, patterns in intent_patterns.items():
            if any(pattern in prompt_lower for pattern in patterns):
                return intent
        
        return 'unknown'
    
    def _extract_secondary_intents(self, prompt: str) -> list:
        """提取次要意圖"""
        prompt_lower = prompt.lower()
        secondary_intents = []
        
        if any(word in prompt_lower for word in ['Test', 'test', 'Validate', 'validate']):
            secondary_intents.append('test')
        
        if any(word in prompt_lower for word in ['Record', 'record', 'Save', 'save']):
            secondary_intents.append('record')
        
        if any(word in prompt_lower for word in ['分享', 'share', '發布', 'publish']):
            secondary_intents.append('share')
        
        return secondary_intents
    
    def _calculate_intent_confidence(self, prompt: str) -> float:
        """計算意圖信心度"""
        # 基於關鍵字密度和明確性計算
        word_count = len(prompt.split())
        technical_terms = len(self._extract_technical_keywords(prompt))
        
        # 基礎信心度
        confidence = 0.5
        
        # 技術詞彙增加信心度
        confidence += min(technical_terms * 0.1, 0.3)
        
        # 長度適中增加信心度
        if 20 <= word_count <= 100:
            confidence += 0.1
        
        # 包含具體動詞增加信心度
        action_verbs = self._extract_action_verbs(prompt)
        confidence += min(len(action_verbs) * 0.05, 0.1)
        
        return min(confidence, 1.0)
    
    def _extract_action_verbs(self, prompt: str) -> list:
        """提取Action動詞"""
        action_verbs = [
            'Create', 'Create', '新增', '添加', '寫', '製作',
            '修改', 'Update', '編輯', '改變', '調整',
            'Delete', '移除', '清除', '去除',
            'Query', '搜索', '找', '獲取', '讀取',
            'Analyze', 'Check', 'Validate', 'Test', 'Evaluate',
            '解釋', '說明', '描述', '介紹',
            '修復', '解決', '調試', '除錯',
            'Optimize', '改善', '提升', '增強'
        ]
        
        prompt_lower = prompt.lower()
        found_verbs = [verb for verb in action_verbs if verb in prompt_lower]
        return found_verbs
    
    def _extract_target_objects(self, prompt: str) -> list:
        """提取目標對象"""
        target_objects = [
            'file', 'function', 'class', 'method', 'variable',
            'database', 'table', 'record', 'field',
            'server', 'client', 'api', 'endpoint',
            'component', 'module', 'package', 'library',
            'config', 'setting', 'parameter', 'option'
        ]
        
        prompt_lower = prompt.lower()
        found_objects = [obj for obj in target_objects if obj in prompt_lower]
        return found_objects
    
    def _generate_clarity_suggestions(self, prompt: str) -> list:
        """Generate清晰度建議"""
        suggestions = []
        
        if len(prompt.split()) < 5:
            suggestions.append("建議提供更多具體細節")
        
        if '這個' in prompt or '那個' in prompt:
            suggestions.append("避免使用模糊指代詞，請具體說明")
        
        if not any(verb in prompt.lower() for verb in ['Create', '修改', 'Delete', 'Query']):
            suggestions.append("明確說明要Execute什麼Action")
        
        return suggestions
    
    def _generate_completeness_suggestions(self, prompt: str) -> list:
        """Generate完整性建議"""
        suggestions = []
        
        if 'File' in prompt and not any(ext in prompt for ext in ['.py', '.js', '.json', '.txt']):
            suggestions.append("建議指定FileType或副檔名")
        
        if '修改' in prompt and '原因' not in prompt and '為什麼' not in prompt:
            suggestions.append("建議說明修改的原因或目的")
        
        return suggestions
    
    def _generate_technical_suggestions(self, prompt: str) -> list:
        """Generate技術建議"""
        suggestions = []
        
        if self._contains_code_patterns(prompt):
            suggestions.append("包含代碼片段，建議使用適當的Format化")
        
        technical_count = len(self._extract_technical_keywords(prompt))
        if technical_count > 5:
            suggestions.append("技術詞彙較多，建議分步驟Execute")
        
        return suggestions
    
    def _calculate_prompt_score(self, prompt: str, validation: Dict[str, Any]) -> int:
        """計算提示分數 (0-100)"""
        score = 100
        
        # 根據問題和Warning扣分
        score -= len(validation['issues']) * 20
        score -= len(validation['warnings']) * 5
        
        # 根據長度調整
        word_count = len(prompt.split())
        if word_count < 5:
            score -= 10
        elif word_count > 200:
            score -= 5
        
        # 根據具體性調整
        if any(word in prompt for word in ['這個', '那個', '某些']):
            score -= 10
        
        # 根據技術詞彙調整
        technical_terms = len(self._extract_technical_keywords(prompt))
        if technical_terms > 0:
            score += min(technical_terms * 2, 10)
        
        return max(0, min(100, score))
    
    def _estimate_urgency(self, prompt: str) -> str:
        """Estimate prompt urgency level"""
        urgency_indicators = {
            'high': ['urgent', 'asap', 'immediately', 'critical', 'emergency'],
            'medium': ['soon', 'quickly', 'fast'],
            'low': ['when possible', 'eventually']
        }
        
        prompt_lower = prompt.lower()
        
        for level, indicators in urgency_indicators.items():
            if any(indicator in prompt_lower for indicator in indicators):
                return level
                
        return 'normal'
    
    def _estimate_scope(self, prompt: str) -> str:
        """Estimate prompt scope"""
        scope_indicators = {
            'large': ['entire project', 'all files', 'system', 'architecture'],
            'medium': ['multiple files', 'several', 'batch'],
            'small': ['single file', 'one', 'specific']
        }
        
        prompt_lower = prompt.lower()
        
        for scope, indicators in scope_indicators.items():
            if any(indicator in prompt_lower for indicator in indicators):
                return scope
                
        return 'medium'