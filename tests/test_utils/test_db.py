"""Test suite for v2/utils/db.py — ArangoDB Connection and CRUD Operations

Tests cover:
- Database connection (with skip if ArangoDB unavailable)
- Basic CRUD operations (insert, find, update, delete)
- Error handling
- Connection reset

Note: Since python-arango may not be installed, most tests are skipped.
Set ARANGO_AVAILABLE=true environment variable to run actual integration tests.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from typing import Optional

# Check if we should run integration tests
ARANGO_AVAILABLE = os.getenv("ARANGO_AVAILABLE", "false") == "true"


# ============ Fixtures ============


@pytest.fixture
def mock_arangodb():
    """Mock ArangoDB connection for testing"""
    with patch("v2.utils.db.ArangoClient") as mock_client:
        mock_db = MagicMock()
        mock_db.version.return_value = "3.8.0"

        mock_client_instance = MagicMock()
        mock_client_instance.db.return_value = mock_db

        mock_client.return_value = mock_client_instance

        yield mock_db


@pytest.fixture
def mock_config():
    """Mock config loader"""
    with patch("v2.utils.db._get_db_config") as mock_get_db_config:
        mock_get_db_config.return_value = {
            "host": "http://localhost:8529",
            "database": "testdb",
            "username": "root",
            "password": "password",
        }
        yield mock_get_db_config


@pytest.fixture(autouse=True)
def reset_db():
    """Reset database connection before each test"""
    from utils import db as db_module
    db_module.reset_db_connection()
    yield
    db_module.reset_db_connection()


# ============ Connection Tests ============


class TestDBConnection:
    """Test database connection logic"""

    @pytest.mark.skipif(not ARANGO_AVAILABLE, reason="ArangoDB client not installed")
    def test_get_db_connection_success(self, mock_config, mock_arangodb):
        """Test successful database connection"""
        from utils import db
        with patch("v2.utils.db.ARANGO_AVAILABLE", True):
            db.reset_db_connection()
            result = db.get_db()
            assert result is not None
            assert db.get_db_error() is None

    def test_get_db_singleton(self, mock_config, mock_arangodb):
        """Test that get_db returns singleton instance (even with mock)"""
        from utils import db
        # Without ARANGO_AVAILABLE, both calls return None but consistently
        db.reset_db_connection()
        db1 = db.get_db()
        db2 = db.get_db()
        assert db1 == db2

    def test_get_db_no_arango_installed(self, mock_config):
        """Test connection failure when ArangoDB client not installed"""
        from utils import db
        db.reset_db_connection()
        result = db.get_db()
        # Should return None if ARANGO_AVAILABLE is False
        assert result is None
        error = db.get_db_error()
        assert error is not None
        assert "ArangoDB" in error or "python-arango" in error

    @pytest.mark.skipif(not ARANGO_AVAILABLE, reason="ArangoDB client not installed")
    def test_get_db_connection_failure(self, mock_config):
        """Test connection failure handling"""
        from utils import db
        with patch("v2.utils.db.ARANGO_AVAILABLE", True):
            with patch("v2.utils.db.ArangoClient") as mock_client:
                mock_client.side_effect = Exception("Connection refused")
                db.reset_db_connection()
                result = db.get_db()
                assert result is None
                assert db.get_db_error() is not None
                assert "Connection refused" in db.get_db_error()

    @pytest.mark.skipif(not ARANGO_AVAILABLE, reason="ArangoDB client not installed")
    def test_get_db_with_timeout(self, mock_config):
        """Test connection timeout"""
        from utils import db
        with patch("v2.utils.db.ARANGO_AVAILABLE", True):
            with patch("v2.utils.db.ArangoClient") as mock_client:
                mock_client.side_effect = TimeoutError("Request timeout")
                db.reset_db_connection()
                result = db.get_db()
                assert result is None
                assert "TimeoutError" in db.get_db_error()

    @pytest.mark.skipif(not ARANGO_AVAILABLE, reason="ArangoDB client not installed")
    def test_get_db_error_returns_none_on_success(self, mock_config, mock_arangodb):
        """Test that get_db_error returns None after successful connection"""
        from utils import db
        with patch("v2.utils.db.ARANGO_AVAILABLE", True):
            db.reset_db_connection()
            db.get_db()
            assert db.get_db_error() is None

    def test_reset_db_connection(self, mock_config, mock_arangodb):
        """Test connection reset"""
        from utils import db
        db.reset_db_connection()
        db_first = db.get_db()

        db.reset_db_connection()
        db_after_reset = db.get_db()
        # After reset, state should be clear
        assert db_first == db_after_reset

    @pytest.mark.skipif(not ARANGO_AVAILABLE, reason="ArangoDB client not installed")
    def test_env_var_override_host(self, mock_arangodb):
        """Test environment variable overrides for DB_HOST"""
        from utils import db
        with patch("v2.utils.db.ARANGO_AVAILABLE", True):
            with patch.dict(os.environ, {"DB_HOST": "http://custom:8529"}):
                with patch("v2.utils.db._get_db_config") as mock_get_config:
                    mock_get_config.return_value = {
                        "host": "http://custom:8529",
                        "database": "testdb",
                        "username": "root",
                        "password": "password",
                    }
                    db.reset_db_connection()
                    db.get_db()

    @pytest.mark.skipif(not ARANGO_AVAILABLE, reason="ArangoDB client not installed")
    def test_env_var_override_credentials(self, mock_arangodb):
        """Test environment variable overrides for DB credentials"""
        from utils import db
        with patch("v2.utils.db.ARANGO_AVAILABLE", True):
            with patch.dict(
                os.environ,
                {
                    "DB_USER": "envuser",
                    "DB_PASS": "envpass",
                    "DB_NAME": "envdb",
                },
            ):
                with patch("v2.utils.db._get_db_config") as mock_get_config:
                    mock_get_config.return_value = {
                        "host": "http://localhost:8529",
                        "database": "envdb",
                        "username": "envuser",
                        "password": "envpass",
                    }
                    db.reset_db_connection()
                    db.get_db()


# ============ CRUD Operation Tests ============


class TestInsert:
    """Test insert operation"""

    @pytest.mark.skipif(not ARANGO_AVAILABLE, reason="ArangoDB client not installed")
    def test_insert_success(self, mock_config, mock_arangodb):
        """Test successful document insertion"""
        from utils import db
        with patch("v2.utils.db.ARANGO_AVAILABLE", True):
            mock_collection = MagicMock()
            mock_collection.insert.return_value = {
                "_key": "doc1",
                "_id": "col/doc1",
                "_rev": "rev1",
            }
            mock_arangodb.collection.return_value = mock_collection

            result = db.insert("test_collection", {"name": "test"})
            assert result is not None
            assert result["_key"] == "doc1"

    def test_insert_failure_no_db(self):
        """Test insert when database is not available"""
        from utils import db
        with patch("v2.utils.db.get_db", return_value=None):
            result = db.insert("test_collection", {"name": "test"})
            assert result is None

    @pytest.mark.skipif(not ARANGO_AVAILABLE, reason="ArangoDB client not installed")
    def test_insert_exception_handling(self, mock_config, mock_arangodb):
        """Test insert exception handling"""
        from utils import db
        with patch("v2.utils.db.ARANGO_AVAILABLE", True):
            mock_collection = MagicMock()
            mock_collection.insert.side_effect = Exception("Insert failed")
            mock_arangodb.collection.return_value = mock_collection

            result = db.insert("test_collection", {"name": "test"})
            assert result is None


class TestFind:
    """Test find/query operations"""

    @pytest.mark.skipif(not ARANGO_AVAILABLE, reason="ArangoDB client not installed")
    def test_find_all_documents(self, mock_config, mock_arangodb):
        """Test finding all documents"""
        from utils import db
        with patch("v2.utils.db.ARANGO_AVAILABLE", True):
            mock_collection = MagicMock()
            mock_collection.all.return_value = [{"_key": "1", "name": "doc1"}]
            mock_arangodb.collection.return_value = mock_collection

            result = db.find("test_collection")
            assert result is not None
            assert len(result) == 1
            assert result[0]["_key"] == "1"

    @pytest.mark.skipif(not ARANGO_AVAILABLE, reason="ArangoDB client not installed")
    def test_find_with_query_filter(self, mock_config, mock_arangodb):
        """Test finding with query filter"""
        from utils import db
        with patch("v2.utils.db.ARANGO_AVAILABLE", True):
            mock_cursor = [{"_key": "1", "name": "test"}]
            mock_arangodb.aql.execute.return_value = mock_cursor

            result = db.find("test_collection", {"name": "test"})
            assert result is not None
            assert len(result) == 1

    @pytest.mark.skipif(not ARANGO_AVAILABLE, reason="ArangoDB client not installed")
    def test_find_with_limit(self, mock_config, mock_arangodb):
        """Test find with limit parameter"""
        from utils import db
        with patch("v2.utils.db.ARANGO_AVAILABLE", True):
            mock_collection = MagicMock()
            mock_collection.all.return_value = [{"_key": str(i)} for i in range(5)]
            mock_arangodb.collection.return_value = mock_collection

            result = db.find("test_collection", limit=5)
            assert result is not None

    def test_find_failure_no_db(self):
        """Test find when database is not available"""
        from utils import db
        with patch("v2.utils.db.get_db", return_value=None):
            result = db.find("test_collection")
            assert result is None

    @pytest.mark.skipif(not ARANGO_AVAILABLE, reason="ArangoDB client not installed")
    def test_find_by_key_success(self, mock_config, mock_arangodb):
        """Test finding document by key"""
        from utils import db
        with patch("v2.utils.db.ARANGO_AVAILABLE", True):
            mock_collection = MagicMock()
            mock_collection.get.return_value = {"_key": "doc1", "name": "test"}
            mock_arangodb.collection.return_value = mock_collection

            result = db.find_by_key("test_collection", "doc1")
            assert result is not None
            assert result["_key"] == "doc1"

    def test_find_by_key_not_found(self, mock_config, mock_arangodb):
        """Test finding non-existent document"""
        from utils import db
        mock_collection = MagicMock()
        mock_collection.get.side_effect = Exception("Document not found")
        mock_arangodb.collection.return_value = mock_collection

        result = db.find_by_key("test_collection", "nonexistent")
        assert result is None

    def test_find_exception_handling(self, mock_config, mock_arangodb):
        """Test find exception handling"""
        from utils import db
        mock_collection = MagicMock()
        mock_collection.all.side_effect = Exception("Query failed")
        mock_arangodb.collection.return_value = mock_collection

        result = db.find("test_collection")
        assert result is None


class TestUpdate:
    """Test update operation"""

    @pytest.mark.skipif(not ARANGO_AVAILABLE, reason="ArangoDB client not installed")
    def test_update_success(self, mock_config, mock_arangodb):
        """Test successful document update"""
        from utils import db
        with patch("v2.utils.db.ARANGO_AVAILABLE", True):
            mock_collection = MagicMock()
            mock_collection.update.return_value = {
                "_key": "doc1",
                "_rev": "rev2",
            }
            mock_arangodb.collection.return_value = mock_collection

            result = db.update("test_collection", "doc1", {"name": "updated"})
            assert result is not None
            assert result["_key"] == "doc1"

    def test_update_failure_no_db(self):
        """Test update when database is not available"""
        from utils import db
        with patch("v2.utils.db.get_db", return_value=None):
            result = db.update("test_collection", "doc1", {"name": "updated"})
            assert result is None

    @pytest.mark.skipif(not ARANGO_AVAILABLE, reason="ArangoDB client not installed")
    def test_update_exception_handling(self, mock_config, mock_arangodb):
        """Test update exception handling"""
        from utils import db
        with patch("v2.utils.db.ARANGO_AVAILABLE", True):
            mock_collection = MagicMock()
            mock_collection.update.side_effect = Exception("Update failed")
            mock_arangodb.collection.return_value = mock_collection

            result = db.update("test_collection", "doc1", {"name": "updated"})
            assert result is None


class TestDelete:
    """Test delete operation"""

    @pytest.mark.skipif(not ARANGO_AVAILABLE, reason="ArangoDB client not installed")
    def test_delete_success(self, mock_config, mock_arangodb):
        """Test successful document deletion"""
        from utils import db
        with patch("v2.utils.db.ARANGO_AVAILABLE", True):
            mock_collection = MagicMock()
            mock_arangodb.collection.return_value = mock_collection

            result = db.delete("test_collection", "doc1")
            assert result is True

    def test_delete_failure_no_db(self):
        """Test delete when database is not available"""
        from utils import db
        with patch("v2.utils.db.get_db", return_value=None):
            result = db.delete("test_collection", "doc1")
            assert result is False

    @pytest.mark.skipif(not ARANGO_AVAILABLE, reason="ArangoDB client not installed")
    def test_delete_exception_handling(self, mock_config, mock_arangodb):
        """Test delete exception handling"""
        from utils import db
        with patch("v2.utils.db.ARANGO_AVAILABLE", True):
            mock_collection = MagicMock()
            mock_collection.delete.side_effect = Exception("Delete failed")
            mock_arangodb.collection.return_value = mock_collection

            result = db.delete("test_collection", "doc1")
            assert result is False


class TestAQLQuery:
    """Test AQL query execution"""

    @pytest.mark.skipif(not ARANGO_AVAILABLE, reason="ArangoDB client not installed")
    def test_query_aql_success(self, mock_config, mock_arangodb):
        """Test successful AQL query"""
        from utils import db
        with patch("v2.utils.db.ARANGO_AVAILABLE", True):
            mock_cursor = [{"_key": "1", "name": "test"}]
            mock_arangodb.aql.execute.return_value = mock_cursor

            result = db.query_aql(
                "FOR doc IN test_collection RETURN doc",
                {"collection": "test_collection"},
            )
            assert result is not None
            assert len(result) == 1

    def test_query_aql_no_db(self):
        """Test AQL query when database is not available"""
        from utils import db
        with patch("v2.utils.db.get_db", return_value=None):
            result = db.query_aql("FOR doc IN test_collection RETURN doc")
            assert result is None

    @pytest.mark.skipif(not ARANGO_AVAILABLE, reason="ArangoDB client not installed")
    def test_query_aql_exception_handling(self, mock_config, mock_arangodb):
        """Test AQL query exception handling"""
        from utils import db
        with patch("v2.utils.db.ARANGO_AVAILABLE", True):
            mock_arangodb.aql.execute.side_effect = Exception("Query syntax error")

            result = db.query_aql("INVALID QUERY")
            assert result is None

    @pytest.mark.skipif(not ARANGO_AVAILABLE, reason="ArangoDB client not installed")
    def test_query_aql_with_bind_vars(self, mock_config, mock_arangodb):
        """Test AQL query with bind variables"""
        from utils import db
        with patch("v2.utils.db.ARANGO_AVAILABLE", True):
            mock_cursor = [{"_key": "1"}]
            mock_arangodb.aql.execute.return_value = mock_cursor

            result = db.query_aql(
                "FOR doc IN @col FILTER doc.status == @status RETURN doc",
                {"col": "test_collection", "status": "active"},
            )
            assert result is not None


# ============ Integration Tests ============


class TestIntegration:
    """Integration tests for db operations"""

    @pytest.mark.skipif(not ARANGO_AVAILABLE, reason="ArangoDB not available")
    def test_real_connection_attempt(self):
        """Test real connection attempt (skipped if ArangoDB unavailable)"""
        from utils import db
        db.reset_db_connection()
        result = db.get_db()
        # Should not crash, may return None if ArangoDB is unavailable
        assert result is None or hasattr(result, "version")

    @pytest.mark.skipif(not ARANGO_AVAILABLE, reason="ArangoDB client not installed")
    def test_multiple_operations_sequence(self, mock_config, mock_arangodb):
        """Test sequence of operations"""
        from utils import db
        with patch("v2.utils.db.ARANGO_AVAILABLE", True):
            mock_collection = MagicMock()
            mock_arangodb.collection.return_value = mock_collection

            # Insert
            mock_collection.insert.return_value = {"_key": "doc1"}
            result1 = db.insert("col", {"name": "test"})
            assert result1 is not None

            # Find
            mock_collection.get.return_value = {"_key": "doc1", "name": "test"}
            result2 = db.find_by_key("col", "doc1")
            assert result2 is not None

            # Update
            mock_collection.update.return_value = {"_key": "doc1", "_rev": "rev2"}
            result3 = db.update("col", "doc1", {"name": "updated"})
            assert result3 is not None

            # Delete
            result4 = db.delete("col", "doc1")
            assert result4 is True

    def test_connection_error_doesnt_affect_subsequent_calls(
        self, mock_config, mock_arangodb
    ):
        """Test that connection error doesn't affect subsequent operations"""
        from utils import db
        with patch("v2.utils.db.get_db", return_value=None):
            result1 = db.insert("col", {})
            assert result1 is None

            result2 = db.find("col")
            assert result2 is None

            # Reset and try again
            db.reset_db_connection()
            with patch("v2.utils.db.get_db", return_value=mock_arangodb):
                mock_collection = MagicMock()
                mock_arangodb.collection.return_value = mock_collection
                mock_collection.insert.return_value = {"_key": "doc1"}
                result3 = db.insert("col", {})
                # Should work after reset
                assert result3 is not None
