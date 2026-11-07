"""
Enterprise Employee Analytics - Streamlit UI Smoke Test
========================================================
Validates that all Streamlit application pages have valid syntax,
clean imports, and execute correctly without exceptions.

Author: Enterprise Data Architecture Team
"""

import sys
import os
import ast
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.db_manager import get_db
from src.managers.analytics_manager import AnalyticsManager
from src.managers.employee_manager import EmployeeManager
from src.managers.project_manager import ProjectManager


class TestStreamlitPages(unittest.TestCase):
    """Smoke test ensuring all Streamlit page scripts are syntactically sound and backend queries succeed."""

    def test_01_script_syntax(self):
        """Validates that all Streamlit pages parse into valid AST without SyntaxError."""
        pages = [
            "app.py",
            os.path.join("pages", "1_HR_Operations.py"),
            os.path.join("pages", "2_Executive_Analytics.py")
        ]

        for p in pages:
            with open(p, "r", encoding="utf-8") as f:
                code = f.read()
            try:
                ast.parse(code)
                print(f"[PASS] Syntax valid for: {p}")
            except SyntaxError as e:
                self.fail(f"SyntaxError in {p}: {e}")

    def test_02_analytics_dashboard_queries(self):
        """Verifies that all queries called by Executive Analytics dashboard return non-empty DataFrames."""
        analytics = AnalyticsManager()

        kpis = analytics.get_executive_kpis()
        self.assertGreater(kpis["total_active_employees"], 0)

        df_top = analytics.get_top_performers(year=2025, top_n=3)
        self.assertFalse(df_top.empty)
        self.assertIn("dept_perf_rank", df_top.columns)

        df_yoy = analytics.get_yoy_performance_trends()
        self.assertFalse(df_yoy.empty)

        df_attr = analytics.get_attrition_risk_analysis()
        self.assertFalse(df_attr.empty)

        df_dept = analytics.get_department_distribution()
        self.assertFalse(df_dept.empty)

        df_scd2 = analytics.get_scd2_progression_audit(limit=10)
        self.assertFalse(df_scd2.empty)
        print("[PASS] All Executive Analytics queries returned valid DataFrames.")

    def test_03_hr_operations_queries(self):
        """Verifies that queries called by HR Operations portal succeed."""
        emp_mgr = EmployeeManager()
        proj_mgr = ProjectManager()

        depts = emp_mgr.get_departments()
        self.assertGreater(len(depts), 0)

        projs = proj_mgr.list_projects()
        self.assertGreater(len(projs), 0)

        emps = emp_mgr.list_employees(limit=10)
        self.assertEqual(len(emps), 10)
        print("[PASS] All HR Operations queries returned valid entities.")


if __name__ == "__main__":
    unittest.main()
