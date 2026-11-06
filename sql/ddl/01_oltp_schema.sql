-- ============================================================================
-- Enterprise Employee Analytics & Data Warehouse System
-- Phase 2: OLTP Relational Schema (3NF) & Staging
-- Database: enterprise_hr_oltp
-- ============================================================================

CREATE DATABASE IF NOT EXISTS enterprise_hr_oltp;
USE enterprise_hr_oltp;

-- Drop tables in reverse foreign key order for clean replayability
DROP TABLE IF EXISTS employee_project_assignments;
DROP TABLE IF EXISTS performance_reviews;
DROP TABLE IF EXISTS projects;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS departments;
DROP TABLE IF EXISTS staging_employees;
DROP TABLE IF EXISTS staging_performance_reviews;

-- ----------------------------------------------------------------------------
-- 1. Operational Departments Table
-- ----------------------------------------------------------------------------
CREATE TABLE departments (
    department_id INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE,
    cost_center VARCHAR(20) NOT NULL UNIQUE,
    budget DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_dept_name (department_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Enterprise operational departments';

-- ----------------------------------------------------------------------------
-- 2. Operational Employees Table
-- ----------------------------------------------------------------------------
CREATE TABLE employees (
    employee_id VARCHAR(20) PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(30) NOT NULL,
    gender VARCHAR(10) NOT NULL,
    age INT NOT NULL,
    marital_status VARCHAR(20) NOT NULL,
    hire_date DATE NOT NULL,
    department_id INT NOT NULL,
    job_role VARCHAR(100) NOT NULL,
    education_field VARCHAR(100) NOT NULL,
    monthly_income DECIMAL(12, 2) NOT NULL,
    overtime VARCHAR(5) NOT NULL DEFAULT 'No',
    years_at_company INT NOT NULL DEFAULT 0,
    attrition VARCHAR(5) NOT NULL DEFAULT 'No',
    status VARCHAR(20) NOT NULL DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_emp_dept FOREIGN KEY (department_id) 
        REFERENCES departments (department_id) ON UPDATE CASCADE,
    INDEX idx_emp_dept (department_id),
    INDEX idx_emp_role (job_role),
    INDEX idx_emp_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Active operational employee records';

-- ----------------------------------------------------------------------------
-- 3. Operational Projects Table
-- ----------------------------------------------------------------------------
CREATE TABLE projects (
    project_id INT AUTO_INCREMENT PRIMARY KEY,
    project_code VARCHAR(20) NOT NULL UNIQUE,
    project_name VARCHAR(150) NOT NULL,
    department_id INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    budget DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
    status VARCHAR(30) NOT NULL DEFAULT 'Planning',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_proj_dept FOREIGN KEY (department_id) 
        REFERENCES departments (department_id) ON UPDATE CASCADE,
    INDEX idx_proj_dept (department_id),
    INDEX idx_proj_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Enterprise initiatives and client projects';

-- ----------------------------------------------------------------------------
-- 4. Employee Project Assignments (Bridge Table)
-- ----------------------------------------------------------------------------
CREATE TABLE employee_project_assignments (
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(20) NOT NULL,
    project_id INT NOT NULL,
    assignment_role VARCHAR(50) NOT NULL,
    allocation_percentage INT NOT NULL DEFAULT 100,
    assigned_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_assign_emp FOREIGN KEY (employee_id) 
        REFERENCES employees (employee_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_assign_proj FOREIGN KEY (project_id) 
        REFERENCES projects (project_id) ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE KEY uq_emp_proj (employee_id, project_id),
    INDEX idx_assign_proj (project_id),
    INDEX idx_assign_emp (employee_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Staff allocations to projects';

-- ----------------------------------------------------------------------------
-- 5. Operational Performance Reviews Table
-- ----------------------------------------------------------------------------
CREATE TABLE performance_reviews (
    review_id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(20) NOT NULL,
    department_id INT NOT NULL,
    review_date DATE NOT NULL,
    review_year INT NOT NULL,
    performance_rating INT NOT NULL CHECK (performance_rating BETWEEN 1 AND 5),
    monthly_income_at_review DECIMAL(12, 2) NOT NULL,
    percent_salary_hike DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    work_life_balance INT NOT NULL CHECK (work_life_balance BETWEEN 1 AND 4),
    job_satisfaction INT NOT NULL CHECK (job_satisfaction BETWEEN 1 AND 4),
    environment_satisfaction INT NOT NULL CHECK (environment_satisfaction BETWEEN 1 AND 4),
    promotion_given TINYINT(1) NOT NULL DEFAULT 0,
    attrition_risk_score INT NOT NULL DEFAULT 0 CHECK (attrition_risk_score BETWEEN 0 AND 100),
    tenure_at_review INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_rev_emp FOREIGN KEY (employee_id) 
        REFERENCES employees (employee_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_rev_dept FOREIGN KEY (department_id) 
        REFERENCES departments (department_id) ON UPDATE CASCADE,
    INDEX idx_rev_year (review_year),
    INDEX idx_rev_emp (employee_id),
    INDEX idx_rev_rating (performance_rating)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Operational employee appraisals';

-- ----------------------------------------------------------------------------
-- 6. Staging Tables (Bulk Data Ingestion & ETL Buffer)
-- ----------------------------------------------------------------------------
CREATE TABLE staging_employees (
    staging_id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(20) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100),
    phone VARCHAR(30),
    gender VARCHAR(10),
    age INT,
    marital_status VARCHAR(20),
    hire_date DATE,
    department_id INT,
    department_name VARCHAR(100),
    job_role VARCHAR(100),
    education_field VARCHAR(100),
    monthly_income DECIMAL(12, 2),
    overtime VARCHAR(5),
    years_at_company INT,
    attrition VARCHAR(5),
    status VARCHAR(20),
    batch_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_stg_emp_id (employee_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Staging landing table for raw/bulk employee feeds';

CREATE TABLE staging_performance_reviews (
    staging_id INT AUTO_INCREMENT PRIMARY KEY,
    review_id INT,
    employee_id VARCHAR(20),
    department_id INT,
    review_date DATE,
    review_year INT,
    performance_rating INT,
    monthly_income_at_review DECIMAL(12, 2),
    percent_salary_hike DECIMAL(5, 2),
    work_life_balance INT,
    job_satisfaction INT,
    environment_satisfaction INT,
    promotion_given TINYINT(1),
    attrition_risk_score INT,
    tenure_at_review INT,
    batch_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_stg_rev_emp (employee_id),
    INDEX idx_stg_rev_year (review_year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Staging landing table for review feeds';
