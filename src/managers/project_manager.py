"""
Enterprise Employee Analytics - Project & Review Manager (DAL)
==============================================================
Manages enterprise projects, employee staffing allocations, and
submitting performance appraisals.

Author: Enterprise Data Architecture Team
"""

import datetime
from typing import Optional, List, Dict, Any, Tuple
from src.managers.base_manager import BaseManager
from src.entities.project import Project
from src.entities.review import PerformanceReview
from src.exceptions import EntityNotFoundError, ValidationError
from src.logger import get_logger

logger = get_logger("project_manager")


class ProjectManager(BaseManager):
    """Data Access Layer managing Projects, Allocations, and Reviews."""

    def __init__(self, db=None):
        super().__init__(db)
        if self.backend == "mysql":
            self.tbl_proj_oltp = "enterprise_hr_oltp.projects"
            self.tbl_assign = "enterprise_hr_oltp.employee_project_assignments"
            self.tbl_rev_oltp = "enterprise_hr_oltp.performance_reviews"
            self.tbl_proj_dw = "enterprise_hr_dw.Dim_Project"
            self.tbl_fact = "enterprise_hr_dw.Fact_PerformanceReviews"
            self.tbl_emp_dw = "enterprise_hr_dw.Dim_Employee"
            self.tbl_dept_dw = "enterprise_hr_dw.Dim_Department"
        else:
            self.tbl_proj_oltp = "projects_oltp"
            self.tbl_assign = "employee_project_assignments"
            self.tbl_rev_oltp = "performance_reviews_oltp"
            self.tbl_proj_dw = "Dim_Project"
            self.tbl_fact = "Fact_PerformanceReviews"
            self.tbl_emp_dw = "Dim_Employee"
            self.tbl_dept_dw = "Dim_Department"

    def list_projects(self, department_id: Optional[int] = None, status: Optional[str] = None) -> List[Project]:
        """Lists enterprise initiatives with optional filters."""
        clauses = []
        params = []

        if department_id:
            clauses.append("department_id = %s")
            params.append(department_id)

        if status:
            clauses.append("status = %s")
            params.append(status)

        where_str = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"""
            SELECT * FROM {self.tbl_proj_oltp}
            {where_str}
            ORDER BY project_id DESC
        """
        rows = self._execute_query(sql, tuple(params))
        return [Project.from_dict(r) for r in rows]

    def create_project(self, project: Project) -> int:
        """Creates a new project in OLTP and synchronizes with Dim_Project in the warehouse."""
        project.validate()

        # Insert into OLTP
        sql_oltp = f"""
            INSERT INTO {self.tbl_proj_oltp} (
                project_code, project_name, department_id, start_date, end_date, budget, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        self._execute_update(sql_oltp, (
            project.project_code, project.project_name, project.department_id,
            project.start_date, project.end_date, project.budget, project.status
        ))

        # Retrieve created project_id
        sql_get_id = f"SELECT project_id FROM {self.tbl_proj_oltp} WHERE project_code = %s"
        rows = self._execute_query(sql_get_id, (project.project_code,))
        new_id = rows[0]["project_id"]

        # Insert into Dim_Project
        sql_dw = f"""
            INSERT INTO {self.tbl_proj_dw} (project_id, project_code, project_name, budget_tier, status)
            VALUES (%s, %s, %s, %s, %s)
        """
        self._execute_update(sql_dw, (
            new_id, project.project_code, project.project_name, project.budget_tier, project.status
        ))

        logger.info("Created initiative %s (ID: %s)", project.project_code, new_id)
        return new_id

    def assign_employee(self, employee_id: str, project_id: int, role: str, allocation_percentage: int = 100) -> bool:
        """Assigns an employee to a project in the allocation bridge table."""
        assigned_date = datetime.date.today().isoformat()
        sql = f"""
            INSERT INTO {self.tbl_assign} (employee_id, project_id, assignment_role, allocation_percentage, assigned_date)
            VALUES (%s, %s, %s, %s, %s)
        """
        self._execute_update(sql, (employee_id, project_id, role, allocation_percentage, assigned_date))
        logger.info("Assigned %s to project %s (%d%% commitment)", employee_id, project_id, allocation_percentage)
        return True

    def get_project_team(self, project_id: int) -> List[Dict[str, Any]]:
        """Returns all staff members allocated to a specific project."""
        sql = f"""
            SELECT a.assignment_id, a.employee_id, a.assignment_role, a.allocation_percentage, a.assigned_date
            FROM {self.tbl_assign} a
            WHERE a.project_id = %s
        """
        return self._execute_query(sql, (project_id,))

    def submit_performance_review(self, review: PerformanceReview) -> bool:
        """Submits an appraisal into OLTP and loads corresponding fact record in Star Schema."""
        review.validate()

        # 1. Look up exact active SCD2 surrogate key for this employee
        sql_emp_dim = f"""
            SELECT employee_dim_id 
            FROM {self.tbl_emp_dw}
            WHERE employee_id = %s AND is_current = 1
        """
        emp_dim_rows = self._execute_query(sql_emp_dim, (review.employee_id,))
        if not emp_dim_rows:
            raise EntityNotFoundError(f"Active dimension not found for employee {review.employee_id}")
        employee_dim_id = emp_dim_rows[0]["employee_dim_id"]

        # 2. Look up department surrogate key
        sql_dept_dim = f"""
            SELECT department_dim_id 
            FROM {self.tbl_dept_dw}
            WHERE department_id = %s
        """
        dept_dim_rows = self._execute_query(sql_dept_dim, (review.department_id,))
        department_dim_id = dept_dim_rows[0]["department_dim_id"] if dept_dim_rows else 1

        # Date Dim ID
        date_dim_id = int(str(review.review_date).replace("-", ""))

        # 3. Insert into Fact table
        sql_fact = f"""
            INSERT INTO {self.tbl_fact} (
                employee_dim_id, department_dim_id, project_dim_id, date_dim_id,
                review_id, employee_id, performance_rating, monthly_income_at_review,
                percent_salary_hike, work_life_balance, job_satisfaction, environment_satisfaction,
                attrition_risk_score, tenure_at_review, promotion_given
            ) VALUES (%s, %s, 0, %s, 0, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        self._execute_update(sql_fact, (
            employee_dim_id, department_dim_id, date_dim_id, review.employee_id,
            review.performance_rating, review.monthly_income_at_review, review.percent_salary_hike,
            review.work_life_balance, review.job_satisfaction, review.environment_satisfaction,
            review.attrition_risk_score, review.tenure_at_review, review.promotion_given
        ))

        logger.info("Submitted appraisal fact for %s (rating: %s)", review.employee_id, review.performance_rating)
        return True
