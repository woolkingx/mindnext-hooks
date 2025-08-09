"""
ActionConditional - Conditional Control Action Executor
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from .action_base import ActionExecutor, ActionResult
from ..event_layer import HookEvent

class ActionConditional(ActionExecutor):
    """Conditional Control Action Executor"""
    
    def get_action_type(self) -> str:
        return "action.conditional"
    
    def execute(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        """ExecuteConditional controlAction"""
        start_time = datetime.now()
        
        try:
            operation = parameters.get('operation', 'if_then')
            
            if operation == 'if_then':
                result = self._if_then_logic(event, parameters, context)
            elif operation == 'switch_case':
                result = self._switch_case_logic(event, parameters, context)
            elif operation == 'loop_control':
                result = self._loop_control_logic(event, parameters, context)
            elif operation == 'rate_limit':
                result = self._rate_limit_logic(event, parameters, context)
            elif operation == 'circuit_breaker':
                result = self._circuit_breaker_logic(event, parameters, context)
            else:
                return self._create_result(
                    action_id="action.conditional",
                    success=False,
                    execution_time=(datetime.now() - start_time).total_seconds(),
                    error=f"Unknown operation: {operation}"
                )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            return self._create_result(
                action_id="action.conditional",
                success=True,
                execution_time=execution_time,
                output=result
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return self._create_result(
                action_id="action.conditional",
                success=False,
                execution_time=execution_time,
                error=str(e)
            )
    
    def _if_then_logic(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """If-Then 邏輯"""
        conditions = parameters.get('conditions', [])
        actions = parameters.get('actions', {})
        
        results = []
        
        for condition in conditions:
            condition_result = self._evaluate_condition(condition, event, context)
            
            if condition_result['satisfied']:
                # Execute對應的Action
                action_type = condition.get('then_action', 'log')
                action_params = condition.get('action_params', {})
                
                action_result = {
                    'condition': condition.get('expression', ''),
                    'satisfied': True,
                    'action': action_type,
                    'action_params': action_params,
                    'timestamp': datetime.now().isoformat()
                }
                
                results.append(action_result)
            else:
                # Check是否有 else Action
                if 'else_action' in condition:
                    else_action = condition['else_action']
                    else_params = condition.get('else_params', {})
                    
                    action_result = {
                        'condition': condition.get('expression', ''),
                        'satisfied': False,
                        'action': else_action,
                        'action_params': else_params,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    results.append(action_result)
        
        return {
            'logic_type': 'if_then',
            'conditions_evaluated': len(conditions),
            'actions_triggered': len(results),
            'results': results
        }
    
    def _switch_case_logic(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Switch-Case 邏輯"""
        switch_value = parameters.get('switch_value', event.event_type)
        cases = parameters.get('cases', {})
        default_action = parameters.get('default', None)
        
        # Evaluate switch 值
        if isinstance(switch_value, str) and switch_value.startswith('event.'):
            # 動態獲取Event屬性值
            attr_path = switch_value.split('.')[1:]
            value = event
            for attr in attr_path:
                value = getattr(value, attr, None)
                if value is None:
                    break
        else:
            value = switch_value
        
        matched_case = None
        action_result = None
        
        # 尋找匹配的 case
        for case_key, case_action in cases.items():
            if str(value) == str(case_key):
                matched_case = case_key
                action_result = {
                    'case': case_key,
                    'action': case_action.get('action', 'log'),
                    'params': case_action.get('params', {}),
                    'matched': True
                }
                break
        
        # 如果沒有匹配的 case，使用DefaultAction
        if matched_case is None and default_action:
            action_result = {
                'case': 'default',
                'action': default_action.get('action', 'log'),
                'params': default_action.get('params', {}),
                'matched': False
            }
        
        return {
            'logic_type': 'switch_case',
            'switch_value': value,
            'matched_case': matched_case,
            'total_cases': len(cases),
            'result': action_result
        }
    
    def _loop_control_logic(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Loop control邏輯"""
        loop_type = parameters.get('type', 'for')
        max_iterations = parameters.get('max_iterations', 10)
        break_condition = parameters.get('break_condition', None)
        
        iterations = []
        iteration_count = 0
        
        if loop_type == 'for':
            # For 循環
            loop_data = parameters.get('data', [])
            for i, item in enumerate(loop_data[:max_iterations]):
                iteration_result = {
                    'iteration': i,
                    'data': item,
                    'timestamp': datetime.now().isoformat()
                }
                
                # CheckInterrupted條件
                if break_condition and self._check_break_condition(break_condition, item, event, context):
                    iteration_result['break_reason'] = break_condition
                    iterations.append(iteration_result)
                    break
                
                iterations.append(iteration_result)
                iteration_count += 1
        
        elif loop_type == 'while':
            # While 循環
            while_condition = parameters.get('condition', 'iteration_count < 5')
            
            while iteration_count < max_iterations:
                # Evaluate condition
                eval_context = {
                    'iteration_count': iteration_count,
                    'event': event,
                    'context': context
                }
                
                try:
                    if not eval(while_condition, {"__builtins__": {}}, eval_context):
                        break
                except:
                    break
                
                iteration_result = {
                    'iteration': iteration_count,
                    'condition_result': True,
                    'timestamp': datetime.now().isoformat()
                }
                
                iterations.append(iteration_result)
                iteration_count += 1
        
        return {
            'logic_type': 'loop_control',
            'loop_type': loop_type,
            'iterations_executed': iteration_count,
            'max_iterations': max_iterations,
            'completed': iteration_count < max_iterations,
            'iterations': iterations
        }
    
    def _rate_limit_logic(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Rate limit邏輯"""
        limit = parameters.get('limit', 10)  # 每分鐘最大次數
        window = parameters.get('window', 60)  # Time窗口（秒）
        key = parameters.get('key', f"{event.event_type}_{event.tool_name}")
        
        # 簡化的Rate limit實現
        current_time = datetime.now()
        
        # 從上下文獲取歷史Record
        rate_limit_data = context.get('rate_limit_data', {})
        
        if key not in rate_limit_data:
            rate_limit_data[key] = {
                'count': 0,
                'window_start': current_time.timestamp(),
                'requests': []
            }
        
        data = rate_limit_data[key]
        
        # Check是否需要重置Time窗口
        if current_time.timestamp() - data['window_start'] > window:
            data['count'] = 0
            data['window_start'] = current_time.timestamp()
            data['requests'] = []
        
        # Record當前Request
        data['requests'].append(current_time.timestamp())
        data['count'] += 1
        
        # 判斷是否超出限制
        allowed = data['count'] <= limit
        
        # Update上下文
        context['rate_limit_data'] = rate_limit_data
        
        return {
            'logic_type': 'rate_limit',
            'key': key,
            'limit': limit,
            'window': window,
            'current_count': data['count'],
            'allowed': allowed,
            'remaining': max(0, limit - data['count']),
            'reset_time': data['window_start'] + window
        }
    
    def _circuit_breaker_logic(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Circuit breaker邏輯"""
        failure_threshold = parameters.get('failure_threshold', 5)
        recovery_timeout = parameters.get('recovery_timeout', 60)
        key = parameters.get('key', f"circuit_{event.event_type}")
        
        # 從上下文獲取Circuit breakerStatus
        circuit_data = context.get('circuit_breaker_data', {})
        
        if key not in circuit_data:
            circuit_data[key] = {
                'state': 'closed',  # closed, open, half_open
                'failure_count': 0,
                'last_failure_time': None,
                'success_count': 0
            }
        
        data = circuit_data[key]
        current_time = datetime.now()
        
        # Check當前Operation是否Success
        is_success = parameters.get('success', True)
        
        if data['state'] == 'closed':
            if is_success:
                data['failure_count'] = 0
            else:
                data['failure_count'] += 1
                data['last_failure_time'] = current_time.timestamp()
                
                if data['failure_count'] >= failure_threshold:
                    data['state'] = 'open'
        
        elif data['state'] == 'open':
            # Check是否可以嘗試恢復
            if (current_time.timestamp() - data['last_failure_time']) > recovery_timeout:
                data['state'] = 'half_open'
                data['success_count'] = 0
        
        elif data['state'] == 'half_open':
            if is_success:
                data['success_count'] += 1
                if data['success_count'] >= 3:  # 連續3次Success則關閉Circuit breaker
                    data['state'] = 'closed'
                    data['failure_count'] = 0
            else:
                data['state'] = 'open'
                data['failure_count'] += 1
                data['last_failure_time'] = current_time.timestamp()
        
        # Update上下文
        context['circuit_breaker_data'] = circuit_data
        
        return {
            'logic_type': 'circuit_breaker',
            'key': key,
            'state': data['state'],
            'failure_count': data['failure_count'],
            'success_count': data['success_count'],
            'allowed': data['state'] != 'open',
            'failure_threshold': failure_threshold,
            'recovery_timeout': recovery_timeout
        }
    
    def _evaluate_condition(self, condition: Dict[str, Any], event: HookEvent, context: Dict[str, Any]) -> Dict[str, bool]:
        """Evaluate condition"""
        expression = condition.get('expression', 'True')
        condition_type = condition.get('type', 'simple')
        
        try:
            if condition_type == 'simple':
                # 簡單條件Evaluate
                eval_context = {
                    'event_type': event.event_type,
                    'tool_name': event.tool_name or '',
                    'file_count': len(event.file_paths),
                    'event': event,
                    'context': context
                }
                
                result = eval(expression, {"__builtins__": {}}, eval_context)
                
            elif condition_type == 'regex':
                import re
                pattern = condition.get('pattern', expression)
                target = condition.get('target', event.user_prompt or '')
                result = bool(re.search(pattern, target, re.IGNORECASE))
                
            elif condition_type == 'function':
                # 自定義函數條件
                func_name = condition.get('function', expression)
                result = self._call_condition_function(func_name, event, context)
                
            else:
                result = False
            
            return {'satisfied': bool(result), 'error': None}
            
        except Exception as e:
            return {'satisfied': False, 'error': str(e)}
    
    def _check_break_condition(self, break_condition: str, item: Any, event: HookEvent, context: Dict[str, Any]) -> bool:
        """CheckInterrupted條件"""
        try:
            eval_context = {
                'item': item,
                'event': event,
                'context': context
            }
            return bool(eval(break_condition, {"__builtins__": {}}, eval_context))
        except:
            return False
    
    def _call_condition_function(self, func_name: str, event: HookEvent, context: Dict[str, Any]) -> bool:
        """調用條件函數"""
        # 內建條件函數
        builtin_functions = {
            'is_code_file': lambda: any(
                ext in ['.py', '.js', '.ts', '.rs', '.go'] 
                for ext in [Path(fp).suffix for fp in event.file_paths]
            ),
            'is_test_event': lambda: event.event_type.startswith('Test'),
            'has_errors': lambda: event.metadata.get('has_errors', False),
            'is_weekend': lambda: datetime.now().weekday() >= 5,
            'is_working_hours': lambda: 9 <= datetime.now().hour <= 17
        }
        
        if func_name in builtin_functions:
            return builtin_functions[func_name]()
        
        return False