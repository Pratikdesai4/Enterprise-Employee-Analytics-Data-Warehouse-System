"""
Enterprise Employee Analytics - HR Operations Portal (OLTP)
===========================================================
Operational interface for employee onboarding, project allocations,
performance appraisals, and real-time SCD Type 2 career updates.

Author: Enterprise Data Architecture Team
Design: Professional Enterprise UI
"""

import streamlit as st
import datetime
import re
import pandas as pd
from src.database.db_manager import get_db
from src.entities.employee import Employee
from src.entities.project import Project
from src.entities.review import PerformanceReview
from src.managers.employee_manager import EmployeeManager
from src.managers.project_manager import ProjectManager
from src.exceptions import ValidationError
from src.ui import apply_ui_theme, render_page_header, render_sidebar
from src.ui import apply_ui_theme
from src.auth import has_permission, require_authentication

st.set_page_config(page_title="HR Operations Console", layout="wide")
apply_ui_theme()


def validate_onboarding_inputs(
    employee_id: str,
    first_name: str,
    last_name: str,
    email: str,
    phone: str,
    age: int,
    hire_date: datetime.date,
    department_id,
    job_role: str,
    monthly_income: float,
) -> tuple[list[str], list[str]]:
    """Return required-field and data-validation messages for onboarding."""
    missing = []
    errors = []

    if not employee_id.strip():
        missing.append("Employee ID is required.")
    if not first_name.strip():
        missing.append("First Name is required.")
    if not last_name.strip():
        missing.append("Last Name is required.")
    if not email.strip():
        missing.append("Corporate Email is required.")
    if not department_id:
        missing.append("Please select a department.")
    if not job_role.strip():
        missing.append("Job Role is required.")
    if not hire_date:
        missing.append("Hire Date is required.")

    if employee_id.strip() and not re.fullmatch(r"EMP-9\d{5,}", employee_id.strip()):
        errors.append("Invalid Employee ID. Use EMP-9 followed by at least five digits.")
    if email.strip() and not re.fullmatch(
        r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}",
        email.strip(),
    ):
        errors.append("Invalid corporate email address. Please enter a valid email.")
    if phone.strip():
        phone_digits = re.sub(r"\D", "", phone.strip())
        if not re.fullmatch(r"[0-9+().\-\s]{7,25}", phone.strip()) or not 7 <= len(phone_digits) <= 15:
            errors.append("Invalid contact number. Use 7-15 digits and valid phone characters.")
    else:
        missing.append("Contact Phone is required.")
    if age < 18 or age > 75:
        errors.append("Age must be between 18 and 75.")
    if monthly_income <= 0:
        errors.append("Monthly Compensation must be greater than zero.")
    if hire_date and hire_date > datetime.date.today():
        errors.append("Hire Date cannot be in the future.")

    return missing, errors


render_sidebar(
    "HR operations",
    "Employee management",
    "Employees, projects, staffing, and reviews.",
)
render_page_header(
    "HR operations",
    "HR Operations Console",
    "Manage employee records, projects, and performance reviews.",
)
current_user = require_authentication()
can_write = has_permission(current_user["role"], "write")

page_title = "HR Operations & Transactional Console" if can_write else "Workforce Directory"
page_subtitle = (
    "Operational record intake, initiative staffing, and automated SCD Type 2 warehouse updates."
    if can_write
    else "Read-only employee directory. Your account does not have permission to change records."
)
st.markdown(f'<div class="op-header">{page_title}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="op-sub">{page_subtitle}</div>', unsafe_allow_html=True)


def render_workforce_directory(emp_mgr, dept_dict):
    st.markdown('<div class="section-title">Workforce Directory & Audit Log</div>', unsafe_allow_html=True)

    d_col1, d_col2 = st.columns([3, 1])
    with d_col1:
        dir_search = st.text_input("Filter Directory (ID or Name):", placeholder="e.g. EMP-000010 or Sophia")
    with d_col2:
        dir_dept = st.selectbox("Department Filter", ["All Departments"] + list(dept_dict.keys()))

    dept_filter_id = dept_dict.get(dir_dept) if dir_dept != "All Departments" else None
    matched_emps = emp_mgr.list_employees(
        limit=50,
        search=dir_search if dir_search else None,
        department_id=dept_filter_id
    )

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
        st.info("No matching records returned.")

# Initialize Managers
db = get_db()
emp_mgr = EmployeeManager(db)

# Fetch Departments List for Dropdowns
try:
    dept_list = emp_mgr.get_departments()
    dept_dict = {d["department_name"]: d["department_id"] for d in dept_list}
    dept_id_to_name = {d["department_id"]: d["department_name"] for d in dept_list}
except Exception:
    dept_list = []
    dept_dict = {"Research & Development": 1, "Sales": 2, "Human Resources": 3, "Software Engineering": 4, "Finance & Operations": 5}
    dept_id_to_name = {v: k for k, v in dept_dict.items()}

if not can_write:
    render_workforce_directory(emp_mgr, dept_dict)
    st.stop()

proj_mgr = ProjectManager(db)

# Tab Navigation (Clean corporate tab titles without emojis)
tabs = st.tabs([
    "Onboarding",
    "Role & Department Changes",
    "Projects & Staffing",
    "Performance Reviews",
    "Employee Directory"
])

# =============================================================================
# TAB 1: ONBOARD EMPLOYEE
# =============================================================================
with tabs[0]:
    st.markdown('<div class="section-title">Add employee</div>', unsafe_allow_html=True)

    with st.form("onboard_form", clear_on_submit=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            emp_id_input = st.text_input(
                "Employee ID", 
                value="EMP-900004", 
                help="Format must strictly be 'EMP-9XXXXX' (e.g. EMP-900004, EMP-900023, EMP-9001000)"
            )
            first_name = st.text_input("First Name", value="Sophia")
            last_name = st.text_input("Last Name", value="Miller")
            email = st.text_input(
                "Corporate Email", 
                value="sophia.miller@enterprise.corp",
                help="Standard email format: name@domain.com"
            )
            phone = st.text_input("Contact Phone", value="+1-555-829-4100")

        with col2:
            gender = st.selectbox("Gender", ["Female", "Male", "Non-Binary", "Other"])
            age = st.number_input("Age", min_value=18, max_value=75, value=29)
            marital_status = st.selectbox("Marital Status", ["Single", "Married", "Divorced"])
            hire_date = st.date_input("Hire Date", value=datetime.date.today())
            overtime = st.selectbox("Overtime Status", ["No", "Yes"])

        with col3:
            department_options = ["-- Select Department --"] + list(dept_dict.keys())
            dept_selected = st.selectbox("Assigned Department", department_options)
            job_role = st.text_input("Job Role / Functional Title", value="Software Engineer")
            education = st.selectbox("Education Background", [
                "Computer Science", "Life Sciences", "Medical", "Marketing",
                "Technical Degree", "Finance", "Human Resources", "Other"
            ])
            monthly_income = st.number_input("Monthly Compensation ($USD)", min_value=1000.0, max_value=50000.0, value=8500.0, step=250.0)

        submitted = st.form_submit_button("Add employee", type="primary")

        if submitted:
            emp_id_val = emp_id_input.strip()
            first_name_val = first_name.strip()
            last_name_val = last_name.strip()
            email_val = email.strip().lower()
            department_id = dept_dict.get(dept_selected)
            missing, errors = validate_onboarding_inputs(
                employee_id=emp_id_val,
                first_name=first_name_val,
                last_name=last_name_val,
                email=email_val,
                phone=phone.strip(),
                age=int(age),
                hire_date=hire_date,
                department_id=department_id,
                job_role=job_role,
                monthly_income=float(monthly_income),
            )

            if missing:
                st.warning("Employee record could not be added because required information is missing.")
                for message in missing:
                    st.warning(message)
            if errors:
                st.error("Invalid employee record. Please correct the fields before submitting.")
                for message in errors:
                    st.error(message)

            if not missing and not errors:
                try:
                    if emp_mgr.get_employee(emp_id_val):
                        st.error("Employee ID already exists. Please use a unique Employee ID.")
                    else:
                        new_emp = Employee(
                            employee_id=emp_id_val,
                            first_name=first_name_val,
                            last_name=last_name_val,
                            email=email_val,
                            phone=phone.strip(),
                            gender=gender,
                            age=int(age),
                            marital_status=marital_status,
                            hire_date=hire_date.isoformat(),
                            department_id=department_id,
                            job_role=job_role.strip(),
                            education_field=education,
                            monthly_income=float(monthly_income),
                            overtime=overtime,
                            years_at_company=0,
                            status="Active"
                        )
                        emp_mgr.onboard_employee(new_emp)
                        st.session_state["target_emp_id"] = new_emp.employee_id
                        st.success(f"Employee added: {new_emp.full_name} ({new_emp.employee_id}).")
                        st.info(f"Employee {new_emp.employee_id} is ready for role or compensation changes.")
                except ValidationError as e:
                    st.error(f"Employee record could not be added: {e}")
                except Exception as e:
                    error_text = str(e).lower()
                    if "unique" in error_text or "duplicate" in error_text:
                        st.error("Employee ID already exists. Please use a unique Employee ID.")
                    else:
                        st.error("Employee record could not be added because of a database error. No changes were saved.")

# =============================================================================
# TAB 2: CAREER & ROLE REASSIGNMENT (SCD TYPE 2 LIVE TRIGGER)
# =============================================================================
with tabs[1]:
    st.markdown('<div class="section-title">Change employee role or department</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="callout-box">
        Update the employee's department, title, or monthly compensation.
    </div>
    """, unsafe_allow_html=True)

    # Active Employee Selector
    try:
        sample_emps = emp_mgr.list_employees(limit=25)
        sample_options = {f"{e.employee_id} - {e.full_name} ({e.job_role})": e.employee_id for e in sample_emps}
    except Exception:
        sample_options = {}

    lookup_col1, lookup_col2 = st.columns([2, 1])
    with lookup_col1:
        default_val = st.session_state.get("target_emp_id", "EMP-000001")
        target_emp_id = st.text_input("Search by Employee ID or Name:", value=default_val)
    with lookup_col2:
        quick_select = st.selectbox("Or Select from Active Roster:", ["-- Select Employee --"] + list(sample_options.keys()))
        if quick_select != "-- Select Employee --":
            target_emp_id = sample_options[quick_select]

    curr_emp = emp_mgr.get_employee(target_emp_id.strip())

    if curr_emp:
        st.markdown(f"**Selected Record:** {curr_emp.full_name} (`{curr_emp.employee_id}`) | Current Role: **{curr_emp.job_role}** | Department: **{curr_emp.department_name}** | Base Monthly Compensation: **${curr_emp.monthly_income:,.2f}**")

        st.markdown('<span class="audit-badge">Current record</span>', unsafe_allow_html=True)
        st.markdown("##### New details")
        with st.form("scd2_update_form"):
            ucol1, ucol2, ucol3 = st.columns(3)
            with ucol1:
                new_dept_name = st.selectbox(
                    "Target Department",
                    list(dept_dict.keys()),
                    index=list(dept_dict.keys()).index(curr_emp.department_name) if curr_emp.department_name in dept_dict else 0
                )
            with ucol2:
                new_role = st.text_input("Target Job Role", value=curr_emp.job_role)
            with ucol3:
                new_income = st.number_input(
                    "Target Monthly Income ($USD)",
                    min_value=1000.0, max_value=60000.0,
                    value=float(curr_emp.monthly_income * 1.15),
                    step=250.0
                )

            effective_date = st.date_input("Effective Transition Date", value=datetime.date.today())
            trigger_scd2 = st.form_submit_button("Save changes", type="primary")

            if trigger_scd2:
                try:
                    result = emp_mgr.reassign_employee_role_or_dept(
                        employee_id=curr_emp.employee_id,
                        new_department_id=dept_dict[new_dept_name],
                        new_job_role=new_role.strip(),
                        new_monthly_income=float(new_income),
                        effective_date=effective_date.isoformat()
                    )
                    st.success(f"Changes saved. New version active from {result['effective_date']}.")
                except Exception as e:
                    st.error(f"SCD Type 2 Update Failed: {e}")

        st.markdown(f"##### Employee history: `{curr_emp.employee_id}`")
        history = emp_mgr.get_employee_scd2_history(curr_emp.employee_id)
        if history:
            df_hist = pd.DataFrame(history)
            df_hist["Status"] = df_hist["is_current"].apply(
                lambda x: "Active (Current)" if x == 1 else "Historical (Expired)"
            )
            st.dataframe(
                df_hist[[
                    "version", "Status", "department_name", "job_role",
                    "monthly_income", "start_date", "end_date", "employee_dim_id"
                ]],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("No historical versions found for this record.")
    else:
        st.warning(f"Employee identifier '{target_emp_id}' not found in the repository.")

# =============================================================================
# TAB 3: PROJECT INITIATIVES & STAFFING ALLOCATION
# =============================================================================
with tabs[2]:
    st.markdown('<div class="section-title">Projects and staffing</div>', unsafe_allow_html=True)

    p_col1, p_col2 = st.columns([1, 1])

    with p_col1:
        st.markdown("##### Create project")
        with st.form("create_proj_form"):
            p_code = st.text_input("Project Code", value=f"PRJ-{datetime.datetime.now().strftime('%m%d')}")
            p_name = st.text_input("Project Name", placeholder="e.g. NextGen Microservices Overhaul")
            p_dept = st.selectbox("Sponsoring Department", list(dept_dict.keys()), key="pdept")
            p_budget = st.number_input("Approved Budget ($USD)", min_value=10000.0, max_value=25000000.0, value=750000.0, step=50000.0)
            p_start = st.date_input("Start Date", value=datetime.date.today(), key="pstart")
            p_end = st.date_input("Target Completion Date", value=datetime.date.today() + datetime.timedelta(days=180), key="pend")
            p_status = st.selectbox("Operational Status", ["Planning", "In Progress", "Completed", "On Hold"])

            p_submit = st.form_submit_button("Create project", type="primary")
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
                    st.success(f"Initiative registered: {new_proj.project_name} ({new_proj.project_code}) with ID {new_pid}.")
                except Exception as e:
                    st.error(f"Project Creation Error: {e}")

    with p_col2:
        st.markdown("##### Assign employee")
        with st.form("assign_staff_form"):
            all_projs = proj_mgr.list_projects()
            proj_options = {f"{p.project_code} - {p.project_name}": p.project_id for p in all_projs} if all_projs else {}

            selected_proj_label = st.selectbox("Project", list(proj_options.keys()) if proj_options else ["No Projects Available"])
            assign_emp_id = st.text_input("Assigned Employee ID", value="EMP-000042")
            assign_role = st.selectbox("Functional Role", [
                "Project Lead", "Senior Developer", "Core Contributor",
                "Quality Assurance", "Business Analyst", "Data Architect"
            ])
            allocation_pct = st.select_slider("Allocation Commitment (%)", options=[25, 50, 75, 100], value=50)

            assign_submit = st.form_submit_button("Assign employee", type="primary")
            if assign_submit:
                if not proj_options:
                    st.error("No valid initiatives available for allocation.")
                else:
                    try:
                        proj_id = proj_options[selected_proj_label]
                        proj_mgr.assign_employee(assign_emp_id.strip(), proj_id, assign_role, allocation_pct)
                        st.success(f"Allocation committed: {assign_emp_id} allocated to {selected_proj_label} at {allocation_pct}% commitment.")
                    except Exception as e:
                        st.error(f"Allocation Error: {e}")

# =============================================================================
# TAB 4: SUBMIT PERFORMANCE REVIEW
# =============================================================================
with tabs[3]:
    st.markdown('<div class="section-title">Record performance review</div>', unsafe_allow_html=True)

    with st.form("review_form"):
        r_col1, r_col2, r_col3 = st.columns(3)
        with r_col1:
            rev_emp_id = st.text_input("Reviewee Employee ID", value="EMP-000001")
            rev_dept = st.selectbox("Evaluating Department", list(dept_dict.keys()), key="revdept")
            rev_date = st.date_input("Evaluation Date", value=datetime.date.today(), key="revdate")
            rev_salary = st.number_input("Base Compensation at Review ($USD)", min_value=1000.0, max_value=60000.0, value=6500.0, step=100.0)

        with r_col2:
            perf_rating = st.slider("Performance Score (Scale: 1 to 5)", 1, 5, 4)
            salary_hike = st.slider("Merit Salary Increase (%)", 0.0, 25.0, 8.0, step=0.5)
            promoted_flag = st.checkbox("Promotion Conferred", value=True if perf_rating >= 4 else False)

        with r_col3:
            wlb = st.slider("Work-Life Balance (Scale: 1 to 4)", 1, 4, 3)
            job_sat = st.slider("Job Satisfaction (Scale: 1 to 4)", 1, 4, 3)
            env_sat = st.slider("Environment Satisfaction (Scale: 1 to 4)", 1, 4, 3)

        rev_submitted = st.form_submit_button("Save review", type="primary")

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
                st.success(f"Performance appraisal recorded for {rev_emp_id}. Loaded into Fact_PerformanceReviews.")
            except Exception as e:
                st.error(f"Appraisal Transaction Error: {e}")

# =============================================================================
# TAB 5: DIRECTORY & SCD2 INSPECTOR
# =============================================================================
with tabs[4]:
    st.markdown('<div class="section-title">Employee directory</div>', unsafe_allow_html=True)

    d_col1, d_col2 = st.columns([3, 1])
    with d_col1:
        dir_search = st.text_input("Filter Directory (ID or Name):", placeholder="e.g. EMP-000010 or Sophia")
    with d_col2:
        dir_dept = st.selectbox("Department Filter", ["All Departments"] + list(dept_dict.keys()))

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
        st.info("No matching records returned.")
    render_workforce_directory(emp_mgr, dept_dict)
