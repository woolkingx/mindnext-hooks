"""Load v2-local config.toml once.

v2 is intentionally self-contained. This loader only reads:
    v2/config/config.toml
"""

import tomllib
from pathlib import Path
from typing import Dict, Any, Optional

_CONFIG_PATH = Path(__file__).parent.parent / "config" / "config.toml"
_config_cache: Optional[Dict[str, Any]] = None


def load() -> Dict[str, Any]:
    """Load v2 config (called once during startup)."""
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    try:
        with open(_CONFIG_PATH, "rb") as f:
            _config_cache = tomllib.load(f)
    except FileNotFoundError:
        _config_cache = {}
    except Exception:
        _config_cache = {}

    return _config_cache


def get(key: str, default: Any = None) -> Any:
    """取得單個設定值

    Args:
        key: 點號分隔的鍵，如 "ai.model"
        default: 預設值

    Returns:
        設定值或預設值
    """
    cfg = load()
    keys = key.split(".")
    value = cfg

    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
            if value is None:
                return default
        else:
            return default

    return value if value is not None else default
