"""
Enterprise Employee Analytics - Performance Review Domain Entity
================================================================
Encapsulates performance appraisal scores, salary hikes, and attrition risk.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import datetime


@dataclass
class PerformanceReview:
    employee_id: str
    department_id: int
    review_date: str
    performance_rating: int
    monthly_income_at_review: float
    percent_salary_hike: float
    work_life_balance: int
    job_satisfaction: int
    environment_satisfaction: int
    review_id: Optional[int] = None
    review_year: Optional[int] = None
    promotion_given: int = 0
    attrition_risk_score: int = 0
    tenure_at_review: int = 0

    def __post_init__(self):
        if self.review_year is None and self.review_date:
            try:
                self.review_year = int(str(self.review_date)[:4])
            except Exception:
                self.review_year = datetime.date.today().year

        if not self.attrition_risk_score:
            self.attrition_risk_score = self.calculate_attrition_risk()

        self.validate()

    @property
    def is_high_performer(self) -> bool:
        """Determines if the employee performed at top tiers (4 or 5)."""
        return self.performance_rating >= 4

    @property
    def risk_level(self) -> str:
        """Categorizes attrition threat level."""
        if self.attrition_risk_score >= 70:
            return "High"
        elif self.attrition_risk_score >= 40:
            return "Medium"
        else:
            return "Low"

    def calculate_attrition_risk(self) -> int:
        """Heuristic risk model based on work-life balance, satisfaction, and rating."""
        risk = 15
        if self.work_life_balance <= 2:
            risk += 25
        if self.job_satisfaction <= 2:
            risk += 25
        if self.performance_rating <= 2:
            risk += 15
        if self.percent_salary_hike <= 5.0:
            risk += 10
        return min(100, max(5, risk))

    def validate(self) -> bool:
        """Enforces domain review rules."""
        if not (1 <= self.performance_rating <= 5):
            raise ValueError(f"Performance rating must be between 1 and 5 (got {self.performance_rating}).")
        if not (1 <= self.work_life_balance <= 4):
            raise ValueError(f"Work life balance must be between 1 and 4 (got {self.work_life_balance}).")
        if not (1 <= self.job_satisfaction <= 4):
            raise ValueError(f"Job satisfaction must be between 1 and 4 (got {self.job_satisfaction}).")
        if not (1 <= self.environment_satisfaction <= 4):
            raise ValueError(f"Environment satisfaction must be between 1 and 4 (got {self.environment_satisfaction}).")
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Converts entity to dictionary."""
        return {
            "review_id": self.review_id,
            "employee_id": self.employee_id,
            "department_id": self.department_id,
            "review_date": str(self.review_date),
            "review_year": self.review_year,
            "performance_rating": self.performance_rating,
            "monthly_income_at_review": float(self.monthly_income_at_review),
            "percent_salary_hike": float(self.percent_salary_hike),
            "work_life_balance": self.work_life_balance,
            "job_satisfaction": self.job_satisfaction,
            "environment_satisfaction": self.environment_satisfaction,
            "promotion_given": self.promotion_given,
            "attrition_risk_score": self.attrition_risk_score,
            "risk_level": self.risk_level,
            "tenure_at_review": self.tenure_at_review
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceReview':
        """Constructs PerformanceReview entity from dictionary."""
        return cls(
            review_id=data.get("review_id"),
            employee_id=str(data.get("employee_id")),
            department_id=int(data.get("department_id", 1)),
            review_date=str(data.get("review_date", datetime.date.today().isoformat())),
            review_year=data.get("review_year"),
            performance_rating=int(data.get("performance_rating", 3)),
            monthly_income_at_review=float(data.get("monthly_income_at_review", 5000.0)),
            percent_salary_hike=float(data.get("percent_salary_hike", 5.0)),
            work_life_balance=int(data.get("work_life_balance", 3)),
            job_satisfaction=int(data.get("job_satisfaction", 3)),
            environment_satisfaction=int(data.get("environment_satisfaction", 3)),
            promotion_given=int(data.get("promotion_given", 0)),
            attrition_risk_score=int(data.get("attrition_risk_score", 0)),
            tenure_at_review=int(data.get("tenure_at_review", 0))
        )
