"""
Enterprise Employee Analytics - Database Connection Manager
===========================================================
Thread-safe Singleton Database Manager supporting MySQL with
automatic fallback to local analytics database and auto-provisioning
for cloud deployments (e.g. Streamlit Community Cloud).
Includes SQLAlchemy Engine integration and centralized logging.

Author: Enterprise Data Architecture Team
Design Pattern: Singleton (Gang of Four)
"""

import os
import sqlite3
import threading
from typing import Optional, Dict, Any, List, Tuple
from contextlib import contextmanager
import pandas as pd

from src.logger import get_logger
from src.exceptions import DatabaseError

logger = get_logger("db_manager")

try:
    import pymysql
    from pymysql.cursors import DictCursor
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False

try:
    from sqlalchemy import create_engine, Engine
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Engine = Any  # type: ignore


class DatabaseConnection:
    """
    Singleton Database Connection Manager.
    Guarantees a single synchronized connection instance across the application.
    """
    _instance: Optional['DatabaseConnection'] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(DatabaseConnection, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if self._initialized:
            return

        with self._lock:
            self.config = config or self._default_config()
            self.backend = self.config.get("backend", "auto")
            self.sqlite_path = self.config.get("sqlite_path", os.path.join("data", "enterprise_analytics.db"))
            self._mysql_conn = None
            self._sqlite_conn = None
            self._active_backend = None
            self._sqlalchemy_engines: Dict[str, Any] = {}
            self._connect()
            self._initialized = True
            logger.info("DatabaseConnection initialized. Active backend: %s", self._active_backend)

    @staticmethod
    def _default_config() -> Dict[str, Any]:
        """Loads default configuration from Streamlit secrets, environment, or fallback."""
        cfg = {
            "backend": os.getenv("DB_BACKEND", "auto"),
            "mysql_host": os.getenv("MYSQL_HOST", "127.0.0.1"),
            "mysql_port": int(os.getenv("MYSQL_PORT", 3306)),
            "mysql_user": os.getenv("MYSQL_USER", "root"),
            "mysql_password": os.getenv("MYSQL_PASSWORD", ""),
            "mysql_oltp_db": os.getenv("MYSQL_OLTP_DB", "enterprise_hr_oltp"),
            "mysql_olap_db": os.getenv("MYSQL_OLAP_DB", "enterprise_hr_dw"),
            "sqlite_path": os.getenv("SQLITE_PATH", os.path.join("data", "enterprise_analytics.db"))
        }

        # Seamlessly load from Streamlit Cloud Secrets (st.secrets) if deployed
        try:
            import streamlit as st
            if hasattr(st, "secrets"):
                if "app" in st.secrets and "backend" in st.secrets["app"]:
                    cfg["backend"] = st.secrets["app"]["backend"]
                if "mysql" in st.secrets:
                    sec = st.secrets["mysql"]
                    cfg["mysql_host"] = sec.get("host", cfg["mysql_host"])
                    cfg["mysql_port"] = int(sec.get("port", cfg["mysql_port"]))
                    cfg["mysql_user"] = sec.get("user", cfg["mysql_user"])
                    cfg["mysql_password"] = sec.get("password", cfg["mysql_password"])
                    cfg["mysql_oltp_db"] = sec.get("oltp_database", cfg["mysql_oltp_db"])
                    cfg["mysql_olap_db"] = sec.get("olap_database", cfg["mysql_olap_db"])
                    cfg["backend"] = "mysql"
        except Exception:
            pass

        return cfg

    def _get_mysql_kwargs(self, database: Optional[str] = None) -> Dict[str, Any]:
        """Builds connection kwargs with SSL/TLS support for cloud MySQL providers."""
        target_db = database or self.config["mysql_oltp_db"]
        kwargs: Dict[str, Any] = {
            "host": self.config["mysql_host"],
            "port": self.config["mysql_port"],
            "user": self.config["mysql_user"],
            "password": self.config["mysql_password"],
            "database": target_db,
            "cursorclass": DictCursor,
            "connect_timeout": 10
        }
        # Automatically enable TLS/SSL for remote cloud hosts (e.g. TiDB Cloud port 4000, Aiven, AWS RDS)
        if self.config["mysql_host"] not in ("127.0.0.1", "localhost") or self.config["mysql_port"] == 4000:
            kwargs["ssl_verify_cert"] = True
            kwargs["ssl_verify_identity"] = True
        return kwargs

    def _connect(self) -> None:
        """Determines best database backend and establishes connection."""
        if self.backend in ("mysql", "auto") and PYMYSQL_AVAILABLE:
            try:
                # Attempt MySQL test connection
                conn_kwargs = self._get_mysql_kwargs()
                conn = pymysql.connect(**conn_kwargs)
                conn.close()
                self._active_backend = "mysql"
                logger.info("Successfully connected to MySQL server at %s:%s",
                            self.config["mysql_host"], self.config["mysql_port"])
                return
            except Exception as e:
                logger.warning("MySQL connection probe failed (%s). Falling back to SQLite warehouse.", e)

        # Fallback to local SQLite Data Warehouse
        self._active_backend = "sqlite"
        self._ensure_sqlite_ready()

    def _ensure_sqlite_ready(self) -> None:
        """Auto-provisions schema and data if running for the first time or in cloud."""
        db_dir = os.path.dirname(self.sqlite_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        needs_provision = False
        if not os.path.exists(self.sqlite_path):
            needs_provision = True
        else:
            try:
                conn = sqlite3.connect(self.sqlite_path)
                cur = conn.cursor()
                cur.execute("SELECT 1 FROM Dim_Employee LIMIT 1;")
                conn.close()
            except Exception:
                needs_provision = True

        if needs_provision:
            logger.info("Database or tables not found. Provisioning Data Warehouse at %s...", self.sqlite_path)
            try:
                from scripts.run_etl import ETLOrchestrator
                from scripts.data_synthesizer import SynthesizerConfig, BaseDatasetProfiler, EnterpriseDataSynthesizer

                # Check if synthesized CSVs exist, if not generate them
                emp_csv = os.path.join("data", "synthesized", "employees_scd2_full.csv")
                if not os.path.exists(emp_csv):
                    logger.info("Synthesizing initial datasets...")
                    cfg = SynthesizerConfig(num_employees=10_000, output_dir=os.path.join("data", "synthesized"))
                    profiler = BaseDatasetProfiler(cfg.base_dataset_path)
                    profiler.load_and_profile()
                    synth = EnterpriseDataSynthesizer(cfg, profiler)
                    synth.generate_departments()
                    synth.generate_projects()
                    synth.generate_employees()
                    synth.generate_project_assignments()
                    synth.generate_performance_reviews()
                    synth.export_all()

                # Run ETL
                etl = ETLOrchestrator(data_dir=os.path.join("data", "synthesized"), db_path=self.sqlite_path)
                etl.initialize_sqlite_warehouse()
                etl.populate_dim_date(2018, 2030)
                etl.load_synthesized_data()
                logger.info("Data Warehouse successfully initialized!")
            except Exception as e:
                logger.error("Error during warehouse auto-provisioning: %s", e)
                raise DatabaseError(f"Auto-provisioning failed: {e}") from e

    def get_backend_name(self) -> str:
        """Returns active database backend ('mysql' or 'sqlite')."""
        return self._active_backend

    def get_sqlalchemy_engine(self, database: Optional[str] = None) -> Engine:
        """
        Creates and caches a SQLAlchemy Engine matching the active database backend.
        Supports relational ORM/DAL integration and pandas data-pipelining.
        """
        if not SQLALCHEMY_AVAILABLE:
            raise DatabaseError("SQLAlchemy is not installed. Install via 'pip install sqlalchemy'.")

        target_db = database or (self.config["mysql_oltp_db"] if self._active_backend == "mysql" else self.sqlite_path)
        cache_key = f"{self._active_backend}::{target_db}"

        if cache_key in self._sqlalchemy_engines:
            return self._sqlalchemy_engines[cache_key]

        try:
            if self._active_backend == "mysql":
                url = (
                    f"mysql+pymysql://{self.config['mysql_user']}:{self.config['mysql_password']}"
                    f"@{self.config['mysql_host']}:{self.config['mysql_port']}/{target_db}"
                )
                connect_args = {}
                if self.config["mysql_host"] not in ("127.0.0.1", "localhost") or self.config["mysql_port"] == 4000:
                    connect_args = {"ssl_verify_cert": True, "ssl_verify_identity": True}
                engine = create_engine(url, connect_args=connect_args, pool_pre_ping=True, pool_recycle=3600)
            else:
                engine = create_engine(f"sqlite:///{os.path.abspath(self.sqlite_path)}")

            self._sqlalchemy_engines[cache_key] = engine
            logger.info("Created SQLAlchemy engine for %s", target_db)
            return engine
        except Exception as e:
            logger.error("Failed to instantiate SQLAlchemy Engine: %s", e)
            raise DatabaseError(f"Failed to create SQLAlchemy engine: {e}") from e

    @contextmanager
    def get_connection(self, database: Optional[str] = None):
        """Context manager providing an active database connection."""
        if self._active_backend == "mysql":
            target_db = database or self.config["mysql_oltp_db"]
            try:
                conn_kwargs = self._get_mysql_kwargs(target_db)
                conn_kwargs["autocommit"] = False
                conn = pymysql.connect(**conn_kwargs)
            except Exception as e:
                logger.error("Failed to connect to MySQL database %s: %s", target_db, e)
                raise DatabaseError(f"MySQL connection failed: {e}") from e

            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error("Transaction rolled back due to error: %s", e)
                raise DatabaseError(f"Database transaction error: {e}") from e
            finally:
                conn.close()
        else:
            # SQLite connection
            try:
                conn = sqlite3.connect(self.sqlite_path, check_same_thread=False)
                conn.row_factory = sqlite3.Row
            except Exception as e:
                logger.error("Failed to connect to SQLite at %s: %s", self.sqlite_path, e)
                raise DatabaseError(f"SQLite connection failed: {e}") from e

            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error("SQLite transaction rolled back: %s", e)
                raise DatabaseError(f"Database transaction error: {e}") from e
            finally:
                conn.close()

    def execute_query(self, sql: str, params: Optional[Tuple] = None, database: Optional[str] = None) -> List[Dict[str, Any]]:
        """Executes a SELECT query and returns a list of dictionaries."""
        try:
            with self.get_connection(database=database) as conn:
                cursor = conn.cursor()
                if self._active_backend == "mysql":
                    cursor.execute(sql, params or ())
                    return cursor.fetchall()
                else:
                    sqlite_sql = sql.replace("%s", "?")
                    cursor.execute(sqlite_sql, params or ())
                    rows = cursor.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            if not isinstance(e, DatabaseError):
                raise DatabaseError(f"Query execution error: {e}") from e
            raise

    def execute_update(self, sql: str, params: Optional[Tuple] = None, database: Optional[str] = None) -> int:
        """Executes an INSERT, UPDATE, or DELETE query and returns rows affected."""
        try:
            with self.get_connection(database=database) as conn:
                cursor = conn.cursor()
                if self._active_backend == "mysql":
                    cursor.execute(sql, params or ())
                    return cursor.rowcount
                else:
                    sqlite_sql = sql.replace("%s", "?")
                    cursor.execute(sqlite_sql, params or ())
                    return cursor.rowcount
        except Exception as e:
            if not isinstance(e, DatabaseError):
                raise DatabaseError(f"Update execution error: {e}") from e
            raise

    def fetch_dataframe(self, sql: str, params: Optional[Tuple] = None, database: Optional[str] = None) -> pd.DataFrame:
        """Executes a query and directly returns a pandas DataFrame."""
        try:
            with self.get_connection(database=database) as conn:
                if self._active_backend == "mysql":
                    return pd.read_sql_query(sql, conn, params=params)
                else:
                    sqlite_sql = sql.replace("%s", "?")
                    return pd.read_sql_query(sqlite_sql, conn, params=params)
        except Exception as e:
            if not isinstance(e, DatabaseError):
                raise DatabaseError(f"DataFrame fetch error: {e}") from e
            raise


def get_db(config: Optional[Dict[str, Any]] = None) -> DatabaseConnection:
    """Convenience factory function returning the DatabaseConnection Singleton."""
    return DatabaseConnection(config=config)
