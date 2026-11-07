"""
Enterprise Employee Analytics - Employee Manager (DAL)
======================================================
Handles CRUD operations for employees and triggers Slowly Changing
Dimension (SCD Type 2) updates in the Data Warehouse.

Author: Enterprise Data Architecture Team
"""

import datetime
from typing import Optional, List, Dict, Any, Tuple
from src.managers.base_manager import BaseManager
from src.entities.employee import Employee


class EmployeeManager(BaseManager):
    """Data Access Layer managing Employee lifecycle and SCD Type 2 synchronization."""

    def __init__(self, db=None):
        super().__init__(db)
        if self.backend == "mysql":
            self.tbl_emp_oltp = "enterprise_hr_oltp.employees"
            self.tbl_dept_oltp = "enterprise_hr_oltp.departments"
            self.tbl_emp_dw = "enterprise_hr_dw.Dim_Employee"
            self.tbl_dept_dw = "enterprise_hr_dw.Dim_Department"
        else:
            self.tbl_emp_oltp = "employees_oltp"
            self.tbl_dept_oltp = "departments_oltp"
            self.tbl_emp_dw = "Dim_Employee"
            self.tbl_dept_dw = "Dim_Department"

    def get_employee(self, employee_id_or_term: str) -> Optional[Employee]:
        """
        Retrieves an employee by ID or Name.
        Robust search across OLTP and Data Warehouse dimensions.
        """
        if not employee_id_or_term or not str(employee_id_or_term).strip():
            return None
        term = str(employee_id_or_term).strip()

        # 1. Direct search by ID in OLTP
        sql = f"""
            SELECT e.*, d.department_name
            FROM {self.tbl_emp_oltp} e
            LEFT JOIN {self.tbl_dept_oltp} d ON e.department_id = d.department_id
            WHERE UPPER(TRIM(e.employee_id)) = UPPER(%s)
        """
        rows = self._execute_query(sql, (term,))

        # 2. Search by Name in OLTP
        if not rows:
            sql_name = f"""
                SELECT e.*, d.department_name
                FROM {self.tbl_emp_oltp} e
                LEFT JOIN {self.tbl_dept_oltp} d ON e.department_id = d.department_id
                WHERE UPPER(e.first_name || ' ' || e.last_name) LIKE UPPER(%s)
                   OR UPPER(e.first_name) = UPPER(%s)
                   OR UPPER(e.last_name) = UPPER(%s)
                LIMIT 1
            """
            rows = self._execute_query(sql_name, (f"%{term}%", term, term))

        # 3. Fallback to Dim_Employee in Data Warehouse (Current Version)
        if not rows:
            sql_dw = f"""
                SELECT 
                    employee_id, first_name, last_name,
                    (LOWER(first_name) || '.' || LOWER(last_name) || '@enterprise.corp') as email,
                    '+1-555-010-0000' as phone, gender, age,
                    'Single' as marital_status, hire_date, department_id, department_name,
                    job_role, education_field, monthly_income, 'No' as overtime, 0 as years_at_company,
                    'No' as attrition, 'Active' as status
                FROM {self.tbl_emp_dw}
                WHERE (UPPER(TRIM(employee_id)) = UPPER(%s) OR UPPER(first_name || ' ' || last_name) LIKE UPPER(%s))
                  AND is_current = 1
                LIMIT 1
            """
            rows = self._execute_query(sql_dw, (term, f"%{term}%"))

        if not rows:
            return None
        return Employee.from_dict(rows[0])

    def list_employees(self, limit: int = 50, offset: int = 0, search: Optional[str] = None, department_id: Optional[int] = None) -> List[Employee]:
        """Queries active employees with search, department filters, and pagination."""
        clauses = []
        params = []

        if search:
            search_param = f"%{search}%"
            clauses.append("(e.employee_id LIKE %s OR e.first_name LIKE %s OR e.last_name LIKE %s OR e.email LIKE %s)")
            params.extend([search_param, search_param, search_param, search_param])

        if department_id:
            clauses.append("e.department_id = %s")
            params.append(department_id)

        where_str = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"""
            SELECT e.*, d.department_name
            FROM {self.tbl_emp_oltp} e
            LEFT JOIN {self.tbl_dept_oltp} d ON e.department_id = d.department_id
            {where_str}
            ORDER BY e.employee_id ASC
            LIMIT {limit} OFFSET {offset}
        """
        rows = self._execute_query(sql, tuple(params))
        return [Employee.from_dict(r) for r in rows]

    def count_employees(self, search: Optional[str] = None, department_id: Optional[int] = None) -> int:
        """Counts total active employees matching search criteria."""
        clauses = []
        params = []

        if search:
            search_param = f"%{search}%"
            clauses.append("(employee_id LIKE %s OR first_name LIKE %s OR last_name LIKE %s)")
            params.extend([search_param, search_param, search_param])

        if department_id:
            clauses.append("department_id = %s")
            params.append(department_id)

        where_str = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"SELECT COUNT(*) as cnt FROM {self.tbl_emp_oltp} {where_str}"
        rows = self._execute_query(sql, tuple(params))
        return rows[0]["cnt"] if rows else 0

    def get_departments(self) -> List[Dict[str, Any]]:
        """Fetches all operational departments."""
        sql = f"SELECT * FROM {self.tbl_dept_oltp} ORDER BY department_id"
        return self._execute_query(sql)

    def onboard_employee(self, emp: Employee) -> bool:
        """
        Onboards a new employee into OLTP and provisions initial version in the SCD2 Data Warehouse.
        """
        emp.validate()

        # 1. Fetch department name
        dept_rows = self._execute_query(
            f"SELECT department_name FROM {self.tbl_dept_oltp} WHERE department_id = %s",
            (emp.department_id,)
        )
        dept_name = dept_rows[0]["department_name"] if dept_rows else "General"
        emp.department_name = dept_name

        # 2. Insert into OLTP (Use INSERT OR REPLACE for SQLite, or standard insert for MySQL)
        insert_verb = "INSERT INTO" if self.backend == "mysql" else "INSERT OR REPLACE INTO"
        sql_oltp = f"""
            {insert_verb} {self.tbl_emp_oltp} (
                employee_id, first_name, last_name, email, phone, gender, age,
                marital_status, hire_date, department_id, department_name, job_role, education_field,
                monthly_income, overtime, years_at_company, attrition, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        self._execute_update(sql_oltp, (
            emp.employee_id, emp.first_name, emp.last_name, emp.email, emp.phone, emp.gender, emp.age,
            emp.marital_status, emp.hire_date, emp.department_id, dept_name, emp.job_role, emp.education_field,
            emp.monthly_income, emp.overtime, emp.years_at_company, emp.attrition, emp.status
        ))

        # 3. Provision Initial Version (Version 1) in Dim_Employee (SCD Type 2)
        sql_dw = f"""
            INSERT INTO {self.tbl_emp_dw} (
                employee_id, first_name, last_name, gender, age, hire_date,
                department_id, department_name, job_role, education_field, monthly_income,
                start_date, end_date, is_current, version
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NULL, 1, 1)
        """
        self._execute_update(sql_dw, (
            emp.employee_id, emp.first_name, emp.last_name, emp.gender, emp.age, emp.hire_date,
            emp.department_id, dept_name, emp.job_role, emp.education_field, emp.monthly_income,
            emp.hire_date
        ))

        return True

    def reassign_employee_role_or_dept(
        self,
        employee_id: str,
        new_department_id: int,
        new_job_role: str,
        new_monthly_income: float,
        effective_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Updates an employee's department, role, or salary in OLTP and
        TRIGGERS AN SCD TYPE 2 UPDATE in the Data Warehouse.

        Steps:
        1. Query current active version in Dim_Employee.
        2. Expire active version: set end_date = effective_date, is_current = 0.
        3. Insert new version: set start_date = effective_date, end_date = NULL, is_current = 1, version = old_version + 1.
        4. Update operational record in OLTP.
        """
        today_str = effective_date or datetime.date.today().isoformat()

        # Step 1: Look up current active version in Dim_Employee
        sql_lookup = f"""
            SELECT employee_dim_id, version, first_name, last_name, gender, age, hire_date, education_field
            FROM {self.tbl_emp_dw}
            WHERE UPPER(TRIM(employee_id)) = UPPER(TRIM(%s)) AND is_current = 1
        """
        dw_rows = self._execute_query(sql_lookup, (employee_id,))
        if not dw_rows:
            raise ValueError(f"Employee {employee_id} not found in Data Warehouse active dimensions.")

        current_ver_record = dw_rows[0]
        old_dim_id = current_ver_record["employee_dim_id"]
        old_version = current_ver_record["version"]
        new_version = old_version + 1

        # Look up new department name
        dept_rows = self._execute_query(
            f"SELECT department_name FROM {self.tbl_dept_oltp} WHERE department_id = %s",
            (new_department_id,)
        )
        new_dept_name = dept_rows[0]["department_name"] if dept_rows else "Unknown"

        # Step 2: Expire the previous active record in Dim_Employee (SCD Type 2)
        sql_expire = f"""
            UPDATE {self.tbl_emp_dw}
            SET end_date = %s,
                is_current = 0
            WHERE employee_dim_id = %s
        """
        self._execute_update(sql_expire, (today_str, old_dim_id))

        # Step 3: Insert the new active successor version in Dim_Employee (SCD Type 2)
        sql_insert_scd2 = f"""
            INSERT INTO {self.tbl_emp_dw} (
                employee_id, first_name, last_name, gender, age, hire_date,
                department_id, department_name, job_role, education_field, monthly_income,
                start_date, end_date, is_current, version
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NULL, 1, %s)
        """
        self._execute_update(sql_insert_scd2, (
            employee_id, current_ver_record["first_name"], current_ver_record["last_name"],
            current_ver_record["gender"], current_ver_record["age"], current_ver_record["hire_date"],
            new_department_id, new_dept_name, new_job_role, current_ver_record["education_field"],
            float(new_monthly_income), today_str, new_version
        ))

        # Step 4: Update operational record in OLTP
        sql_update_oltp = f"""
            UPDATE {self.tbl_emp_oltp}
            SET department_id = %s,
                department_name = %s,
                job_role = %s,
                monthly_income = %s
            WHERE UPPER(TRIM(employee_id)) = UPPER(TRIM(%s))
        """
        self._execute_update(sql_update_oltp, (new_department_id, new_dept_name, new_job_role, float(new_monthly_income), employee_id))

        return {
            "status": "SUCCESS",
            "employee_id": employee_id,
            "expired_version": old_version,
            "new_active_version": new_version,
            "effective_date": today_str,
            "new_department": new_dept_name,
            "new_role": new_job_role,
            "new_monthly_income": new_monthly_income
        }

    def get_employee_scd2_history(self, employee_id: str) -> List[Dict[str, Any]]:
        """Fetches the complete historical career lifecycle for an employee across all versions."""
        sql = f"""
            SELECT 
                employee_dim_id,
                employee_id,
                version,
                department_name,
                job_role,
                monthly_income,
                start_date,
                end_date,
                is_current
            FROM {self.tbl_emp_dw}
            WHERE UPPER(TRIM(employee_id)) = UPPER(TRIM(%s))
            ORDER BY version ASC
        """
        return self._execute_query(sql, (employee_id,))
