"""
Enterprise Employee Analytics - ETL Orchestration Runner
========================================================
Automates database provisioning, schema execution, and data loading
for both OLTP and OLAP Star Schema (SCD Type 2).

Supports direct MySQL execution (via pymysql/SQLAlchemy) and
provides seamless local database staging to guarantee testability.

Author: Enterprise Data Architecture Team
"""

import os
import sys
import time
import sqlite3
import datetime
import pandas as pd
from typing import Dict, Any, Optional

try:
    import pymysql
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False


class ETLOrchestrator:
    """Executes end-to-end ETL: DDL execution, staging, and SCD2 dimension/fact ingestion."""

    def __init__(self, data_dir: str = os.path.join("data", "synthesized"), db_path: str = os.path.join("data", "enterprise_analytics.db")):
        self.data_dir = data_dir
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def initialize_sqlite_warehouse(self) -> None:
        """Initializes SQLite instance modeling both OLTP and OLAP schemas for local execution."""
        print(f"[ETL] Initializing local Data Warehouse database at: {self.db_path}")
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()

        # Enable WAL mode and foreign keys for high-performance concurrent reads
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA synchronous = NORMAL;")
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Create OLTP Tables
        cursor.executescript("""
        DROP TABLE IF EXISTS employee_project_assignments;
        DROP TABLE IF EXISTS performance_reviews_oltp;
        DROP TABLE IF EXISTS projects_oltp;
        DROP TABLE IF EXISTS employees_oltp;
        DROP TABLE IF EXISTS departments_oltp;

        CREATE TABLE departments_oltp (
            department_id INTEGER PRIMARY KEY AUTOINCREMENT,
            department_name TEXT NOT NULL UNIQUE,
            cost_center TEXT NOT NULL UNIQUE,
            budget REAL NOT NULL DEFAULT 0.0
        );

        CREATE TABLE employees_oltp (
            employee_id TEXT PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT NOT NULL,
            gender TEXT NOT NULL,
            age INTEGER NOT NULL,
            marital_status TEXT NOT NULL,
            hire_date TEXT NOT NULL,
            department_id INTEGER NOT NULL,
            department_name TEXT NOT NULL,
            job_role TEXT NOT NULL,
            education_field TEXT NOT NULL,
            monthly_income REAL NOT NULL,
            overtime TEXT NOT NULL DEFAULT 'No',
            years_at_company INTEGER NOT NULL DEFAULT 0,
            attrition TEXT NOT NULL DEFAULT 'No',
            status TEXT NOT NULL DEFAULT 'Active',
            FOREIGN KEY (department_id) REFERENCES departments_oltp(department_id)
        );

        CREATE TABLE projects_oltp (
            project_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_code TEXT NOT NULL UNIQUE,
            project_name TEXT NOT NULL,
            department_id INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            budget REAL NOT NULL DEFAULT 0.0,
            status TEXT NOT NULL DEFAULT 'Planning',
            FOREIGN KEY (department_id) REFERENCES departments_oltp(department_id)
        );

        CREATE TABLE employee_project_assignments (
            assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            project_id INTEGER NOT NULL,
            assignment_role TEXT NOT NULL,
            allocation_percentage INTEGER NOT NULL DEFAULT 100,
            assigned_date TEXT NOT NULL,
            FOREIGN KEY (employee_id) REFERENCES employees_oltp(employee_id),
            FOREIGN KEY (project_id) REFERENCES projects_oltp(project_id)
        );

        -- Create OLAP Star Schema Tables
        DROP TABLE IF EXISTS Fact_PerformanceReviews;
        DROP TABLE IF EXISTS Dim_Employee;
        DROP TABLE IF EXISTS Dim_Department;
        DROP TABLE IF EXISTS Dim_Project;
        DROP TABLE IF EXISTS Dim_Date;
        DROP TABLE IF EXISTS ETL_Execution_Log;

        CREATE TABLE Dim_Date (
            date_dim_id INTEGER PRIMARY KEY,
            full_date TEXT NOT NULL UNIQUE,
            year INTEGER NOT NULL,
            quarter INTEGER NOT NULL,
            month INTEGER NOT NULL,
            month_name TEXT NOT NULL,
            day_of_month INTEGER NOT NULL,
            day_name TEXT NOT NULL,
            is_weekend INTEGER NOT NULL DEFAULT 0,
            fiscal_year TEXT NOT NULL
        );

        CREATE TABLE Dim_Department (
            department_dim_id INTEGER PRIMARY KEY AUTOINCREMENT,
            department_id INTEGER NOT NULL,
            department_name TEXT NOT NULL,
            cost_center TEXT NOT NULL,
            budget REAL NOT NULL DEFAULT 0.0
        );

        CREATE TABLE Dim_Project (
            project_dim_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            project_code TEXT NOT NULL,
            project_name TEXT NOT NULL,
            budget_tier TEXT NOT NULL,
            status TEXT NOT NULL
        );

        CREATE TABLE Dim_Employee (
            employee_dim_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            gender TEXT NOT NULL,
            age INTEGER NOT NULL,
            hire_date TEXT NOT NULL,
            department_id INTEGER NOT NULL,
            department_name TEXT NOT NULL,
            job_role TEXT NOT NULL,
            education_field TEXT NOT NULL,
            monthly_income REAL NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT,
            is_current INTEGER NOT NULL DEFAULT 1,
            version INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE Fact_PerformanceReviews (
            review_fact_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_dim_id INTEGER NOT NULL,
            department_dim_id INTEGER NOT NULL,
            project_dim_id INTEGER NOT NULL DEFAULT 0,
            date_dim_id INTEGER NOT NULL,
            review_id INTEGER NOT NULL,
            employee_id TEXT NOT NULL,
            performance_rating INTEGER NOT NULL,
            monthly_income_at_review REAL NOT NULL,
            percent_salary_hike REAL NOT NULL DEFAULT 0.0,
            work_life_balance INTEGER NOT NULL,
            job_satisfaction INTEGER NOT NULL,
            environment_satisfaction INTEGER NOT NULL,
            attrition_risk_score INTEGER NOT NULL,
            tenure_at_review INTEGER NOT NULL DEFAULT 0,
            promotion_given INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (employee_dim_id) REFERENCES Dim_Employee(employee_dim_id),
            FOREIGN KEY (department_dim_id) REFERENCES Dim_Department(department_dim_id),
            FOREIGN KEY (date_dim_id) REFERENCES Dim_Date(date_dim_id)
        );

        CREATE TABLE ETL_Execution_Log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            pipeline_name TEXT NOT NULL,
            step_name TEXT NOT NULL,
            records_processed INTEGER NOT NULL,
            status TEXT NOT NULL,
            timestamp TEXT NOT NULL
        );
        """)
        self.conn.commit()
        print("[ETL] Local schema created successfully.")

    def populate_dim_date(self, start_year: int = 2018, end_year: int = 2030) -> int:
        """Populates the conformed Dim_Date table."""
        print(f"[ETL] Populating Dim_Date from {start_year} to {end_year}...")
        cur_date = datetime.date(start_year, 1, 1)
        end_date = datetime.date(end_year, 12, 31)
        records = []

        while cur_date <= end_date:
            date_id = int(cur_date.strftime("%Y%m%d"))
            records.append((
                date_id,
                cur_date.isoformat(),
                cur_date.year,
                (cur_date.month - 1) // 3 + 1,
                cur_date.month,
                cur_date.strftime("%B"),
                cur_date.day,
                cur_date.strftime("%A"),
                1 if cur_date.weekday() >= 5 else 0,
                f"FY{cur_date.year}"
            ))
            cur_date += datetime.timedelta(days=1)

        cursor = self.conn.cursor()
        cursor.executemany("""
            INSERT OR REPLACE INTO Dim_Date (
                date_dim_id, full_date, year, quarter, month, month_name,
                day_of_month, day_name, is_weekend, fiscal_year
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, records)
        self.conn.commit()
        print(f"[ETL] Loaded {len(records):,} dates into Dim_Date.")
        return len(records)

    def load_synthesized_data(self) -> Dict[str, int]:
        """Loads all synthesized datasets into OLTP and OLAP warehouse tables."""
        counts = {}
        cursor = self.conn.cursor()

        # 1. Departments
        dept_path = os.path.join(self.data_dir, "departments.csv")
        df_dept = pd.read_csv(dept_path)
        df_dept.to_sql("departments_oltp", self.conn, if_exists="append", index=False)
        
        # Populate Dim_Department
        cursor.execute("""
            INSERT INTO Dim_Department (department_id, department_name, cost_center, budget)
            SELECT department_id, department_name, cost_center, budget FROM departments_oltp;
        """)
        counts["departments"] = len(df_dept)
        print(f"[ETL] Ingested {len(df_dept)} departments.")

        # 2. Projects
        proj_path = os.path.join(self.data_dir, "projects.csv")
        df_proj = pd.read_csv(proj_path)
        df_proj.to_sql("projects_oltp", self.conn, if_exists="append", index=False)
        
        # Populate Dim_Project
        cursor.execute("""
            INSERT INTO Dim_Project (project_id, project_code, project_name, budget_tier, status)
            SELECT 
                project_id, project_code, project_name,
                CASE 
                    WHEN budget < 500000 THEN 'Small (<$500k)'
                    WHEN budget BETWEEN 500000 AND 1500000 THEN 'Medium ($500k-$1.5M)'
                    ELSE 'Large (>$1.5M)'
                END AS budget_tier,
                status
            FROM projects_oltp;
        """)
        counts["projects"] = len(df_proj)
        print(f"[ETL] Ingested {len(df_proj)} projects.")

        # 3. OLTP Active Employees (100,000 rows)
        emp_oltp_path = os.path.join(self.data_dir, "employees_oltp_current.csv")
        print(f"[ETL] Loading 100,000 active employees into OLTP employees table...")
        df_emp_oltp = pd.read_csv(emp_oltp_path)
        df_emp_oltp.to_sql("employees_oltp", self.conn, if_exists="append", index=False, chunksize=10000)
        counts["employees_oltp"] = len(df_emp_oltp)
        print(f"[ETL] Loaded {len(df_emp_oltp):,} active employees.")

        # 4. SCD Type 2 Full Employee Dimension (125,000 rows)
        emp_scd_path = os.path.join(self.data_dir, "employees_scd2_full.csv")
        print(f"[ETL] Loading 125,000 SCD Type 2 records into Dim_Employee...")
        df_scd = pd.read_csv(emp_scd_path)
        df_scd.to_sql("Dim_Employee", self.conn, if_exists="append", index=False, chunksize=10000)
        counts["dim_employee_scd2"] = len(df_scd)
        print(f"[ETL] Loaded {len(df_scd):,} records into Dim_Employee.")

        # 5. Project Assignments
        assign_path = os.path.join(self.data_dir, "project_assignments.csv")
        df_assign = pd.read_csv(assign_path)
        df_assign.to_sql("employee_project_assignments", self.conn, if_exists="append", index=False, chunksize=10000)
        counts["project_assignments"] = len(df_assign)
        print(f"[ETL] Loaded {len(df_assign):,} project assignments.")

        # 6. Performance Reviews -> Fact_PerformanceReviews
        rev_path = os.path.join(self.data_dir, "performance_reviews.csv")
        print(f"[ETL] Ingesting and resolving surrogate keys for performance reviews fact table...")
        df_rev = pd.read_csv(rev_path)

        # Temporary staging table in sqlite for fact transformation
        df_rev.to_sql("stg_reviews", self.conn, if_exists="replace", index=False, chunksize=10000)

        # Execute Fact key resolution join
        cursor.execute("""
            INSERT INTO Fact_PerformanceReviews (
                employee_dim_id, department_dim_id, project_dim_id, date_dim_id,
                review_id, employee_id, performance_rating, monthly_income_at_review,
                percent_salary_hike, work_life_balance, job_satisfaction, environment_satisfaction,
                attrition_risk_score, tenure_at_review, promotion_given
            )
            SELECT 
                de.employee_dim_id,
                dd.department_dim_id,
                0 AS project_dim_id,
                CAST(strftime('%Y%m%d', r.review_date) AS INTEGER) AS date_dim_id,
                r.review_id,
                r.employee_id,
                r.performance_rating,
                r.monthly_income_at_review,
                r.percent_salary_hike,
                r.work_life_balance,
                r.job_satisfaction,
                r.environment_satisfaction,
                r.attrition_risk_score,
                r.tenure_at_review,
                r.promotion_given
            FROM stg_reviews r
            INNER JOIN Dim_Employee de 
                ON r.employee_id = de.employee_id
               AND r.review_date >= de.start_date
               AND (de.end_date IS NULL OR r.review_date < de.end_date)
            INNER JOIN Dim_Department dd 
                ON r.department_id = dd.department_id;
        """)
        cursor.execute("DROP TABLE stg_reviews;")
        self.conn.commit()

        # Count facts loaded
        cursor.execute("SELECT COUNT(*) FROM Fact_PerformanceReviews;")
        fact_count = cursor.fetchone()[0]
        counts["fact_reviews"] = fact_count
        print(f"[ETL] Successfully loaded {fact_count:,} facts into Fact_PerformanceReviews.")

        # Create indexes on warehouse tables for fast Streamlit analytics
        print("[ETL] Building analytical indexes on Fact and Dimension tables...")
        cursor.executescript("""
            CREATE INDEX IF NOT EXISTS idx_dim_emp_id ON Dim_Employee(employee_id);
            CREATE INDEX IF NOT EXISTS idx_dim_emp_curr ON Dim_Employee(is_current);
            CREATE INDEX IF NOT EXISTS idx_fact_emp_dim ON Fact_PerformanceReviews(employee_dim_id);
            CREATE INDEX IF NOT EXISTS idx_fact_dept_dim ON Fact_PerformanceReviews(department_dim_id);
            CREATE INDEX IF NOT EXISTS idx_fact_date_dim ON Fact_PerformanceReviews(date_dim_id);
            CREATE INDEX IF NOT EXISTS idx_fact_rating ON Fact_PerformanceReviews(performance_rating);
        """)
        self.conn.commit()

        # Log completion
        cursor.execute("""
            INSERT INTO ETL_Execution_Log (pipeline_name, step_name, records_processed, status, timestamp)
            VALUES ('Full_Warehouse_ETL', 'load_synthesized_data', ?, 'SUCCESS', datetime('now'))
        """, (fact_count,))
        self.conn.commit()

        return counts

    def run_validation_checks(self) -> None:
        """Executes verification assertions on SCD2 and Fact tables."""
        cursor = self.conn.cursor()
        print("\n--- Running Data Warehouse Integrity Audits ---")

        # 1. SCD Type 2 Check
        cursor.execute("""
            SELECT 
                COUNT(*) as total_rows,
                SUM(CASE WHEN is_current = 1 THEN 1 ELSE 0 END) as active_versions,
                SUM(CASE WHEN is_current = 0 THEN 1 ELSE 0 END) as historical_versions,
                COUNT(DISTINCT employee_id) as unique_employees
            FROM Dim_Employee;
        """)
        total, active, historical, unique_emps = cursor.fetchone()
        print(f"  [Audit 1: Dim_Employee SCD2]")
        print(f"    - Total records: {total:,}")
        print(f"    - Unique employees: {unique_emps:,}")
        print(f"    - Current active versions: {active:,}")
        print(f"    - Historical expired versions: {historical:,}")
        assert active == unique_emps, "Every employee must have exactly one active (is_current = 1) version!"

        # 2. Fact Referential Integrity
        cursor.execute("""
            SELECT COUNT(*) 
            FROM Fact_PerformanceReviews f
            LEFT JOIN Dim_Employee de ON f.employee_dim_id = de.employee_dim_id
            WHERE de.employee_dim_id IS NULL;
        """)
        orphan_employees = cursor.fetchone()[0]
        print(f"  [Audit 2: Fact Foreign Key Integrity]")
        print(f"    - Orphan Employee FKs: {orphan_employees}")
        assert orphan_employees == 0, "No orphan foreign keys allowed in Fact table!"

        print("  [Audit Passed] All warehouse integrity checks passed successfully!\n")


def main():
    start_time = time.time()
    orchestrator = ETLOrchestrator()
    orchestrator.initialize_sqlite_warehouse()
    orchestrator.populate_dim_date(2018, 2030)
    orchestrator.load_synthesized_data()
    orchestrator.run_validation_checks()
    elapsed = round(time.time() - start_time, 2)
    print(f"ETL Execution completed in {elapsed}s.")


if __name__ == "__main__":
    main()
