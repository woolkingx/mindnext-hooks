"""agents 功能 — 代理匹配和協作建議

職責：
- 從 prompt 檢測是否需要代理
- 推薦合適的代理
- 返回代理協作指引
"""

from typing import Optional
from utils.context import get_event

def process() -> Optional[str]:
    """處理代理匹配

    Args:
        注意: event 從全局 EventContext.get() 取得

    Returns:
        代理建議或 None
    """
    event = get_event()
    prompt = event.prompt if hasattr(event, 'prompt') else ''

    # 檢測是否需要代理
    agents = match_agents(prompt)
    if not agents:
        return None

    # 返回代理建議
    results = []
    for agent in agents:
        info = get_agent_info(agent)
        if info:
            results.append(info)

    if results:
        return '\n\n'.join(results)

    return None

def match_agents(text: str) -> list:
    """從 prompt 檢測是否需要代理

    Args:
        text: Prompt 文本

    Returns:
        匹配的代理列表
    """
    # 簡單的關鍵字匹配
    keywords = {
        'code-review': ['code review', 'review code', 'peer review'],
        'security': ['security', 'vulnerability', 'secure'],
        'performance': ['performance', 'optimize', 'slow'],
        'architecture': ['architecture', 'design pattern', 'structure'],
    }

    matched = []
    text_lower = text.lower()

    for agent, keywords_list in keywords.items():
        if any(kw in text_lower for kw in keywords_list):
            matched.append(agent)

    return matched

def get_agent_info(agent: str) -> Optional[str]:
    """取得代理信息

    Args:
        agent: 代理名稱

    Returns:
        代理信息或 None
    """
    # 代理數據庫
    agents_db = {
        'code-review': 'Code Review Agent: Analyzing code quality, style, and best practices.',
        'security': 'Security Agent: Checking for vulnerabilities and security issues.',
        'performance': 'Performance Agent: Optimizing code for speed and efficiency.',
        'architecture': 'Architecture Agent: Evaluating system design and structure.',
    }

    return agents_db.get(agent)
