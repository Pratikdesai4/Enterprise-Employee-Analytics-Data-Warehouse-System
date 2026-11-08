"""
EmployeeManager – OOP data‑access layer for the OLTP `employees_oltp` table.
Provides CRUD operations using the singleton DatabaseConnection.
"""

from typing import List, Optional
from datetime import date

from db_manager import DatabaseConnection
from models import Employee

class EmployeeManager:
    """High‑level manager for Employee entities.

    All methods open a cursor, execute a query, and commit.
    Errors are wrapped in ``RuntimeError`` for uniform handling.
    """

    def __init__(self):
        self._db = DatabaseConnection.instance().get_connection()

    def _commit(self) -> None:
        self._db.commit()

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------
    def create(self, employee: Employee) -> None:
        """Insert a new employee row.
        Raises ``RuntimeError`` if the INSERT fails (e.g., duplicate PK)."""
        sql = (
            "INSERT INTO employees_oltp (employee_id, first_name, last_name, email, phone, gender, age, "
            "marital_status, hire_date, department_id, department_name, job_role, education_field, "
            "monthly_income, overtime, years_at_company, attrition, status) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        values = (
            employee.employee_id,
            employee.first_name,
            employee.last_name,
            employee.email,
            employee.phone,
            employee.gender,
            employee.age,
            employee.marital_status,
            employee.hire_date.isoformat(),
            employee.department_id,
            employee.department_name,
            employee.job_role,
            employee.education_field,
            employee.monthly_income,
            employee.overtime,
            employee.years_at_company,
            employee.attrition,
            employee.status,
        )
        try:
            cur = self._db.cursor()
            cur.execute(sql, values)
            self._commit()
        except Exception as e:
            raise RuntimeError(f"Failed to create employee {employee.employee_id}: {e}")

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------
    def get(self, employee_id: str) -> Optional[Employee]:
        """Retrieve an employee by PK. Returns ``None`` if not found."""
        sql = "SELECT * FROM employees_oltp WHERE employee_id = %s"
        cur = self._db.cursor(dictionary=True)
        cur.execute(sql, (employee_id,))
        row = cur.fetchone()
        if not row:
            return None
        return Employee(
            employee_id=row["employee_id"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            email=row["email"],
            phone=row["phone"],
            gender=row["gender"],
            age=row["age"],
            marital_status=row["marital_status"],
            hire_date=date.fromisoformat(row["hire_date"]),
            department_id=row["department_id"],
            department_name=row["department_name"],
            job_role=row["job_role"],
            education_field=row["education_field"],
            monthly_income=row["monthly_income"],
            overtime=row["overtime"],
            years_at_company=row["years_at_company"],
            attrition=row["attrition"],
            status=row["status"],
        )

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------
    def update(self, employee: Employee) -> None:
        """Update mutable fields of an employee."""
        sql = (
            "UPDATE employees_oltp SET first_name=%s, last_name=%s, email=%s, phone=%s, gender=%s, age=%s, "
            "marital_status=%s, department_id=%s, department_name=%s, job_role=%s, education_field=%s, "
            "monthly_income=%s, overtime=%s, years_at_company=%s, attrition=%s, status=%s "
            "WHERE employee_id=%s"
        )
        values = (
            employee.first_name,
            employee.last_name,
            employee.email,
            employee.phone,
            employee.gender,
            employee.age,
            employee.marital_status,
            employee.department_id,
            employee.department_name,
            employee.job_role,
            employee.education_field,
            employee.monthly_income,
            employee.overtime,
            employee.years_at_company,
            employee.attrition,
            employee.status,
            employee.employee_id,
        )
        try:
            cur = self._db.cursor()
            cur.execute(sql, values)
            self._commit()
        except Exception as e:
            raise RuntimeError(f"Failed to update employee {employee.employee_id}: {e}")

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------
    def delete(self, employee_id: str) -> None:
        """Delete an employee row permanently."""
        sql = "DELETE FROM employees_oltp WHERE employee_id = %s"
        try:
            cur = self._db.cursor()
            cur.execute(sql, (employee_id,))
            self._commit()
        except Exception as e:
            raise RuntimeError(f"Failed to delete employee {employee_id}: {e}")

    # ------------------------------------------------------------------
    # LIST ALL
    # ------------------------------------------------------------------
    def list_all(self) -> List[Employee]:
        """Return a list of all employees (useful for admin screens)."""
        sql = "SELECT * FROM employees_oltp"
        cur = self._db.cursor(dictionary=True)
        cur.execute(sql)
        rows = cur.fetchall()
        result: List[Employee] = []
        for row in rows:
            result.append(
                Employee(
                    employee_id=row["employee_id"],
                    first_name=row["first_name"],
                    last_name=row["last_name"],
                    email=row["email"],
                    phone=row["phone"],
                    gender=row["gender"],
                    age=row["age"],
                    marital_status=row["marital_status"],
                    hire_date=date.fromisoformat(row["hire_date"]),
                    department_id=row["department_id"],
                    department_name=row["department_name"],
                    job_role=row["job_role"],
                    education_field=row["education_field"],
                    monthly_income=row["monthly_income"],
                    overtime=row["overtime"],
                    years_at_company=row["years_at_company"],
                    attrition=row["attrition"],
                    status=row["status"],
                )
            )
        return result
