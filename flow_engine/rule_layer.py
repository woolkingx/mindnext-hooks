"""
規則層 - 負責規則匹配和條件判斷
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime
import re
from pathlib import Path
from .event_layer import HookEvent

@dataclass
class RuleCondition:
    """規則條件"""
    expression: str                    # 條件表達式
    condition_type: str = "simple"     # simple, regex, function, composite
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Rule:
    """規則定義"""
    id: str
    name: str
    conditions: List[RuleCondition]
    actions: List[str]                 # 要Execute的ActionID列表
    
    # 規則屬性
    priority: int = 100
    enabled: bool = True
    event_types: List[str] = field(default_factory=list)  # 適用的Event type
    
    # Execute控制
    block_on_fail: bool = False        # Failed時是否阻止後續Process
    async_execution: bool = False      # 是否異步Execute
    cooldown_seconds: int = 0          # 冷卻Time
    
    # 規則統計
    triggered_count: int = 0
    last_triggered: Optional[datetime] = None
    
    # 條件限制
    file_patterns: List[str] = field(default_factory=list)  # File path模式
    exclude_patterns: List[str] = field(default_factory=list)
    
    metadata: Dict[str, Any] = field(default_factory=dict)

class RuleEngine:
    """Rule Engine - 負責規則的Load、匹配和Execute決策"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.rules: Dict[str, Rule] = {}
        self.custom_functions: Dict[str, Callable] = {}
        self.session_state: Dict[str, Any] = {}
        
        if config_path:
            self.load_rules_from_config(config_path)
        
        self._register_builtin_functions()
    
    def _register_builtin_functions(self):
        """註冊內建條件函數"""
        self.custom_functions.update({
            'contains': self._func_contains,
            'matches': self._func_matches,
            'file_extension': self._func_file_extension,
            'file_size_gt': self._func_file_size_gt,
            'code_complexity': self._func_code_complexity,
            'has_keyword': self._func_has_keyword,
            'is_test_file': self._func_is_test_file,
            'session_count': self._func_session_count,
            'recent_pattern': self._func_recent_pattern,
            'time_since_last': self._func_time_since_last
        })
    
    def load_rules_from_config(self, config_path: str):
        """從ConfigurationFileLoad規則"""
        import json
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            for rule_data in config.get('rules', []):
                rule = self._parse_rule_config(rule_data)
                self.rules[rule.id] = rule
                
        except Exception as e:
            print(f"Load規則ConfigurationFailed: {e}")
    
    def _parse_rule_config(self, rule_data: Dict[str, Any]) -> Rule:
        """解析規則Configuration"""
        conditions = []
        for cond_data in rule_data.get('conditions', []):
            condition = RuleCondition(
                expression=cond_data['expression'],
                condition_type=cond_data.get('type', 'simple'),
                metadata=cond_data.get('metadata', {})
            )
            conditions.append(condition)
        
        rule = Rule(
            id=rule_data['id'],
            name=rule_data['name'],
            conditions=conditions,
            actions=rule_data.get('actions', []),
            priority=rule_data.get('priority', 100),
            enabled=rule_data.get('enabled', True),
            event_types=rule_data.get('event_types', []),
            block_on_fail=rule_data.get('block_on_fail', False),
            async_execution=rule_data.get('async_execution', False),
            cooldown_seconds=rule_data.get('cooldown_seconds', 0),
            file_patterns=rule_data.get('file_patterns', []),
            exclude_patterns=rule_data.get('exclude_patterns', []),
            metadata=rule_data.get('metadata', {})
        )
        
        return rule
    
    def add_rule(self, rule: Rule):
        """動態添加規則"""
        self.rules[rule.id] = rule
    
    def remove_rule(self, rule_id: str):
        """移除規則"""
        if rule_id in self.rules:
            del self.rules[rule_id]
    
    def enable_rule(self, rule_id: str):
        """啟用規則"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
    
    def disable_rule(self, rule_id: str):
        """禁用規則"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
    
    def match_rules(self, event: HookEvent) -> List[Rule]:
        """匹配適用於Event的規則"""
        matched_rules = []
        
        for rule in self.rules.values():
            if self._should_rule_apply(rule, event):
                if self._evaluate_rule_conditions(rule, event):
                    # Update規則統計
                    rule.triggered_count += 1
                    rule.last_triggered = datetime.now()
                    matched_rules.append(rule)
        
        # 按優先級排序
        matched_rules.sort(key=lambda r: r.priority)
        return matched_rules
    
    def _should_rule_apply(self, rule: Rule, event: HookEvent) -> bool:
        """判斷規則是否應該應用於Event"""
        # Check規則是否啟用
        if not rule.enabled:
            return False
        
        # CheckEvent type
        if rule.event_types and event.event_type not in rule.event_types:
            return False
        
        # Check冷卻Time
        if rule.cooldown_seconds > 0 and rule.last_triggered:
            time_since_last = (datetime.now() - rule.last_triggered).total_seconds()
            if time_since_last < rule.cooldown_seconds:
                return False
        
        # CheckFile path模式
        if rule.file_patterns and event.file_paths:
            file_match = False
            for file_path in event.file_paths:
                if any(self._match_pattern(file_path, pattern) for pattern in rule.file_patterns):
                    file_match = True
                    break
            if not file_match:
                return False
        
        # Check排除模式
        if rule.exclude_patterns and event.file_paths:
            for file_path in event.file_paths:
                if any(self._match_pattern(file_path, pattern) for pattern in rule.exclude_patterns):
                    return False
        
        return True
    
    def _match_pattern(self, text: str, pattern: str) -> bool:
        """匹配Path模式"""
        try:
            # 支持 glob 風格的模式匹配
            import fnmatch
            return fnmatch.fnmatch(text, pattern)
        except:
            return pattern in text
    
    def _evaluate_rule_conditions(self, rule: Rule, event: HookEvent) -> bool:
        """Evaluate規則條件"""
        if not rule.conditions:
            return True
        
        # 所有條件都必須滿足 (AND 邏輯)
        for condition in rule.conditions:
            if not self._evaluate_single_condition(condition, event):
                return False
        
        return True
    
    def _evaluate_single_condition(self, condition: RuleCondition, event: HookEvent) -> bool:
        """Evaluate單個條件"""
        try:
            if condition.condition_type == "simple":
                return self._evaluate_simple_condition(condition.expression, event)
            elif condition.condition_type == "regex":
                return self._evaluate_regex_condition(condition.expression, event)
            elif condition.condition_type == "function":
                return self._evaluate_function_condition(condition.expression, event)
            elif condition.condition_type == "composite":
                return self._evaluate_composite_condition(condition.expression, event)
            else:
                return False
        except Exception as e:
            print(f"條件EvaluateFailed: {condition.expression}, Error: {e}")
            return False
    
    def _evaluate_simple_condition(self, expression: str, event: HookEvent) -> bool:
        """Evaluate簡單條件"""
        # CreateEvaluate上下文
        context = {
            'event_type': event.event_type,
            'tool_name': event.tool_name or '',
            'file_paths': event.file_paths,
            'content': event.content or '',
            'user_prompt': event.user_prompt or '',
            'metadata': event.metadata,
            'session': self.session_state
        }
        
        # 替換內建函數調用
        for func_name, func in self.custom_functions.items():
            if f'{func_name}(' in expression:
                # 簡化的函數調用Process
                pattern = rf'{func_name}\(([^)]*)\)'
                matches = re.findall(pattern, expression)
                for match in matches:
                    try:
                        args = [arg.strip().strip('"\'') for arg in match.split(',') if arg.strip()]
                        result = func(event, *args)
                        expression = expression.replace(f'{func_name}({match})', str(result))
                    except:
                        return False
        
        # Evaluate表達式
        try:
            # 安全的表達式Evaluate (限制可用的命名空間)
            allowed_names = {
                'event_type': context['event_type'],
                'tool_name': context['tool_name'],
                'file_paths': context['file_paths'],
                'content': context['content'],
                'user_prompt': context['user_prompt'],
                'True': True,
                'False': False,
                'len': len,
                'any': any,
                'all': all,
                'in': lambda x, y: x in y,
                'not': lambda x: not x
            }
            
            return eval(expression, {"__builtins__": {}}, allowed_names)
        except:
            return False
    
    def _evaluate_regex_condition(self, expression: str, event: HookEvent) -> bool:
        """Evaluate正則表達式條件"""
        # 從 metadata 中提取目標文本
        target_text = ""
        if event.user_prompt:
            target_text += event.user_prompt + " "
        if event.content:
            target_text += event.content + " "
        
        return bool(re.search(expression, target_text, re.IGNORECASE))
    
    def _evaluate_function_condition(self, expression: str, event: HookEvent) -> bool:
        """Evaluate函數條件"""
        # 函數條件Format: function_name(args)
        match = re.match(r'(\w+)\((.*)\)', expression)
        if not match:
            return False
        
        func_name, args_str = match.groups()
        if func_name not in self.custom_functions:
            return False
        
        args = [arg.strip().strip('"\'') for arg in args_str.split(',') if arg.strip()]
        return self.custom_functions[func_name](event, *args)
    
    def _evaluate_composite_condition(self, expression: str, event: HookEvent) -> bool:
        """Evaluate複合條件 (支持 AND, OR, NOT)"""
        # 簡化的複合條件解析
        expression = expression.replace(' AND ', ' and ').replace(' OR ', ' or ').replace(' NOT ', ' not ')
        
        # 遞歸Evaluate子條件
        return self._evaluate_simple_condition(expression, event)
    
    # 內建條件函數
    def _func_contains(self, event: HookEvent, keyword: str) -> bool:
        """Check是否包含關鍵字"""
        text = f"{event.user_prompt or ''} {event.content or ''}".lower()
        return keyword.lower() in text
    
    def _func_matches(self, event: HookEvent, pattern: str) -> bool:
        """Check是否匹配正則表達式"""
        text = f"{event.user_prompt or ''} {event.content or ''}"
        return bool(re.search(pattern, text, re.IGNORECASE))
    
    def _func_file_extension(self, event: HookEvent, *extensions: str) -> bool:
        """CheckFile副檔名"""
        for file_path in event.file_paths:
            ext = Path(file_path).suffix.lower()
            if ext in extensions:
                return True
        return False
    
    def _func_file_size_gt(self, event: HookEvent, size_str: str) -> bool:
        """CheckFileSize大於指定值"""
        try:
            size_limit = int(size_str)
            for file_path in event.file_paths:
                if Path(file_path).stat().st_size > size_limit:
                    return True
            return False
        except:
            return False
    
    def _func_code_complexity(self, event: HookEvent, threshold_str: str) -> bool:
        """Check代碼複雜度"""
        try:
            threshold = float(threshold_str)
            complexity = event.metadata.get('estimated_complexity', 'simple')
            complexity_values = {'simple': 1, 'medium': 2, 'complex': 3}
            return complexity_values.get(complexity, 1) >= threshold
        except:
            return False
    
    def _func_has_keyword(self, event: HookEvent, keyword: str) -> bool:
        """Check是否包含特定關鍵字"""
        keywords = event.metadata.get('contains_keywords', [])
        return keyword in keywords
    
    def _func_is_test_file(self, event: HookEvent) -> bool:
        """Check是否為TestFile"""
        test_patterns = ['/test/', '/tests/', '.test.', '.spec.', '_test.', '_spec.']
        return any(pattern in fp.lower() for fp in event.file_paths for pattern in test_patterns)
    
    def _func_session_count(self, event: HookEvent, event_type: str, count_str: str) -> bool:
        """CheckSession中特定Event的計數"""
        try:
            target_count = int(count_str)
            current_count = self.session_state.get(f'count_{event_type}', 0)
            return current_count >= target_count
        except:
            return False
    
    def _func_recent_pattern(self, event: HookEvent, pattern: str, count_str: str) -> bool:
        """Check最近Event中的模式"""
        try:
            count = int(count_str)
            recent_events = self.session_state.get('recent_events', [])[-count:]
            return any(pattern in str(event_data) for event_data in recent_events)
        except:
            return False
    
    def _func_time_since_last(self, event: HookEvent, event_type: str, seconds_str: str) -> bool:
        """Check距離上次Event的Time"""
        try:
            seconds_threshold = int(seconds_str)
            last_time_key = f'last_{event_type}_time'
            last_time = self.session_state.get(last_time_key)
            
            if last_time is None:
                return True  # 沒有Record時返回 True
            
            time_diff = (datetime.now() - last_time).total_seconds()
            return time_diff >= seconds_threshold
        except:
            return False
    
    def update_session_state(self, key: str, value: Any):
        """UpdateSessionStatus"""
        self.session_state[key] = value
    
    def get_rule_statistics(self) -> Dict[str, Any]:
        """獲取規則統計Information"""
        stats = {}
        for rule_id, rule in self.rules.items():
            stats[rule_id] = {
                'name': rule.name,
                'triggered_count': rule.triggered_count,
                'last_triggered': rule.last_triggered.isoformat() if rule.last_triggered else None,
                'enabled': rule.enabled,
                'priority': rule.priority
            }
        return stats