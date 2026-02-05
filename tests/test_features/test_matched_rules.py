"""matched_rules 功能測試"""

import pytest
from unittest.mock import patch
from features import matched_rules


class TestMatchedRulesProcess:
    """測試 matched_rules.process()"""

    def test_process_with_valid_prompt(self):
        """測試有效提示詞返回"""
        mock_rules = [
            {'key': 'mr1', 'name': 'Matched 1', 'content': 'Content 1', 'score': 2},
        ]

        handle_payload = {
            'rule': {},
            'claude': {'prompt': 'testing framework'}
        }

        with patch('v2.features.matched_rules._match_rules', return_value=mock_rules):
            result = matched_rules.process(handle_payload)
            assert result is not None
            assert 'Matched 1' in result
            assert 'Matched Rules' in result

    def test_process_with_empty_prompt(self):
        """測試空提示詞"""
        handle_payload = {
            'rule': {},
            'claude': {'prompt': ''}
        }

        result = matched_rules.process(handle_payload)
        assert result is None

    def test_process_with_no_keywords(self):
        """測試無關鍵詞的提示詞"""
        handle_payload = {
            'rule': {},
            'claude': {'prompt': 'a b'}
        }

        result = matched_rules.process(handle_payload)
        assert result is None

    def test_process_with_no_matching_rules(self):
        """測試沒有匹配規則"""
        handle_payload = {
            'rule': {},
            'claude': {'prompt': 'test something'}
        }

        with patch('v2.features.matched_rules._match_rules', return_value=[]):
            result = matched_rules.process(handle_payload)
            assert result is None


class TestExtractKeywords:
    """測試 _extract_keywords()"""

    def test_extract_keywords_valid(self):
        """測試提取有效關鍵詞"""
        keywords = matched_rules._extract_keywords('testing framework design')
        assert 'testing' in keywords
        assert 'framework' in keywords
        assert 'design' in keywords

    def test_extract_keywords_lowercase(self):
        """測試關鍵詞轉小寫"""
        keywords = matched_rules._extract_keywords('TESTING Framework')
        assert 'testing' in keywords
        assert 'framework' in keywords

    def test_extract_keywords_filters_short(self):
        """測試過濾短詞"""
        keywords = matched_rules._extract_keywords('a bb testing')
        assert 'a' not in keywords
        assert 'bb' not in keywords
        assert 'testing' in keywords

    def test_extract_keywords_empty(self):
        """測試空字符串"""
        keywords = matched_rules._extract_keywords('')
        assert keywords == []


class TestMatchRules:
    """測試 _match_rules()"""

    def test_match_rules_success(self):
        """測試成功匹配規則"""
        mock_results = [
            {'key': 'r1', 'name': 'Rule 1', 'content': 'content', 'score': 2},
        ]

        with patch('v2.utils.db.query_aql', return_value=mock_results):
            result = matched_rules._match_rules(['test', 'keyword'])
            assert result == mock_results

    def test_match_rules_empty(self):
        """測試無結果"""
        with patch('v2.utils.db.query_aql', return_value=[]):
            result = matched_rules._match_rules(['test'])
            assert result == []

    def test_match_rules_none(self):
        """測試 None 返回"""
        with patch('v2.utils.db.query_aql', return_value=None):
            result = matched_rules._match_rules(['test'])
            assert result == []

    def test_match_rules_exception(self):
        """測試異常處理"""
        with patch('v2.utils.db.query_aql', side_effect=Exception('DB Error')):
            result = matched_rules._match_rules(['test'])
            assert result == []

    def test_match_rules_with_config(self):
        """測試讀取配置"""
        mock_results = [{'key': 'r1', 'name': 'Rule', 'content': 'c', 'score': 1}]

        with patch('v2.loaders.config.get', return_value={'max_matched': 5}):
            with patch('v2.utils.db.query_aql', return_value=mock_results) as mock_query:
                result = matched_rules._match_rules(['test'])
                # 驗證查詢被調用
                assert mock_query.called


class TestFormatRules:
    """測試 _format_rules()"""

    def test_format_rules_with_data(self):
        """測試格式化匹配規則"""
        rules = [
            {'key': 'r1', 'name': 'First', 'content': 'First content', 'score': 2},
            {'key': 'r2', 'name': 'Second', 'content': 'Second content', 'score': 1},
        ]

        result = matched_rules._format_rules(rules)
        assert 'First' in result
        assert 'Second' in result
        assert 'Matched Rules' in result

    def test_format_rules_empty(self):
        """測試空規則"""
        result = matched_rules._format_rules([])
        assert result is None

    def test_format_rules_with_missing_fields(self):
        """測試缺失欄位"""
        rules = [
            {'key': 'r1', 'content': 'Just content'},
        ]

        result = matched_rules._format_rules(rules)
        assert result is not None
