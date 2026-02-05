"""Handle 層：UserPromptSubmit 工作流編排

職責：
- 檢查 action
- 調用 features
- 整合結果
"""
import asyncio
from typing import Optional, List, Dict, Any
from type_defs import HookResult
from utils.context import get_event


async def process(rule: Dict[str, Any]) -> Optional[HookResult]:
    """工作流編排

    Rule 4: Handle 是工作流編排
    - 不實現具體邏輯
    - 只負責調用順序

    Args:
        rule: rule 配置 (dict)

    注意: event 從全局 EventContext 取得
    """
    # 從全局取得 event
    event = get_event()

    # 型別窄化 (告訴 IDE 這是 UserPromptSubmit)
    if event.hook_event_name != 'UserPromptSubmit':
        return None

    # 現在可以直接訪問屬性,有 IDE 自動補全!
    # event.prompt
    # event.session_id
    # event.cwd

    # 1. additionalContext（直接注入，最優先）
    if 'additionalContext' in rule:
        return HookResult(
            event_name='UserPromptSubmit',
            additional_context=rule['additionalContext']
        )

    # 2. action: block
    if rule.get('action') == 'block':
        return HookResult(
            event_name='UserPromptSubmit',
            block=True,
            block_reason=rule.get('reason', 'Blocked')
        )

    # 3. feature: 調用 features
    features = rule.get('feature', [])
    if features:
        contexts = await _run_features(features)
        if contexts:
            return HookResult(
                event_name='UserPromptSubmit',
                additional_context='\n\n'.join(contexts)
            )

    return None


async def _run_features(feature_names: List[str]) -> List[str]:
    """並發執行多個 features

    注意: features 也從全局 EventContext 取 event
    """
    tasks = [_call_feature(name) for name in feature_names]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 過濾有效結果
    return [r for r in results if r and not isinstance(r, Exception)]


async def _call_feature(feature_name: str) -> Optional[str]:
    """調用 feature 模組

    注意: feature 的 process() 不再接受參數
          直接從 EventContext 取 event
    """
    try:
        import importlib
        mod = importlib.import_module(f"features.{feature_name}")

        if not hasattr(mod, 'process'):
            return f"⚠️ feature '{feature_name}' 沒有 process 函數"

        # process() 無參數,從全局取 event
        result = mod.process()

        # 支援 async
        if hasattr(result, '__await__'):
            result = await result

        # 處理不同返回類型
        if isinstance(result, HookResult):
            return result.additional_context
        elif isinstance(result, str):
            return result

        return None

    except ModuleNotFoundError:
        return f"⚠️ 找不到 feature: {feature_name}"
    except Exception as e:
        return f"⚠️ feature '{feature_name}' 錯誤: {e}"
