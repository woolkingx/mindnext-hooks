"""
FlowCoordinator - Three-Layer Flow Coordinator
Unified management of complete flow: Event Layer → Rule Layer → Action Flow Layer
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import json
from pathlib import Path

from .event_layer import EventProcessor, HookEvent
from .rule_layer import RuleEngine, Rule
from .action_layer import ActionFlowExecutor

# Import modular action executors
from .actions import (
    ActionPrompt, ActionAI, ActionQuality, ActionMemory, 
    ActionNotification, ActionAnalysis, ActionConditional, ActionUtility
)

class FlowCoordinator:
    """
    Flow Coordinator - Core controller of three-layer architecture
    Responsible for coordinating complete Event → Rule → Action flow
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir) if config_dir else Path("/root/Dev/mindnext/hooks/config")
        
        # Initialize three-layer components
        self.event_processor = EventProcessor()
        self.rule_engine = RuleEngine(str(self.config_dir / "rules_config.json"))
        self.action_executor = ActionFlowExecutor()
        
        # Register modular action executors
        self._register_modular_actions()
        
        # Load action pipeline configuration
        self._load_action_pipelines()
        
        # Global state
        self.global_context = {}
        self.execution_history = []
        self.performance_metrics = {
            'total_events': 0,
            'rules_triggered': 0,
            'actions_executed': 0,
            'average_processing_time': 0.0
        }
        
        # Cache and buffers
        self.result_cache = {}
        self.event_buffer = []
        
    def _register_modular_actions(self):
        """Register modular action executors"""
        modular_actions = [
            ActionPrompt(),
            ActionAI(),
            ActionQuality(),
            ActionMemory(),
            ActionNotification(),
            ActionAnalysis(),
            ActionConditional(),
            ActionUtility()
        ]
        
        for action in modular_actions:
            self.action_executor.register_executor(action)
    
    def _load_action_pipelines(self):
        """Load action pipeline configuration"""
        pipeline_config_path = self.config_dir / "pipelines_config.json"
        if pipeline_config_path.exists():
            self.action_executor.load_pipelines_from_config(str(pipeline_config_path))
    
    async def process_hook_event(self, event_type: str, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process complete Hook event flow
        Event Layer → Rule Layer → Action Flow Layer
        """
        start_time = datetime.now()
        
        try:
            # === Event Layer: Event Processing ===
            event = self._process_event_layer(event_type, raw_data)
            
            # === Rule Layer: Rule Matching ===
            matched_rules = self._process_rule_layer(event)
            
            # === Action Flow Layer: Action Execution ===
            action_results = await self._process_action_layer(matched_rules, event)
            
            # Update performance metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_performance_metrics(processing_time, len(matched_rules), len(action_results))
            
            # Record execution history
            execution_record = {
                'timestamp': start_time.isoformat(),
                'event_type': event_type,
                'rules_matched': len(matched_rules),
                'actions_executed': len(action_results),
                'processing_time': processing_time,
                'success': all(result.success for result in action_results)
            }
            self.execution_history.append(execution_record)
            
            # Keep recent 100 records
            self.execution_history = self.execution_history[-100:]
            
            return {
                'success': True,
                'event': {
                    'type': event.event_type,
                    'tool': event.tool_name,
                    'files': len(event.file_paths),
                    'timestamp': event.timestamp.isoformat()
                },
                'rules_matched': [rule.id for rule in matched_rules],
                'actions_executed': len(action_results),
                'processing_time': processing_time,
                'results': [self._serialize_action_result(result) for result in action_results]
            }
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            error_record = {
                'timestamp': start_time.isoformat(),
                'event_type': event_type,
                'error': str(e),
                'processing_time': processing_time
            }
            self.execution_history.append(error_record)
            
            return {
                'success': False,
                'error': str(e),
                'processing_time': processing_time
            }
    
    def _process_event_layer(self, event_type: str, raw_data: Dict[str, Any]) -> HookEvent:
        """Process event layer"""
        event = self.event_processor.process_hook_event(event_type, raw_data)
        
        # Update global context
        self.global_context.update({
            'latest_event': event,
            'session_context': self.event_processor.get_session_context()
        })
        
        # Event buffering
        self.event_buffer.append({
            'event': event,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep recent 50 events
        self.event_buffer = self.event_buffer[-50:]
        
        return event
    
    def _process_rule_layer(self, event: HookEvent) -> List[Rule]:
        """Process rule layer"""
        # Update rule engine session state
        session_context = self.event_processor.get_session_context()
        for key, value in session_context.items():
            self.rule_engine.update_session_state(key, value)
        
        # Update recent event information
        self.rule_engine.update_session_state('recent_events', self.event_buffer[-5:])
        self.rule_engine.update_session_state(f'last_{event.event_type}_time', datetime.now())
        
        # Match rules
        matched_rules = self.rule_engine.match_rules(event)
        
        return matched_rules
    
    async def _process_action_layer(self, matched_rules: List[Rule], event: HookEvent) -> List[Any]:
        """Process action layer"""
        all_results = []
        
        # Prepare execution context
        execution_context = self.global_context.copy()
        execution_context.update({
            'matched_rules': [rule.id for rule in matched_rules],
            'event_buffer': self.event_buffer,
            'performance_metrics': self.performance_metrics,
            'rule_engine_state': self.rule_engine.session_state
        })
        
        # Execute rule actions by priority
        for rule in matched_rules:
            if not rule.enabled:
                continue
            
            try:
                # Check circuit breaker status
                if self._should_skip_rule_execution(rule, execution_context):
                    continue
                
                # Execute rule actions
                if rule.async_execution:
                    # Async execution
                    rule_results = await self.action_executor.execute_actions(
                        rule.actions, event, execution_context
                    )
                else:
                    # Sync execution
                    rule_results = await self.action_executor.execute_actions(
                        rule.actions, event, execution_context
                    )
                
                all_results.extend(rule_results)
                
                # Check if subsequent rules should be aborted
                if rule.block_on_fail and any(not result.success for result in rule_results):
                    print(f"Rule {rule.id} execution failed, aborting subsequent rule execution")
                    break
                
            except Exception as e:
                print(f"Rule {rule.id} execution error: {str(e)}")
                if rule.block_on_fail:
                    break
        
        return all_results
    
    def _should_skip_rule_execution(self, rule: Rule, context: Dict[str, Any]) -> bool:
        """Determine if rule execution should be skipped"""
        # Check circuit breaker status
        circuit_data = context.get('circuit_breaker_data', {})
        circuit_key = f"rule_{rule.id}"
        
        if circuit_key in circuit_data:
            circuit_state = circuit_data[circuit_key].get('state', 'closed')
            if circuit_state == 'open':
                return True
        
        # Check rate limiting
        rate_limit_data = context.get('rate_limit_data', {})
        rate_key = f"rule_{rule.id}"
        
        if rate_key in rate_limit_data:
            rate_info = rate_limit_data[rate_key]
            if not rate_info.get('allowed', True):
                return True
        
        return False
    
    def _serialize_action_result(self, result: Any) -> Dict[str, Any]:
        """Serialize action results"""
        if hasattr(result, '__dict__'):
            return {
                'action_id': getattr(result, 'action_id', 'unknown'),
                'success': getattr(result, 'success', False),
                'execution_time': getattr(result, 'execution_time', 0.0),
                'output': str(getattr(result, 'output', '')),
                'error': getattr(result, 'error', None)
            }
        else:
            return {'result': str(result)}
    
    def _update_performance_metrics(self, processing_time: float, rules_count: int, actions_count: int):
        """Update performance metrics"""
        self.performance_metrics['total_events'] += 1
        self.performance_metrics['rules_triggered'] += rules_count
        self.performance_metrics['actions_executed'] += actions_count
        
        # 更新平均處理時間
        total_events = self.performance_metrics['total_events']
        current_avg = self.performance_metrics['average_processing_time']
        
        new_avg = ((current_avg * (total_events - 1)) + processing_time) / total_events
        self.performance_metrics['average_processing_time'] = new_avg
    
    def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        return {
            'coordinator_status': 'operational',
            'performance_metrics': self.performance_metrics,
            'component_status': {
                'event_processor': {
                    'events_processed': self.event_processor.event_sequence,
                    'session_context_size': len(self.event_processor.session_context)
                },
                'rule_engine': {
                    'total_rules': len(self.rule_engine.rules),
                    'active_rules': len([r for r in self.rule_engine.rules.values() if r.enabled]),
                    'session_state_size': len(self.rule_engine.session_state)
                },
                'action_executor': {
                    'registered_executors': len(self.action_executor.executors),
                    'registered_pipelines': len(self.action_executor.pipelines),
                    'execution_history_size': len(self.action_executor.execution_history)
                }
            },
            'recent_execution_history': self.execution_history[-5:],
            'cache_status': {
                'result_cache_size': len(self.result_cache),
                'event_buffer_size': len(self.event_buffer)
            }
        }
    
    def get_rule_statistics(self) -> Dict[str, Any]:
        """獲取規則統計"""
        return self.rule_engine.get_rule_statistics()
    
    def get_action_statistics(self) -> Dict[str, Any]:
        """獲取動作統計"""
        return self.action_executor.get_execution_statistics()
    
    def enable_rule(self, rule_id: str) -> bool:
        """啟用規則"""
        self.rule_engine.enable_rule(rule_id)
        return rule_id in self.rule_engine.rules and self.rule_engine.rules[rule_id].enabled
    
    def disable_rule(self, rule_id: str) -> bool:
        """禁用規則"""
        self.rule_engine.disable_rule(rule_id)
        return rule_id in self.rule_engine.rules and not self.rule_engine.rules[rule_id].enabled
    
    def reload_configuration(self) -> Dict[str, Any]:
        """重新載入配置"""
        try:
            # 重新載入規則配置
            rules_config_path = str(self.config_dir / "rules_config.json")
            self.rule_engine.load_rules_from_config(rules_config_path)
            
            # 重新載入動作管道配置
            self._load_action_pipelines()
            
            return {
                'success': True,
                'message': '配置重新載入成功',
                'rules_loaded': len(self.rule_engine.rules),
                'pipelines_loaded': len(self.action_executor.pipelines)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def export_execution_report(self, format: str = 'json') -> Dict[str, Any]:
        """導出執行報告"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'system_status': self.get_system_status(),
            'rule_statistics': self.get_rule_statistics(),
            'action_statistics': self.get_action_statistics(),
            'execution_history': self.execution_history,
            'performance_summary': {
                'total_events_processed': self.performance_metrics['total_events'],
                'average_processing_time': self.performance_metrics['average_processing_time'],
                'rules_efficiency': (
                    self.performance_metrics['rules_triggered'] / 
                    max(1, self.performance_metrics['total_events'])
                ),
                'actions_efficiency': (
                    self.performance_metrics['actions_executed'] / 
                    max(1, self.performance_metrics['rules_triggered'])
                )
            }
        }
        
        if format == 'json':
            # 保存到文件
            report_dir = Path("/root/Dev/mindnext/record")
            report_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = report_dir / f"hooks_execution_report_{timestamp}.json"
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            return {
                'success': True,
                'report_path': str(report_path),
                'report_size': len(json.dumps(report))
            }
        
        return report
    
    async def test_flow(self, test_event: Dict[str, Any]) -> Dict[str, Any]:
        """測試完整流程"""
        print("🧪 開始測試三層流程...")
        
        # 模擬事件數據
        test_data = {
            'tool_name': test_event.get('tool_name', 'Write'),
            'tool_input': {
                'file_path': test_event.get('file_path', '/test/example.py'),
                'content': test_event.get('content', 'print("Hello, MindNext!")')
            },
            'env': {
                'CLAUDE_FILE_PATHS': test_event.get('file_path', '/test/example.py')
            }
        }
        
        # 執行完整流程
        result = await self.process_hook_event('PostToolUse', test_data)
        
        print(f"✅ 測試完成: {result['success']}")
        print(f"📊 處理時間: {result['processing_time']:.3f}s")
        print(f"🎯 匹配規則: {len(result['rules_matched'])}")
        print(f"⚡ 執行動作: {result['actions_executed']}")
        
        return result