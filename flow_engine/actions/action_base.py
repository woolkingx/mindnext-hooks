"""
Base Action Executor Classes
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime

# Import with try-catch to handle relative import issues
try:
    from ..event_layer import HookEvent
except ImportError:
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from event_layer import HookEvent

@dataclass
class ActionResult:
    """Action execution result"""
    action_id: str
    success: bool
    execution_time: float
    output: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class ActionExecutor(ABC):
    """Abstract action executor base class"""
    
    def __init__(self):
        self.execution_count = 0
        self.last_execution = None
        self.total_execution_time = 0.0
    
    @abstractmethod
    def execute(self, event: HookEvent, parameters: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        """Execute action"""
        pass
    
    @abstractmethod
    def get_action_type(self) -> str:
        """Get action type"""
        pass
    
    def get_action_name(self) -> str:
        """Get action name"""
        return self.__class__.__name__
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get execution statistics"""
        return {
            'action_type': self.get_action_type(),
            'action_name': self.get_action_name(),
            'execution_count': self.execution_count,
            'last_execution': self.last_execution.isoformat() if self.last_execution else None,
            'total_execution_time': self.total_execution_time,
            'average_execution_time': self.total_execution_time / self.execution_count if self.execution_count > 0 else 0
        }
    
    def _update_statistics(self, result: ActionResult):
        """Update statistics information"""
        self.execution_count += 1
        self.last_execution = datetime.now()
        self.total_execution_time += result.execution_time
    
    def _create_result(self, action_id: str, success: bool, execution_time: float = 0.0, 
                      output: Any = None, error: Optional[str] = None, 
                      metadata: Dict[str, Any] = None) -> ActionResult:
        """Create action result"""
        result = ActionResult(
            action_id=action_id,
            success=success,
            execution_time=execution_time,
            output=output,
            error=error,
            metadata=metadata or {}
        )
        self._update_statistics(result)
        return result

# Alias for backward compatibility
BaseActionExecutor = ActionExecutor