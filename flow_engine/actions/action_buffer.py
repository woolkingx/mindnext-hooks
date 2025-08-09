"""
ActionBuffer - Core Buffer Service Interface
Single-purpose action executor for buffer operations
"""

from typing import Dict, Any, Optional
from datetime import datetime
import json

from .action_base import ActionExecutor, ActionResult
from ..event_layer import HookEvent


class ActionBuffer(ActionExecutor):
    """Buffer Action Executor - Pure interface to CoreBuffer service"""
    
    def __init__(self, core_buffer=None):
        super().__init__()
        self.core_buffer = core_buffer  # Injected by system
    
    def get_action_type(self) -> str:
        return "action.buffer"
    
    def execute(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        """Execute single buffer operation"""
        start_time = datetime.now()
        
        if not self.core_buffer:
            return self._create_result(
                action_id="action.buffer",
                success=False,
                execution_time=0,
                error="CoreBuffer service not available"
            )
        
        try:
            operation = parameters.get('operation', 'get_latest')
            
            # Single-purpose operations only
            if operation == 'get_latest':
                result = self._get_latest_events(parameters)
            elif operation == 'push':
                result = self._push_event(parameters)
            elif operation == 'get_info':
                result = self._get_buffer_info(parameters)
            elif operation == 'clear':
                result = self._clear_buffer(parameters)
            elif operation == 'export':
                result = self._export_buffer(parameters)
            else:
                return self._create_result(
                    action_id="action.buffer",
                    success=False,
                    execution_time=(datetime.now() - start_time).total_seconds(),
                    error=f"Unknown operation: {operation}"
                )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            return self._create_result(
                action_id="action.buffer",
                success=True,
                execution_time=execution_time,
                data=result
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return self._create_result(
                action_id="action.buffer",
                success=False,
                execution_time=execution_time,
                error=str(e)
            )
    
    def _get_latest_events(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get latest events from buffer"""
        count = parameters.get('count', 5)
        buffer_id = parameters.get('buffer_id', 'events')
        
        if buffer_id == 'events':
            events = self.core_buffer.get_latest_events(count)
            return {
                'operation': 'get_latest',
                'events': events,
                'count': len(events)
            }
        else:
            result = self.core_buffer.get_latest(buffer_id, count)
            return result
    
    def _push_event(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Push event to buffer"""
        data = parameters.get('data')
        metadata = parameters.get('metadata', {})
        buffer_id = parameters.get('buffer_id', 'events')
        
        if not data:
            raise ValueError("No data provided for push operation")
        
        result = self.core_buffer.push(buffer_id, data, metadata)
        return result
    
    def _get_buffer_info(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get buffer information"""
        buffer_id = parameters.get('buffer_id', 'events')
        
        if buffer_id == 'all':
            return self.core_buffer.list_all_buffers()
        else:
            return self.core_buffer.get_buffer_info(buffer_id)
    
    def _clear_buffer(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Clear specific buffer"""
        buffer_id = parameters.get('buffer_id', 'events')
        return self.core_buffer.clear_buffer(buffer_id)
    
    def _export_buffer(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Export buffer data"""
        buffer_id = parameters.get('buffer_id', 'events')
        format = parameters.get('format', 'json')
        
        return self.core_buffer.export_buffer_data(buffer_id, format)
    
    def get_supported_operations(self) -> list:
        """Get list of supported operations"""
        return [
            'get_latest',    # Get latest events
            'push',          # Push new event
            'get_info',      # Get buffer info
            'clear',         # Clear buffer
            'export'         # Export buffer data
        ]