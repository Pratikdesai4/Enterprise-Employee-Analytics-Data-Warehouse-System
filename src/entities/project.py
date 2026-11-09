"""
Enterprise Employee Analytics - Project Domain Entity
=====================================================
Encapsulates enterprise project attributes, budgets, and lifecycle state.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import datetime

from src.exceptions import ValidationError


@dataclass
class Project:
    project_id: Optional[int]
    project_code: str
    project_name: str
    department_id: int
    start_date: str
    end_date: str
    budget: float
    status: str = "Planning"

    def __post_init__(self):
        self.validate()

    @property
    def budget_tier(self) -> str:
        """Categorizes project financial scale."""
        if self.budget < 500_000:
            return "Small (<$500k)"
        elif self.budget <= 1_500_000:
            return "Medium ($500k-$1.5M)"
        else:
            return "Large (>$1.5M)"

    @property
    def duration_days(self) -> int:
        """Calculates project duration in days."""
        try:
            d_start = datetime.date.fromisoformat(str(self.start_date))
            d_end = datetime.date.fromisoformat(str(self.end_date))
            return max(0, (d_end - d_start).days)
        except Exception:
            return 0

    def validate(self) -> bool:
        """Validates project constraints."""
        if not self.project_name or not self.project_name.strip():
            raise ValidationError("Project name cannot be empty.")
        if self.budget < 0:
            raise ValidationError("Project budget cannot be negative.")
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Converts entity to dictionary."""
        return {
            "project_id": self.project_id,
            "project_code": self.project_code,
            "project_name": self.project_name,
            "department_id": self.department_id,
            "start_date": str(self.start_date),
            "end_date": str(self.end_date),
            "budget": float(self.budget),
            "budget_tier": self.budget_tier,
            "status": self.status
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Constructs Project entity from dictionary."""
        return cls(
            project_id=data.get("project_id"),
            project_code=str(data.get("project_code", "")),
            project_name=str(data.get("project_name", "")),
            department_id=int(data.get("department_id", 1)),
            start_date=str(data.get("start_date", datetime.date.today().isoformat())),
            end_date=str(data.get("end_date", datetime.date.today().isoformat())),
            budget=float(data.get("budget", 100000.0)),
            status=str(data.get("status", "Planning"))
        )
