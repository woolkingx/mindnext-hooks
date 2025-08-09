"""
Action Flow Layer - Responsible for executing specific actions and action pipelines
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable, Union
from abc import ABC, abstractmethod
from datetime import datetime
import asyncio
import json
from pathlib import Path

from .event_layer import HookEvent

@dataclass
class ActionResult:
    """Action execution result"""
    action_id: str
    success: bool
    execution_time: float
    output: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ActionStep:
    """Action step"""
    action_id: str
    action_type: str                   # builtin, quality_check, analysis, notification, etc.
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Execution control
    required: bool = True              # Whether execution is required
    retry_count: int = 0               # Retry count
    timeout_seconds: int = 30          # Timeout in seconds
    
    # Conditional execution
    condition: Optional[str] = None    # Execution condition
    
    # Data flow
    input_from: Optional[str] = None   # From which step to get input
    output_to: Optional[str] = None    # Output to which variable
    
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ActionPipeline:
    """Action pipeline"""
    pipeline_id: str
    name: str
    steps: List[ActionStep]
    
    # Pipeline configuration
    parallel_execution: bool = False   # Whether to execute in parallel
    stop_on_error: bool = True         # Whether to stop on error
    
    # Input/Output
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    
    metadata: Dict[str, Any] = field(default_factory=dict)

class ActionExecutor(ABC):
    """Abstract action executor base class"""
    
    @abstractmethod
    def execute(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        """執行動作"""
        pass
    
    @abstractmethod
    def get_action_type(self) -> str:
        """獲取動作類型"""
        pass

class ActionFlowExecutor:
    """動作流執行器 - 負責執行動作和動作管道"""
    
    def __init__(self):
        self.executors: Dict[str, ActionExecutor] = {}
        self.pipelines: Dict[str, ActionPipeline] = {}
        self.execution_history: List[Dict[str, Any]] = []
        
        # 不在這裡註冊內建執行器，由 FlowCoordinator 負責註冊模組化執行器
    
    def _register_builtin_executors(self):
        """Register builtin executors - Deprecated: Use modular actions instead"""
        # This method is kept for backward compatibility but should not be used
        # Use FlowCoordinator to register modular actions from the actions package
        pass
    
    def register_executor(self, executor: ActionExecutor):
        """註冊動作執行器"""
        self.executors[executor.get_action_type()] = executor
    
    def register_pipeline(self, pipeline: ActionPipeline):
        """註冊動作管道"""
        self.pipelines[pipeline.pipeline_id] = pipeline
    
    def load_pipelines_from_config(self, config_path: str):
        """從配置文件載入管道"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            for pipeline_data in config.get('pipelines', []):
                pipeline = self._parse_pipeline_config(pipeline_data)
                self.register_pipeline(pipeline)
                
        except Exception as e:
            print(f"載入管道配置失敗: {e}")
    
    def _parse_pipeline_config(self, pipeline_data: Dict[str, Any]) -> ActionPipeline:
        """解析管道配置"""
        steps = []
        for step_data in pipeline_data.get('steps', []):
            step = ActionStep(
                action_id=step_data['action_id'],
                action_type=step_data['action_type'],
                parameters=step_data.get('parameters', {}),
                required=step_data.get('required', True),
                retry_count=step_data.get('retry_count', 0),
                timeout_seconds=step_data.get('timeout_seconds', 30),
                condition=step_data.get('condition'),
                input_from=step_data.get('input_from'),
                output_to=step_data.get('output_to'),
                metadata=step_data.get('metadata', {})
            )
            steps.append(step)
        
        pipeline = ActionPipeline(
            pipeline_id=pipeline_data['pipeline_id'],
            name=pipeline_data['name'],
            steps=steps,
            parallel_execution=pipeline_data.get('parallel_execution', False),
            stop_on_error=pipeline_data.get('stop_on_error', True),
            input_schema=pipeline_data.get('input_schema', {}),
            output_schema=pipeline_data.get('output_schema', {}),
            metadata=pipeline_data.get('metadata', {})
        )
        
        return pipeline
    
    async def execute_actions(self, action_ids: List[str], event: HookEvent, context: Dict[str, Any] = None) -> List[ActionResult]:
        """執行動作列表"""
        if context is None:
            context = {}
        
        results = []
        
        for action_id in action_ids:
            if action_id in self.pipelines:
                # 執行管道
                pipeline_result = await self.execute_pipeline(action_id, event, context)
                results.extend(pipeline_result)
            elif '/' in action_id:  # 格式: action_type/parameters
                # 直接執行動作
                action_type, param_str = action_id.split('/', 1)
                try:
                    parameters = json.loads(param_str) if param_str else {}
                except:
                    parameters = {'param': param_str}
                
                result = await self.execute_single_action(action_type, event, parameters, context)
                results.append(result)
            else:
                # 查找預定義管道或動作
                if action_id in self.pipelines:
                    pipeline_result = await self.execute_pipeline(action_id, event, context)
                    results.extend(pipeline_result)
                else:
                    # 嘗試作為動作類型執行
                    result = await self.execute_single_action(action_id, event, {}, context)
                    results.append(result)
        
        return results
    
    async def execute_single_action(self, action_type: str, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        """執行單個動作"""
        start_time = datetime.now()
        
        try:
            if action_type not in self.executors:
                return ActionResult(
                    action_id=action_type,
                    success=False,
                    execution_time=0.0,
                    error=f"未找到執行器: {action_type}"
                )
            
            executor = self.executors[action_type]
            
            # 執行動作
            if asyncio.iscoroutinefunction(executor.execute):
                result = await executor.execute(event, parameters, context)
            else:
                result = executor.execute(event, parameters, context)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            result.execution_time = execution_time
            
            # 記錄執行歷史
            self._record_execution(action_type, result, event)
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            result = ActionResult(
                action_id=action_type,
                success=False,
                execution_time=execution_time,
                error=str(e)
            )
            
            self._record_execution(action_type, result, event)
            return result
    
    async def execute_pipeline(self, pipeline_id: str, event: HookEvent, context: Dict[str, Any]) -> List[ActionResult]:
        """執行動作管道"""
        if pipeline_id not in self.pipelines:
            return [ActionResult(
                action_id=pipeline_id,
                success=False,
                execution_time=0.0,
                error=f"未找到管道: {pipeline_id}"
            )]
        
        pipeline = self.pipelines[pipeline_id]
        results = []
        pipeline_context = context.copy()
        pipeline_context['pipeline_data'] = {}
        
        if pipeline.parallel_execution:
            # 並行執行
            tasks = []
            for step in pipeline.steps:
                if self._should_execute_step(step, event, pipeline_context):
                    task = self._execute_pipeline_step(step, event, pipeline_context)
                    tasks.append(task)
            
            if tasks:
                step_results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in step_results:
                    if isinstance(result, Exception):
                        results.append(ActionResult(
                            action_id="parallel_step",
                            success=False,
                            execution_time=0.0,
                            error=str(result)
                        ))
                    else:
                        results.append(result)
        else:
            # 順序執行
            for step in pipeline.steps:
                if self._should_execute_step(step, event, pipeline_context):
                    result = await self._execute_pipeline_step(step, event, pipeline_context)
                    results.append(result)
                    
                    # 更新管道上下文
                    if result.success and step.output_to:
                        pipeline_context['pipeline_data'][step.output_to] = result.output
                    
                    # 錯誤處理
                    if not result.success and pipeline.stop_on_error and step.required:
                        break
        
        return results
    
    def _should_execute_step(self, step: ActionStep, event: HookEvent, context: Dict[str, Any]) -> bool:
        """判斷是否應該執行步驟"""
        if not step.condition:
            return True
        
        # 簡單的條件評估
        try:
            # 建立評估上下文
            eval_context = {
                'event': event,
                'context': context,
                'metadata': event.metadata,
                'tool_name': event.tool_name,
                'event_type': event.event_type
            }
            
            return eval(step.condition, {"__builtins__": {}}, eval_context)
        except:
            return True  # 條件評估失敗時預設執行
    
    async def _execute_pipeline_step(self, step: ActionStep, event: HookEvent, context: Dict[str, Any]) -> ActionResult:
        """執行管道步驟"""
        parameters = step.parameters.copy()
        
        # 處理輸入數據
        if step.input_from and step.input_from in context.get('pipeline_data', {}):
            parameters['input_data'] = context['pipeline_data'][step.input_from]
        
        # 執行動作
        result = await self.execute_single_action(step.action_type, event, parameters, context)
        result.action_id = step.action_id
        
        return result
    
    def _record_execution(self, action_type: str, result: ActionResult, event: HookEvent):
        """記錄執行歷史"""
        record = {
            'timestamp': datetime.now().isoformat(),
            'action_type': action_type,
            'action_id': result.action_id,
            'success': result.success,
            'execution_time': result.execution_time,
            'event_type': event.event_type,
            'tool_name': event.tool_name,
            'error': result.error
        }
        
        self.execution_history.append(record)
        
        # 保持最近 1000 條記錄
        self.execution_history = self.execution_history[-1000:]
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """獲取執行統計"""
        if not self.execution_history:
            return {}
        
        total_executions = len(self.execution_history)
        successful_executions = sum(1 for record in self.execution_history if record['success'])
        
        # 按動作類型統計
        action_stats = {}
        for record in self.execution_history:
            action_type = record['action_type']
            if action_type not in action_stats:
                action_stats[action_type] = {'count': 0, 'success': 0, 'total_time': 0}
            
            action_stats[action_type]['count'] += 1
            if record['success']:
                action_stats[action_type]['success'] += 1
            action_stats[action_type]['total_time'] += record['execution_time']
        
        return {
            'total_executions': total_executions,
            'success_rate': successful_executions / total_executions,
            'action_statistics': action_stats
        }

# 內建執行器實現

class QualityCheckExecutor(ActionExecutor):
    """品質檢查執行器"""
    
    def get_action_type(self) -> str:
        return "quality_check"
    
    def execute(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        """執行品質檢查"""
        try:
            # 整合現有的品質檢查系統
            from ..quality_modules import PythonQualityChecker, JavaScriptQualityChecker, TypeScriptQualityChecker
            
            checkers = {
                '.py': PythonQualityChecker(),
                '.js': JavaScriptQualityChecker(), 
                '.jsx': JavaScriptQualityChecker(),
                '.ts': TypeScriptQualityChecker(),
                '.tsx': TypeScriptQualityChecker()
            }
            
            all_results = []
            
            for file_path in event.file_paths:
                file_ext = Path(file_path).suffix.lower()
                if file_ext in checkers:
                    checker = checkers[file_ext]
                    result = checker.check_file(file_path)
                    all_results.append({
                        'file': file_path,
                        'checker': checker.get_checker_name(),
                        'issues': len(result.issues),
                        'errors': result.error_count,
                        'warnings': result.warning_count,
                        'result': result
                    })
            
            # 判斷是否有阻止性錯誤
            has_blocking_errors = any(r['errors'] > 0 for r in all_results)
            
            return ActionResult(
                action_id="quality_check",
                success=not has_blocking_errors,
                execution_time=0.0,
                output={
                    'results': all_results,
                    'total_issues': sum(r['issues'] for r in all_results),
                    'total_errors': sum(r['errors'] for r in all_results),
                    'blocking': has_blocking_errors
                }
            )
            
        except Exception as e:
            return ActionResult(
                action_id="quality_check",
                success=False,
                execution_time=0.0,
                error=str(e)
            )

class MemoryRecordExecutor(ActionExecutor):
    """記憶記錄執行器"""
    
    def get_action_type(self) -> str:
        return "memory_record"
    
    def execute(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        """執行記憶記錄"""
        try:
            # 這裡可以整合到 MindNext Graph 系統
            record_data = {
                'timestamp': datetime.now().isoformat(),
                'event_type': event.event_type,
                'tool_name': event.tool_name,
                'files': event.file_paths,
                'summary': parameters.get('summary', ''),
                'metadata': event.metadata
            }
            
            # TODO: 實際記錄到 QKVL 系統
            
            return ActionResult(
                action_id="memory_record",
                success=True,
                execution_time=0.0,
                output=record_data
            )
            
        except Exception as e:
            return ActionResult(
                action_id="memory_record",
                success=False,
                execution_time=0.0,
                error=str(e)
            )

class NotificationExecutor(ActionExecutor):
    """通知執行器"""
    
    def get_action_type(self) -> str:
        return "notification"
    
    def execute(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        """執行通知"""
        try:
            message = parameters.get('message', '')
            severity = parameters.get('severity', 'info')
            
            # 輸出通知
            icons = {'info': '💡', 'warning': '⚠️', 'error': '❌', 'success': '✅'}
            icon = icons.get(severity, '📢')
            
            print(f"{icon} {message}")
            
            return ActionResult(
                action_id="notification",
                success=True,
                execution_time=0.0,
                output={'message': message, 'severity': severity}
            )
            
        except Exception as e:
            return ActionResult(
                action_id="notification",
                success=False,
                execution_time=0.0,
                error=str(e)
            )

class AnalysisExecutor(ActionExecutor):
    """分析執行器"""
    
    def get_action_type(self) -> str:
        return "analysis"
    
    def execute(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        """執行分析"""
        try:
            analysis_type = parameters.get('type', 'basic')
            
            analysis_result = {
                'event_analysis': {
                    'type': event.event_type,
                    'complexity': event.metadata.get('estimated_complexity', 'unknown'),
                    'file_count': len(event.file_paths),
                    'file_types': event.metadata.get('file_types', {}),
                },
                'recommendations': []
            }
            
            # 基於事件類型提供建議
            if event.event_type == "PostToolUse" and event.tool_name in ['Write', 'Edit']:
                analysis_result['recommendations'].append("建議執行代碼品質檢查")
            
            if event.metadata.get('estimated_intent') == 'create':
                analysis_result['recommendations'].append("新創建的代碼建議添加測試")
            
            return ActionResult(
                action_id="analysis",
                success=True,
                execution_time=0.0,
                output=analysis_result
            )
            
        except Exception as e:
            return ActionResult(
                action_id="analysis",
                success=False,
                execution_time=0.0,
                error=str(e)
            )

class ConditionalExecutor(ActionExecutor):
    """條件執行器"""
    
    def get_action_type(self) -> str:
        return "conditional"
    
    def execute(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        """條件執行"""
        try:
            condition = parameters.get('condition', 'True')
            true_action = parameters.get('true_action')
            false_action = parameters.get('false_action')
            
            # 評估條件
            eval_context = {
                'event': event,
                'context': context,
                'tool_name': event.tool_name,
                'file_count': len(event.file_paths)
            }
            
            condition_result = eval(condition, {"__builtins__": {}}, eval_context)
            
            selected_action = true_action if condition_result else false_action
            
            return ActionResult(
                action_id="conditional",
                success=True,
                execution_time=0.0,
                output={
                    'condition_result': condition_result,
                    'selected_action': selected_action
                }
            )
            
        except Exception as e:
            return ActionResult(
                action_id="conditional",
                success=False,
                execution_time=0.0,
                error=str(e)
            )

class UtilityExecutor(ActionExecutor):
    """工具執行器"""
    
    def get_action_type(self) -> str:
        return "utility"
    
    def execute(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        """執行工具操作"""
        try:
            operation = parameters.get('operation', 'noop')
            
            if operation == 'delay':
                import time
                delay_seconds = parameters.get('seconds', 1)
                time.sleep(delay_seconds)
                return ActionResult(
                    action_id="utility",
                    success=True,
                    execution_time=delay_seconds,
                    output=f"延遲 {delay_seconds} 秒"
                )
            elif operation == 'log':
                message = parameters.get('message', 'Log message')
                print(f"📝 {message}")
                return ActionResult(
                    action_id="utility",
                    success=True,
                    execution_time=0.0,
                    output=message
                )
            else:
                return ActionResult(
                    action_id="utility",
                    success=False,
                    execution_time=0.0,
                    error=f"未知操作: {operation}"
                )
                
        except Exception as e:
            return ActionResult(
                action_id="utility",
                success=False,
                execution_time=0.0,
                error=str(e)
            )