"""
Database connection manager implementing a thread‑safe Singleton pattern.
Provides a single MySQL connection (via mysql.connector) that can be shared
across the OOP backend services.
"""

import threading
from typing import Optional

import mysql.connector
from mysql.connector import MySQLConnection, Error

class DatabaseConnection:
    """Singleton wrapper for a MySQL connection.

    Usage::
        db = DatabaseConnection.instance()
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(...)
    """

    _instance: Optional["DatabaseConnection"] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self, host: str = "localhost", user: str = "root", password: str = "", database: str = "enterprise_hr_dw") -> None:
        # Prevent direct instantiation – use .instance()
        raise RuntimeError("Use DatabaseConnection.instance() to get the singleton.")

    @classmethod
    def _create_instance(cls) -> None:
        """Internal helper to create the singleton instance.
        Reads connection parameters from environment variables if present.
        """
        import os
        conn_params = {
            "host": os.getenv("MYSQL_HOST", "localhost"),
            "user": os.getenv("MYSQL_USER", "root"),
            "password": os.getenv("MYSQL_PASSWORD", ""),
            "database": os.getenv("MYSQL_DATABASE", "enterprise_hr_dw"),
        }
        try:
            connection: MySQLConnection = mysql.connector.connect(**conn_params, autocommit=False)
        except Error as e:
            raise RuntimeError(f"Failed to connect to MySQL: {e}")
        instance = object.__new__(cls)
        instance._connection = connection
        cls._instance = instance

    @classmethod
    def instance(cls) -> "DatabaseConnection":
        """Return the singleton instance, creating it on first call."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._create_instance()
        return cls._instance

    def get_connection(self) -> MySQLConnection:
        """Retrieve the underlying MySQL connection object."""
        return self._connection

    def close(self) -> None:
        """Close the connection and reset the singleton (useful for tests)."""
        if self._connection.is_connected():
            self._connection.close()
        type(self)._instance = None
