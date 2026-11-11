#!/usr/bin/env python
"""
demo_employee_manager.py – Sanity-check verification script for the OOP backend.
Uses canonical src/ entities and managers.
"""

import uuid
import sys
import os
from datetime import date

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.entities.employee import Employee
from src.managers.employee_manager import EmployeeManager


def main():
    mgr = EmployeeManager()

    # 1️ Create a test employee
    emp_id = f"EMP-{uuid.uuid4().hex[:6].upper()}"
    emp = Employee(
        employee_id=emp_id,
        first_name="Alice",
        last_name="Smith",
        email=f"alice.{uuid.uuid4().hex[:4]}@enterprise.corp",
        phone="+1-555-123-4567",
        gender="Female",
        age=30,
        marital_status="Single",
        hire_date=date(2022, 5, 1).isoformat(),
        department_id=4,
        department_name="Software Engineering",
        job_role="Software Engineer",
        education_field="Computer Science",
        monthly_income=8500.00,
    )
    print(f"[Demo] Creating employee {emp_id} …")
    mgr.create(emp)

    # 2️ Read it back
    fetched = mgr.get(emp.employee_id)
    print(f"[Demo] Fetched: {fetched.full_name} ({fetched.job_role}, ${fetched.monthly_income:,.2f})")

    # 3️ Update a mutable field
    fetched.monthly_income = 9100.00
    mgr.update(fetched)
    print("[Demo] Updated monthly_income to $9,100.00")

    # 4️ Verify update
    refreshed = mgr.get(emp.employee_id)
    print(f"[Demo] After update verified: ${refreshed.monthly_income:,.2f}")

    # 5️ Clean up (delete)
    mgr.delete(emp.employee_id)
    print(f"[Demo] Deleted test employee {emp.employee_id}")
    print("[Demo] OOP Backend Verification Completed Successfully!")


if __name__ == "__main__":
    main()
