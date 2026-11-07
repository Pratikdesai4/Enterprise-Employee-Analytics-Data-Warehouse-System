"""
Enterprise Employee Analytics - Executive Analytics Dashboard (OLAP)
===================================================================
Interactive dashboards connected directly to the Dimensional Star Schema
powered by SQL Window Functions, Plotly visualizations, and SCD2 audits.

Author: Enterprise Data Architecture Team
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.database.db_manager import get_db
from src.managers.analytics_manager import AnalyticsManager

st.set_page_config(page_title="Executive Analytics Dashboard", page_icon="📊", layout="wide")

# Custom Styling
st.markdown("""
<style>
    .page-title { font-size: 2rem; font-weight: 700; color: #0F172A; }
    .sub-title { font-size: 1rem; color: #475569; margin-bottom: 1.5rem; }
    .metric-card {
        background-color: #FFFFFF; border: 1px solid #E2E8F0;
        border-radius: 8px; padding: 16px; text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-val { font-size: 1.8rem; font-weight: 700; color: #1E40AF; }
    .metric-lbl { font-size: 0.8rem; color: #64748B; text-transform: uppercase; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="page-title">📊 Executive Analytics Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Multi-dimensional enterprise intelligence driven directly by the OLAP Star Schema & Window Functions.</div>', unsafe_allow_html=True)

# Initialize Analytics DAL
db = get_db()
analytics_mgr = AnalyticsManager(db)

# Sidebar Filters
st.sidebar.header("🔍 Analytical Filters")
year_filter = st.sidebar.selectbox("Review Evaluation Year", [2025, 2024, 2023, 2022, 2021], index=0)
dept_options = ["All Departments", "Research & Development", "Sales", "Human Resources", "Software Engineering", "Finance & Operations"]
dept_filter = st.sidebar.selectbox("Department Focus", dept_options, index=0)
top_n_filter = st.sidebar.slider("Top Performers Rank Tier (DENSE_RANK)", min_value=1, max_value=5, value=3)

# Load Executive KPIs
kpis = analytics_mgr.get_executive_kpis()

k_col1, k_col2, k_col3, k_col4, k_col5, k_col6 = st.columns(6)
with k_col1:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{kpis["total_active_employees"]:,}</div><div class="metric-lbl">Total Workforce</div></div>', unsafe_allow_html=True)
with k_col2:
    st.markdown(f'<div class="metric-card"><div class="metric-val">${kpis["avg_monthly_salary"]:,.0f}</div><div class="metric-lbl">Avg Monthly Salary</div></div>', unsafe_allow_html=True)
with k_col3:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{kpis["avg_performance_rating"]:.2f}</div><div class="metric-lbl">Avg Performance</div></div>', unsafe_allow_html=True)
with k_col4:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{kpis["avg_attrition_risk"]:.1f}%</div><div class="metric-lbl">Avg Flight Risk</div></div>', unsafe_allow_html=True)
with k_col5:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{kpis["total_promotions"]:,}</div><div class="metric-lbl">Total Promotions</div></div>', unsafe_allow_html=True)
with k_col6:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{kpis["career_transitioned_employees"]:,}</div><div class="metric-lbl">SCD2 Historical Transitions</div></div>', unsafe_allow_html=True)

st.write("")
st.divider()

# =============================================================================
# SECTION 1: TOP PERFORMERS VIA SQL WINDOW FUNCTION DENSE_RANK()
# =============================================================================
st.subheader(f"🏆 Top Performing Employees by Department (Year: {year_filter})")
st.caption(f"Powered by SQL Window Function: `DENSE_RANK() OVER (PARTITION BY department_name ORDER BY performance_rating DESC, percent_salary_hike DESC)`")

dept_param = None if dept_filter == "All Departments" else dept_filter
df_top = analytics_mgr.get_top_performers(year=year_filter, top_n=top_n_filter, department_name=dept_param)

if not df_top.empty:
    chart_col, table_col = st.columns([1, 1])

    with chart_col:
        # Plotly chart of top performers
        fig_top = px.bar(
            df_top.head(25),
            x="monthly_income_at_review",
            y="full_name",
            color="percent_salary_hike",
            orientation="h",
            labels={
                "monthly_income_at_review": "Monthly Income ($USD)",
                "full_name": "Employee Name",
                "percent_salary_hike": "Salary Hike (%)"
            },
            title=f"Top Ranked Talent by Compensation & Merit Hike (Top 25)",
            color_continuous_scale="Blues"
        )
        fig_top.update_layout(yaxis={'categoryorder': 'total ascending'}, height=450, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_top, use_container_width=True)

    with table_col:
        st.dataframe(
            df_top[[
                "dept_perf_rank", "department_name", "employee_id", "full_name",
                "job_role", "performance_rating", "percent_salary_hike", "monthly_income_at_review"
            ]],
            use_container_width=True,
            hide_index=True,
            height=450
        )
else:
    st.info("No performance records found for the selected filter.")

st.divider()

# =============================================================================
# SECTION 2: YEAR-OVER-YEAR (YOY) PERFORMANCE & COMPENSATION TRAJECTORIES
# =============================================================================
st.subheader("📈 Longitudinal Year-over-Year (YoY) Performance Trends")
st.caption("Longitudinal tracking of performance scores and merit salary increments across 2021–2025.")

df_yoy = analytics_mgr.get_yoy_performance_trends()

if not df_yoy.empty:
    yoy_col1, yoy_col2 = st.columns([2, 1])

    with yoy_col1:
        # Dual-Axis Plotly Line + Bar chart
        fig_yoy = go.Figure()
        fig_yoy.add_trace(go.Bar(
            x=df_yoy["review_year"],
            y=df_yoy["avg_hike_pct"],
            name="Avg Merit Hike (%)",
            marker_color="#93C5FD",
            opacity=0.7
        ))
        fig_yoy.add_trace(go.Scatter(
            x=df_yoy["review_year"],
            y=df_yoy["avg_rating"],
            name="Avg Performance Rating (1-5)",
            yaxis="y2",
            mode="lines+markers+text",
            line=dict(color="#1D4ED8", width=3),
            text=df_yoy["avg_rating"].apply(lambda v: f"{v:.2f}"),
            textposition="top center"
        ))
        fig_yoy.update_layout(
            title="Longitudinal Trend: Performance Rating vs Salary Hike (%)",
            xaxis=dict(title="Review Year"),
            yaxis=dict(title="Average Merit Hike (%)"),
            yaxis2=dict(title="Average Rating", overlaying="y", side="right", range=[1, 5]),
            legend=dict(x=0.01, y=0.99),
            height=400,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_yoy, use_container_width=True)

    with yoy_col2:
        fig_prom = px.bar(
            df_yoy,
            x="review_year",
            y="total_promotions",
            text="total_promotions",
            labels={"review_year": "Year", "total_promotions": "Promotions Granted"},
            title="Total Annual Promotions Awarded",
            color="total_promotions",
            color_continuous_scale="Greens"
        )
        fig_prom.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_prom, use_container_width=True)

st.divider()

# =============================================================================
# SECTION 3: ATTRITION RISK HEATMAP & BOTTLENECK ANALYSIS
# =============================================================================
st.subheader("⚠️ Attrition Risk Radar & Flight Risk Diagnostics")
st.caption("Identifying high-attrition-risk roles and satisfaction outliers.")

df_attr = analytics_mgr.get_attrition_risk_analysis()

if not df_attr.empty:
    r_col1, r_col2 = st.columns([1, 1])

    with r_col1:
        # Scatter Plot: Attrition Risk vs Work-Life Balance
        fig_scatter = px.scatter(
            df_attr,
            x="avg_work_life_balance",
            y="avg_risk_score",
            size="employee_count",
            color="department_name",
            hover_name="job_role",
            labels={
                "avg_work_life_balance": "Avg Work-Life Balance (1-4)",
                "avg_risk_score": "Avg Attrition Risk Score (0-100)",
                "department_name": "Department"
            },
            title="Work-Life Balance vs Attrition Risk by Role"
        )
        fig_scatter.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_scatter, use_container_width=True)

    with r_col2:
        # Roles with highest flight risk
        st.markdown("#### High Flight Risk Watchlist (Score ≥ 50)")
        df_high_risk = df_attr[df_attr["avg_risk_score"] >= 45].sort_values(by="avg_risk_score", ascending=False)
        st.dataframe(
            df_high_risk[["department_name", "job_role", "avg_risk_score", "avg_work_life_balance", "high_risk_count"]],
            use_container_width=True,
            hide_index=True,
            height=350
        )

st.divider()

# =============================================================================
# SECTION 4: DEPARTMENT HEADCOUNT & ANNUAL PAYROLL SPEND
# =============================================================================
st.subheader("🏛 Department Headcount & Payroll Allocation")

df_dept_dist = analytics_mgr.get_department_distribution()

if not df_dept_dist.empty:
    d_col1, d_col2 = st.columns([1, 1])
    with d_col1:
        fig_donut = px.pie(
            df_dept_dist,
            values="headcount",
            names="department_name",
            title="Workforce Distribution Across Departments",
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        fig_donut.update_layout(height=380, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_donut, use_container_width=True)

    with d_col2:
        fig_pay = px.bar(
            df_dept_dist,
            x="department_name",
            y="total_payroll_annual",
            text="total_payroll_annual",
            labels={"total_payroll_annual": "Annual Payroll ($USD)", "department_name": "Department"},
            title="Total Annualized Payroll Spend by Department",
            color="avg_salary",
            color_continuous_scale="Purples"
        )
        fig_pay.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
        fig_pay.update_layout(height=380, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_pay, use_container_width=True)

st.divider()

# =============================================================================
# SECTION 5: SCD TYPE 2 ENTERPRISE MOBILITY AUDIT TRAIL
# =============================================================================
st.subheader("📜 SCD Type 2 Longitudinal Career Mobility Audit")
st.caption("Inspect multi-version career histories showing career progression, role promotions, and salary bumps preserved in Dim_Employee.")

df_scd2_audit = analytics_mgr.get_scd2_progression_audit(limit=30)
if not df_scd2_audit.empty:
    st.dataframe(
        df_scd2_audit,
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No multi-version SCD Type 2 employee histories found.")
