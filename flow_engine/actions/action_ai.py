"""
ActionAI - Core Claude SDK Service Interface
Single-purpose action executor for AI operations
"""

from typing import Dict, Any, List
from datetime import datetime
import json

from .action_base import ActionExecutor, ActionResult
from ..event_layer import HookEvent


class ActionAI(ActionExecutor):
    """AI Action Executor - Pure interface to CoreClaudeSDK service"""
    
    def __init__(self, core_claude_sdk=None):
        super().__init__()
        self.core_claude_sdk = core_claude_sdk  # Injected by system
    
    def get_action_type(self) -> str:
        return "action.ai"
    
    def execute(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        """Execute single AI operation"""
        start_time = datetime.now()
        
        if not self.core_claude_sdk:
            return self._create_result(
                action_id="action.ai",
                success=False,
                execution_time=0,
                error="CoreClaudeSDK service not available"
            )
        
        try:
            operation = parameters.get('operation', 'call')
            
            # Single-purpose operations only
            if operation == 'call':
                result = self._call_claude(parameters)
            elif operation == 'analyze_patterns':
                result = self._analyze_patterns(parameters)
            elif operation == 'analyze_risks':
                result = self._analyze_risks(parameters)
            elif operation == 'analyze_productivity':
                result = self._analyze_productivity(parameters)
            elif operation == 'get_suggestions':
                result = self._get_suggestions(parameters)
            elif operation == 'analyze_code_quality':
                result = self._analyze_code_quality(parameters)
            elif operation == 'get_status':
                result = self._get_status(parameters)
            elif operation == 'clear_cache':
                result = self._clear_cache(parameters)
            else:
                return self._create_result(
                    action_id="action.ai",
                    success=False,
                    execution_time=(datetime.now() - start_time).total_seconds(),
                    error=f"Unknown operation: {operation}"
                )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            return self._create_result(
                action_id="action.ai",
                success=True,
                execution_time=execution_time,
                data=result
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return self._create_result(
                action_id="action.ai",
                success=False,
                execution_time=execution_time,
                error=str(e)
            )
    
    def _call_claude(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Direct Claude SDK call"""
        prompt = parameters.get('prompt')
        system_prompt = parameters.get('system_prompt')
        cache_key = parameters.get('cache_key')
        
        if not prompt:
            raise ValueError("No prompt provided for Claude call")
        
        response = self.core_claude_sdk.call_claude(prompt, system_prompt, cache_key)
        
        return {
            'operation': 'call',
            'response': response,
            'success': response is not None
        }
    
    def _analyze_patterns(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze patterns in event data"""
        event_data = parameters.get('event_data', [])
        
        if not event_data:
            raise ValueError("No event data provided for pattern analysis")
        
        result = self.core_claude_sdk.analyze_patterns(event_data)
        return result
    
    def _analyze_risks(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze risks and potential issues"""
        recent_activities = parameters.get('recent_activities', [])
        tool_usage = parameters.get('tool_usage', {})
        
        result = self.core_claude_sdk.analyze_risks(recent_activities, tool_usage)
        return result
    
    def _analyze_productivity(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze productivity and efficiency"""
        statistics = parameters.get('statistics', {})
        event_distribution = parameters.get('event_distribution', {})
        
        result = self.core_claude_sdk.analyze_productivity(statistics, event_distribution)
        return result
    
    def _get_suggestions(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get smart suggestions"""
        current_context = parameters.get('current_context', {})
        historical_patterns = parameters.get('historical_patterns', [])
        
        result = self.core_claude_sdk.get_smart_suggestions(current_context, historical_patterns)
        return result
    
    def _analyze_code_quality(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code quality"""
        code_changes = parameters.get('code_changes', [])
        development_tools = parameters.get('development_tools', {})
        
        result = self.core_claude_sdk.analyze_code_quality(code_changes, development_tools)
        return result
    
    def _get_status(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get AI service status"""
        return self.core_claude_sdk.get_system_status()
    
    def _clear_cache(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Clear AI analysis cache"""
        return self.core_claude_sdk.clear_cache()
    
    def get_supported_operations(self) -> list:
        """Get list of supported operations"""
        return [
            'call',                    # Direct Claude API call
            'analyze_patterns',        # Pattern analysis
            'analyze_risks',          # Risk analysis
            'analyze_productivity',   # Productivity analysis
            'get_suggestions',        # Smart suggestions
            'analyze_code_quality',   # Code quality analysis
            'get_status',            # Service status
            'clear_cache'            # Clear cache
        ]