"""
Enterprise Employee Analytics - Executive Analytics Dashboard (OLAP)
===================================================================
Business intelligence dashboards connected directly to the Dimensional Star Schema
powered by SQL Window Functions, Plotly & Altair visualizations, and SCD2 audits.

Author: Enterprise Data Architecture Team
Design: Professional Enterprise UI
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import altair as alt
from src.database.db_manager import get_db
from src.managers.analytics_manager import AnalyticsManager

st.set_page_config(page_title="Executive Analytics Dashboard", layout="wide")

# Professional Enterprise Styling
st.markdown("""
<style>
    .dash-header {
        font-size: 1.75rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 0.25rem;
    }
    .dash-sub {
        font-size: 0.92rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }
    .exec-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 1rem 0.85rem;
        text-align: left;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
        border-top: 3px solid #1E40AF;
    }
    .exec-val {
        font-size: 1.6rem;
        font-weight: 700;
        color: #0F172A;
        font-feature-settings: "tnum";
    }
    .exec-lbl {
        font-size: 0.72rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-top: 0.2rem;
    }
    .section-title {
        font-size: 1.15rem;
        font-weight: 600;
        color: #0F172A;
        margin-bottom: 0.25rem;
    }
    .section-desc {
        font-size: 0.85rem;
        color: #64748B;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="dash-header">Executive Analytics & Workforce Intelligence</div>', unsafe_allow_html=True)
st.markdown('<div class="dash-sub">Multi-dimensional analytics driven directly by the OLAP Star Schema and SQL Window Functions.</div>', unsafe_allow_html=True)

# Initialize Analytics DAL
db = get_db()
analytics_mgr = AnalyticsManager(db)

# Sidebar Filters (Clean titles without emojis)
st.sidebar.markdown("### Analytical Filters")
year_filter = st.sidebar.selectbox("Evaluation Period (Year)", [2025, 2024, 2023, 2022, 2021], index=0)
dept_options = ["All Departments", "Research & Development", "Sales", "Human Resources", "Software Engineering", "Finance & Operations"]
dept_filter = st.sidebar.selectbox("Department Scope", dept_options, index=0)
top_n_filter = st.sidebar.slider("DENSE_RANK Cutoff Tier", min_value=1, max_value=5, value=3)

# Load Executive KPIs
kpis = analytics_mgr.get_executive_kpis()

k_col1, k_col2, k_col3, k_col4, k_col5, k_col6 = st.columns(6)
with k_col1:
    st.markdown(f'<div class="exec-card"><div class="exec-val">{kpis["total_active_employees"]:,}</div><div class="exec-lbl">Active Headcount</div></div>', unsafe_allow_html=True)
with k_col2:
    st.markdown(f'<div class="exec-card"><div class="exec-val">${kpis["avg_monthly_salary"]:,.0f}</div><div class="exec-lbl">Avg Compensation</div></div>', unsafe_allow_html=True)
with k_col3:
    st.markdown(f'<div class="exec-card"><div class="exec-val">{kpis["avg_performance_rating"]:.2f}</div><div class="exec-lbl">Avg Score (/5)</div></div>', unsafe_allow_html=True)
with k_col4:
    st.markdown(f'<div class="exec-card"><div class="exec-val">{kpis["avg_attrition_risk"]:.1f}%</div><div class="exec-lbl">Flight Risk Index</div></div>', unsafe_allow_html=True)
with k_col5:
    st.markdown(f'<div class="exec-card"><div class="exec-val">{kpis["total_promotions"]:,}</div><div class="exec-lbl">Promotions Awarded</div></div>', unsafe_allow_html=True)
with k_col6:
    st.markdown(f'<div class="exec-card"><div class="exec-val">{kpis["career_transitioned_employees"]:,}</div><div class="exec-lbl">SCD2 Transitions</div></div>', unsafe_allow_html=True)

st.write("")
st.divider()

# =============================================================================
# SECTION 1: TOP PERFORMERS VIA SQL WINDOW FUNCTION DENSE_RANK()
# =============================================================================
st.markdown(f'<div class="section-title">Department Talent Rankings: Period {year_filter}</div>', unsafe_allow_html=True)
st.markdown('<div class="section-desc">Rankings evaluated using SQL Window Function: <code>DENSE_RANK() OVER (PARTITION BY department_name ORDER BY performance_rating DESC, percent_salary_hike DESC)</code></div>', unsafe_allow_html=True)

dept_param = None if dept_filter == "All Departments" else dept_filter
df_top = analytics_mgr.get_top_performers(year=year_filter, top_n=top_n_filter, department_name=dept_param)

if not df_top.empty:
    chart_col, table_col = st.columns([1, 1])

    with chart_col:
        fig_top = px.bar(
            df_top.head(25),
            x="monthly_income_at_review",
            y="full_name",
            color="percent_salary_hike",
            orientation="h",
            labels={
                "monthly_income_at_review": "Monthly Compensation ($USD)",
                "full_name": "Employee Name",
                "percent_salary_hike": "Merit Hike (%)"
            },
            title="Compensation & Merit Increase for Ranked Talent (Top 25)",
            color_continuous_scale="Blues"
        )
        fig_top.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            height=430,
            margin=dict(l=10, r=10, t=35, b=10),
            font=dict(family="sans-serif", size=11)
        )
        st.plotly_chart(fig_top, use_container_width=True)

    with table_col:
        st.dataframe(
            df_top[[
                "dept_perf_rank", "department_name", "employee_id", "full_name",
                "job_role", "performance_rating", "percent_salary_hike", "monthly_income_at_review"
            ]],
            use_container_width=True,
            hide_index=True,
            height=430
        )
else:
    st.info("No appraisal records returned for the specified filter criteria.")

st.divider()

# =============================================================================
# SECTION 2: YEAR-OVER-YEAR (YOY) PERFORMANCE & COMPENSATION TRAJECTORIES
# =============================================================================
st.markdown('<div class="section-title">Longitudinal Performance & Compensation Trajectories</div>', unsafe_allow_html=True)
st.markdown('<div class="section-desc">Longitudinal tracking of appraisal performance scores and merit salary adjustments across multi-year cycles.</div>', unsafe_allow_html=True)

df_yoy = analytics_mgr.get_yoy_performance_trends()

if not df_yoy.empty:
    yoy_col1, yoy_col2 = st.columns([2, 1])

    with yoy_col1:
        fig_yoy = go.Figure()
        fig_yoy.add_trace(go.Bar(
            x=df_yoy["review_year"],
            y=df_yoy["avg_hike_pct"],
            name="Avg Merit Hike (%)",
            marker_color="#93C5FD",
            opacity=0.75
        ))
        fig_yoy.add_trace(go.Scatter(
            x=df_yoy["review_year"],
            y=df_yoy["avg_rating"],
            name="Avg Performance Score",
            yaxis="y2",
            mode="lines+markers+text",
            line=dict(color="#1E40AF", width=2.5),
            text=df_yoy["avg_rating"].apply(lambda v: f"{v:.2f}"),
            textposition="top center"
        ))
        fig_yoy.update_layout(
            title="Trend: Mean Performance Rating vs Merit Salary Increase",
            xaxis=dict(title="Appraisal Year"),
            yaxis=dict(title="Mean Merit Hike (%)"),
            yaxis2=dict(title="Mean Rating (Scale: 1-5)", overlaying="y", side="right", range=[1, 5]),
            legend=dict(x=0.01, y=0.99),
            height=390,
            margin=dict(l=10, r=10, t=35, b=10),
            font=dict(family="sans-serif", size=11)
        )
        st.plotly_chart(fig_yoy, use_container_width=True)

    with yoy_col2:
        fig_prom = px.bar(
            df_yoy,
            x="review_year",
            y="total_promotions",
            text="total_promotions",
            labels={"review_year": "Year", "total_promotions": "Promotions Awarded"},
            title="Total Promotions Granted by Cycle",
            color="total_promotions",
            color_continuous_scale="Blues"
        )
        fig_prom.update_layout(height=390, margin=dict(l=10, r=10, t=35, b=10), font=dict(family="sans-serif", size=11))
        st.plotly_chart(fig_prom, use_container_width=True)

st.divider()

# =============================================================================
# SECTION 3: ATTRITION RISK HEATMAP & FLIGHT RISK DIAGNOSTICS
# =============================================================================
st.markdown('<div class="section-title">Attrition Diagnostics & Flight Risk Modeling</div>', unsafe_allow_html=True)
st.markdown('<div class="section-desc">Identification of flight-risk roles based on work-life balance, satisfaction indices, and tenure metrics.</div>', unsafe_allow_html=True)

df_attr = analytics_mgr.get_attrition_risk_analysis()

if not df_attr.empty:
    r_col1, r_col2 = st.columns([1, 1])

    with r_col1:
        fig_scatter = px.scatter(
            df_attr,
            x="avg_work_life_balance",
            y="avg_risk_score",
            size="employee_count",
            color="department_name",
            hover_name="job_role",
            labels={
                "avg_work_life_balance": "Avg Work-Life Balance (1-4)",
                "avg_risk_score": "Attrition Risk Score (0-100)",
                "department_name": "Department"
            },
            title="Work-Life Balance vs Attrition Risk by Functional Role"
        )
        fig_scatter.update_layout(height=390, margin=dict(l=10, r=10, t=35, b=10), font=dict(family="sans-serif", size=11))
        st.plotly_chart(fig_scatter, use_container_width=True)

    with r_col2:
        st.markdown("##### High Flight-Risk Functional Roles (Score ≥ 45)")
        df_high_risk = df_attr[df_attr["avg_risk_score"] >= 45].sort_values(by="avg_risk_score", ascending=False)
        st.dataframe(
            df_high_risk[["department_name", "job_role", "avg_risk_score", "avg_work_life_balance", "high_risk_count"]],
            use_container_width=True,
            hide_index=True,
            height=340
        )

st.divider()

# =============================================================================
# SECTION 4: DEPARTMENT HEADCOUNT & ANNUAL PAYROLL SPEND
# =============================================================================
st.markdown('<div class="section-title">Workforce Allocation & Payroll Expenditure by Department</div>', unsafe_allow_html=True)

df_dept_dist = analytics_mgr.get_department_distribution()

if not df_dept_dist.empty:
    d_col1, d_col2 = st.columns([1, 1])
    with d_col1:
        fig_donut = px.pie(
            df_dept_dist,
            values="headcount",
            names="department_name",
            title="Headcount Distribution by Business Unit",
            hole=0.45,
            color_discrete_sequence=["#1E40AF", "#3B82F6", "#60A5FA", "#93C5FD", "#BFDBFE"]
        )
        fig_donut.update_layout(height=370, margin=dict(l=10, r=10, t=35, b=10), font=dict(family="sans-serif", size=11))
        st.plotly_chart(fig_donut, use_container_width=True)

    with d_col2:
        fig_pay = px.bar(
            df_dept_dist,
            x="department_name",
            y="total_payroll_annual",
            text="total_payroll_annual",
            labels={"total_payroll_annual": "Annual Payroll ($USD)", "department_name": "Department"},
            title="Annualized Payroll Expenditure by Business Unit",
            color="avg_salary",
            color_continuous_scale="Blues"
        )
        fig_pay.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
        fig_pay.update_layout(height=370, margin=dict(l=10, r=10, t=35, b=10), font=dict(family="sans-serif", size=11))
        st.plotly_chart(fig_pay, use_container_width=True)

st.divider()

# =============================================================================
# SECTION 5: PROJECT ALLOCATION & BOTTLENECK ANALYSIS (ALTAIR VISUAL ENGINE)
# =============================================================================
st.markdown('<div class="section-title">Project Allocation & Bottleneck Workload Diagnostics</div>', unsafe_allow_html=True)
st.markdown('<div class="section-desc">Interactive resource allocation analytics generated via Altair — identifies departmental workload pressure and staffing bottlenecks.</div>', unsafe_allow_html=True)

df_proj_alloc = analytics_mgr.get_project_allocation_analysis()

if not df_proj_alloc.empty:
    b_col1, b_col2 = st.columns([3, 2])

    with b_col1:
        # Altair grouped bar chart comparing Active Projects vs Full-Time Equivalent (FTE) Allocated
        melted = df_proj_alloc.melt(
            id_vars=["department_name", "bottleneck_status"],
            value_vars=["active_projects", "total_fte_allocated"],
            var_name="Metric",
            value_name="Value"
        )
        metric_labels = {
            "active_projects": "Active Initiatives",
            "total_fte_allocated": "Total FTE Allocated"
        }
        melted["MetricLabel"] = melted["Metric"].map(metric_labels)

        alt_chart = alt.Chart(melted).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            x=alt.X("department_name:N", title="Department", axis=alt.Axis(labelAngle=-15)),
            y=alt.Y("Value:Q", title="Capacity Volume"),
            color=alt.Color(
                "MetricLabel:N",
                scale=alt.Scale(domain=["Active Initiatives", "Total FTE Allocated"], range=["#3B82F6", "#1E40AF"]),
                legend=alt.Legend(title="Allocation Dimension", orient="top")
            ),
            xOffset="MetricLabel:N",
            tooltip=[
                alt.Tooltip("department_name:N", title="Department"),
                alt.Tooltip("MetricLabel:N", title="Metric"),
                alt.Tooltip("Value:Q", title="Count/FTE", format=",.1f"),
                alt.Tooltip("bottleneck_status:N", title="Workload Risk")
            ]
        ).properties(
            title="Department Staffing Capacity vs Active Initiatives (Altair Engine)",
            height=370
        ).configure_title(fontSize=13, anchor="start", color="#0F172A")

        st.altair_chart(alt_chart, use_container_width=True)

    with b_col2:
        st.markdown("##### Department Workload & Bottleneck Registry")
        st.dataframe(
            df_proj_alloc[[
                "department_name", "active_projects", "assigned_staff",
                "avg_allocation_pct", "bottleneck_status"
            ]],
            use_container_width=True,
            hide_index=True,
            height=350
        )
else:
    st.info("No project allocation records available for analysis.")

st.divider()

# =============================================================================
# SECTION 6: SCD TYPE 2 ENTERPRISE MOBILITY AUDIT TRAIL
# =============================================================================
st.markdown('<div class="section-title">SCD Type 2 Career Mobility & Historical Transition Audit</div>', unsafe_allow_html=True)
st.markdown('<div class="section-desc">Audit of historical dimension versions tracking promotions, departmental transfers, and salary trajectories preserved in Dim_Employee.</div>', unsafe_allow_html=True)

df_scd2_audit = analytics_mgr.get_scd2_progression_audit(limit=30)
if not df_scd2_audit.empty:
    st.dataframe(
        df_scd2_audit,
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No multi-version records located in dimensional storage.")
