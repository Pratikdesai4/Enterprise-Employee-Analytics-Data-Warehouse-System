"""
Enterprise Employee Analytics - Base Manager
============================================
Provides shared database access, transaction isolation, and structured logging.
"""

from typing import Optional, Dict, Any, List, Tuple
from src.database.db_manager import DatabaseConnection, get_db
from src.logger import get_logger
from src.exceptions import DatabaseError

logger = get_logger("base_manager")


class BaseManager:
    """Base class for all Data Access Layer (DAL) managers."""

    def __init__(self, db: Optional[DatabaseConnection] = None):
        self.db = db or get_db()
        self.backend = self.db.get_backend_name()

    def _execute_query(self, sql: str, params: Optional[Tuple] = None, database: Optional[str] = None) -> List[Dict[str, Any]]:
        """Safe query executor returning records as dictionaries."""
        try:
            return self.db.execute_query(sql, params, database=database)
        except Exception as e:
            logger.error("Query execution failed: %s | SQL: %s | Params: %s", e, sql, params)
            if not isinstance(e, DatabaseError):
                raise DatabaseError(f"Query execution failed: {e}") from e
            raise

    def _execute_update(self, sql: str, params: Optional[Tuple] = None, database: Optional[str] = None) -> int:
        """Safe update executor returning rows modified."""
        try:
            return self.db.execute_update(sql, params, database=database)
        except Exception as e:
            logger.error("Update execution failed: %s | SQL: %s | Params: %s", e, sql, params)
            if not isinstance(e, DatabaseError):
                raise DatabaseError(f"Update execution failed: {e}") from e
            raise
