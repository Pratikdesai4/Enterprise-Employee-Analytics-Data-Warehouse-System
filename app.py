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

# Streamlit Page Configuration
st.set_page_config(
    page_title="Enterprise Data Warehouse Portal",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional Enterprise Theme Styling
st.markdown("""
<style>
    /* Main Layout & Headers */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .enterprise-header {
        font-size: 1.85rem;
        font-weight: 700;
        color: #0F172A;
        letter-spacing: -0.02em;
        margin-bottom: 0.25rem;
    }
    .enterprise-sub {
        font-size: 0.95rem;
        color: #475569;
        margin-bottom: 1.75rem;
        line-height: 1.5;
    }
    
    /* Metrics & KPI Cards */
    .kpi-container {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 1.25rem 1rem;
        text-align: left;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
        border-top: 3px solid #1E40AF;
    }
    .kpi-num {
        font-size: 1.75rem;
        font-weight: 700;
        color: #0F172A;
        font-feature-settings: "tnum";
    }
    .kpi-title {
        font-size: 0.75rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.25rem;
    }

    /* Portal Navigation Cards */
    .portal-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1.5rem;
        height: 100%;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }
    .portal-card h4 {
        margin-top: 0;
        font-size: 1.15rem;
        font-weight: 600;
        color: #0F172A;
    }
    .portal-card p {
        font-size: 0.88rem;
        color: #475569;
        line-height: 1.5;
    }
    .portal-card ul {
        margin-bottom: 1rem;
        padding-left: 1.25rem;
        font-size: 0.85rem;
        color: #334155;
    }
    .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.65rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        background-color: #DCFCE7;
        color: #166534;
        border: 1px solid #BBF7D0;
    }
    .status-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background-color: #16A34A;
        margin-right: 6px;
    }
</style>
""", unsafe_allow_html=True)


def main():
    # Sidebar
    st.sidebar.markdown("### System Architecture")
    st.sidebar.markdown("**Operational Store (OLTP):** 3NF Relational")
    st.sidebar.markdown("**Data Warehouse (OLAP):** Star Schema")
    st.sidebar.markdown("**Temporal Model:** SCD Type 2 Active")
    st.sidebar.divider()

    db = get_db()
    backend_name = db.get_backend_name().upper()
    st.sidebar.markdown(f"""
    <div class="status-badge">
        <span class="status-dot"></span>Backend: {backend_name}
    </div>
    """, unsafe_allow_html=True)

    # Main Header
    st.markdown('<div class="enterprise-header">Enterprise Employee Analytics & Data Warehouse System</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="enterprise-sub">Unified Operational Data Store (OLTP) and Dimensional Warehouse (OLAP) with Automated Slowly Changing Dimension (SCD Type 2) Lifecycle Tracking.</div>',
        unsafe_allow_html=True
    )

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
            <div class="kpi-title">Attrition Flight Risk</div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-num">{kpis['career_transitioned_employees']:,}</div>
            <div class="kpi-title">SCD2 Historical Transitions</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    st.write("")

    # Portal Module Navigation Cards
    st.markdown("### Functional Modules")
    card_col1, card_col2 = st.columns(2)

    with card_col1:
        st.markdown("""
        <div class="portal-card">
            <h4>HR Operations Management (OLTP)</h4>
            <p>Transactional console for personnel records, project staffing, and career progression management:</p>
            <ul>
                <li><strong>Personnel Onboarding:</strong> Standardized data intake with corporate email and credential validation.</li>
                <li><strong>Role & Compensation Transitions:</strong> Adjust department, title, or compensation with real-time <strong>SCD Type 2</strong> versioning in the data warehouse.</li>
                <li><strong>Initiative Resource Allocation:</strong> Provision client and internal projects and allocate staffing capacity.</li>
                <li><strong>Performance Appraisals:</strong> Log annual appraisals and synchronize with fact tables.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        st.page_link("pages/1_HR_Operations.py", label="Access HR Operations Portal →")

    with card_col2:
        st.markdown("""
        <div class="portal-card">
            <h4>Executive Analytics & Business Intelligence (OLAP)</h4>
            <p>Dimensional analytics powered directly by the Star Schema and advanced SQL window functions:</p>
            <ul>
                <li><strong>Department Talent Rankings:</strong> Departmental performance tiers determined via SQL <code>DENSE_RANK()</code>.</li>
                <li><strong>Longitudinal YoY Trajectories:</strong> Multi-year evaluation of merit salary adjustments and ratings.</li>
                <li><strong>Flight Risk Diagnostics:</strong> Correlation models identifying compensation anomalies and turnover risk.</li>
                <li><strong>Career Mobility Audits:</strong> Full historical SCD Type 2 career transitions and salary progression.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        st.page_link("pages/2_Executive_Analytics.py", label="Access Executive Analytics Dashboard →")

    st.divider()

    # System Architecture Information
    with st.expander("System Architecture & Data Warehousing Specifications", expanded=False):
        st.markdown("""
        #### Architecture Overview
        - **OLTP Operational Store (3NF):** High-integrity relational schema handling transaction processing across `employees`, `departments`, `projects`, and `employee_project_assignments`.
        - **OLAP Dimensional Warehouse (Star Schema):** Modeled around `Fact_PerformanceReviews` with integer surrogate keys referencing conformed dimensions (`Dim_Department`, `Dim_Project`, `Dim_Date`) and the temporal Slowly Changing Dimension (`Dim_Employee`).
        - **SCD Type 2 Execution:**
          - Department transfers, title changes, or compensation modifications trigger the expiration of the current active dimension record (`end_date = CURRENT_DATE, is_current = 0`).
          - A successor record is appended (`start_date = CURRENT_DATE, end_date = NULL, is_current = 1, version = n + 1`).
          - Past appraisals remain tied to their respective historical versions without retroactive disruption.
        """)


if __name__ == "__main__":
    main()
