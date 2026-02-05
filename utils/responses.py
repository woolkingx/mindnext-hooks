"""
Claude Code Hooks 輸出結構的型別定義
Based on docs/hooks-matrix.md Section 3
"""
from dataclasses import dataclass, field, asdict
from typing import Optional, Literal, Dict, Any
from abc import ABC, abstractmethod


# ============================================================================
# 通用輸出字段
# ============================================================================

@dataclass
class BaseResponse(ABC):
    """所有 hook 輸出的基類"""
    continue_: Optional[bool] = field(default=None, metadata={'json_key': 'continue'})
    stop_reason: Optional[str] = field(default=None, metadata={'json_key': 'stopReason'})
    suppress_output: Optional[bool] = field(default=None, metadata={'json_key': 'suppressOutput'})
    system_message: Optional[str] = field(default=None, metadata={'json_key': 'systemMessage'})

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """轉換為 JSON dict"""
        pass

    def _base_dict(self) -> Dict[str, Any]:
        """提取通用字段"""
        result = {}
        if self.continue_ is not None:
            result['continue'] = self.continue_
        if self.stop_reason:
            result['stopReason'] = self.stop_reason
        if self.suppress_output is not None:
            result['suppressOutput'] = self.suppress_output
        if self.system_message:
            result['systemMessage'] = self.system_message
        return result


# ============================================================================
# PreToolUse / PermissionRequest 輸出
# ============================================================================

@dataclass
class PreToolUseResponse(BaseResponse):
    """PreToolUse 專用輸出"""
    permission_decision: Optional[Literal['allow', 'deny', 'ask']] = None
    permission_decision_reason: Optional[str] = None
    updated_input: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = self._base_dict()

        hook_specific = {}
        if self.permission_decision:
            hook_specific['permissionDecision'] = self.permission_decision
        if self.permission_decision_reason:
            hook_specific['permissionDecisionReason'] = self.permission_decision_reason
        if self.updated_input:
            hook_specific['updatedInput'] = self.updated_input

        if hook_specific:
            result['hookSpecificOutput'] = hook_specific

        return result


@dataclass
class PermissionRequestResponse(BaseResponse):
    """PermissionRequest 專用輸出"""
    behavior: Optional[Literal['allow', 'deny']] = None
    updated_input: Optional[Dict[str, Any]] = None
    message: Optional[str] = None  # deny 時必填
    interrupt: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        result = self._base_dict()

        decision = {}
        if self.behavior:
            decision['behavior'] = self.behavior
        if self.updated_input:
            decision['updatedInput'] = self.updated_input
        if self.message:
            decision['message'] = self.message
        if self.interrupt is not None:
            decision['interrupt'] = self.interrupt

        if decision:
            result['hookSpecificOutput'] = {'decision': decision}

        return result


# ============================================================================
# PostToolUse / UserPromptSubmit / Stop / SubagentStop 輸出 (可阻止)
# ============================================================================

@dataclass
class BlockableResponse(BaseResponse):
    """可阻止的事件通用輸出"""
    decision: Optional[Literal['block']] = None
    reason: Optional[str] = None
    additional_context: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = self._base_dict()

        if self.decision:
            result['decision'] = self.decision
        if self.reason:
            result['reason'] = self.reason

        if self.additional_context:
            result['hookSpecificOutput'] = {
                'additionalContext': self.additional_context
            }

        return result


# ============================================================================
# 僅 Context 輸出 (SessionStart / SubagentStart / Notification / etc.)
# ============================================================================

@dataclass
class ContextOnlyResponse(BaseResponse):
    """僅提供 additionalContext 的事件"""
    additional_context: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = self._base_dict()

        if self.additional_context:
            result['hookSpecificOutput'] = {
                'additionalContext': self.additional_context
            }

        return result


# ============================================================================
# 無輸出控制 (SessionEnd / Notification / PreCompact)
# ============================================================================

@dataclass
class NoControlResponse(BaseResponse):
    """無法控制行為的事件（僅日誌/副作用）"""

    def to_dict(self) -> Dict[str, Any]:
        # 這些事件通常只返回通用字段
        return self._base_dict()


# ============================================================================
# 事件 → Response 映射
# ============================================================================

RESPONSE_CLASSES = {
    "PreToolUse": PreToolUseResponse,
    "PermissionRequest": PermissionRequestResponse,
    "PostToolUse": BlockableResponse,
    "PostToolUseFailure": ContextOnlyResponse,
    "UserPromptSubmit": BlockableResponse,
    "Stop": BlockableResponse,
    "SubagentStart": ContextOnlyResponse,
    "SubagentStop": BlockableResponse,
    "SessionStart": ContextOnlyResponse,
    "SessionEnd": NoControlResponse,
    "Notification": NoControlResponse,
    "PreCompact": NoControlResponse,
}


def create_response(event_name: str) -> BaseResponse:
    """
    根據事件類型創建對應的 Response 物件

    Args:
        event_name: 事件名稱 (如 'PreToolUse')

    Returns:
        對應的 Response 物件

    Raises:
        ValueError: 未知的事件類型
    """
    response_class = RESPONSE_CLASSES.get(event_name)

    if not response_class:
        raise ValueError(f"Unknown event type: {event_name}")

    return response_class()


# ============================================================================
# 型別聯合
# ============================================================================

Response = (
    PreToolUseResponse |
    PermissionRequestResponse |
    BlockableResponse |
    ContextOnlyResponse |
    NoControlResponse
)
