"""
Enterprise Employee Analytics - Database Connection Manager
===========================================================
Thread-safe Singleton Database Manager supporting MySQL with
automatic fallback to local analytics database and auto-provisioning
for cloud deployments (e.g. Streamlit Community Cloud).

Author: Enterprise Data Architecture Team
Design Pattern: Singleton (Gang of Four)
"""

import os
import sqlite3
import threading
from typing import Optional, Dict, Any, List, Tuple
from contextlib import contextmanager
import pandas as pd

try:
    import pymysql
    from pymysql.cursors import DictCursor
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False


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
            self._connect()
            self._initialized = True

    @staticmethod
    def _default_config() -> Dict[str, Any]:
        """Loads default configuration from environment or fallback."""
        return {
            "backend": os.getenv("DB_BACKEND", "auto"),
            "mysql_host": os.getenv("MYSQL_HOST", "127.0.0.1"),
            "mysql_port": int(os.getenv("MYSQL_PORT", 3306)),
            "mysql_user": os.getenv("MYSQL_USER", "root"),
            "mysql_password": os.getenv("MYSQL_PASSWORD", ""),
            "mysql_oltp_db": os.getenv("MYSQL_OLTP_DB", "enterprise_hr_oltp"),
            "mysql_olap_db": os.getenv("MYSQL_OLAP_DB", "enterprise_hr_dw"),
            "sqlite_path": os.getenv("SQLITE_PATH", os.path.join("data", "enterprise_analytics.db"))
        }

    def _connect(self) -> None:
        """Determines best database backend and establishes connection."""
        if self.backend in ("mysql", "auto") and PYMYSQL_AVAILABLE:
            try:
                # Attempt MySQL test connection
                conn = pymysql.connect(
                    host=self.config["mysql_host"],
                    port=self.config["mysql_port"],
                    user=self.config["mysql_user"],
                    password=self.config["mysql_password"],
                    database=self.config["mysql_oltp_db"],
                    connect_timeout=2,
                    cursorclass=DictCursor
                )
                conn.close()
                self._active_backend = "mysql"
                return
            except Exception:
                pass

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
            print("[Auto-Provisioner] Database or tables not found. Provisioning Data Warehouse...")
            try:
                from scripts.run_etl import ETLOrchestrator
                from scripts.data_synthesizer import SynthesizerConfig, BaseDatasetProfiler, EnterpriseDataSynthesizer

                # Check if synthesized CSVs exist, if not generate them
                emp_csv = os.path.join("data", "synthesized", "employees_scd2_full.csv")
                if not os.path.exists(emp_csv):
                    print("[Auto-Provisioner] Synthesizing initial datasets...")
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
                print("[Auto-Provisioner] Data Warehouse successfully initialized!")
            except Exception as e:
                print(f"[Auto-Provisioner] Error during auto-provisioning: {e}")

    def get_backend_name(self) -> str:
        """Returns active database backend ('mysql' or 'sqlite')."""
        return self._active_backend

    @contextmanager
    def get_connection(self, database: Optional[str] = None):
        """Context manager providing an active database connection."""
        if self._active_backend == "mysql":
            target_db = database or self.config["mysql_oltp_db"]
            conn = pymysql.connect(
                host=self.config["mysql_host"],
                port=self.config["mysql_port"],
                user=self.config["mysql_user"],
                password=self.config["mysql_password"],
                database=target_db,
                cursorclass=DictCursor,
                autocommit=False
            )
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
        else:
            # SQLite connection
            conn = sqlite3.connect(self.sqlite_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def execute_query(self, sql: str, params: Optional[Tuple] = None, database: Optional[str] = None) -> List[Dict[str, Any]]:
        """Executes a SELECT query and returns a list of dictionaries."""
        with self.get_connection(database=database) as conn:
            cursor = conn.cursor()
            if self._active_backend == "mysql":
                cursor.execute(sql, params or ())
                return cursor.fetchall()
            else:
                # Replace MySQL %s with ? for SQLite compatibility
                sqlite_sql = sql.replace("%s", "?")
                cursor.execute(sqlite_sql, params or ())
                rows = cursor.fetchall()
                return [dict(row) for row in rows]

    def execute_update(self, sql: str, params: Optional[Tuple] = None, database: Optional[str] = None) -> int:
        """Executes an INSERT, UPDATE, or DELETE query and returns rows affected."""
        with self.get_connection(database=database) as conn:
            cursor = conn.cursor()
            if self._active_backend == "mysql":
                cursor.execute(sql, params or ())
                return cursor.rowcount
            else:
                sqlite_sql = sql.replace("%s", "?")
                cursor.execute(sqlite_sql, params or ())
                return cursor.rowcount

    def fetch_dataframe(self, sql: str, params: Optional[Tuple] = None, database: Optional[str] = None) -> pd.DataFrame:
        """Executes a query and directly returns a pandas DataFrame."""
        with self.get_connection(database=database) as conn:
            if self._active_backend == "mysql":
                return pd.read_sql_query(sql, conn, params=params)
            else:
                sqlite_sql = sql.replace("%s", "?")
                return pd.read_sql_query(sqlite_sql, conn, params=params)


def get_db(config: Optional[Dict[str, Any]] = None) -> DatabaseConnection:
    """Convenience factory function returning the DatabaseConnection Singleton."""
    return DatabaseConnection(config=config)
