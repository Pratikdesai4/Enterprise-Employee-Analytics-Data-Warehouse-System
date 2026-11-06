"""
Enterprise Employee Analytics - Analytics Manager (DAL)
=======================================================
Interprets the OLAP Star Schema, executes advanced window functions,
and delivers analytical dataframes for Streamlit dashboards.

Author: Enterprise Data Architecture Team
"""

import pandas as pd
from typing import Optional, Dict, Any, List
from src.managers.base_manager import BaseManager


class AnalyticsManager(BaseManager):
    """Data Access Layer interfacing directly with the Dimensional Star Schema."""

    def __init__(self, db=None):
        super().__init__(db)
        if self.backend == "mysql":
            self.tbl_fact = "enterprise_hr_dw.Fact_PerformanceReviews"
            self.tbl_emp_dw = "enterprise_hr_dw.Dim_Employee"
            self.tbl_dept_dw = "enterprise_hr_dw.Dim_Department"
            self.tbl_proj_dw = "enterprise_hr_dw.Dim_Project"
            self.tbl_date_dw = "enterprise_hr_dw.Dim_Date"
        else:
            self.tbl_fact = "Fact_PerformanceReviews"
            self.tbl_emp_dw = "Dim_Employee"
            self.tbl_dept_dw = "Dim_Department"
            self.tbl_proj_dw = "Dim_Project"
            self.tbl_date_dw = "Dim_Date"

    def get_executive_kpis(self) -> Dict[str, Any]:
        """Calculates headline operational and warehouse metrics."""
        # 1. Total Active Employees & Avg Monthly Salary
        sql_emp = f"""
            SELECT 
                COUNT(*) as total_active_employees,
                AVG(monthly_income) as avg_monthly_salary
            FROM {self.tbl_emp_dw}
            WHERE is_current = 1
        """
        emp_metrics = self._execute_query(sql_emp)[0]

        # 2. Fact Table Review Averages (Latest Year)
        sql_fact = f"""
            SELECT 
                AVG(performance_rating) as avg_rating,
                AVG(attrition_risk_score) as avg_attrition_risk,
                SUM(promotion_given) as total_promotions,
                COUNT(*) as total_reviews
            FROM {self.tbl_fact}
        """
        fact_metrics = self._execute_query(sql_fact)[0]

        # 3. Active Projects Count
        sql_proj = f"SELECT COUNT(*) as total_projects FROM {self.tbl_proj_dw}"
        proj_metrics = self._execute_query(sql_proj)[0]

        # 4. SCD2 Transitioned Employees Count
        sql_scd2 = f"""
            SELECT COUNT(DISTINCT employee_id) as total_promoted_employees
            FROM {self.tbl_emp_dw}
            WHERE version > 1
        """
        scd2_metrics = self._execute_query(sql_scd2)[0]

        return {
            "total_active_employees": emp_metrics["total_active_employees"] or 0,
            "avg_monthly_salary": round(float(emp_metrics["avg_monthly_salary"] or 0.0), 2),
            "avg_performance_rating": round(float(fact_metrics["avg_rating"] or 0.0), 2),
            "avg_attrition_risk": round(float(fact_metrics["avg_attrition_risk"] or 0.0), 1),
            "total_promotions": fact_metrics["total_promotions"] or 0,
            "total_reviews": fact_metrics["total_reviews"] or 0,
            "total_projects": proj_metrics["total_projects"] or 0,
            "career_transitioned_employees": scd2_metrics["total_promoted_employees"] or 0
        }

    def get_top_performers(self, year: int = 2025, top_n: int = 3, department_name: Optional[str] = None) -> pd.DataFrame:
        """
        Executes SQL Window Function DENSE_RANK() to identify top-performing tiers.
        """
        dept_clause = f"AND dd.department_name = '{department_name}'" if department_name else ""

        sql = f"""
            WITH DepartmentPerformanceRanking AS (
                SELECT 
                    dd.department_name,
                    de.employee_id,
                    de.first_name || ' ' || de.last_name AS full_name,
                    de.job_role,
                    f.performance_rating,
                    f.percent_salary_hike,
                    f.monthly_income_at_review,
                    f.attrition_risk_score,
                    d.year AS review_year,
                    DENSE_RANK() OVER (
                        PARTITION BY dd.department_name 
                        ORDER BY f.performance_rating DESC, f.percent_salary_hike DESC
                    ) AS dept_perf_rank
                FROM {self.tbl_fact} f
                INNER JOIN {self.tbl_emp_dw} de ON f.employee_dim_id = de.employee_dim_id
                INNER JOIN {self.tbl_dept_dw} dd ON f.department_dim_id = dd.department_dim_id
                INNER JOIN {self.tbl_date_dw} d ON f.date_dim_id = d.date_dim_id
                WHERE d.year = {year} {dept_clause}
            )
            SELECT 
                dept_perf_rank,
                department_name,
                employee_id,
                full_name,
                job_role,
                performance_rating,
                percent_salary_hike,
                monthly_income_at_review,
                attrition_risk_score
            FROM DepartmentPerformanceRanking
            WHERE dept_perf_rank <= {top_n}
            ORDER BY department_name, dept_perf_rank, full_name
        """
        return self.db.fetch_dataframe(sql)

    def get_yoy_performance_trends(self) -> pd.DataFrame:
        """Computes annual longitudinal performance ratings and salary hike trends."""
        sql = f"""
            SELECT 
                d.year as review_year,
                ROUND(AVG(f.performance_rating), 2) as avg_rating,
                ROUND(AVG(f.percent_salary_hike), 2) as avg_hike_pct,
                ROUND(AVG(f.monthly_income_at_review), 2) as avg_income,
                ROUND(AVG(f.attrition_risk_score), 1) as avg_attrition_risk,
                SUM(f.promotion_given) as total_promotions,
                COUNT(*) as review_count
            FROM {self.tbl_fact} f
            INNER JOIN {self.tbl_date_dw} d ON f.date_dim_id = d.date_dim_id
            GROUP BY d.year
            ORDER BY d.year ASC
        """
        return self.db.fetch_dataframe(sql)

    def get_attrition_risk_analysis(self) -> pd.DataFrame:
        """Analyzes attrition risks grouped by department and job role."""
        sql = f"""
            SELECT 
                dd.department_name,
                de.job_role,
                COUNT(*) as employee_count,
                ROUND(AVG(f.attrition_risk_score), 1) as avg_risk_score,
                ROUND(AVG(f.work_life_balance), 2) as avg_work_life_balance,
                ROUND(AVG(f.job_satisfaction), 2) as avg_job_satisfaction,
                SUM(CASE WHEN f.attrition_risk_score >= 65 THEN 1 ELSE 0 END) as high_risk_count
            FROM {self.tbl_fact} f
            INNER JOIN {self.tbl_emp_dw} de ON f.employee_dim_id = de.employee_dim_id
            INNER JOIN {self.tbl_dept_dw} dd ON f.department_dim_id = dd.department_dim_id
            INNER JOIN {self.tbl_date_dw} d ON f.date_dim_id = d.date_dim_id
            WHERE d.year = 2025
            GROUP BY dd.department_name, de.job_role
            ORDER BY avg_risk_score DESC
        """
        return self.db.fetch_dataframe(sql)

    def get_department_distribution(self) -> pd.DataFrame:
        """Returns headcount and compensation volume per department."""
        sql = f"""
            SELECT 
                department_name,
                COUNT(*) as headcount,
                ROUND(AVG(monthly_income), 2) as avg_salary,
                ROUND(SUM(monthly_income) * 12, 2) as total_payroll_annual
            FROM {self.tbl_emp_dw}
            WHERE is_current = 1
            GROUP BY department_name
            ORDER BY headcount DESC
        """
        return self.db.fetch_dataframe(sql)

    def get_scd2_progression_audit(self, limit: int = 50) -> pd.DataFrame:
        """Queries multi-version career histories and promotion salary deltas."""
        sql = f"""
            WITH MultiVersionEmployees AS (
                SELECT employee_id
                FROM {self.tbl_emp_dw}
                GROUP BY employee_id
                HAVING COUNT(*) > 1
                LIMIT {limit}
            )
            SELECT 
                de.employee_id,
                de.first_name || ' ' || de.last_name as full_name,
                de.version,
                de.is_current,
                de.department_name,
                de.job_role,
                de.monthly_income,
                de.start_date,
                COALESCE(de.end_date, 'Present') as end_date
            FROM {self.tbl_emp_dw} de
            INNER JOIN MultiVersionEmployees m ON de.employee_id = m.employee_id
            ORDER BY de.employee_id, de.version ASC
        """
        return self.db.fetch_dataframe(sql)
