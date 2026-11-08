#!/usr/bin/env python
# demo_employee_manager.py – quick sanity‑check for the OOP backend

import uuid
import sys, os
from datetime import date

# Add the scripts directory to PYTHONPATH so imports work from the project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "")))

from services.employee_manager import EmployeeManager
from models import Employee

def main():
    mgr = EmployeeManager()

    # 1️⃣ Create a dummy employee
    emp = Employee(
        employee_id=f"EMP-{uuid.uuid4().hex[:6].upper()}",
        first_name="Alice",
        last_name="Smith",
        email="alice.smith@example.com",
        phone="555-123-4567",
        gender="Female",
        age=30,
        marital_status="Single",
        hire_date=date(2022, 5, 1),
        department_id=4,
        department_name="Software Engineering",
        job_role="Software Engineer",
        education_field="Computer Science",
        monthly_income=8500.00,
    )
    print("[Demo] Creating employee …")
    mgr.create(emp)

    # 2️⃣ Read it back
    fetched = mgr.get(emp.employee_id)
    print("[Demo] Fetched:", fetched)

    # 3️⃣ Update a mutable field
    fetched.monthly_income = 9100.00
    mgr.update(fetched)
    print("[Demo] Updated monthly_income to 9100.00")

    # 4️⃣ Verify update
    refreshed = mgr.get(emp.employee_id)
    print("[Demo] After update:", refreshed.monthly_income)

    # 5️⃣ Clean up (delete)
    mgr.delete(emp.employee_id)
    print("[Demo] Deleted employee", emp.employee_id)

if __name__ == "__main__":
    main()
