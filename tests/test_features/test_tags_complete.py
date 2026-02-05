"""完整 tags 功能測試 - 包含 todo 和 note 的 CRUD 操作

測試策略:
- 使用 unittest.mock.patch mock v2.utils.db 的函數
- 避免依賴真實 ArangoDB (CI/CD 友好)
- 測試業務邏輯正確性
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from features.tags import process
from features.tags import todo, note, search


# ============ Todo Tests ============

class TestTodoAdd:
    """測試 /tags todo add"""

    @patch('v2.utils.db.get_db')
    @patch('v2.utils.db.insert')
    def test_todo_add_success(self, mock_insert, mock_get_db):
        """測試成功新增 todo"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_insert.return_value = {'_key': 'abc123'}

        handle_payload = {
            'claude': {'prompt': '/tags todo add "測試任務" #high'}
        }

        result = process(handle_payload)

        assert result is not None
        assert '✅' in result
        assert '新增' in result
        # 檢查返回結果包含新增任務內容
        assert '測試任務' in result
        mock_insert.assert_called_once()

    @patch('v2.utils.db.get_db')
    def test_todo_add_no_content(self, mock_get_db):
        """測試新增無內容的 todo"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        handle_payload = {
            'claude': {'prompt': '/tags todo add'}
        }

        result = process(handle_payload)

        assert result is not None
        assert '請提供任務內容' in result

    @patch('v2.utils.db.get_db')
    @patch('v2.utils.db.insert')
    def test_todo_add_with_priority(self, mock_insert, mock_get_db):
        """測試新增 todo 帶優先級"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_insert.return_value = {'_key': 'xyz789'}

        handle_payload = {
            'claude': {'prompt': '/tags todo add "高優先任務" -P high'}
        }

        result = process(handle_payload)

        assert result is not None
        assert '✅' in result
        # 檢查 insert 時是否設定優先級為 8
        call_args = mock_insert.call_args[0][1]
        assert call_args.get('priority') == 8

    @patch('v2.utils.db.get_db')
    def test_todo_add_db_not_available(self, mock_get_db):
        """測試 DB 不可用"""
        mock_get_db.return_value = None

        with patch('v2.utils.db.get_db_error', return_value='Connection failed'):
            handle_payload = {
                'claude': {'prompt': '/tags todo add "測試"'}
            }
            result = process(handle_payload)

            assert '❌' in result
            assert 'Connection failed' in result


class TestTodoList:
    """測試 /tags todo list"""

    @patch('v2.utils.db.get_db')
    @patch('v2.utils.db.query_aql')
    def test_todo_list_success(self, mock_query, mock_get_db):
        """測試成功列出 todos"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_todos = [
            {
                '_key': 'todo1',
                'content': '任務1',
                'priority': 8,
                'status': 'pending',
                'tags': ['#high'],
                'project': '_user',
                'created_at': '2025-01-19T10:00:00'
            },
            {
                '_key': 'todo2',
                'content': '任務2',
                'priority': 5,
                'status': 'done',
                'tags': [],
                'project': '_user',
                'created_at': '2025-01-19T11:00:00'
            }
        ]
        mock_query.return_value = mock_todos

        handle_payload = {
            'claude': {'prompt': '/tags todo list -a'}  # -a to show all including done
        }

        result = process(handle_payload)

        assert result is not None
        assert '**全局 Todo**' in result or '全局' in result or 'Todo' in result
        assert '任務1' in result
        assert '任務2' in result

    @patch('v2.utils.db.get_db')
    @patch('v2.utils.db.query_aql')
    def test_todo_list_empty(self, mock_query, mock_get_db):
        """測試列出空的 todos"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_query.return_value = None

        handle_payload = {
            'claude': {'prompt': '/tags todo list'}
        }

        result = process(handle_payload)

        assert result is not None
        assert '無 todo' in result

    @patch('v2.utils.db.get_db')
    @patch('v2.utils.db.query_aql')
    def test_todo_list_with_filter_tags(self, mock_query, mock_get_db):
        """測試按標籤過濾 todos"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_todos = [
            {
                '_key': 'todo1',
                'content': '高優先任務',
                'priority': 8,
                'status': 'pending',
                'tags': ['#high'],
                'project': '_user',
                'created_at': '2025-01-19T10:00:00'
            }
        ]
        mock_query.return_value = mock_todos

        handle_payload = {
            'claude': {'prompt': '/tags todo list #high'}
        }

        result = process(handle_payload)

        assert result is not None
        assert '高優先任務' in result


class TestTodoDone:
    """測試 /tags todo done"""

    @patch('v2.utils.db.get_db')
    @patch('v2.utils.db.find_by_key')
    @patch('v2.utils.db.update')
    def test_todo_done_success(self, mock_update, mock_find, mock_get_db):
        """測試成功完成 todo"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_doc = {
            '_key': 'todo1',
            'content': '完成這個任務',
            'status': 'pending'
        }
        mock_find.return_value = mock_doc
        mock_update.return_value = {'_rev': 'new_rev'}

        handle_payload = {
            'claude': {'prompt': '/tags todo done todo1'}
        }

        result = process(handle_payload)

        assert result is not None
        assert '✅' in result
        assert '完成' in result
        assert 'todo1' in result
        mock_update.assert_called_once()

    @patch('v2.utils.db.get_db')
    @patch('v2.utils.db.find_by_key')
    def test_todo_done_not_found(self, mock_find, mock_get_db):
        """測試完成不存在的 todo"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_find.return_value = None

        handle_payload = {
            'claude': {'prompt': '/tags todo done nonexistent'}
        }

        result = process(handle_payload)

        assert result is not None
        assert '❌' in result
        assert '找不到' in result


class TestTodoRemove:
    """測試 /tags todo rm"""

    @patch('v2.utils.db.get_db')
    @patch('v2.utils.db.find_by_key')
    @patch('v2.utils.db.delete')
    def test_todo_remove_success(self, mock_delete, mock_find, mock_get_db):
        """測試成功刪除 todo"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_doc = {
            '_key': 'todo1',
            'content': '要刪除的任務'
        }
        mock_find.return_value = mock_doc
        mock_delete.return_value = True

        handle_payload = {
            'claude': {'prompt': '/tags todo rm todo1'}
        }

        result = process(handle_payload)

        assert result is not None
        assert '🗑' in result
        assert '刪除' in result
        assert 'todo1' in result


class TestTodoUpdate:
    """測試 /tags todo update"""

    @patch('v2.utils.db.get_db')
    @patch('v2.utils.db.find_by_key')
    @patch('v2.utils.db.update')
    def test_todo_update_content(self, mock_update, mock_find, mock_get_db):
        """測試更新 todo 內容"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_doc = {'_key': 'todo1', 'content': '舊內容'}
        mock_find.return_value = mock_doc
        mock_update.return_value = {'_rev': 'new_rev'}

        handle_payload = {
            'claude': {'prompt': '/tags todo update todo1 "新內容"'}
        }

        result = process(handle_payload)

        assert result is not None
        assert '✏️' in result
        assert '已更新' in result

    @patch('v2.utils.db.get_db')
    @patch('v2.utils.db.find_by_key')
    @patch('v2.utils.db.update')
    def test_todo_update_priority(self, mock_update, mock_find, mock_get_db):
        """測試更新 todo 優先級"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_doc = {'_key': 'todo1', 'priority': 5}
        mock_find.return_value = mock_doc
        mock_update.return_value = {'_rev': 'new_rev'}

        handle_payload = {
            'claude': {'prompt': '/tags todo update todo1 -P 9'}
        }

        result = process(handle_payload)

        assert result is not None
        assert '✏️' in result


# ============ Note Tests ============

class TestNoteAdd:
    """測試 /tags note add"""

    @patch('v2.utils.db.get_db')
    @patch('v2.utils.db.insert')
    def test_note_add_success(self, mock_insert, mock_get_db):
        """測試成功新增 note"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_insert.return_value = {'_key': 'note1'}

        handle_payload = {
            'claude': {'prompt': '/tags note add "這是一個筆記" #topic'}
        }

        result = process(handle_payload)

        assert result is not None
        assert '✅' in result
        assert '新增筆記' in result
        assert 'note1' in result
        mock_insert.assert_called_once()

    @patch('v2.utils.db.get_db')
    def test_note_add_no_content(self, mock_get_db):
        """測試新增無內容的 note"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        handle_payload = {
            'claude': {'prompt': '/tags note add'}
        }

        result = process(handle_payload)

        assert result is not None
        assert '請提供筆記內容' in result


class TestNoteList:
    """測試 /tags note list"""

    @patch('v2.utils.db.get_db')
    @patch('v2.utils.db.query_aql')
    def test_note_list_success(self, mock_query, mock_get_db):
        """測試成功列出 notes"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_notes = [
            {
                '_key': 'note1',
                'title': '筆記1',
                'content': '內容1',
                'tags': ['#topic1'],
                'created_at': '2025-01-19T10:00:00'
            }
        ]
        mock_query.return_value = mock_notes

        handle_payload = {
            'claude': {'prompt': '/tags note list'}
        }

        result = process(handle_payload)

        assert result is not None
        assert '**Notes**' in result
        assert '筆記1' in result

    @patch('v2.utils.db.get_db')
    @patch('v2.utils.db.query_aql')
    def test_note_list_empty(self, mock_query, mock_get_db):
        """測試列出空的 notes"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_query.return_value = None

        handle_payload = {
            'claude': {'prompt': '/tags note list'}
        }

        result = process(handle_payload)

        assert result is not None
        assert '無筆記' in result


class TestNoteRemove:
    """測試 /tags note rm"""

    @patch('v2.utils.db.get_db')
    @patch('v2.utils.db.find_by_key')
    @patch('v2.utils.db.delete')
    def test_note_remove_success(self, mock_delete, mock_find, mock_get_db):
        """測試成功刪除 note"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_doc = {
            '_key': 'note1',
            'title': '要刪除的筆記'
        }
        mock_find.return_value = mock_doc
        mock_delete.return_value = True

        handle_payload = {
            'claude': {'prompt': '/tags note rm note1'}
        }

        result = process(handle_payload)

        assert result is not None
        assert '🗑' in result
        assert '刪除' in result


# ============ Search Tests ============

class TestSearch:
    """測試 /tags search"""

    @patch('v2.utils.db.get_db')
    @patch('v2.utils.db.query_aql')
    def test_search_success(self, mock_query, mock_get_db):
        """測試成功搜尋"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_results = [
            {
                'type': 'todo',
                'key': 'todo1',
                'title': '搜尋結果1',
                'tags': ['#search'],
                'score': 2,
                'status': 'pending',
                'created': '2025-01-19T10:00:00'
            },
            {
                'type': 'note',
                'key': 'note1',
                'title': '搜尋結果2',
                'tags': [],
                'score': 1,
                'created': '2025-01-19T09:00:00'
            }
        ]
        mock_query.return_value = mock_results

        handle_payload = {
            'claude': {'prompt': '/tags search 搜尋'}
        }

        result = process(handle_payload)

        assert result is not None
        assert '**搜尋:' in result
        assert '搜尋結果1' in result or '搜尋結果2' in result

    @patch('v2.utils.db.get_db')
    @patch('v2.utils.db.query_aql')
    def test_search_no_results(self, mock_query, mock_get_db):
        """測試搜尋無結果"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_query.return_value = None

        handle_payload = {
            'claude': {'prompt': '/tags search 不存在的'}
        }

        result = process(handle_payload)

        assert result is not None
        assert '無結果' in result


# ============ Integration Tests ============

class TestTagsIntegration:
    """整合測試"""

    @patch('v2.utils.db.get_db')
    def test_tags_non_tags_command(self, mock_get_db):
        """測試非 tags 命令被忽略"""
        handle_payload = {
            'claude': {'prompt': 'hello world'}
        }

        result = process(handle_payload)

        assert result is None

    @patch('v2.utils.db.get_db')
    def test_tags_help(self, mock_get_db):
        """測試幫助命令"""
        handle_payload = {
            'claude': {'prompt': '/tags help'}
        }

        result = process(handle_payload)

        assert result is not None
        assert '**/tags' in result

    @patch('v2.utils.db.get_db')
    def test_tags_todo_help(self, mock_get_db):
        """測試 todo 幫助命令"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        handle_payload = {
            'claude': {'prompt': '/tags todo help'}
        }

        result = process(handle_payload)

        assert result is not None
        assert '**/tags todo' in result

    @patch('v2.utils.db.get_db')
    def test_tags_note_help(self, mock_get_db):
        """測試 note 幫助命令"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        handle_payload = {
            'claude': {'prompt': '/tags note help'}
        }

        result = process(handle_payload)

        assert result is not None
        assert '**/tags note' in result

    def test_tags_with_hash_prefix(self):
        """測試 #tags 前綴轉換"""
        with patch('v2.utils.db.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db

            handle_payload = {
                'claude': {'prompt': '#tags help'}
            }

            result = process(handle_payload)

            assert result is not None
            # Should process same as /tags


# ============ Priority Tests ============

class TestPriorityParsing:
    """優先級解析測試"""

    @patch('v2.utils.db.get_db')
    @patch('v2.utils.db.insert')
    def test_priority_high(self, mock_insert, mock_get_db):
        """測試優先級 high"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_insert.return_value = {'_key': 'abc'}

        handle_payload = {
            'claude': {'prompt': '/tags todo add "任務" -P high'}
        }

        process(handle_payload)

        call_args = mock_insert.call_args[0][1]
        assert call_args.get('priority') == 8

    @patch('v2.utils.db.get_db')
    @patch('v2.utils.db.insert')
    def test_priority_low(self, mock_insert, mock_get_db):
        """測試優先級 low"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_insert.return_value = {'_key': 'abc'}

        handle_payload = {
            'claude': {'prompt': '/tags todo add "任務" -P low'}
        }

        process(handle_payload)

        call_args = mock_insert.call_args[0][1]
        assert call_args.get('priority') == 2

    @patch('v2.utils.db.get_db')
    @patch('v2.utils.db.insert')
    def test_priority_numeric(self, mock_insert, mock_get_db):
        """測試優先級數字"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_insert.return_value = {'_key': 'abc'}

        handle_payload = {
            'claude': {'prompt': '/tags todo add "任務" -P 7'}
        }

        process(handle_payload)

        call_args = mock_insert.call_args[0][1]
        assert call_args.get('priority') == 7


# ============ Tag Tests ============

class TestTagHandling:
    """標籤處理測試"""

    @patch('v2.utils.db.get_db')
    @patch('v2.utils.db.insert')
    def test_tags_single(self, mock_insert, mock_get_db):
        """測試單個標籤"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_insert.return_value = {'_key': 'abc'}

        handle_payload = {
            'claude': {'prompt': '/tags todo add "任務" #important'}
        }

        process(handle_payload)

        call_args = mock_insert.call_args[0][1]
        assert '#important' in call_args.get('tags', [])

    @patch('v2.utils.db.get_db')
    @patch('v2.utils.db.insert')
    def test_tags_multiple(self, mock_insert, mock_get_db):
        """測試多個標籤"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_insert.return_value = {'_key': 'abc'}

        handle_payload = {
            'claude': {'prompt': '/tags todo add "任務" #work #urgent'}
        }

        process(handle_payload)

        call_args = mock_insert.call_args[0][1]
        tags = call_args.get('tags', [])
        assert '#work' in tags
        assert '#urgent' in tags
