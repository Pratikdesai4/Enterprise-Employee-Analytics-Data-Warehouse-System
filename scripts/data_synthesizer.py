"""
Enterprise Employee Analytics - Data Synthesizer Engine
======================================================
Scales base IBM HR Analytics dataset to 100,000+ realistic enterprise records
and synthesizes historical Slowly Changing Dimension (SCD Type 2) transitions.

Author: Enterprise Data Architecture Team
Architecture: Object-Oriented Synthesis Pipeline
"""

import os
import json
import time
import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any

import numpy as np
import pandas as pd
from faker import Faker


@dataclass
class SynthesizerConfig:
    """Configuration parameters for enterprise data synthesis."""
    base_dataset_path: str = os.path.join("data", "raw", "WA_Fn-UseC_-HR-Employee-Attrition.csv")
    output_dir: str = os.path.join("data", "synthesized")
    num_employees: int = 100_000
    scd2_historical_ratio: float = 0.25  # 25% of employees have historical SCD2 transitions
    num_projects: int = 60
    random_seed: int = 42
    start_year: int = 2018
    current_year: int = 2026


class BaseDatasetProfiler:
    """Profiles and extracts empirical distributions from the IBM HR dataset."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.df_base: pd.DataFrame = pd.DataFrame()
        self.distributions: Dict[str, Any] = {}

    def load_and_profile(self) -> Dict[str, Any]:
        """Loads the raw IBM dataset and extracts frequency distributions."""
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"Raw dataset not found at {self.filepath}")

        self.df_base = pd.read_csv(self.filepath)
        print(f"[Profiler] Ingested seed dataset: {len(self.df_base)} rows, {len(self.df_base.columns)} columns.")

        # Compute distributions
        dept_counts = self.df_base['Department'].value_counts(normalize=True)
        role_counts = self.df_base['JobRole'].value_counts(normalize=True)
        edu_counts = self.df_base['EducationField'].value_counts(normalize=True)
        gender_counts = self.df_base['Gender'].value_counts(normalize=True)
        marital_counts = self.df_base['MaritalStatus'].value_counts(normalize=True)
        travel_counts = self.df_base['BusinessTravel'].value_counts(normalize=True)
        overtime_counts = self.df_base['OverTime'].value_counts(normalize=True)

        # Department to Job Roles mapping
        dept_roles = self.df_base.groupby('Department')['JobRole'].unique().to_dict()

        # Role salary distributions (mean and std dev)
        salary_stats = self.df_base.groupby('JobRole')['MonthlyIncome'].agg(['mean', 'std', 'min', 'max']).to_dict('index')

        self.distributions = {
            'department_prob': dept_counts.to_dict(),
            'role_prob': role_counts.to_dict(),
            'education_prob': edu_counts.to_dict(),
            'gender_prob': gender_counts.to_dict(),
            'marital_prob': marital_counts.to_dict(),
            'business_travel_prob': travel_counts.to_dict(),
            'overtime_prob': overtime_counts.to_dict(),
            'dept_to_roles': dept_roles,
            'salary_stats': salary_stats,
            'age_mean': float(self.df_base['Age'].mean()),
            'age_std': float(self.df_base['Age'].std()),
        }
        return self.distributions


class EnterpriseDataSynthesizer:
    """Core Object-Oriented engine to generate scaled relational and dimensional records."""

    def __init__(self, config: SynthesizerConfig, profiler: BaseDatasetProfiler):
        self.config = config
        self.profiler = profiler
        self.fake = Faker()
        Faker.seed(config.random_seed)
        np.random.seed(config.random_seed)

        os.makedirs(self.config.output_dir, exist_ok=True)

        self.departments: pd.DataFrame = pd.DataFrame()
        self.projects: pd.DataFrame = pd.DataFrame()
        self.employees_current: pd.DataFrame = pd.DataFrame()
        self.employees_scd2: pd.DataFrame = pd.DataFrame()
        self.project_assignments: pd.DataFrame = pd.DataFrame()
        self.performance_reviews: pd.DataFrame = pd.DataFrame()

    def generate_departments(self) -> pd.DataFrame:
        """Generates enterprise departments with cost centers and metadata."""
        dept_specs = [
            {"department_id": 1, "department_name": "Research & Development", "cost_center": "CC-RND-101", "budget": 12500000.00},
            {"department_id": 2, "department_name": "Sales", "cost_center": "CC-SLS-202", "budget": 8500000.00},
            {"department_id": 3, "department_name": "Human Resources", "cost_center": "CC-HR-303", "budget": 3200000.00},
            {"department_id": 4, "department_name": "Software Engineering", "cost_center": "CC-SWE-404", "budget": 15000000.00},
            {"department_id": 5, "department_name": "Finance & Operations", "cost_center": "CC-OPS-505", "budget": 6800000.00},
        ]
        self.departments = pd.DataFrame(dept_specs)
        return self.departments

    def generate_projects(self) -> pd.DataFrame:
        """Generates enterprise projects with timelines, budgets, and statuses."""
        project_names = [
            "Cloud Infrastructure Migration", "NextGen ERP Implementation", "AI Copilot Integration",
            "Customer 360 Analytics", "Zero Trust Security Architecture", "Omnichannel Mobile Portal",
            "Supply Chain Visibility Engine", "Automated Compliance Reporting", "Data Lakehouse Modernization",
            "Microservices Decomposition", "DevOps Continuous Delivery Hub", "Predictive Attrition Pipeline",
            "Global HR Workday Integration", "Enterprise Search Knowledge Graph", "API Gateway Modernization",
            "Billing & Invoicing Redesign", "Edge IoT Telemetry Platform", "SOC2 Compliance Automation",
            "Self-Service BI Workspace", "Unified Customer Support Desk"
        ]

        projects = []
        statuses = ["In Progress", "Completed", "Planning", "On Hold"]
        status_weights = [0.55, 0.30, 0.10, 0.05]

        for pid in range(1, self.config.num_projects + 1):
            base_name = project_names[(pid - 1) % len(project_names)]
            version_suffix = f"Phase {((pid - 1) // len(project_names)) + 1}"
            dept_id = int((pid % len(self.departments)) + 1)
            
            start_offset = np.random.randint(0, 1500)
            proj_start = datetime.date(2020, 1, 1) + datetime.timedelta(days=int(start_offset))
            proj_duration = np.random.randint(90, 730)
            proj_end = proj_start + datetime.timedelta(days=int(proj_duration))
            
            status = np.random.choice(statuses, p=status_weights)
            budget = float(np.random.randint(150, 2500) * 1000)

            projects.append({
                "project_id": pid,
                "project_code": f"PRJ-{pid:04d}",
                "project_name": f"{base_name} ({version_suffix})",
                "department_id": dept_id,
                "start_date": proj_start.isoformat(),
                "end_date": proj_end.isoformat(),
                "budget": budget,
                "status": status
            })

        self.projects = pd.DataFrame(projects)
        return self.projects

    def generate_employees(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Synthesizes 100,000+ employees and generates historical SCD Type 2 transitions.
        Returns:
            employees_current: 100,000 active employee records for OLTP.
            employees_scd2: Full dimensional records with historical versions for OLAP.
        """
        n = self.config.num_employees
        print(f"[Synthesizer] Synthesizing {n:,} base employee records...")

        # Fast pool of Faker names
        pool_size = 5000
        first_names = [self.fake.first_name() for _ in range(pool_size)]
        last_names = [self.fake.last_name() for _ in range(pool_size)]

        chosen_first = np.random.choice(first_names, size=n)
        chosen_last = np.random.choice(last_names, size=n)
        emp_ids = [f"EMP-{i:06d}" for i in range(1, n + 1)]

        # Map departments
        dept_ids = np.random.choice([1, 2, 3, 4, 5], size=n, p=[0.25, 0.20, 0.10, 0.30, 0.15])
        dept_map = dict(zip(self.departments['department_id'], self.departments['department_name']))

        # Job roles per department
        role_map = {
            1: ["Research Scientist", "Laboratory Technician", "Research Director", "R&D Specialist"],
            2: ["Sales Executive", "Sales Representative", "Account Manager", "Regional Sales Director"],
            3: ["HR Specialist", "HR Generalist", "Talent Acquisition Lead", "HR Business Partner"],
            4: ["Software Engineer", "Senior Software Engineer", "DevOps Engineer", "Engineering Manager", "Data Engineer"],
            5: ["Financial Analyst", "Operations Coordinator", "Finance Manager", "Business Controller"]
        }

        roles = [np.random.choice(role_map[d]) for d in dept_ids]

        # Age and Tenure
        ages = np.clip(np.random.normal(37, 8, size=n).astype(int), 21, 65)
        tenure_years = np.clip(np.random.exponential(4, size=n).astype(int), 0, 30)
        tenure_years = np.minimum(tenure_years, ages - 20)

        # Base hire date
        today = datetime.date(2026, 3, 1)
        hire_dates = [
            (today - datetime.timedelta(days=int(ty * 365.25 + np.random.randint(0, 360)))).isoformat()
            for ty in tenure_years
        ]

        # Salary ranges by role level
        salary_levels = {
            "Representative": (3200, 4800), "Technician": (3500, 5200),
            "Coordinator": (3800, 5500), "Specialist": (4500, 7000),
            "Analyst": (5000, 8000), "Engineer": (6500, 10500),
            "Scientist": (6800, 11000), "Generalist": (4800, 7500),
            "Senior": (8500, 14000), "Lead": (9000, 15000),
            "Manager": (11000, 18000), "Director": (15000, 24000),
            "Controller": (12000, 19000), "Partner": (10000, 16000)
        }

        salaries = []
        for r in roles:
            matched = False
            for key, (low, high) in salary_levels.items():
                if key in r:
                    salaries.append(float(np.random.randint(low, high)))
                    matched = True
                    break
            if not matched:
                salaries.append(float(np.random.randint(4500, 9500)))

        education_fields = np.random.choice(
            ["Computer Science", "Life Sciences", "Medical", "Marketing", "Technical Degree", "Finance", "Human Resources"],
            size=n,
            p=[0.30, 0.20, 0.10, 0.15, 0.10, 0.10, 0.05]
        )
        genders = np.random.choice(["Male", "Female"], size=n, p=[0.58, 0.42])
        marital_statuses = np.random.choice(["Single", "Married", "Divorced"], size=n, p=[0.32, 0.46, 0.22])
        overtime_flags = np.random.choice(["Yes", "No"], size=n, p=[0.28, 0.72])
        attrition_flags = np.random.choice(["No", "Yes"], size=n, p=[0.84, 0.16])

        # Contacts
        emails = [f"{fn.lower()}.{ln.lower()}{i+100}@enterprise.corp" for i, (fn, ln) in enumerate(zip(chosen_first, chosen_last))]
        phones = [f"+1-555-{np.random.randint(100, 999)}-{np.random.randint(1000, 9999)}" for _ in range(n)]

        # Assemble current OLTP employees
        df_curr = pd.DataFrame({
            "employee_id": emp_ids,
            "first_name": chosen_first,
            "last_name": chosen_last,
            "email": emails,
            "phone": phones,
            "gender": genders,
            "age": ages,
            "marital_status": marital_statuses,
            "hire_date": hire_dates,
            "department_id": dept_ids,
            "department_name": [dept_map[d] for d in dept_ids],
            "job_role": roles,
            "education_field": education_fields,
            "monthly_income": salaries,
            "overtime": overtime_flags,
            "years_at_company": tenure_years,
            "attrition": attrition_flags,
            "status": ["Terminated" if att == "Yes" else "Active" for att in attrition_flags]
        })

        # -------------------------------------------------------------
        # ENGINEER HISTORICAL SCD TYPE 2 RECORDS
        # -------------------------------------------------------------
        print(f"[Synthesizer] Engineering SCD Type 2 historical records for ~{int(n * self.config.scd2_historical_ratio):,} employees...")
        num_scd = int(n * self.config.scd2_historical_ratio)
        eligible_indices = np.where(df_curr['years_at_company'] >= 2)[0]
        selected_indices = np.random.choice(eligible_indices, size=min(num_scd, len(eligible_indices)), replace=False)

        scd_records = []
        surrogate_key = 1

        # Track which employees have SCD history
        scd_index_set = set(selected_indices)

        for idx in range(n):
            row = df_curr.iloc[idx]
            emp_id = row['employee_id']
            hire_d = datetime.date.fromisoformat(row['hire_date'])

            if idx in scd_index_set:
                # Employee experienced a historical career event (e.g. transfer, promotion, salary raise)
                # Event occurred between 1 and 3 years ago
                transition_days = int(np.random.randint(365, min(1400, max(366, row['years_at_company'] * 365))))
                transition_date = today - datetime.timedelta(days=transition_days)
                if transition_date <= hire_d:
                    transition_date = hire_d + datetime.timedelta(days=180)

                # Prior state (Version 1)
                prior_salary = round(row['monthly_income'] * np.random.uniform(0.75, 0.88), 2)
                # 50% chance of prior department transfer, 50% promotion in same dept
                if np.random.rand() > 0.5:
                    prior_dept_id = 3 if row['department_id'] != 3 else 1
                else:
                    prior_dept_id = row['department_id']
                
                prior_role = f"Associate {row['job_role'].replace('Senior ', '').replace('Lead ', '').replace('Director', 'Specialist')}"

                # Append Version 1 (Historical - Expired)
                scd_records.append({
                    "employee_dim_id": surrogate_key,
                    "employee_id": emp_id,
                    "first_name": row['first_name'],
                    "last_name": row['last_name'],
                    "gender": row['gender'],
                    "age": max(20, row['age'] - (transition_days // 365)),
                    "hire_date": row['hire_date'],
                    "department_id": prior_dept_id,
                    "department_name": dept_map[prior_dept_id],
                    "job_role": prior_role,
                    "education_field": row['education_field'],
                    "monthly_income": prior_salary,
                    "start_date": row['hire_date'],
                    "end_date": transition_date.isoformat(),
                    "is_current": 0,
                    "version": 1
                })
                surrogate_key += 1

                # Append Version 2 (Current Active Record)
                scd_records.append({
                    "employee_dim_id": surrogate_key,
                    "employee_id": emp_id,
                    "first_name": row['first_name'],
                    "last_name": row['last_name'],
                    "gender": row['gender'],
                    "age": row['age'],
                    "hire_date": row['hire_date'],
                    "department_id": row['department_id'],
                    "department_name": row['department_name'],
                    "job_role": row['job_role'],
                    "education_field": row['education_field'],
                    "monthly_income": row['monthly_income'],
                    "start_date": transition_date.isoformat(),
                    "end_date": None,
                    "is_current": 1,
                    "version": 2
                })
                surrogate_key += 1

            else:
                # Stable employee (Single current version from hire date to present)
                scd_records.append({
                    "employee_dim_id": surrogate_key,
                    "employee_id": emp_id,
                    "first_name": row['first_name'],
                    "last_name": row['last_name'],
                    "gender": row['gender'],
                    "age": row['age'],
                    "hire_date": row['hire_date'],
                    "department_id": row['department_id'],
                    "department_name": row['department_name'],
                    "job_role": row['job_role'],
                    "education_field": row['education_field'],
                    "monthly_income": row['monthly_income'],
                    "start_date": row['hire_date'],
                    "end_date": None,
                    "is_current": 1,
                    "version": 1
                })
                surrogate_key += 1

        self.employees_current = df_curr
        self.employees_scd2 = pd.DataFrame(scd_records)
        return self.employees_current, self.employees_scd2

    def generate_project_assignments(self) -> pd.DataFrame:
        """Assigns a subset of active employees to enterprise projects."""
        print("[Synthesizer] Generating project assignments...")
        assignments = []
        assignment_id = 1
        roles = ["Project Lead", "Senior Developer", "Core Contributor", "Quality Assurance", "Business Analyst"]
        
        # Sample 40,000 assignments
        emp_sample = np.random.choice(self.employees_current['employee_id'], size=40000, replace=True)
        proj_sample = np.random.choice(self.projects['project_id'], size=40000, replace=True)
        allocations = np.random.choice([25, 50, 75, 100], size=40000, p=[0.1, 0.4, 0.3, 0.2])

        for eid, pid, alloc in zip(emp_sample, proj_sample, allocations):
            assignments.append({
                "assignment_id": assignment_id,
                "employee_id": eid,
                "project_id": pid,
                "assignment_role": np.random.choice(roles),
                "allocation_percentage": int(alloc),
                "assigned_date": datetime.date(2023, 1, 1).isoformat()
            })
            assignment_id += 1

        self.project_assignments = pd.DataFrame(assignments).drop_duplicates(subset=['employee_id', 'project_id'])
        return self.project_assignments

    def generate_performance_reviews(self) -> pd.DataFrame:
        """
        Generates longitudinal performance reviews (2021-2025) for fact table loading.
        Maps reviews to employee SCD records and captures KPIs.
        """
        print("[Synthesizer] Synthesizing longitudinal performance review facts...")
        reviews = []
        review_id = 1
        review_years = [2021, 2022, 2023, 2024, 2025]

        # Use current and historical employees
        sample_size = min(len(self.employees_current), 60000)
        selected_emps = self.employees_current.sample(n=sample_size, random_state=self.config.random_seed)

        for _, emp in selected_emps.iterrows():
            hire_year = int(emp['hire_date'][:4])
            years_eligible = [y for y in review_years if y >= hire_year]

            for yr in years_eligible:
                rev_date = f"{yr}-12-15"
                rating = int(np.random.choice([1, 2, 3, 4, 5], p=[0.05, 0.15, 0.50, 0.20, 0.10]))
                wlb = int(np.random.choice([1, 2, 3, 4], p=[0.10, 0.25, 0.45, 0.20]))
                job_sat = int(np.random.choice([1, 2, 3, 4], p=[0.08, 0.22, 0.50, 0.20]))
                env_sat = int(np.random.choice([1, 2, 3, 4], p=[0.08, 0.22, 0.50, 0.20]))
                hike = float(np.random.choice([0.0, 5.0, 8.0, 12.0, 15.0, 20.0], p=[0.10, 0.25, 0.35, 0.15, 0.10, 0.05]))
                promoted = 1 if (rating >= 4 and hike >= 12.0) else 0

                # Calculate calculated attrition risk score (0 to 100)
                risk = 15
                if emp['overtime'] == 'Yes': risk += 25
                if wlb <= 2: risk += 20
                if job_sat <= 2: risk += 20
                if rating <= 2: risk += 15
                if hike <= 5.0: risk += 10
                attrition_risk_score = min(100, max(5, risk + np.random.randint(-5, 6)))

                reviews.append({
                    "review_id": review_id,
                    "employee_id": emp['employee_id'],
                    "department_id": emp['department_id'],
                    "review_date": rev_date,
                    "review_year": yr,
                    "performance_rating": rating,
                    "monthly_income_at_review": emp['monthly_income'],
                    "percent_salary_hike": hike,
                    "work_life_balance": wlb,
                    "job_satisfaction": job_sat,
                    "environment_satisfaction": env_sat,
                    "promotion_given": promoted,
                    "attrition_risk_score": attrition_risk_score,
                    "tenure_at_review": max(0, yr - hire_year)
                })
                review_id += 1

        self.performance_reviews = pd.DataFrame(reviews)
        return self.performance_reviews

    def export_all(self) -> Dict[str, str]:
        """Saves all generated datasets to CSV and exports manifest."""
        print("[Synthesizer] Writing datasets to disk...")
        paths = {}

        exports = [
            ("departments.csv", self.departments),
            ("projects.csv", self.projects),
            ("employees_oltp_current.csv", self.employees_current),
            ("employees_scd2_full.csv", self.employees_scd2),
            ("project_assignments.csv", self.project_assignments),
            ("performance_reviews.csv", self.performance_reviews)
        ]

        for filename, df in exports:
            filepath = os.path.join(self.config.output_dir, filename)
            df.to_csv(filepath, index=False)
            paths[filename] = filepath
            print(f"  -> Exported {filename}: {len(df):,} rows ({os.path.getsize(filepath) / (1024 * 1024):.2f} MB)")

        # Create metadata manifest
        manifest = {
            "generated_at": datetime.datetime.now().isoformat(),
            "config": {
                "num_employees": self.config.num_employees,
                "scd2_historical_ratio": self.config.scd2_historical_ratio,
                "num_projects": self.config.num_projects,
                "random_seed": self.config.random_seed
            },
            "record_counts": {
                "departments": len(self.departments),
                "projects": len(self.projects),
                "employees_oltp_current": len(self.employees_current),
                "employees_scd2_full": len(self.employees_scd2),
                "project_assignments": len(self.project_assignments),
                "performance_reviews": len(self.performance_reviews)
            },
            "scd2_breakdown": {
                "total_records": len(self.employees_scd2),
                "current_active_records": int((self.employees_scd2['is_current'] == 1).sum()),
                "historical_expired_records": int((self.employees_scd2['is_current'] == 0).sum())
            }
        }

        manifest_path = os.path.join(self.config.output_dir, "synthesis_manifest.json")
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        paths["manifest"] = manifest_path

        print(f"[Synthesizer] Manifest saved to {manifest_path}")
        return paths


def main():
    start_time = time.time()
    config = SynthesizerConfig(num_employees=100_000)
    profiler = BaseDatasetProfiler(config.base_dataset_path)
    profiler.load_and_profile()

    synthesizer = EnterpriseDataSynthesizer(config, profiler)
    synthesizer.generate_departments()
    synthesizer.generate_projects()
    synthesizer.generate_employees()
    synthesizer.generate_project_assignments()
    synthesizer.generate_performance_reviews()
    paths = synthesizer.export_all()

    elapsed = round(time.time() - start_time, 2)
    print(f"\n=======================================================")
    print(f"Data Synthesis Completed Successfully in {elapsed} seconds!")
    print(f"=======================================================")


if __name__ == "__main__":
    main()
