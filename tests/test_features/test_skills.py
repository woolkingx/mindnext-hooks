"""skills 功能測試"""

import pytest
from features import skills


class TestSkillsProcess:
    """測試 skills.process()"""

    def test_process_refactor_skill(self):
        """測試 refactor 技能檢測"""
        handle_payload = {
            'rule': {},
            'claude': {'prompt': 'Can you refactor this code?'}
        }

        result = skills.process(handle_payload)
        assert result is not None
        assert 'Refactor' in result

    def test_process_debug_skill(self):
        """測試 debug 技能檢測"""
        handle_payload = {
            'rule': {},
            'claude': {'prompt': 'Help me debug this issue'}
        }

        result = skills.process(handle_payload)
        assert result is not None
        assert 'Debug' in result

    def test_process_test_skill(self):
        """測試 test 技能檢測"""
        handle_payload = {
            'rule': {},
            'claude': {'prompt': 'Write unit tests for this'}
        }

        result = skills.process(handle_payload)
        assert result is not None
        assert 'Test' in result

    def test_process_document_skill(self):
        """測試 document 技能檢測"""
        handle_payload = {
            'rule': {},
            'claude': {'prompt': 'Write documentation for this'}
        }

        result = skills.process(handle_payload)
        assert result is not None
        assert 'Document' in result

    def test_process_no_skill_match(self):
        """測試無技能匹配"""
        handle_payload = {
            'rule': {},
            'claude': {'prompt': 'Hello world'}
        }

        result = skills.process(handle_payload)
        assert result is None

    def test_process_multiple_skills(self):
        """測試多個技能匹配"""
        handle_payload = {
            'rule': {},
            'claude': {'prompt': 'Refactor and test this code'}
        }

        result = skills.process(handle_payload)
        assert result is not None
        # 至少包含一個技能
        assert 'skill' in result.lower() or 'Refactor' in result or 'Test' in result


class TestMatchSkills:
    """測試 match_skills()"""

    def test_match_refactor_keyword(self):
        """測試 refactor 關鍵字"""
        matched = skills.match_skills('refactor the code')
        assert 'refactor' in matched

    def test_match_rewrite_keyword(self):
        """測試 rewrite 關鍵字"""
        matched = skills.match_skills('rewrite this')
        assert 'refactor' in matched

    def test_match_debug_keyword(self):
        """測試 debug 關鍵字"""
        matched = skills.match_skills('I need to debug')
        assert 'debug' in matched

    def test_match_test_keyword(self):
        """測試 test 關鍵字"""
        matched = skills.match_skills('testing is important')
        assert 'test' in matched

    def test_match_case_insensitive(self):
        """測試不分大小寫"""
        matched = skills.match_skills('REFACTOR THIS')
        assert 'refactor' in matched

    def test_match_no_skill(self):
        """測試無匹配"""
        matched = skills.match_skills('hello world')
        assert matched == []

    def test_match_empty_text(self):
        """測試空文本"""
        matched = skills.match_skills('')
        assert matched == []


class TestGetSkillInfo:
    """測試 get_skill_info()"""

    def test_get_refactor_info(self):
        """測試取得 refactor 信息"""
        info = skills.get_skill_info('refactor')
        assert info is not None
        assert 'Refactor' in info

    def test_get_debug_info(self):
        """測試取得 debug 信息"""
        info = skills.get_skill_info('debug')
        assert info is not None
        assert 'Debug' in info

    def test_get_test_info(self):
        """測試取得 test 信息"""
        info = skills.get_skill_info('test')
        assert info is not None
        assert 'Test' in info

    def test_get_document_info(self):
        """測試取得 document 信息"""
        info = skills.get_skill_info('document')
        assert info is not None
        assert 'Document' in info

    def test_get_nonexistent_skill(self):
        """測試不存在的技能"""
        info = skills.get_skill_info('nonexistent')
        assert info is None

    def test_skill_info_format(self):
        """測試技能信息格式"""
        info = skills.get_skill_info('refactor')
        assert isinstance(info, str)
        assert len(info) > 0
