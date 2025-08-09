"""
MindNext Hooks Three-layer Flow Engine
Event Layer → Rule Layer → Action Flow Layer

架構說明:
1. Event Layer: 捕獲和分類Event (UserPromptSubmit, PreToolUse, PostToolUse 等)
2. Rule Layer: 基於條件匹配決定觸發哪些規則
3. Action Flow Layer: Execute具體Action管道 (Quality check, Record, Analyze等)
"""

from .event_layer import EventProcessor, HookEvent
from .rule_layer import RuleEngine, Rule, RuleCondition
from .action_layer import ActionFlowExecutor, ActionPipeline, ActionStep
from .flow_coordinator import FlowCoordinator

__all__ = [
    'EventProcessor', 'HookEvent',
    'RuleEngine', 'Rule', 'RuleCondition', 
    'ActionFlowExecutor', 'ActionPipeline', 'ActionStep',
    'FlowCoordinator'
]