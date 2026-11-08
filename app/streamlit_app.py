"""
Streamlit UI entry point for Enterprise Employee Analytics.
Provides forms for onboarding employees, projects, reviews and an analytical dashboard.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date

# Import OOP backend managers
from services.employee_manager import EmployeeManager
from services.project_manager import ProjectManager  # will be created later
from services.review_manager import ReviewManager    # will be created later

# Helper to display a success toast
def _show_success(msg: str):
    st.success(msg)

st.set_page_config(page_title="Enterprise Employee Analytics", layout="wide")

# -------------------------------------------------
# Sidebar navigation
# -------------------------------------------------
section = st.sidebar.radio(
    "Navigation",
    ["Home", "Employee Onboarding", "Project Management", "Performance Reviews", "Analytics Dashboard"],
)

# -------------------------------------------------
# Home page
# -------------------------------------------------
if section == "Home":
    st.title("🏢 Enterprise Employee Analytics")
    st.write(
        "Welcome! Use the sidebar to manage employees, projects, reviews, or explore the analytical dashboard."
    )

# -------------------------------------------------
# Employee Onboarding form
# -------------------------------------------------
elif section == "Employee Onboarding":
    st.title("👤 Employee Onboarding")
    with st.form("employee_form"):
        emp_id = st.text_input("Employee ID", value=f"EMP-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        age = st.number_input("Age", min_value=18, max_value=80, step=1)
        marital = st.selectbox("Marital Status", ["Single", "Married", "Divorced", "Widowed"])
        hire = st.date_input("Hire Date", value=date.today())
        dept_id = st.number_input("Department ID", min_value=1, step=1)
        dept_name = st.text_input("Department Name")
        job_role = st.text_input("Job Role")
        edu = st.text_input("Education Field")
        salary = st.number_input("Monthly Income", min_value=0.0, step=100.0)
        submitted = st.form_submit_button("Add Employee")
    if submitted:
        emp = Employee(
            employee_id=emp_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            gender=gender,
            age=int(age),
            marital_status=marital,
            hire_date=hire,
            department_id=int(dept_id),
            department_name=dept_name,
            job_role=job_role,
            education_field=edu,
            monthly_income=salary,
        )
        try:
            EmployeeManager().create(emp)
            _show_success(f"Employee {emp_id} added successfully.")
        except Exception as e:
            st.error(str(e))

# -------------------------------------------------
# Project Management form (placeholder – will be functional once ProjectManager exists)
# -------------------------------------------------
elif section == "Project Management":
    st.title("📁 Project Management")
    st.info("Project manager implementation is pending. Use the backend scripts for now.")

# -------------------------------------------------
# Performance Reviews form (placeholder – will be functional once ReviewManager exists)
# -------------------------------------------------
elif section == "Performance Reviews":
    st.title("📊 Performance Reviews")
    st.info("Review manager implementation is pending. Use the backend scripts for now.")

# -------------------------------------------------
# Analytics Dashboard
# -------------------------------------------------
elif section == "Analytics Dashboard":
    st.title("📈 Analytics Dashboard")
    # Pull data directly via the OOP managers (for demo we use pandas reads from MySQL)
    db = DatabaseConnection.instance().get_connection()
    df = pd.read_sql("SELECT * FROM Fact_PerformanceReviews LIMIT 5000", con=db)
    if df.empty:
        st.warning("No performance review data available yet.")
    else:
        # Example: Year‑over‑Year performance trend
        df["review_year"] = pd.to_datetime(df["date_dim_id"], format="%Y%m%d").dt.year
        yearly = df.groupby("review_year").agg({"performance_rating": "mean"}).reset_index()
        fig = px.line(yearly, x="review_year", y="performance_rating", title="Average Performance Rating by Year")
        st.plotly_chart(fig, use_container_width=True)

        # Example: Top‑performing employees by department
        top_emp = (
            df.groupby(["department_dim_id", "employee_id"]).agg({"performance_rating": "mean"})
            .reset_index()
            .sort_values("performance_rating", ascending=False)
            .head(10)
        )
        st.subheader("Top‑Performing Employees (by avg rating)")
        st.dataframe(top_emp)

        # Example: Attrition risk distribution
        fig2 = px.histogram(df, x="attrition_risk_score", nbins=20, title="Attrition Risk Score Distribution")
        st.plotly_chart(fig2, use_container_width=True)

st.caption("© 2026 Enterprise Employee Analytics – built with Streamlit, MySQL, and OOP Python.")
