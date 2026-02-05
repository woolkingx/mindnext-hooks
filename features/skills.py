"""skills 功能 — 技能匹配和載入

職責：
- 從 prompt 檢測技能關鍵字
- 載入技能信息
"""

from typing import Optional
from utils.context import get_event

def process() -> Optional[str]:
    """處理技能匹配

    Args:
        注意: event 從全局 EventContext.get() 取得

    Returns:
        技能信息或 None
    """
    event = get_event()
    prompt = event.prompt if hasattr(event, 'prompt') else ''

    # 檢測技能關鍵字
    skills = match_skills(prompt)
    if not skills:
        return None

    # 載入技能信息
    results = []
    for skill in skills:
        info = get_skill_info(skill)
        if info:
            results.append(info)

    if results:
        return '\n\n'.join(results)

    return None

def match_skills(text: str) -> list:
    """從 prompt 檢測技能

    Args:
        text: Prompt 文本

    Returns:
        匹配的技能列表
    """
    # 簡單的關鍵字匹配
    keywords = {
        'refactor': ['refactor', 'rewrite', 'restructure'],
        'debug': ['debug', 'troubleshoot', 'fix bug'],
        'test': ['test', 'unit test', 'testing'],
        'document': ['document', 'write doc', 'docstring'],
    }

    matched = []
    text_lower = text.lower()

    for skill, keywords_list in keywords.items():
        if any(kw in text_lower for kw in keywords_list):
            matched.append(skill)

    return matched

def get_skill_info(skill: str) -> Optional[str]:
    """取得技能信息

    Args:
        skill: 技能名稱

    Returns:
        技能信息或 None
    """
    # 技能數據庫
    skills_db = {
        'refactor': 'Refactor skill: Breaking down complex code into cleaner, more maintainable pieces.',
        'debug': 'Debug skill: Systematic approach to identify and fix issues.',
        'test': 'Test skill: Writing comprehensive unit and integration tests.',
        'document': 'Document skill: Clear and comprehensive documentation practices.',
    }

    return skills_db.get(skill)
