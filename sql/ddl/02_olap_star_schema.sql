-- ============================================================================
-- Enterprise Employee Analytics & Data Warehouse System
-- Phase 2: OLAP Dimensional Star Schema (SCD Type 2)
-- Database: enterprise_hr_dw
-- ============================================================================

CREATE DATABASE IF NOT EXISTS enterprise_hr_dw;
USE enterprise_hr_dw;

-- Drop tables in reverse foreign key order for clean replayability
DROP TABLE IF EXISTS Fact_PerformanceReviews;
DROP TABLE IF EXISTS Dim_Employee;
DROP TABLE IF EXISTS Dim_Project;
DROP TABLE IF EXISTS Dim_Department;
DROP TABLE IF EXISTS Dim_Date;
DROP TABLE IF EXISTS ETL_Execution_Log;

-- ----------------------------------------------------------------------------
-- 1. Dimension: Dim_Date (Conformed Calendar Dimension)
-- ----------------------------------------------------------------------------
CREATE TABLE Dim_Date (
    date_dim_id INT PRIMARY KEY COMMENT 'Surrogate Key formatted as YYYYMMDD (e.g., 20251215)',
    full_date DATE NOT NULL UNIQUE,
    year INT NOT NULL,
    quarter INT NOT NULL CHECK (quarter BETWEEN 1 AND 4),
    month INT NOT NULL CHECK (month BETWEEN 1 AND 12),
    month_name VARCHAR(20) NOT NULL,
    day_of_month INT NOT NULL CHECK (day_of_month BETWEEN 1 AND 31),
    day_name VARCHAR(20) NOT NULL,
    is_weekend TINYINT(1) NOT NULL DEFAULT 0,
    fiscal_year VARCHAR(10) NOT NULL,
    INDEX idx_date_year_month (year, month),
    INDEX idx_date_fiscal (fiscal_year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Conformed enterprise date dimension';

-- ----------------------------------------------------------------------------
-- 2. Dimension: Dim_Department (Conformed Dimension)
-- ----------------------------------------------------------------------------
CREATE TABLE Dim_Department (
    department_dim_id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Surrogate Key',
    department_id INT NOT NULL COMMENT 'Natural Business Key from OLTP',
    department_name VARCHAR(100) NOT NULL,
    cost_center VARCHAR(20) NOT NULL,
    budget DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_dim_dept_bk (department_id),
    INDEX idx_dim_dept_name (department_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Department dimension table';

-- ----------------------------------------------------------------------------
-- 3. Dimension: Dim_Project (Conformed Dimension)
-- ----------------------------------------------------------------------------
CREATE TABLE Dim_Project (
    project_dim_id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Surrogate Key',
    project_id INT NOT NULL COMMENT 'Natural Business Key from OLTP',
    project_code VARCHAR(20) NOT NULL,
    project_name VARCHAR(150) NOT NULL,
    budget_tier VARCHAR(30) NOT NULL,
    status VARCHAR(30) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_dim_proj_bk (project_id),
    INDEX idx_dim_proj_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Project dimension table';

-- ----------------------------------------------------------------------------
-- 4. Dimension: Dim_Employee (Slowly Changing Dimension Type 2)
-- ----------------------------------------------------------------------------
CREATE TABLE Dim_Employee (
    employee_dim_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT 'Surrogate Key (Unique across all historical versions)',
    employee_id VARCHAR(20) NOT NULL COMMENT 'Natural Business Key from OLTP',
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    gender VARCHAR(10) NOT NULL,
    age INT NOT NULL,
    hire_date DATE NOT NULL,
    department_id INT NOT NULL COMMENT 'Natural Department FK',
    department_name VARCHAR(100) NOT NULL,
    job_role VARCHAR(100) NOT NULL,
    education_field VARCHAR(100) NOT NULL,
    monthly_income DECIMAL(12, 2) NOT NULL,
    -- Slowly Changing Dimension Type 2 Metadata Columns --
    start_date DATE NOT NULL COMMENT 'Effective validity start date',
    end_date DATE NULL COMMENT 'Effective validity expiration date (NULL for active record)',
    is_current TINYINT(1) NOT NULL DEFAULT 1 COMMENT '1 = Active Current Version, 0 = Expired Historical Version',
    version INT NOT NULL DEFAULT 1 COMMENT 'Version sequence (1 = initial, 2 = first transition, etc.)',
    dw_load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_dim_emp_bk_current (employee_id, is_current),
    INDEX idx_dim_emp_is_current (is_current),
    INDEX idx_dim_emp_dept (department_name),
    INDEX idx_dim_emp_role (job_role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Employee dimension supporting SCD Type 2 tracking';

-- ----------------------------------------------------------------------------
-- 5. Central Fact Table: Fact_PerformanceReviews
-- ----------------------------------------------------------------------------
CREATE TABLE Fact_PerformanceReviews (
    review_fact_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT 'Fact Surrogate Key',
    -- Dimensional Foreign Keys (Surrogate Keys) --
    employee_dim_id BIGINT NOT NULL COMMENT 'FK to Dim_Employee (points to exact version active at review date)',
    department_dim_id INT NOT NULL COMMENT 'FK to Dim_Department',
    project_dim_id INT NOT NULL COMMENT 'FK to Dim_Project (default 0 if unassigned)',
    date_dim_id INT NOT NULL COMMENT 'FK to Dim_Date (format YYYYMMDD)',
    -- Degenerate Dimensions --
    review_id INT NOT NULL COMMENT 'Operational review identifier',
    employee_id VARCHAR(20) NOT NULL COMMENT 'Natural business key for direct lookup',
    -- Additive and Semi-Additive Measures --
    performance_rating INT NOT NULL CHECK (performance_rating BETWEEN 1 AND 5),
    monthly_income_at_review DECIMAL(12, 2) NOT NULL,
    percent_salary_hike DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    work_life_balance INT NOT NULL CHECK (work_life_balance BETWEEN 1 AND 4),
    job_satisfaction INT NOT NULL CHECK (job_satisfaction BETWEEN 1 AND 4),
    environment_satisfaction INT NOT NULL CHECK (environment_satisfaction BETWEEN 1 AND 4),
    attrition_risk_score INT NOT NULL CHECK (attrition_risk_score BETWEEN 0 AND 100),
    tenure_at_review INT NOT NULL DEFAULT 0,
    promotion_given TINYINT(1) NOT NULL DEFAULT 0,
    dw_load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_fact_emp_dim FOREIGN KEY (employee_dim_id) 
        REFERENCES Dim_Employee (employee_dim_id) ON UPDATE CASCADE,
    CONSTRAINT fk_fact_dept_dim FOREIGN KEY (department_dim_id) 
        REFERENCES Dim_Department (department_dim_id) ON UPDATE CASCADE,
    CONSTRAINT fk_fact_date_dim FOREIGN KEY (date_dim_id) 
        REFERENCES Dim_Date (date_dim_id) ON UPDATE CASCADE,
    INDEX idx_fact_date (date_dim_id),
    INDEX idx_fact_emp_dim (employee_dim_id),
    INDEX idx_fact_dept_dim (department_dim_id),
    INDEX idx_fact_rating (performance_rating),
    INDEX idx_fact_attrition (attrition_risk_score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Central fact table tracking employee reviews and analytical metrics';

-- ----------------------------------------------------------------------------
-- 6. Audit & Operational Log Table
-- ----------------------------------------------------------------------------
CREATE TABLE ETL_Execution_Log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    pipeline_name VARCHAR(100) NOT NULL,
    step_name VARCHAR(100) NOT NULL,
    records_processed INT NOT NULL DEFAULT 0,
    records_inserted INT NOT NULL DEFAULT 0,
    records_updated INT NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL, -- 'SUCCESS', 'FAILED', 'IN_PROGRESS'
    error_message TEXT NULL,
    execution_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    execution_end TIMESTAMP NULL,
    duration_seconds DECIMAL(10, 2) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ETL execution audit logs';
