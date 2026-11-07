"""
Enterprise Employee Analytics & Data Warehouse System
======================================================
Main Streamlit Application Entrypoint & Executive Overview

Author: Enterprise Data Architecture Team
"""

import streamlit as st
import pandas as pd
from src.database.db_manager import get_db
from src.managers.analytics_manager import AnalyticsManager

# Streamlit Page Configuration
st.set_page_config(
    page_title="Enterprise Employee Analytics",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }
    .kpi-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        text-align: center;
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: 700;
        color: #2563EB;
    }
    .kpi-label {
        font-size: 0.85rem;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .module-card {
        background: linear-gradient(135deg, #FFFFFF 0%, #F1F5F9 100%);
        border: 1px solid #CBD5E1;
        border-radius: 12px;
        padding: 24px;
        height: 100%;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .module-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
</style>
""", unsafe_allow_html=True)


def main():
    # Sidebar
    st.sidebar.image("https://img.icons8.com/fluency/96/organization.png", width=64)
    st.sidebar.title("Enterprise DW Portal")
    st.sidebar.markdown("**System Architecture: 2-Tier**")
    st.sidebar.markdown("- **OLTP:** 3NF Operational Backend")
    st.sidebar.markdown("- **OLAP:** Star Schema Data Warehouse")
    st.sidebar.markdown("- **Tracking:** SCD Type 2 Active")
    st.sidebar.divider()

    db = get_db()
    backend_name = db.get_backend_name().upper()
    st.sidebar.success(f"🟢 Connected to: **{backend_name}**")

    # Header
    st.markdown('<div class="main-header">🏢 Enterprise Employee Analytics & Data Warehouse System</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Centralized Data Platform with Real-Time SCD Type 2 Career Tracking & Star Schema Analytics</div>',
        unsafe_allow_html=True
    )

    # Initialize Analytics Manager
    analytics_mgr = AnalyticsManager(db)

    try:
        kpis = analytics_mgr.get_executive_kpis()
    except Exception as e:
        st.error(f"Error connecting to warehouse: {e}")
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
        <div class="kpi-card">
            <div class="kpi-value">{kpis['total_active_employees']:,}</div>
            <div class="kpi-label">Active Employees</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">${kpis['avg_monthly_salary']:,.0f}</div>
            <div class="kpi-label">Avg Monthly Salary</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{kpis['avg_performance_rating']:.2f} / 5.0</div>
            <div class="kpi-label">Avg Performance Rating</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{kpis['avg_attrition_risk']:.1f}%</div>
            <div class="kpi-label">Avg Attrition Risk</div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{kpis['career_transitioned_employees']:,}</div>
            <div class="kpi-label">SCD2 Historical Transitions</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    st.write("")

    # Portal Module Navigation Cards
    st.subheader("🚀 Navigate to Application Portals")
    card_col1, card_col2 = st.columns(2)

    with card_col1:
        st.markdown("""
        <div class="module-card">
            <h3>📝 HR Operations Portal (OLTP)</h3>
            <p style="color: #475569;">
                Manage operational day-to-day HR records, onboarding, and project staff allocations:
            </p>
            <ul>
                <li><strong>Onboard Employees:</strong> Form with strict domain validation & unique corporate email.</li>
                <li><strong>Career & Role Updates:</strong> Change an employee's department or salary and immediately trigger an <strong>SCD Type 2 version update</strong> in the Data Warehouse.</li>
                <li><strong>Project Management:</strong> Launch initiatives and allocate staff workloads.</li>
                <li><strong>Submit Appraisals:</strong> Record performance ratings and satisfaction metrics.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        st.page_link("pages/1_HR_Operations.py", label="Open HR Operations Portal →", icon="📝")

    with card_col2:
        st.markdown("""
        <div class="module-card">
            <h3>📊 Executive Analytics Dashboard (OLAP)</h3>
            <p style="color: #475569;">
                Interactive intelligence dashboards powered directly by the <strong>Dimensional Star Schema</strong>:
            </p>
            <ul>
                <li><strong>Top Performers:</strong> Dynamic leaderboards powered by SQL <code>DENSE_RANK()</code>.</li>
                <li><strong>YoY Performance & Salary Trends:</strong> Longitudinal velocity across 2021–2025.</li>
                <li><strong>Attrition Risk Matrix:</strong> Correlation heatmaps of flight risk vs overtime and compensation.</li>
                <li><strong>SCD Type 2 Audit Trail:</strong> Historical career progression and promotion salary lift.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        st.page_link("pages/2_Executive_Analytics.py", label="Open Executive Analytics Dashboard →", icon="📊")

    st.divider()

    # System Architecture Diagram & Concepts
    with st.expander("ℹ️ Data Warehouse & SCD Type 2 Technical Architecture", expanded=False):
        st.markdown("""
        ### Architecture Highlights
        - **Operational Layer (OLTP - 3NF):** High-concurrency relational model holding active states across `employees`, `departments`, `projects`, and `employee_project_assignments`.
        - **Dimensional Warehouse (OLAP - Star Schema):** Centered on `Fact_PerformanceReviews` linked to conformed dimensions (`Dim_Department`, `Dim_Project`, `Dim_Date`) and the Slowly Changing Dimension `Dim_Employee`.
        - **SCD Type 2 Lifecycle:**
          - Whenever an employee experiences a promotion, department transfer, or salary adjustment, the existing warehouse row is **expired** (`end_date = CURRENT_DATE, is_current = 0`).
          - A new successor record is inserted (`start_date = CURRENT_DATE, is_current = 1, version = old_version + 1`).
          - Historical performance reviews remain linked to the exact version valid at appraisal time!
        """)


if __name__ == "__main__":
    main()
