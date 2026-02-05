"""refer_kwg 功能測試"""

import pytest
from unittest.mock import patch
from features import refer_kwg


class TestReferKwgProcess:
    """測試 refer_kwg.process()"""

    def test_process_with_valid_prompt(self):
        """測試有效提示詞返回"""
        mock_results = [
            {'key': 'k1', 'title': 'Knowledge 1', 'content': 'Some related content here', 'score': 2},
        ]

        handle_payload = {
            'rule': {},
            'claude': {'prompt': 'testing framework'}
        }

        with patch('v2.features.refer_kwg._query_kwg', return_value=mock_results):
            result = refer_kwg.process(handle_payload)
            assert result is not None
            assert 'Knowledge 1' in result
            assert 'Related Knowledge' in result

    def test_process_with_short_prompt(self):
        """測試短提示詞"""
        handle_payload = {
            'rule': {},
            'claude': {'prompt': 'hi'}
        }

        result = refer_kwg.process(handle_payload)
        assert result is None

    def test_process_with_empty_prompt(self):
        """測試空提示詞"""
        handle_payload = {
            'rule': {},
            'claude': {'prompt': ''}
        }

        result = refer_kwg.process(handle_payload)
        assert result is None

    def test_process_with_no_keywords(self):
        """測試無關鍵詞提示詞"""
        handle_payload = {
            'rule': {},
            'claude': {'prompt': 'a b c'}
        }

        result = refer_kwg.process(handle_payload)
        assert result is None

    def test_process_with_no_results(self):
        """測試無結果"""
        handle_payload = {
            'rule': {},
            'claude': {'prompt': 'test something'}
        }

        with patch('v2.features.refer_kwg._query_kwg', return_value=[]):
            result = refer_kwg.process(handle_payload)
            assert result is None


class TestExtractKeywords:
    """測試 _extract_keywords()"""

    def test_extract_keywords_valid(self):
        """測試提取有效關鍵詞"""
        keywords = refer_kwg._extract_keywords('testing framework design patterns')
        assert 'testing' in keywords
        assert 'framework' in keywords
        assert 'design' in keywords
        assert 'patterns' in keywords

    def test_extract_keywords_lowercase(self):
        """測試轉換為小寫"""
        keywords = refer_kwg._extract_keywords('TESTING Framework')
        assert 'testing' in keywords
        assert 'framework' in keywords

    def test_extract_keywords_filters_short(self):
        """測試過濾短詞（<=3字）"""
        keywords = refer_kwg._extract_keywords('a bb ccc testing')
        assert 'a' not in keywords
        assert 'bb' not in keywords
        assert 'ccc' not in keywords
        assert 'testing' in keywords

    def test_extract_keywords_empty(self):
        """測試空字符串"""
        keywords = refer_kwg._extract_keywords('')
        assert keywords == []

    def test_extract_keywords_only_short_words(self):
        """測試全是短詞"""
        keywords = refer_kwg._extract_keywords('a b c')
        assert keywords == []


class TestQueryKwg:
    """測試 _query_kwg()"""

    def test_query_kwg_success(self):
        """測試成功查詢"""
        mock_results = [
            {'key': 'k1', 'title': 'Knowledge', 'content': 'Content', 'score': 2},
        ]

        with patch('v2.utils.db.query_aql', return_value=mock_results):
            result = refer_kwg._query_kwg(['test', 'keyword'])
            assert result == mock_results

    def test_query_kwg_empty(self):
        """測試空結果"""
        with patch('v2.utils.db.query_aql', return_value=[]):
            result = refer_kwg._query_kwg(['test'])
            assert result == []

    def test_query_kwg_none(self):
        """測試 None 返回"""
        with patch('v2.utils.db.query_aql', return_value=None):
            result = refer_kwg._query_kwg(['test'])
            assert result == []

    def test_query_kwg_exception(self):
        """測試異常處理"""
        with patch('v2.utils.db.query_aql', side_effect=Exception('DB Error')):
            result = refer_kwg._query_kwg(['test'])
            assert result == []

    def test_query_kwg_with_config(self):
        """測試讀取配置中的限制"""
        mock_results = [
            {'key': 'k1', 'title': 'K1', 'content': 'c', 'score': 1},
        ]

        with patch('v2.loaders.config.get', return_value={'refer_kwg_limit': 3}):
            with patch('v2.utils.db.query_aql', return_value=mock_results) as mock_query:
                result = refer_kwg._query_kwg(['test'])
                assert mock_query.called
                # 驗證傳入的限制參數
                call_args = mock_query.call_args
                assert call_args is not None


class TestFormatResults:
    """測試 _format_results()"""

    def test_format_results_with_data(self):
        """測試格式化結果"""
        results = [
            {'key': 'k1', 'title': 'First', 'content': 'First knowledge content', 'score': 2},
            {'key': 'k2', 'title': 'Second', 'content': 'Second knowledge content', 'score': 1},
        ]

        result = refer_kwg._format_results(results)
        assert 'First' in result
        assert 'Second' in result
        assert 'Related Knowledge' in result

    def test_format_results_truncates_content(self):
        """測試內容截斷"""
        long_content = 'a' * 200
        results = [
            {'key': 'k1', 'title': 'Test', 'content': long_content, 'score': 1},
        ]

        result = refer_kwg._format_results(results)
        # 應該被截斷到100字符
        assert long_content not in result

    def test_format_results_empty(self):
        """測試空結果"""
        result = refer_kwg._format_results([])
        assert result is None

    def test_format_results_none(self):
        """測試 None 輸入"""
        result = refer_kwg._format_results(None)
        assert result is None

    def test_format_results_with_missing_fields(self):
        """測試缺失欄位"""
        results = [
            {'key': 'k1', 'content': 'Just content'},
            {'title': 'Just title'},
        ]

        result = refer_kwg._format_results(results)
        assert result is not None

    def test_format_results_contains_header(self):
        """測試包含標題"""
        results = [
            {'key': 'k1', 'title': 'Test', 'content': 'content', 'score': 1},
        ]

        result = refer_kwg._format_results(results)
        assert result.startswith('**Related Knowledge:**')
