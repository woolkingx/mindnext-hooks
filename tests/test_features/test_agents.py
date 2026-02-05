"""agents 功能測試"""

import pytest
from features import agents


class TestAgentsProcess:
    """測試 agents.process()"""

    def test_process_code_review_agent(self):
        """測試 code-review 代理檢測"""
        handle_payload = {
            'rule': {},
            'claude': {'prompt': 'Please do a code review'}
        }

        result = agents.process(handle_payload)
        assert result is not None
        assert 'Code Review' in result or 'code-review' in result.lower()

    def test_process_security_agent(self):
        """測試 security 代理檢測"""
        handle_payload = {
            'rule': {},
            'claude': {'prompt': 'Check for security vulnerabilities'}
        }

        result = agents.process(handle_payload)
        assert result is not None
        assert 'Security' in result

    def test_process_performance_agent(self):
        """測試 performance 代理檢測"""
        handle_payload = {
            'rule': {},
            'claude': {'prompt': 'Optimize for performance'}
        }

        result = agents.process(handle_payload)
        assert result is not None
        assert 'Performance' in result

    def test_process_architecture_agent(self):
        """測試 architecture 代理檢測"""
        handle_payload = {
            'rule': {},
            'claude': {'prompt': 'Review the architecture'}
        }

        result = agents.process(handle_payload)
        assert result is not None
        assert 'Architecture' in result

    def test_process_no_agent_match(self):
        """測試無代理匹配"""
        handle_payload = {
            'rule': {},
            'claude': {'prompt': 'Hello world'}
        }

        result = agents.process(handle_payload)
        assert result is None

    def test_process_multiple_agents(self):
        """測試多個代理匹配"""
        handle_payload = {
            'rule': {},
            'claude': {'prompt': 'Review code for security and performance'}
        }

        result = agents.process(handle_payload)
        assert result is not None
        # 應該包含多個代理建議


class TestMatchAgents:
    """測試 match_agents()"""

    def test_match_code_review_keyword(self):
        """測試 code review 關鍵字"""
        matched = agents.match_agents('code review')
        assert 'code-review' in matched

    def test_match_review_code_keyword(self):
        """測試 review code 關鍵字"""
        matched = agents.match_agents('review code')
        assert 'code-review' in matched

    def test_match_peer_review_keyword(self):
        """測試 peer review 關鍵字"""
        matched = agents.match_agents('peer review')
        assert 'code-review' in matched

    def test_match_security_keyword(self):
        """測試 security 關鍵字"""
        matched = agents.match_agents('check security')
        assert 'security' in matched

    def test_match_vulnerability_keyword(self):
        """測試 vulnerability 關鍵字"""
        matched = agents.match_agents('find vulnerability')
        assert 'security' in matched

    def test_match_performance_keyword(self):
        """測試 performance 關鍵字"""
        matched = agents.match_agents('improve performance')
        assert 'performance' in matched

    def test_match_optimize_keyword(self):
        """測試 optimize 關鍵字"""
        matched = agents.match_agents('optimize the code')
        assert 'performance' in matched

    def test_match_architecture_keyword(self):
        """測試 architecture 關鍵字"""
        matched = agents.match_agents('architecture review')
        assert 'architecture' in matched

    def test_match_design_pattern_keyword(self):
        """測試 design pattern 關鍵字"""
        matched = agents.match_agents('use design pattern')
        assert 'architecture' in matched

    def test_match_case_insensitive(self):
        """測試不分大小寫"""
        matched = agents.match_agents('CODE REVIEW')
        assert 'code-review' in matched

    def test_match_no_agent(self):
        """測試無匹配"""
        matched = agents.match_agents('hello world')
        assert matched == []


class TestGetAgentInfo:
    """測試 get_agent_info()"""

    def test_get_code_review_info(self):
        """測試取得 code-review 信息"""
        info = agents.get_agent_info('code-review')
        assert info is not None
        assert 'Code Review' in info

    def test_get_security_info(self):
        """測試取得 security 信息"""
        info = agents.get_agent_info('security')
        assert info is not None
        assert 'Security' in info

    def test_get_performance_info(self):
        """測試取得 performance 信息"""
        info = agents.get_agent_info('performance')
        assert info is not None
        assert 'Performance' in info

    def test_get_architecture_info(self):
        """測試取得 architecture 信息"""
        info = agents.get_agent_info('architecture')
        assert info is not None
        assert 'Architecture' in info

    def test_get_nonexistent_agent(self):
        """測試不存在的代理"""
        info = agents.get_agent_info('nonexistent')
        assert info is None

    def test_agent_info_format(self):
        """測試代理信息格式"""
        info = agents.get_agent_info('security')
        assert isinstance(info, str)
        assert len(info) > 0
