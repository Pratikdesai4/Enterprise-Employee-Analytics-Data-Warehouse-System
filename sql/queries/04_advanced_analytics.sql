-- ============================================================================
-- Enterprise Employee Analytics & Data Warehouse System
-- Phase 2: Advanced SQL Scripts (CTEs & Window Functions)
-- Database: enterprise_hr_dw
-- ============================================================================

USE enterprise_hr_dw;

-- ============================================================================
-- QUERY 1: Department Top Performers via DENSE_RANK() Window Function
-- Identifies top 3 performing tiers per department based on rating and merit hike.
-- ============================================================================
WITH DepartmentPerformanceRanking AS (
    SELECT 
        dd.department_name,
        de.employee_id,
        CONCAT(de.first_name, ' ', de.last_name) AS full_name,
        de.job_role,
        f.performance_rating,
        f.percent_salary_hike,
        f.monthly_income_at_review,
        f.attrition_risk_score,
        d.year AS review_year,
        DENSE_RANK() OVER (
            PARTITION BY dd.department_name, d.year 
            ORDER BY f.performance_rating DESC, f.percent_salary_hike DESC
        ) AS dept_perf_rank
    FROM Fact_PerformanceReviews f
    INNER JOIN Dim_Employee de ON f.employee_dim_id = de.employee_dim_id
    INNER JOIN Dim_Department dd ON f.department_dim_id = dd.department_dim_id
    INNER JOIN Dim_Date d ON f.date_dim_id = d.date_dim_id
    WHERE d.year = 2025
)
SELECT 
    dept_perf_rank,
    department_name,
    employee_id,
    full_name,
    job_role,
    performance_rating,
    percent_salary_hike,
    monthly_income_at_review,
    attrition_risk_score
FROM DepartmentPerformanceRanking
WHERE dept_perf_rank <= 3
ORDER BY department_name, dept_perf_rank, full_name;


-- ============================================================================
-- QUERY 2: Year-over-Year (YoY) Salary & Rating Velocity via LAG() Window Function
-- Calculates the exact compensation delta and rating trajectory per employee.
-- ============================================================================
WITH EmployeeYearlyReviews AS (
    SELECT 
        f.employee_id,
        CONCAT(de.first_name, ' ', de.last_name) AS full_name,
        dd.department_name,
        d.year AS review_year,
        f.performance_rating,
        f.monthly_income_at_review,
        f.promotion_given,
        LAG(f.performance_rating, 1) OVER (
            PARTITION BY f.employee_id 
            ORDER BY d.year
        ) AS prior_year_rating,
        LAG(f.monthly_income_at_review, 1) OVER (
            PARTITION BY f.employee_id 
            ORDER BY d.year
        ) AS prior_year_income
    FROM Fact_PerformanceReviews f
    INNER JOIN Dim_Employee de ON f.employee_dim_id = de.employee_dim_id
    INNER JOIN Dim_Department dd ON f.department_dim_id = dd.department_dim_id
    INNER JOIN Dim_Date d ON f.date_dim_id = d.date_dim_id
)
SELECT 
    employee_id,
    full_name,
    department_name,
    review_year,
    prior_year_rating,
    performance_rating AS current_rating,
    (performance_rating - prior_year_rating) AS rating_delta,
    prior_year_income,
    monthly_income_at_review AS current_income,
    ROUND(((monthly_income_at_review - prior_year_income) / prior_year_income) * 100, 2) AS yoy_salary_growth_pct,
    promotion_given
FROM EmployeeYearlyReviews
WHERE prior_year_income IS NOT NULL
ORDER BY yoy_salary_growth_pct DESC
LIMIT 50;


-- ============================================================================
-- QUERY 3: SCD Type 2 Historical Career Progression CTE
-- Compares performance and compensation before and after departmental transfers.
-- ============================================================================
WITH EmployeeSCDVersions AS (
    SELECT 
        employee_id,
        version,
        department_name,
        job_role,
        monthly_income,
        start_date,
        end_date,
        is_current,
        COUNT(*) OVER (PARTITION BY employee_id) AS total_career_transitions
    FROM Dim_Employee
),
MultiVersionEmployees AS (
    SELECT * 
    FROM EmployeeSCDVersions
    WHERE total_career_transitions > 1
)
SELECT 
    m.employee_id,
    m.version,
    m.is_current,
    m.department_name,
    m.job_role,
    m.monthly_income,
    m.start_date,
    COALESCE(CAST(m.end_date AS CHAR), 'Active / Present') AS end_date,
    LAG(m.monthly_income, 1) OVER (PARTITION BY m.employee_id ORDER BY m.version) AS previous_version_salary,
    ROUND(
        m.monthly_income - LAG(m.monthly_income, 1) OVER (PARTITION BY m.employee_id ORDER BY m.version), 2
    ) AS promotion_salary_lift
FROM MultiVersionEmployees m
ORDER BY m.employee_id, m.version;


-- ============================================================================
-- QUERY 4: Attrition Risk Benchmark & Quartiles via NTILE() & AVG() OVER()
-- Identifies high-risk compensation outliers across job roles.
-- ============================================================================
WITH RoleAttritionAggregates AS (
    SELECT 
        dd.department_name,
        de.job_role,
        f.employee_id,
        CONCAT(de.first_name, ' ', de.last_name) AS full_name,
        f.monthly_income_at_review,
        f.attrition_risk_score,
        f.work_life_balance,
        AVG(f.attrition_risk_score) OVER (
            PARTITION BY dd.department_name, de.job_role
        ) AS role_avg_attrition_risk,
        AVG(f.monthly_income_at_review) OVER (
            PARTITION BY de.job_role
        ) AS role_avg_monthly_income,
        NTILE(4) OVER (
            PARTITION BY de.job_role 
            ORDER BY f.monthly_income_at_review
        ) AS salary_quartile
    FROM Fact_PerformanceReviews f
    INNER JOIN Dim_Employee de ON f.employee_dim_id = de.employee_dim_id
    INNER JOIN Dim_Department dd ON f.department_dim_id = dd.department_dim_id
    INNER JOIN Dim_Date d ON f.date_dim_id = d.date_dim_id
    WHERE d.year = 2025
)
SELECT 
    department_name,
    job_role,
    employee_id,
    full_name,
    monthly_income_at_review,
    salary_quartile,
    ROUND(role_avg_monthly_income, 2) AS benchmark_salary,
    attrition_risk_score,
    ROUND(role_avg_attrition_risk, 2) AS benchmark_attrition_risk,
    CASE 
        WHEN attrition_risk_score > role_avg_attrition_risk AND salary_quartile = 1 THEN 'CRITICAL: Underpaid High-Risk'
        WHEN attrition_risk_score > role_avg_attrition_risk THEN 'ELEVATED: Flight Risk'
        ELSE 'STABLE'
    END AS risk_tier
FROM RoleAttritionAggregates
WHERE attrition_risk_score >= 60
ORDER BY attrition_risk_score DESC, monthly_income_at_review ASC
LIMIT 100;
