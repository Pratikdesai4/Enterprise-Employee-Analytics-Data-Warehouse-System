"""
Enterprise Employee Analytics - Employee Domain Entity
======================================================
Encapsulates employee attributes, state, and domain validations.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import datetime
import re

from src.exceptions import ValidationError


@dataclass
class Employee:
    employee_id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    gender: str
    age: int
    marital_status: str
    hire_date: str
    department_id: int
    job_role: str
    education_field: str
    monthly_income: float
    department_name: Optional[str] = None
    overtime: str = "No"
    years_at_company: int = 0
    attrition: str = "No"
    status: str = "Active"

    def __post_init__(self):
        self.validate()

    @property
    def full_name(self) -> str:
        """Returns the employee's full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def annual_salary(self) -> float:
        """Computes annual compensation."""
        return round(float(self.monthly_income) * 12.0, 2)

    def validate(self) -> bool:
        """Enforces domain validations."""
        if not self.employee_id or not self.employee_id.strip():
            raise ValidationError("Employee ID cannot be empty.")
        if self.age < 18 or self.age > 75:
            raise ValidationError(f"Invalid employee age: {self.age}. Must be between 18 and 75.")
        if self.monthly_income <= 0:
            raise ValidationError("Monthly income must be a positive number.")
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", self.email):
            raise ValidationError(f"Invalid email address format: {self.email}")
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Converts entity to dictionary."""
        return {
            "employee_id": self.employee_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "gender": self.gender,
            "age": self.age,
            "marital_status": self.marital_status,
            "hire_date": str(self.hire_date),
            "department_id": self.department_id,
            "department_name": self.department_name,
            "job_role": self.job_role,
            "education_field": self.education_field,
            "monthly_income": float(self.monthly_income),
            "overtime": self.overtime,
            "years_at_company": self.years_at_company,
            "attrition": self.attrition,
            "status": self.status
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Employee':
        """Constructs Employee entity from dictionary."""
        return cls(
            employee_id=str(data.get("employee_id")),
            first_name=str(data.get("first_name", "")),
            last_name=str(data.get("last_name", "")),
            email=str(data.get("email", "")),
            phone=str(data.get("phone", "")),
            gender=str(data.get("gender", "Other")),
            age=int(data.get("age", 30)),
            marital_status=str(data.get("marital_status", "Single")),
            hire_date=str(data.get("hire_date", datetime.date.today().isoformat())),
            department_id=int(data.get("department_id", 1)),
            department_name=data.get("department_name"),
            job_role=str(data.get("job_role", "")),
            education_field=str(data.get("education_field", "Technical Degree")),
            monthly_income=float(data.get("monthly_income", 5000.0)),
            overtime=str(data.get("overtime", "No")),
            years_at_company=int(data.get("years_at_company", 0)),
            attrition=str(data.get("attrition", "No")),
            status=str(data.get("status", "Active"))
        )
