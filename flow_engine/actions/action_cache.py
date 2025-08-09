"""
ActionCache - Core Cache Service Interface
Single-purpose action executor for cache operations
"""

from typing import Dict, Any, Optional
from datetime import datetime
import json

from .action_base import ActionExecutor, ActionResult
from ..event_layer import HookEvent


class ActionCache(ActionExecutor):
    """Cache Action Executor - Pure interface to CoreCache service"""
    
    def __init__(self, core_cache=None):
        super().__init__()
        self.core_cache = core_cache  # Injected by system
    
    def get_action_type(self) -> str:
        return "action.cache"
    
    def execute(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        """Execute single cache operation"""
        start_time = datetime.now()
        
        if not self.core_cache:
            return self._create_result(
                action_id="action.cache",
                success=False,
                execution_time=0,
                error="CoreCache service not available"
            )
        
        try:
            operation = parameters.get('operation', 'get')
            
            # Single-purpose operations only
            if operation == 'get':
                result = self._get_cache(parameters)
            elif operation == 'set':
                result = self._set_cache(parameters)
            elif operation == 'delete':
                result = self._delete_cache(parameters)
            elif operation == 'exists':
                result = self._check_exists(parameters)
            elif operation == 'clear':
                result = self._clear_cache(parameters)
            elif operation == 'stats':
                result = self._get_stats(parameters)
            elif operation == 'cleanup':
                result = self._cleanup_expired(parameters)
            else:
                return self._create_result(
                    action_id="action.cache",
                    success=False,
                    execution_time=(datetime.now() - start_time).total_seconds(),
                    error=f"Unknown operation: {operation}"
                )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            return self._create_result(
                action_id="action.cache",
                success=True,
                execution_time=execution_time,
                data=result
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return self._create_result(
                action_id="action.cache",
                success=False,
                execution_time=execution_time,
                error=str(e)
            )
    
    def _get_cache(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get value from cache"""
        key = parameters.get('key')
        default = parameters.get('default')
        
        if not key:
            raise ValueError("No key provided for get operation")
        
        if default is not None:
            # Use convenience method
            value = self.core_cache.get_value(key, default)
            return {
                'operation': 'get',
                'key': key,
                'value': value,
                'found': value != default
            }
        else:
            # Use full method with metadata
            result = self.core_cache.get(key)
            return result
    
    def _set_cache(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Set value in cache"""
        key = parameters.get('key')
        value = parameters.get('value')
        ttl_minutes = parameters.get('ttl_minutes')
        
        if not key:
            raise ValueError("No key provided for set operation")
        if value is None:
            raise ValueError("No value provided for set operation")
        
        result = self.core_cache.set(key, value, ttl_minutes)
        return result
    
    def _delete_cache(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Delete cache entry"""
        key = parameters.get('key')
        
        if not key:
            raise ValueError("No key provided for delete operation")
        
        result = self.core_cache.delete(key)
        return result
    
    def _check_exists(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Check if key exists in cache"""
        key = parameters.get('key')
        
        if not key:
            raise ValueError("No key provided for exists operation")
        
        result = self.core_cache.exists(key)
        return result
    
    def _clear_cache(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Clear all cache entries"""
        return self.core_cache.clear_all()
    
    def _get_stats(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get cache statistics"""
        return self.core_cache.get_stats()
    
    def _cleanup_expired(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up expired cache entries"""
        return self.core_cache.cleanup_expired()
    
    def get_supported_operations(self) -> list:
        """Get list of supported operations"""
        return [
            'get',       # Get cache value
            'set',       # Set cache value
            'delete',    # Delete cache entry
            'exists',    # Check if key exists
            'clear',     # Clear all cache
            'stats',     # Get cache statistics
            'cleanup'    # Cleanup expired entries
        ]