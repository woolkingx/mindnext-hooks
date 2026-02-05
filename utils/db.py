"""Database Connection — ArangoDB 連線管理

從 config.toml 讀取設定
返回值語義：
  - StandardDatabase：連接成功
  - None：連接失敗（詳見 get_db_error()）
"""

import os
import logging
from typing import Optional

try:
    from arango import ArangoClient
    from arango.database import StandardDatabase
    ARANGO_AVAILABLE = True
except ImportError:
    ARANGO_AVAILABLE = False
    ArangoClient = None
    StandardDatabase = None

logger = logging.getLogger(__name__)

_db_instance: Optional[StandardDatabase] = None
_db_error: Optional[str] = None


def _get_db_config() -> dict:
    """從 config.toml 取得資料庫設定"""
    from loaders import config

    db_config = config.get("database", {})

    # 環境變數優先
    db_config["host"] = os.getenv("DB_HOST", db_config.get("host"))
    db_config["database"] = os.getenv("DB_NAME", db_config.get("database"))
    db_config["username"] = os.getenv("DB_USER", db_config.get("username"))
    db_config["password"] = os.getenv("DB_PASS", db_config.get("password"))

    return db_config


def get_db() -> Optional[StandardDatabase]:
    """取得資料庫連線（單例）

    返回值：
      - StandardDatabase：連接成功
      - None：連接失敗（詳見 get_db_error()）

    連不上就返回 None，不重試不卡住
    """
    global _db_instance, _db_error

    if not ARANGO_AVAILABLE:
        error_msg = "DB 連接失敗: ArangoDB client not installed (python-arango)"
        logger.debug(error_msg)
        _db_error = error_msg
        return None

    if _db_instance is not None:
        return _db_instance

    config = _get_db_config()

    try:
        from arango.http import DefaultHTTPClient

        class NoRetryHTTPClient(DefaultHTTPClient):
            """不重試的 HTTP Client"""

            def __init__(self):
                super().__init__(request_timeout=2, retry_attempts=0)

        client = ArangoClient(
            hosts=config["host"],
            http_client=NoRetryHTTPClient(),
        )
        db = client.db(
            config["database"],
            username=config["username"],
            password=config["password"],
        )
        db.version()
        _db_instance = db
        _db_error = None
        return db
    except Exception as e:
        error_msg = f"DB 連接失敗: {type(e).__name__}: {str(e)}"
        logger.debug(error_msg)
        _db_error = error_msg
        return None


def get_db_error() -> Optional[str]:
    """取得最後的 DB 連接錯誤信息

    返回值：
      - str：連接失敗時的錯誤信息
      - None：連接成功，或尚未嘗試連接
    """
    return _db_error


def reset_db_connection():
    """重置資料庫連線"""
    global _db_instance, _db_error
    _db_instance = None
    _db_error = None


# ============ CRUD Operations ============


def insert(collection: str, document: dict) -> Optional[dict]:
    """插入文檔

    Args:
        collection: 集合名稱
        document: 文檔內容

    Returns:
        插入後的文檔（含 _key, _id, _rev）或 None（失敗）
    """
    db = get_db()
    if not db:
        return None

    try:
        col = db.collection(collection)
        meta = col.insert(document)
        return meta
    except Exception as e:
        logger.warning(f"Insert failed for {collection}: {str(e)}")
        return None


def find(collection: str, query: Optional[dict] = None, limit: int = 100) -> Optional[list]:
    """查詢文檔

    Args:
        collection: 集合名稱
        query: 查詢條件（簡單 dict 匹配，None 時查詢全部）
        limit: 最多返回筆數

    Returns:
        文檔列表或 None（失敗）
    """
    db = get_db()
    if not db:
        return None

    try:
        col = db.collection(collection)

        if query is None:
            # 查詢全部
            return list(col.all(limit=limit))

        # 簡單查詢
        aql = "FOR doc IN @collection FILTER"
        filter_parts = []
        bind_vars = {"collection": collection}

        for key, value in query.items():
            filter_parts.append(f"doc.{key} == @{key}")
            bind_vars[key] = value

        filter_str = " AND ".join(filter_parts)
        aql = f"{aql} {filter_str} LIMIT @limit RETURN doc"
        bind_vars["limit"] = limit

        cursor = db.aql.execute(aql, bind_vars=bind_vars)
        return list(cursor)
    except Exception as e:
        logger.warning(f"Find failed for {collection}: {str(e)}")
        return None


def find_by_key(collection: str, key: str) -> Optional[dict]:
    """按 _key 查詢單個文檔

    Args:
        collection: 集合名稱
        key: 文檔 _key

    Returns:
        文檔或 None（失敗或不存在）
    """
    db = get_db()
    if not db:
        return None

    try:
        col = db.collection(collection)
        return col.get(key)
    except Exception as e:
        logger.warning(f"Find by key failed for {collection}/{key}: {str(e)}")
        return None


def update(collection: str, key: str, document: dict) -> Optional[dict]:
    """更新文檔

    Args:
        collection: 集合名稱
        key: 文檔 _key
        document: 更新內容

    Returns:
        更新後的文檔或 None（失敗）
    """
    db = get_db()
    if not db:
        return None

    try:
        col = db.collection(collection)
        meta = col.update({"_key": key, **document})
        return meta
    except Exception as e:
        logger.warning(f"Update failed for {collection}/{key}: {str(e)}")
        return None


def delete(collection: str, key: str) -> bool:
    """刪除文檔

    Args:
        collection: 集合名稱
        key: 文檔 _key

    Returns:
        成功返回 True，失敗返回 False
    """
    db = get_db()
    if not db:
        return False

    try:
        col = db.collection(collection)
        col.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Delete failed for {collection}/{key}: {str(e)}")
        return False


def query_aql(aql_query: str, bind_vars: Optional[dict] = None) -> Optional[list]:
    """執行自定義 AQL 查詢

    Args:
        aql_query: AQL 查詢語句
        bind_vars: 綁定變數

    Returns:
        查詢結果列表或 None（失敗）
    """
    db = get_db()
    if not db:
        return None

    try:
        cursor = db.aql.execute(aql_query, bind_vars=bind_vars or {})
        return list(cursor)
    except Exception as e:
        logger.warning(f"AQL query failed: {str(e)}")
        return None
