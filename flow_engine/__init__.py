"""
MindNext Hooks 三層流程引擎
Event Layer → Rule Layer → Action Flow Layer

架構說明:
1. Event Layer: 捕獲和分類事件 (UserPromptSubmit, PreToolUse, PostToolUse 等)
2. Rule Layer: 基於條件匹配決定觸發哪些規則
3. Action Flow Layer: 執行具體動作管道 (品質檢查, 記錄, 分析等)
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