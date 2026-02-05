from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class HookResult:
    """Hook 處理結果統一介面"""

    # 事件名稱
    event_name: Optional[str] = None

    # Permission 類（PreToolUse, PermissionRequest）
    permission: Optional[str] = None  # allow/deny/ask
    permission_reason: Optional[str] = None
    updated_input: Optional[Dict] = None
    interrupt: bool = False

    # Decision 類（PostToolUse, UserPromptSubmit, Stop, SubagentStop）
    block: bool = False
    block_reason: Optional[str] = None

    # Context 類（所有事件）
    additional_context: Optional[str] = None

    # System 類
    continue_processing: bool = True
    stop_reason: Optional[str] = None
    suppress: bool = False
    system_message: Optional[str] = None

    # 完整控制（高級用法）
    hook_output: Optional[Dict] = None


# 類型別名
RulePayload = Dict[str, Any]  # Rule 配置 (仍用 dict,因為結構動態)

# HandlePayload 現在包含型別化的 event
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from utils.events import BaseEvent

class HandlePayload(Dict[str, Any]):
    """
    Handle Payload 結構

    包含:
    - rule: RulePayload (dict)
    - event: BaseEvent (型別化物件)
    """
    pass
