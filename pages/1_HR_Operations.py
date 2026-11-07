"""
Enterprise Employee Analytics - HR Operations Portal (OLTP)
===========================================================
Operational forms for employee onboarding, project allocations,
performance appraisals, and real-time SCD Type 2 career updates.

Author: Enterprise Data Architecture Team
"""

import streamlit as st
import datetime
import pandas as pd
from src.database.db_manager import get_db
from src.entities.employee import Employee
from src.entities.project import Project
from src.entities.review import PerformanceReview
from src.managers.employee_manager import EmployeeManager
from src.managers.project_manager import ProjectManager

st.set_page_config(page_title="HR Operations Portal", page_icon="📝", layout="wide")

# Custom Styling
st.markdown("""
<style>
    .page-title { font-size: 2rem; font-weight: 700; color: #0F172A; }
    .sub-title { font-size: 1rem; color: #475569; margin-bottom: 1.5rem; }
    .success-box {
        background-color: #F0FDF4; border: 1px solid #86EFAC;
        border-radius: 8px; padding: 16px; margin-bottom: 16px;
    }
    .scd2-pill-active {
        background-color: #DCFCE7; color: #166534; font-weight: 600;
        padding: 4px 10px; border-radius: 12px; font-size: 0.8rem;
    }
    .scd2-pill-expired {
        background-color: #FEE2E2; color: #991B1B; font-weight: 600;
        padding: 4px 10px; border-radius: 12px; font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="page-title">📝 HR Operations & Transactional Portal</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Manage operational employee records, project staffing, and trigger real-time SCD Type 2 warehouse updates.</div>', unsafe_allow_html=True)

# Initialize Managers
db = get_db()
emp_mgr = EmployeeManager(db)
proj_mgr = ProjectManager(db)

# Fetch Departments List for Dropdowns
try:
    dept_list = emp_mgr.get_departments()
    dept_dict = {d["department_name"]: d["department_id"] for d in dept_list}
    dept_id_to_name = {d["department_id"]: d["department_name"] for d in dept_list}
except Exception as e:
    dept_list = []
    dept_dict = {"Research & Development": 1, "Sales": 2, "Human Resources": 3, "Software Engineering": 4, "Finance & Operations": 5}
    dept_id_to_name = {v: k for k, v in dept_dict.items()}

# Tab Navigation
tabs = st.tabs([
    "👤 Onboard Employee",
    "🔄 Career & Role Reassignment (SCD Type 2)",
    "🚀 Project Initiatives & Staffing",
    "⭐ Submit Performance Appraisal",
    "📑 Directory & Career Audit"
])

# =============================================================================
# TAB 1: ONBOARD EMPLOYEE
# =============================================================================
with tabs[0]:
    st.subheader("Onboard New Employee")
    st.caption("Inserts operational record in OLTP and provisions initial version (Version 1) in Dim_Employee.")

    with st.form("onboard_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            emp_id_input = st.text_input("Employee ID *", value=f"EMP-{datetime.datetime.now().strftime('%m%d%H%M')}")
            first_name = st.text_input("First Name *", placeholder="e.g. John")
            last_name = st.text_input("Last Name *", placeholder="e.g. Smith")
            email = st.text_input("Corporate Email *", placeholder="e.g. john.smith@enterprise.corp")
            phone = st.text_input("Phone Number *", placeholder="+1-555-010-0200")

        with col2:
            gender = st.selectbox("Gender *", ["Male", "Female", "Non-Binary", "Other"])
            age = st.number_input("Age *", min_value=18, max_value=75, value=28)
            marital_status = st.selectbox("Marital Status *", ["Single", "Married", "Divorced"])
            hire_date = st.date_input("Hire Date *", value=datetime.date.today())
            overtime = st.selectbox("Overtime Eligible", ["No", "Yes"])

        with col3:
            dept_selected = st.selectbox("Department *", list(dept_dict.keys()))
            job_role = st.text_input("Job Role / Title *", placeholder="e.g. Software Engineer")
            education = st.selectbox("Education Field *", [
                "Computer Science", "Life Sciences", "Medical", "Marketing",
                "Technical Degree", "Finance", "Human Resources", "Other"
            ])
            monthly_income = st.number_input("Monthly Income ($USD) *", min_value=1000.0, max_value=50000.0, value=7500.0, step=250.0)

        submitted = st.form_submit_button("Submit Onboarding Transaction", type="primary")

        if submitted:
            try:
                new_emp = Employee(
                    employee_id=emp_id_input.strip(),
                    first_name=first_name.strip(),
                    last_name=last_name.strip(),
                    email=email.strip().lower(),
                    phone=phone.strip(),
                    gender=gender,
                    age=int(age),
                    marital_status=marital_status,
                    hire_date=hire_date.isoformat(),
                    department_id=dept_dict[dept_selected],
                    job_role=job_role.strip(),
                    education_field=education,
                    monthly_income=float(monthly_income),
                    overtime=overtime,
                    years_at_company=0,
                    status="Active"
                )
                emp_mgr.onboard_employee(new_emp)
                st.success(f"✅ Employee **{new_emp.full_name}** ({new_emp.employee_id}) onboarded successfully into OLTP and synced with Dim_Employee (Version 1)!")
            except Exception as e:
                st.error(f"❌ Onboarding Failed: {e}")

# =============================================================================
# TAB 2: CAREER & ROLE REASSIGNMENT (SCD TYPE 2 LIVE TRIGGER)
# =============================================================================
with tabs[1]:
    st.subheader("🔄 Career Progression & Role Update (SCD Type 2)")
    st.markdown("""
    When an employee transitions to a new department, role, or salary:
    1. The operational record in OLTP is updated.
    2. The previous warehouse record is **expired** (`end_date = CURRENT_DATE, is_current = 0`).
    3. A new active record is **inserted** (`start_date = CURRENT_DATE, is_current = 1, version = old_version + 1`).
    """)

    lookup_col1, lookup_col2 = st.columns([3, 1])
    with lookup_col1:
        target_emp_id = st.text_input("Enter Employee ID to Update:", value="EMP-000001", help="Enter exact ID e.g. EMP-000001")
    with lookup_col2:
        search_clicked = st.button("Lookup Employee", type="secondary", use_container_width=True)

    curr_emp = emp_mgr.get_employee(target_emp_id.strip())

    if curr_emp:
        st.info(f"**Loaded:** {curr_emp.full_name} | Current Role: **{curr_emp.job_role}** | Department: **{curr_emp.department_name}** | Monthly Salary: **${curr_emp.monthly_income:,.2f}**")

        st.markdown("#### Enter Career & Compensation Transition:")
        with st.form("scd2_update_form"):
            ucol1, ucol2, ucol3 = st.columns(3)
            with ucol1:
                new_dept_name = st.selectbox(
                    "New Department",
                    list(dept_dict.keys()),
                    index=list(dept_dict.keys()).index(curr_emp.department_name) if curr_emp.department_name in dept_dict else 0
                )
            with ucol2:
                new_role = st.text_input("New Job Role / Title", value=curr_emp.job_role)
            with ucol3:
                new_income = st.number_input(
                    "New Monthly Income ($USD)",
                    min_value=1000.0, max_value=60000.0,
                    value=float(curr_emp.monthly_income * 1.15),
                    step=250.0
                )

            effective_date = st.date_input("Effective Transition Date", value=datetime.date.today())
            trigger_scd2 = st.form_submit_button("Execute SCD Type 2 Reassignment", type="primary")

            if trigger_scd2:
                try:
                    result = emp_mgr.reassign_employee_role_or_dept(
                        employee_id=curr_emp.employee_id,
                        new_department_id=dept_dict[new_dept_name],
                        new_job_role=new_role.strip(),
                        new_monthly_income=float(new_income),
                        effective_date=effective_date.isoformat()
                    )
                    st.success(f"🎉 **SCD Type 2 Update Executed Successfully!** Version {result['expired_version']} expired; Version {result['new_active_version']} created as active.")
                except Exception as e:
                    st.error(f"❌ Error triggering SCD2 update: {e}")

        # Display Live SCD Type 2 History for this Employee
        st.markdown(f"#### 📜 Live Data Warehouse Versions for `{curr_emp.employee_id}`")
        history = emp_mgr.get_employee_scd2_history(curr_emp.employee_id)
        if history:
            df_hist = pd.DataFrame(history)
            df_hist["status_badge"] = df_hist["is_current"].apply(
                lambda x: "🟢 Active (Version Successor)" if x == 1 else "🔴 Expired (Historical Snapshot)"
            )
            st.dataframe(
                df_hist[[
                    "version", "status_badge", "department_name", "job_role",
                    "monthly_income", "start_date", "end_date", "employee_dim_id"
                ]],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("No warehouse version records found for this employee.")
    else:
        st.warning(f"Employee `{target_emp_id}` not found. Please verify the Employee ID.")

# =============================================================================
# TAB 3: PROJECT INITIATIVES & STAFFING ALLOCATION
# =============================================================================
with tabs[2]:
    st.subheader("🚀 Project Initiatives & Team Allocations")

    p_col1, p_col2 = st.columns([1, 1])

    with p_col1:
        st.markdown("#### 1. Create New Project Initiative")
        with st.form("create_proj_form"):
            p_code = st.text_input("Project Code *", value=f"PRJ-{datetime.datetime.now().strftime('%m%d')}")
            p_name = st.text_input("Project Name *", placeholder="e.g. NextGen Microservices Overhaul")
            p_dept = st.selectbox("Sponsoring Department *", list(dept_dict.keys()), key="pdept")
            p_budget = st.number_input("Budget ($USD) *", min_value=10000.0, max_value=25000000.0, value=750000.0, step=50000.0)
            p_start = st.date_input("Start Date *", value=datetime.date.today(), key="pstart")
            p_end = st.date_input("Target Completion Date *", value=datetime.date.today() + datetime.timedelta(days=180), key="pend")
            p_status = st.selectbox("Status", ["Planning", "In Progress", "Completed", "On Hold"])

            p_submit = st.form_submit_button("Create Project", type="primary")
            if p_submit:
                try:
                    new_proj = Project(
                        project_id=None,
                        project_code=p_code.strip(),
                        project_name=p_name.strip(),
                        department_id=dept_dict[p_dept],
                        start_date=p_start.isoformat(),
                        end_date=p_end.isoformat(),
                        budget=float(p_budget),
                        status=p_status
                    )
                    new_pid = proj_mgr.create_project(new_proj)
                    st.success(f"✅ Project **{new_proj.project_name}** ({new_proj.project_code}) created with ID {new_pid}!")
                except Exception as e:
                    st.error(f"❌ Failed to create project: {e}")

    with p_col2:
        st.markdown("#### 2. Staff Allocation Console")
        with st.form("assign_staff_form"):
            all_projs = proj_mgr.list_projects()
            proj_options = {f"{p.project_code} - {p.project_name}": p.project_id for p in all_projs} if all_projs else {}

            selected_proj_label = st.selectbox("Select Project *", list(proj_options.keys()) if proj_options else ["No Projects Available"])
            assign_emp_id = st.text_input("Employee ID to Assign *", value="EMP-000042")
            assign_role = st.selectbox("Assignment Role *", [
                "Project Lead", "Senior Developer", "Core Contributor",
                "Quality Assurance", "Business Analyst", "Data Architect"
            ])
            allocation_pct = st.select_slider("Time Allocation (%)", options=[25, 50, 75, 100], value=50)

            assign_submit = st.form_submit_button("Assign Staff Member", type="primary")
            if assign_submit:
                if not proj_options:
                    st.error("No active projects to assign to.")
                else:
                    try:
                        proj_id = proj_options[selected_proj_label]
                        proj_mgr.assign_employee(assign_emp_id.strip(), proj_id, assign_role, allocation_pct)
                        st.success(f"✅ Assigned **{assign_emp_id}** to **{selected_proj_label}** at {allocation_pct}% commitment!")
                    except Exception as e:
                        st.error(f"❌ Allocation failed: {e}")

# =============================================================================
# TAB 4: SUBMIT PERFORMANCE REVIEW
# =============================================================================
with tabs[3]:
    st.subheader("⭐ Submit Performance Appraisal")
    st.caption("Submits appraisal rating to OLTP and maps point-in-time surrogate key to Fact_PerformanceReviews.")

    with st.form("review_form"):
        r_col1, r_col2, r_col3 = st.columns(3)
        with r_col1:
            rev_emp_id = st.text_input("Reviewee Employee ID *", value="EMP-000001")
            rev_dept = st.selectbox("Department at Review *", list(dept_dict.keys()), key="revdept")
            rev_date = st.date_input("Appraisal Date *", value=datetime.date.today(), key="revdate")
            rev_salary = st.number_input("Monthly Salary at Appraisal ($USD) *", min_value=1000.0, max_value=60000.0, value=6500.0, step=100.0)

        with r_col2:
            perf_rating = st.slider("Performance Rating (1 = Low, 5 = Exceptional) *", 1, 5, 4)
            salary_hike = st.slider("Merit Salary Hike (%)", 0.0, 25.0, 8.0, step=0.5)
            promoted_flag = st.checkbox("Promotion Granted as Part of Review", value=True if perf_rating >= 4 else False)

        with r_col3:
            wlb = st.slider("Work-Life Balance (1 = Poor, 4 = Excellent)", 1, 4, 3)
            job_sat = st.slider("Job Satisfaction (1 = Poor, 4 = High)", 1, 4, 3)
            env_sat = st.slider("Environment Satisfaction (1 = Poor, 4 = High)", 1, 4, 3)

        rev_submitted = st.form_submit_button("Submit Performance Review", type="primary")

        if rev_submitted:
            try:
                review_obj = PerformanceReview(
                    employee_id=rev_emp_id.strip(),
                    department_id=dept_dict[rev_dept],
                    review_date=rev_date.isoformat(),
                    performance_rating=perf_rating,
                    monthly_income_at_review=float(rev_salary),
                    percent_salary_hike=float(salary_hike),
                    work_life_balance=wlb,
                    job_satisfaction=job_sat,
                    environment_satisfaction=env_sat,
                    promotion_given=1 if promoted_flag else 0,
                    tenure_at_review=2
                )
                proj_mgr.submit_performance_review(review_obj)
                st.success(f"✅ Performance appraisal recorded for **{rev_emp_id}**! Integrated into Fact_PerformanceReviews.")
            except Exception as e:
                st.error(f"❌ Review submission failed: {e}")

# =============================================================================
# TAB 5: DIRECTORY & SCD2 INSPECTOR
# =============================================================================
with tabs[4]:
    st.subheader("📑 Employee Directory & SCD Type 2 Lifecycle Audit")

    d_col1, d_col2 = st.columns([3, 1])
    with d_col1:
        dir_search = st.text_input("Search Directory (by ID or Name):", placeholder="e.g. EMP-000010 or John")
    with d_col2:
        dir_dept = st.selectbox("Filter Department", ["All Departments"] + list(dept_dict.keys()))

    dept_filter_id = dept_dict.get(dir_dept) if dir_dept != "All Departments" else None
    matched_emps = emp_mgr.list_employees(limit=50, search=dir_search if dir_search else None, department_id=dept_filter_id)

    if matched_emps:
        df_dir = pd.DataFrame([e.to_dict() for e in matched_emps])
        st.dataframe(
            df_dir[[
                "employee_id", "first_name", "last_name", "department_name",
                "job_role", "monthly_income", "hire_date", "overtime", "status"
            ]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No matching employees found.")
