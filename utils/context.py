"""
全局 Event Context
物件化後,event 作為只讀環境,全局訪問
"""
from typing import Optional, Any


class EventContext:
    """全局 Event 上下文 (單例)"""

    _event: Optional[Any] = None

    @classmethod
    def set(cls, event: Any):
        """設置當前 event (main.py 啟動時調用一次)"""
        cls._event = event

    @classmethod
    def get(cls) -> Any:
        """取得當前 event"""
        if cls._event is None:
            raise RuntimeError("Event not initialized. Call EventContext.set() first.")
        return cls._event

    @classmethod
    def clear(cls):
        """清除 event (測試用)"""
        cls._event = None


# 便捷函數
def get_event() -> Any:
    """取得當前 event"""
    return EventContext.get()
