"""
Rule Layer - Responsible for rule matching and condition evaluation
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime
import re
from pathlib import Path
from .event_layer import HookEvent

# Supported rule types
SUPPORTED_RULE_TYPES = {
    'simple',     # Simple condition matching
    'regex',      # Regular expression matching
    'keyword',    # Keyword matching
    'function',   # Function-based evaluation
    'composite'   # Composite conditions
}

@dataclass
class RuleCondition:
    """Rule condition definition"""
    expression: str                    # Condition expression
    condition_type: str = "simple"     # simple, regex, function, composite
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Rule:
    """Rule definition"""
    id: str
    name: str
    conditions: List[RuleCondition]
    actions: List[str]                 # List of ActionIDs to execute
    
    # Rule properties
    priority: int = 100
    enabled: bool = True
    event_types: List[str] = field(default_factory=list)  # Applicable event types
    
    # Execution control
    block_on_fail: bool = False        # Whether to block subsequent processing on failure
    async_execution: bool = False      # Whether to execute asynchronously
    cooldown_seconds: int = 0          # Cooldown time
    
    # Rule statistics
    triggered_count: int = 0
    last_triggered: Optional[datetime] = None
    
    # Condition constraints
    file_patterns: List[str] = field(default_factory=list)  # File path patterns
    exclude_patterns: List[str] = field(default_factory=list)
    
    metadata: Dict[str, Any] = field(default_factory=dict)

class RuleEngine:
    """Rule Engine - Responsible for rule loading, matching, and execution decisions"""
    
    def __init__(self, config_path: Optional[str] = None, config_dir: Optional[str] = None):
        self.rules: Dict[str, Rule] = {}
        self.custom_functions: Dict[str, Callable] = {}
        self.session_state: Dict[str, Any] = {}
        self.system_config: Dict[str, Any] = {}
        
        self.config_dir = Path(config_dir) if config_dir else Path("/root/Dev/mindnext/hooks/config")
        
        # Load system configuration first
        self._load_system_config()
        
        if config_path:
            self.load_rules_from_config(config_path)
        else:
                # Auto-load all rules_config_*.json and TOML files
            self._load_all_rule_configs()
        
        self._register_builtin_functions()
    
    def _load_system_config(self):
        """Load system configuration from system.config.toml"""
        system_config_file = self.config_dir / "system.config.toml"
        if system_config_file.exists():
            try:
                import toml
                with open(system_config_file, 'r', encoding='utf-8') as f:
                    self.system_config = toml.load(f)
                print(f"[system] {Path(system_config_file).name}")
            except Exception as e:
                print(f"Failed to load system config: {e}")
                self.system_config = self._get_default_system_config()
        else:
            self.system_config = self._get_default_system_config()
    
    def _get_default_system_config(self):
        """Get default system configuration"""
        return {
            'config': {'enable': True, 'debug_mode': False},
            'engine': {'max_concurrent_rules': 10, 'enable_rule_chaining': True},
            'rules': {'default_priority': 90, 'default_cooldown': 2, 'max_actions_per_trigger': 5},
            'actions': {'parallel_execution': True, 'timeout_seconds': 30},
            'memory': {'enable_buffer': True, 'buffer_size': 100},
            'notifications': {'enable_console': True, 'log_notifications': True},
            'security': {'validate_actions': True, 'sandbox_mode': False},
            'performance': {'cache_enabled': True, 'metrics_collection': True}
        }
    
    def _register_builtin_functions(self):
        """Register built-in condition functions"""
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
        """Load rules from config file (JSON or TOML)"""
        import json
        import os
        try:
            filename = os.path.basename(config_path)
            
            # Load based on file extension
            if config_path.endswith('.toml'):
                import toml
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = toml.load(f)
            else:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            # Check config.enable at file level
            if not config.get('config', {}).get('enable', True):
                return  # Skip disabled config
            
            # Check if it's mapping format or standard format
            if 'mappings' in config:
                self._load_mapping_format(config)
            else:
                # Standard format
                for rule_data in config.get('rules', []):
                    rule = self._parse_rule_config(rule_data)
                    self.rules[rule.id] = rule
                
        except Exception as e:
            print(f"Load rules failed: {e}")
    
    def _load_mapping_format(self, config: Dict[str, Any]):
        """Load mapping format: event → rule → action_flow"""
        for i, mapping in enumerate(config.get('mappings', [])):
            if not mapping.get('enable', True):
                continue
            
            # Get expression and rule type
            expression = mapping['condition']
            rule_type = mapping['rule']
                
            rule = Rule(
                id=f"mapping_rule_{i+1}",
                name=f"Mapping: {mapping['event']} - {str(mapping['condition'])[:30]}",
                conditions=[RuleCondition(
                    expression=expression,
                    condition_type=rule_type
                )],
                actions=mapping['action_flow'],
                priority=self.system_config.get('rules', {}).get('default_priority', 90),
                enabled=True,
                event_types=[mapping['event']],
                cooldown_seconds=self.system_config.get('rules', {}).get('default_cooldown', 2),
                metadata={'return': mapping.get('return', {})}  # Store return definition
            )
            self.rules[rule.id] = rule
    
    def _parse_rule_config(self, rule_data: Dict[str, Any]) -> Rule:
        """Parse rule configuration"""
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
        """Dynamically add rule"""
        self.rules[rule.id] = rule
    
    def remove_rule(self, rule_id: str):
        """Remove rule"""
        if rule_id in self.rules:
            del self.rules[rule_id]
    
    def enable_rule(self, rule_id: str):
        """Enable rule"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
    
    def disable_rule(self, rule_id: str):
        """Disable rule"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
    
    def match_rules(self, event: HookEvent) -> List[Rule]:
        """Match applicable rules for event"""
        matched_rules = []
        
        for rule in self.rules.values():
            if self._should_rule_apply(rule, event):
                if self._evaluate_rule_conditions(rule, event):
                    # Update rule statistics
                    rule.triggered_count += 1
                    rule.last_triggered = datetime.now()
                    matched_rules.append(rule)
        
        # Sort by priority
        matched_rules.sort(key=lambda r: r.priority)
        return matched_rules
    
    def _should_rule_apply(self, rule: Rule, event: HookEvent) -> bool:
        """Determine if rule should apply to event"""
        # Check if rule is enabled
        if not rule.enabled:
            return False
        
        # Check event type
        if rule.event_types and event.event_type not in rule.event_types:
            return False
        
        # Check cooldown time
        if rule.cooldown_seconds > 0 and rule.last_triggered:
            time_since_last = (datetime.now() - rule.last_triggered).total_seconds()
            if time_since_last < rule.cooldown_seconds:
                return False
        
        # Check file path patterns
        if rule.file_patterns and event.file_paths:
            file_match = False
            for file_path in event.file_paths:
                if any(self._match_pattern(file_path, pattern) for pattern in rule.file_patterns):
                    file_match = True
                    break
            if not file_match:
                return False
        
        # Check exclude patterns
        if rule.exclude_patterns and event.file_paths:
            for file_path in event.file_paths:
                if any(self._match_pattern(file_path, pattern) for pattern in rule.exclude_patterns):
                    return False
        
        return True
    
    def _match_pattern(self, text: str, pattern: str) -> bool:
        """Match path pattern"""
        try:
            # Support glob-style pattern matching
            import fnmatch
            return fnmatch.fnmatch(text, pattern)
        except:
            return pattern in text
    
    def _evaluate_rule_conditions(self, rule: Rule, event: HookEvent) -> bool:
        """Evaluate rule conditions"""
        if not rule.conditions:
            return True
        
        # All conditions must be satisfied (AND logic)
        for condition in rule.conditions:
            if not self._evaluate_single_condition(condition, event):
                return False
        
        return True
    
    def _evaluate_single_condition(self, condition: RuleCondition, event: HookEvent) -> bool:
        """Evaluate single condition"""
        try:
            if condition.condition_type == "simple":
                return self._evaluate_simple_condition(condition.expression, event)
            elif condition.condition_type == "keyword":
                return self._evaluate_keyword_condition(condition.expression, event)
            elif condition.condition_type == "regex":
                return self._evaluate_regex_condition(condition.expression, event)
            elif condition.condition_type == "function":
                return self._evaluate_function_condition(condition.expression, event)
            elif condition.condition_type == "composite":
                return self._evaluate_composite_condition(condition.expression, event)
            else:
                return False
        except Exception as e:
            print(f"Condition evaluation failed: {condition.expression}, Error: {e}")
            return False
    
    def _evaluate_simple_condition(self, expression: str, event: HookEvent) -> bool:
        """Evaluate simple condition"""
        # Create evaluation context
        context = {
            'event_type': event.event_type,
            'tool_name': event.tool_name or '',
            'file_paths': event.file_paths,
            'content': event.content or '',
            'user_prompt': event.user_prompt or '',
            'metadata': event.metadata,
            'session': self.session_state
        }
        
        # Replace built-in function calls
        for func_name, func in self.custom_functions.items():
            if f'{func_name}(' in expression:
                # Simplified function call processing
                pattern = rf'{func_name}\(([^)]*)\)'
                matches = re.findall(pattern, expression)
                for match in matches:
                    try:
                        args = [arg.strip().strip('"\'') for arg in match.split(',') if arg.strip()]
                        result = func(event, *args)
                        expression = expression.replace(f'{func_name}({match})', str(result))
                    except:
                        return False
        
        # Evaluate expression
        try:
            # Safe expression evaluation (restricted namespace)
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
    
    def _evaluate_keyword_condition(self, expression: Union[str, List[str]], event: HookEvent) -> bool:
        """Evaluate keyword condition - supports both string and array"""
        # Get text to search in
        search_text = event.user_prompt or event.content or ''
        
        # Handle array of keywords (OR logic)
        if isinstance(expression, list):
            return any(keyword in search_text for keyword in expression)
        # Handle single keyword
        elif isinstance(expression, str):
            return expression in search_text
        else:
            return False
    
    def _evaluate_regex_condition(self, expression: str, event: HookEvent) -> bool:
        """Evaluate regex condition"""
        # Extract target text from metadata
        target_text = ""
        if event.user_prompt:
            target_text += event.user_prompt + " "
        if event.content:
            target_text += event.content + " "
        
        return bool(re.search(expression, target_text, re.IGNORECASE))
    
    def _evaluate_function_condition(self, expression: str, event: HookEvent) -> bool:
        """Evaluate function condition"""
        # Function condition format: function_name(args)
        match = re.match(r'(\w+)\((.*)\)', expression)
        if not match:
            return False
        
        func_name, args_str = match.groups()
        if func_name not in self.custom_functions:
            return False
        
        args = [arg.strip().strip('"\'') for arg in args_str.split(',') if arg.strip()]
        return self.custom_functions[func_name](event, *args)
    
    def _evaluate_composite_condition(self, expression: str, event: HookEvent) -> bool:
        """Evaluate composite condition (supports AND, OR, NOT)"""
        # Simplified composite condition parsing
        expression = expression.replace(' AND ', ' and ').replace(' OR ', ' or ').replace(' NOT ', ' not ')
        
        # Recursively evaluate sub-conditions
        return self._evaluate_simple_condition(expression, event)
    
    # Built-in condition functions
    def _func_contains(self, event: HookEvent, keyword: str) -> bool:
        """Check if contains keyword"""
        text = f"{event.user_prompt or ''} {event.content or ''}".lower()
        return keyword.lower() in text
    
    def _func_matches(self, event: HookEvent, pattern: str) -> bool:
        """Check if matches regex pattern"""
        text = f"{event.user_prompt or ''} {event.content or ''}"
        return bool(re.search(pattern, text, re.IGNORECASE))
    
    def _func_file_extension(self, event: HookEvent, *extensions: str) -> bool:
        """Check file extension"""
        for file_path in event.file_paths:
            ext = Path(file_path).suffix.lower()
            if ext in extensions:
                return True
        return False
    
    def _func_file_size_gt(self, event: HookEvent, size_str: str) -> bool:
        """Check if file size is greater than specified value"""
        try:
            size_limit = int(size_str)
            for file_path in event.file_paths:
                if Path(file_path).stat().st_size > size_limit:
                    return True
            return False
        except:
            return False
    
    def _func_code_complexity(self, event: HookEvent, threshold_str: str) -> bool:
        """Check code complexity"""
        try:
            threshold = float(threshold_str)
            complexity = event.metadata.get('estimated_complexity', 'simple')
            complexity_values = {'simple': 1, 'medium': 2, 'complex': 3}
            return complexity_values.get(complexity, 1) >= threshold
        except:
            return False
    
    def _func_has_keyword(self, event: HookEvent, keyword: str) -> bool:
        """Check if contains specific keyword"""
        keywords = event.metadata.get('contains_keywords', [])
        return keyword in keywords
    
    def _func_is_test_file(self, event: HookEvent) -> bool:
        """Check if is test file"""
        test_patterns = ['/test/', '/tests/', '.test.', '.spec.', '_test.', '_spec.']
        return any(pattern in fp.lower() for fp in event.file_paths for pattern in test_patterns)
    
    def _func_session_count(self, event: HookEvent, event_type: str, count_str: str) -> bool:
        """Check count of specific event type in session"""
        try:
            target_count = int(count_str)
            current_count = self.session_state.get(f'count_{event_type}', 0)
            return current_count >= target_count
        except:
            return False
    
    def _func_recent_pattern(self, event: HookEvent, pattern: str, count_str: str) -> bool:
        """Check pattern in recent events"""
        try:
            count = int(count_str)
            recent_events = self.session_state.get('recent_events', [])[-count:]
            return any(pattern in str(event_data) for event_data in recent_events)
        except:
            return False
    
    def _func_time_since_last(self, event: HookEvent, event_type: str, seconds_str: str) -> bool:
        """Check time since last event"""
        try:
            seconds_threshold = int(seconds_str)
            last_time_key = f'last_{event_type}_time'
            last_time = self.session_state.get(last_time_key)
            
            if last_time is None:
                return True  # Return True when no record exists
            
            time_diff = (datetime.now() - last_time).total_seconds()
            return time_diff >= seconds_threshold
        except:
            return False
    
    def update_session_state(self, key: str, value: Any):
        """Update session state"""
        self.session_state[key] = value
    
    def get_rule_statistics(self) -> Dict[str, Any]:
        """Get rule statistics information"""
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
    
    def _load_all_rule_configs(self):
        """Auto-load all rules_config_*.json and TOML files"""
        import json
        import glob
        
        # Load main config file
        main_config = self.config_dir / "rules_config.json"
        if main_config.exists():
            self.load_rules_from_config(str(main_config))
        
        # Auto-load all rules_config_*.json and *.toml files
        json_pattern = str(self.config_dir / "rules_config_*.json")
        toml_pattern = str(self.config_dir / "rules_config_*.toml")
        config_files = glob.glob(json_pattern) + glob.glob(toml_pattern)
        
        for config_file in config_files:
            filename = Path(config_file).name
            # Load config to check if it's enabled
            if config_file.endswith('.toml'):
                import toml
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = toml.load(f)
            else:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            # Print status and load if enabled
            if not config.get('config', {}).get('enable', True):
                print(f"[disabled] {filename}")
            else:
                print(f"[enabled] {filename}")
                self.load_rules_from_config(config_file)