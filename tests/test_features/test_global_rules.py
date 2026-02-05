"""global_rules 功能測試"""

import pytest
from unittest.mock import patch, MagicMock
from features import global_rules


class TestGlobalRulesProcess:
    """測試 global_rules.process()"""

    def test_process_with_valid_rules(self):
        """測試有效規則返回"""
        mock_rules = [
            {'key': 'rule1', 'name': 'Rule 1', 'content': 'Content 1'},
            {'key': 'rule2', 'name': 'Rule 2', 'content': 'Content 2'},
        ]

        handle_payload = {
            'rule': {},
            'claude': {'prompt': 'test'}
        }

        with patch('v2.features.global_rules._load_global_rules', return_value=mock_rules):
            result = global_rules.process(handle_payload)
            assert result is not None
            assert 'Rule 1' in result
            assert 'Rule 2' in result
            assert 'Content 1' in result
            assert 'Content 2' in result

    def test_process_with_empty_rules(self):
        """測試空規則返回 None"""
        handle_payload = {
            'rule': {},
            'claude': {'prompt': 'test'}
        }

        with patch('v2.features.global_rules._load_global_rules', return_value=[]):
            result = global_rules.process(handle_payload)
            assert result is None

    def test_process_with_none_rules(self):
        """測試 None 規則返回 None"""
        handle_payload = {
            'rule': {},
            'claude': {'prompt': 'test'}
        }

        with patch('v2.features.global_rules._load_global_rules', return_value=None):
            result = global_rules.process(handle_payload)
            assert result is None


class TestLoadGlobalRules:
    """測試 _load_global_rules()"""

    def test_load_global_rules_success(self):
        """測試成功載入規則"""
        mock_results = [
            {'key': 'g1', 'name': 'Global 1', 'content': 'Content'},
        ]

        with patch('v2.utils.db.query_aql', return_value=mock_results):
            result = global_rules._load_global_rules()
            assert result == mock_results
            assert len(result) == 1

    def test_load_global_rules_empty(self):
        """測試空結果"""
        with patch('v2.utils.db.query_aql', return_value=[]):
            result = global_rules._load_global_rules()
            assert result == []

    def test_load_global_rules_none_result(self):
        """測試 None 返回"""
        with patch('v2.utils.db.query_aql', return_value=None):
            result = global_rules._load_global_rules()
            assert result == []

    def test_load_global_rules_exception(self):
        """測試異常處理"""
        with patch('v2.utils.db.query_aql', side_effect=Exception('DB Error')):
            result = global_rules._load_global_rules()
            assert result == []


class TestFormatRules:
    """測試 _format_rules()"""

    def test_format_rules_with_data(self):
        """測試格式化規則"""
        rules = [
            {'key': 'r1', 'name': 'First', 'content': 'First content'},
            {'key': 'r2', 'name': 'Second', 'content': 'Second content'},
        ]

        result = global_rules._format_rules(rules)
        assert 'First' in result
        assert 'Second' in result
        assert 'First content' in result
        assert 'Global Rules' in result

    def test_format_rules_with_missing_fields(self):
        """測試缺失欄位處理"""
        rules = [
            {'key': 'r1', 'content': 'Some content'},
            {'name': 'R2'},
        ]

        result = global_rules._format_rules(rules)
        assert result is not None
        assert 'r1' in result or 'Some content' in result

    def test_format_rules_empty(self):
        """測試空規則"""
        result = global_rules._format_rules([])
        assert result is None

    def test_format_rules_none(self):
        """測試 None 輸入"""
        result = global_rules._format_rules(None)
        assert result is None

    def test_format_rules_contains_header(self):
        """測試格式化包含標題"""
        rules = [{'key': 'r1', 'name': 'Test', 'content': 'content'}]
        result = global_rules._format_rules(rules)
        assert result.startswith('**Global Rules:**')
