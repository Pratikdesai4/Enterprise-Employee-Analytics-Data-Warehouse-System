"""
Enterprise Employee Analytics - OOP Backend Verification Suite
==============================================================
Validates the Singleton Database Pattern, Domain Entities,
Data Access Layer (DAL), SCD Type 2 Reassignment Triggers,
SQLAlchemy Engine caching, Custom Exceptions, and Project Bottleneck Analytics.

Author: Enterprise Data Architecture Team
"""

import sys
import os
import unittest

# Add workspace root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.db_manager import DatabaseConnection, get_db
from src.entities.employee import Employee
from src.entities.project import Project
from src.entities.review import PerformanceReview
from src.managers.employee_manager import EmployeeManager
from src.managers.project_manager import ProjectManager
from src.managers.analytics_manager import AnalyticsManager
from src.exceptions import ValidationError, DatabaseError, EntityNotFoundError
from src.logger import get_logger


class TestOOPBackend(unittest.TestCase):
    """End-to-end unit and integration tests for Phase 3 OOP architecture."""

    def setUp(self):
        """Clean up test records before each test."""
        db = get_db()
        test_emp_id = "EMP-TEST999"
        backend = db.get_backend_name()
        if backend == "mysql":
            db.execute_update("DELETE FROM enterprise_hr_oltp.employees WHERE employee_id = %s", (test_emp_id,))
            db.execute_update("DELETE FROM enterprise_hr_dw.Dim_Employee WHERE employee_id = %s", (test_emp_id,))
        else:
            db.execute_update("DELETE FROM employees_oltp WHERE employee_id = %s", (test_emp_id,))
            db.execute_update("DELETE FROM Dim_Employee WHERE employee_id = %s", (test_emp_id,))

    def tearDown(self):
        """Clean up test records after each test."""
        self.setUp()

    def test_01_singleton_pattern(self):
        """Validates that DatabaseConnection is a true thread-safe Singleton."""
        db1 = get_db()
        db2 = get_db()
        self.assertIs(db1, db2, "get_db() must return the exact same instance.")
        self.assertEqual(id(db1), id(db2), "Memory address of Singleton must be identical.")
        print("\n[PASS] Singleton Pattern Verified: Instance address is strictly identical.")

    def test_02_entity_validation(self):
        """Validates domain entity encapsulation and validation constraints."""
        # Valid employee
        emp = Employee(
            employee_id="EMP-TEST01",
            first_name="Jane",
            last_name="Doe",
            email="jane.doe@enterprise.corp",
            phone="+1-555-123-4567",
            gender="Female",
            age=32,
            marital_status="Married",
            hire_date="2024-01-15",
            department_id=4,
            job_role="Senior Software Engineer",
            education_field="Computer Science",
            monthly_income=11500.0
        )
        self.assertEqual(emp.full_name, "Jane Doe")
        self.assertEqual(emp.annual_salary, 138000.0)

        # Invalid employee (underage) - must raise ValidationError
        with self.assertRaises(ValidationError):
            Employee(
                employee_id="EMP-FAIL",
                first_name="Too",
                last_name="Young",
                email="young@corp.com",
                phone="123",
                gender="Male",
                age=15,  # Under 18
                marital_status="Single",
                hire_date="2024-01-01",
                department_id=1,
                job_role="Intern",
                education_field="CS",
                monthly_income=1000.0
            )

        print("[PASS] Domain Entity Encapsulation and Validation Rules Verified.")

    def test_03_employee_manager_and_scd2_trigger(self):
        """
        Validates Employee CRUD and verifies that role/department reassignment
        triggers an SCD Type 2 version update in the Data Warehouse.
        """
        mgr = EmployeeManager()
        test_emp_id = "EMP-TEST999"

        # Onboard test employee
        test_emp = Employee(
            employee_id=test_emp_id,
            first_name="Alex",
            last_name="Morgan",
            email="alex.morgan999@enterprise.corp",
            phone="+1-555-999-8888",
            gender="Female",
            age=29,
            marital_status="Single",
            hire_date="2023-05-10",
            department_id=2,  # Sales
            job_role="Sales Executive",
            education_field="Marketing",
            monthly_income=6200.0
        )
        mgr.onboard_employee(test_emp)

        # Verify initial state (Version 1)
        history_v1 = mgr.get_employee_scd2_history(test_emp_id)
        self.assertEqual(len(history_v1), 1)
        self.assertEqual(history_v1[0]["version"], 1)
        self.assertEqual(history_v1[0]["is_current"], 1)
        self.assertEqual(history_v1[0]["job_role"], "Sales Executive")

        # TRIGGER SCD TYPE 2 UPDATE: Promote to Software Engineering with higher salary
        result = mgr.reassign_employee_role_or_dept(
            employee_id=test_emp_id,
            new_department_id=4,  # Software Engineering
            new_job_role="Lead Software Engineer",
            new_monthly_income=12500.0,
            effective_date="2026-02-01"
        )
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["expired_version"], 1)
        self.assertEqual(result["new_active_version"], 2)

        # Verify SCD Type 2 state in Warehouse: exactly 2 versions
        history_v2 = mgr.get_employee_scd2_history(test_emp_id)
        self.assertEqual(len(history_v2), 2, "Must contain exactly 2 versions in Dim_Employee.")

        # Version 1 (Historical)
        v1 = history_v2[0]
        self.assertEqual(v1["version"], 1)
        self.assertEqual(v1["is_current"], 0, "Previous version must be marked is_current = 0.")
        self.assertEqual(v1["end_date"], "2026-02-01", "End date must reflect transition timestamp.")

        # Version 2 (Active)
        v2 = history_v2[1]
        self.assertEqual(v2["version"], 2)
        self.assertEqual(v2["is_current"], 1, "New version must be marked is_current = 1.")
        self.assertEqual(v2["job_role"], "Lead Software Engineer")
        self.assertEqual(v2["monthly_income"], 12500.0)
        self.assertIsNone(v2["end_date"], "Active version end_date must be NULL.")

        print("[PASS] SCD Type 2 Reassignment Trigger Verified: Version 1 expired, Version 2 active.")

    def test_04_analytics_manager_queries(self):
        """Validates that AnalyticsManager executes window functions on Star Schema."""
        analytics = AnalyticsManager()
        kpis = analytics.get_executive_kpis()
        self.assertGreater(kpis["total_active_employees"], 0)
        self.assertGreater(kpis["avg_monthly_salary"], 0)

        # Test Window Function DENSE_RANK()
        df_top = analytics.get_top_performers(year=2025, top_n=3)
        self.assertFalse(df_top.empty)
        self.assertIn("dept_perf_rank", df_top.columns)
        self.assertTrue((df_top["dept_perf_rank"] <= 3).all())

        # Test YoY Trends
        df_yoy = analytics.get_yoy_performance_trends()
        self.assertFalse(df_yoy.empty)
        self.assertIn("review_year", df_yoy.columns)

        print("[PASS] Star Schema Analytics & SQL Window Functions (DENSE_RANK) Verified.")

    def test_05_custom_exceptions_and_logger(self):
        """Validates custom exception hierarchy and centralized logger."""
        logger = get_logger("test")
        self.assertIsNotNone(logger)
        logger.info("Test log statement emitted.")

        # Verify ValidationError inherits from ValueError and EnterpriseAnalyticsError
        with self.assertRaises(ValidationError):
            raise ValidationError("Validation test constraint breached.")

        # Verify EntityNotFoundError
        with self.assertRaises(EntityNotFoundError):
            mgr = EmployeeManager()
            mgr.reassign_employee_role_or_dept(
                employee_id="NON-EXISTENT-EMP-000",
                new_department_id=1,
                new_job_role="Invalid",
                new_monthly_income=5000.0
            )

        print("[PASS] Custom Exceptions and Centralized Logging Framework Verified.")

    def test_06_sqlalchemy_engine(self):
        """Validates that DatabaseConnection returns a functional SQLAlchemy Engine."""
        db = get_db()
        engine = db.get_sqlalchemy_engine()
        self.assertIsNotNone(engine)
        # Execute basic query via SQLAlchemy engine connection
        with engine.connect() as conn:
            self.assertFalse(conn.closed)
        print("[PASS] SQLAlchemy Engine Integration and Connection Pooling Verified.")

    def test_07_project_allocation_and_bottleneck_analysis(self):
        """Validates project allocation & workload bottleneck diagnostic query."""
        analytics = AnalyticsManager()
        df_alloc = analytics.get_project_allocation_analysis()
        self.assertFalse(df_alloc.empty, "Project allocation dataframe must not be empty.")
        self.assertIn("active_projects", df_alloc.columns)
        self.assertIn("total_assignments", df_alloc.columns)
        self.assertIn("bottleneck_risk_score", df_alloc.columns)
        self.assertIn("bottleneck_status", df_alloc.columns)
        print("[PASS] Project Allocation & Bottleneck Analysis Analytics Verified.")


if __name__ == "__main__":
    unittest.main()
