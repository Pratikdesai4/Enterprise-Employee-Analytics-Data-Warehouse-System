"""
Entity definitions for the Enterprise Employee Analytics backend.
Each entity is a simple dataclass representing a row in the OLTP tables.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional


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
    hire_date: date
    department_id: int
    department_name: str
    job_role: str
    education_field: str
    monthly_income: float
    overtime: str = "No"
    years_at_company: int = 0
    attrition: str = "No"
    status: str = "Active"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


@dataclass
class Project:
    project_id: int
    project_code: str
    project_name: str
    department_id: int
    start_date: date
    end_date: date
    budget: float
    status: str


@dataclass
class Review:
    review_id: int
    employee_id: str
    review_date: date
    performance_rating: int
    monthly_income_at_review: float
    percent_salary_hike: float = 0.0
    work_life_balance: int = 1
    job_satisfaction: int = 1
    environment_satisfaction: int = 1
    attrition_risk_score: int = 0
    tenure_at_review: int = 0
    promotion_given: bool = False
