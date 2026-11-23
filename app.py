"""
Enterprise Employee Analytics & Data Warehouse System
======================================================
Executive Landing Portal & Enterprise System Overview

Author: Enterprise Data Architecture Team
Design: Professional Enterprise UI
"""

import streamlit as st
import pandas as pd
from src.database.db_manager import get_db
from src.managers.analytics_manager import AnalyticsManager
from src.ui import apply_ui_theme, render_page_header, render_sidebar
from src.auth import has_permission, require_authentication

# Streamlit Page Configuration
st.set_page_config(
    page_title="Enterprise Data Warehouse Portal",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_ui_theme()


def main():
    db = get_db()
    current_user = require_authentication()

    # Sidebar
    render_sidebar(
        "Overview",
        "Enterprise HR analytics",
        "Workforce metrics, operations, and reporting.",
    )
    st.sidebar.divider()

    backend_name = db.get_backend_name().upper()
    st.sidebar.markdown(f"""
    <div class="status-badge">
        <span class="status-dot"></span>Backend: {backend_name}
    </div>
    """, unsafe_allow_html=True)

    render_page_header(
        "Enterprise HR analytics",
        "Employee Analytics & Data Warehouse",
        "Workforce metrics and reporting in one place.",
    )

    st.caption(f"Signed in as {current_user['username']} ({current_user['role'].title()})")

    # Initialize Analytics Manager
    analytics_mgr = AnalyticsManager(db)

    try:
        kpis = analytics_mgr.get_executive_kpis()
    except Exception as e:
        st.error(f"Error querying data warehouse: {e}")
        kpis = {
            "total_active_employees": 0,
            "avg_monthly_salary": 0.0,
            "avg_performance_rating": 0.0,
            "avg_attrition_risk": 0.0,
            "total_promotions": 0,
            "career_transitioned_employees": 0,
            "total_projects": 0
        }

    # Top KPI Metrics Row
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-num">{kpis['total_active_employees']:,}</div>
            <div class="kpi-title">Active Workforce</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-num">${kpis['avg_monthly_salary']:,.0f}</div>
            <div class="kpi-title">Avg Monthly Compensation</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-num">{kpis['avg_performance_rating']:.2f} <span style="font-size:0.9rem; color:#64748B;">/ 5.0</span></div>
            <div class="kpi-title">Avg Performance Score</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-num">{kpis['avg_attrition_risk']:.1f}%</div>
            <div class="kpi-title">Attrition Risk</div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-num">{kpis['career_transitioned_employees']:,}</div>
            <div class="kpi-title">Career History Records</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    st.write("")

    # Portal Module Navigation Cards
    st.markdown('<div class="section-title">Platform areas</div>', unsafe_allow_html=True)
    card_col1, card_col2 = st.columns(2)

    with card_col1:
        st.markdown("""
        <div class="portal-card">
            <h4>HR Operations</h4>
            <p>Manage employee records, projects, staffing, and reviews.</p>
            <ul>
                <li>Onboard employees</li>
                <li>Update roles and compensation</li>
                <li>Manage projects and staffing</li>
                <li>Record performance reviews</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        hr_portal_label = (
            "Access HR Operations Portal →"
            if has_permission(current_user["role"], "write")
            else "Access Workforce Directory (Read Only) →"
        )
        st.page_link("pages/1_HR_Operations.py", label=hr_portal_label)

    with card_col2:
        st.markdown("""
        <div class="portal-card">
            <h4>Executive Analytics</h4>
            <p>Review workforce performance, risk, pay, and career movement.</p>
            <ul>
                <li>Compare department performance</li>
                <li>Track pay and performance trends</li>
                <li>Review attrition risk</li>
                <li>Audit employee career history</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        st.page_link("pages/2_Executive_Analytics.py", label="Access Executive Analytics Dashboard →")

    st.divider()

    # System Architecture Information
    st.markdown('<div class="section-title">Data architecture</div>', unsafe_allow_html=True)
    arch1, arch2, arch3 = st.columns(3)
    with arch1:
        st.markdown(
            '<div class="portal-card"><div class="mini-label">01</div><h4>Operational store</h4><p>OLTP records for employees, projects, and reviews.</p></div>',
            unsafe_allow_html=True,
        )
    with arch2:
        st.markdown(
            '<div class="portal-card"><div class="mini-label">02</div><h4>Historical warehouse</h4><p>OLAP history for roles, departments, and compensation.</p></div>',
            unsafe_allow_html=True,
        )
    with arch3:
        st.markdown(
            '<div class="portal-card"><div class="mini-label">03</div><h4>Executive reporting</h4><p>Workforce and capacity insights for management.</p></div>',
            unsafe_allow_html=True,
        )

    with st.expander("System Architecture & Data Warehousing Specifications", expanded=False):
        st.markdown("""
        #### Architecture overview
        - **OLTP:** Relational records for daily HR operations.
        - **OLAP:** Star-schema warehouse for reporting and analysis.
        - **SCD Type 2:** Preserves historical employee roles, departments, and compensation.
        """)


if __name__ == "__main__":
    main()
