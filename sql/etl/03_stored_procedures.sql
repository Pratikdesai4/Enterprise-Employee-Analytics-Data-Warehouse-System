-- ============================================================================
-- Enterprise Employee Analytics & Data Warehouse System
-- Phase 2: Stored Procedures & Advanced ETL Logic
-- Database: enterprise_hr_dw & enterprise_hr_oltp
-- ============================================================================

USE enterprise_hr_dw;

DELIMITER $$

-- ----------------------------------------------------------------------------
-- 1. Stored Procedure: Populate Calendar Date Dimension
-- ----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_populate_dim_date$$
CREATE PROCEDURE sp_populate_dim_date(IN p_start_year INT, IN p_end_year INT)
BEGIN
    DECLARE v_current_date DATE;
    DECLARE v_end_date DATE;
    DECLARE v_inserted_count INT DEFAULT 0;

    SET v_current_date = STR_TO_DATE(CONCAT(p_start_year, '-01-01'), '%Y-%m-%d');
    SET v_end_date = STR_TO_DATE(CONCAT(p_end_year, '-12-31'), '%Y-%m-%d');

    START TRANSACTION;

    WHILE v_current_date <= v_end_date DO
        INSERT INTO Dim_Date (
            date_dim_id, full_date, year, quarter, month, month_name,
            day_of_month, day_name, is_weekend, fiscal_year
        )
        VALUES (
            CAST(DATE_FORMAT(v_current_date, '%Y%m%d') AS UNSIGNED),
            v_current_date,
            YEAR(v_current_date),
            QUARTER(v_current_date),
            MONTH(v_current_date),
            MONTHNAME(v_current_date),
            DAY(v_current_date),
            DAYNAME(v_current_date),
            CASE WHEN DAYOFWEEK(v_current_date) IN (1, 7) THEN 1 ELSE 0 END,
            CONCAT('FY', YEAR(v_current_date))
        )
        ON DUPLICATE KEY UPDATE full_date = VALUES(full_date);

        SET v_inserted_count = v_inserted_count + 1;
        SET v_current_date = DATE_ADD(v_current_date, INTERVAL 1 DAY);
    END WHILE;

    COMMIT;

    INSERT INTO ETL_Execution_Log (pipeline_name, step_name, records_processed, records_inserted, status)
    VALUES ('ETL_Initial_Setup', 'sp_populate_dim_date', v_inserted_count, v_inserted_count, 'SUCCESS');

    SELECT CONCAT('Successfully populated Dim_Date with ', v_inserted_count, ' calendar records.') AS Result;
END$$

-- ----------------------------------------------------------------------------
-- 2. Stored Procedure: Sync Department Dimension from OLTP
-- ----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_etl_sync_departments$$
CREATE PROCEDURE sp_etl_sync_departments()
BEGIN
    DECLARE v_start_time TIMESTAMP;
    DECLARE v_rows_affected INT DEFAULT 0;

    SET v_start_time = CURRENT_TIMESTAMP;

    -- Upsert from OLTP departments table
    INSERT INTO enterprise_hr_dw.Dim_Department (department_id, department_name, cost_center, budget)
    SELECT 
        d.department_id,
        d.department_name,
        d.cost_center,
        d.budget
    FROM enterprise_hr_oltp.departments d
    LEFT JOIN enterprise_hr_dw.Dim_Department dd ON d.department_id = dd.department_id
    WHERE dd.department_id IS NULL;

    SET v_rows_affected = ROW_COUNT();

    -- Update any in-place changes to cost center or budget
    UPDATE enterprise_hr_dw.Dim_Department dd
    INNER JOIN enterprise_hr_oltp.departments d ON dd.department_id = d.department_id
    SET dd.department_name = d.department_name,
        dd.cost_center = d.cost_center,
        dd.budget = d.budget;

    INSERT INTO ETL_Execution_Log (
        pipeline_name, step_name, records_processed, records_inserted, status, 
        execution_start, execution_end, duration_seconds
    )
    VALUES (
        'Daily_Dimensional_Sync', 'sp_etl_sync_departments', v_rows_affected, v_rows_affected, 'SUCCESS',
        v_start_time, CURRENT_TIMESTAMP, TIMESTAMPDIFF(SECOND, v_start_time, CURRENT_TIMESTAMP)
    );

    SELECT 'Departments synchronized successfully' AS Result;
END$$

-- ----------------------------------------------------------------------------
-- 3. Stored Procedure: Sync Project Dimension from OLTP
-- ----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_etl_sync_projects$$
CREATE PROCEDURE sp_etl_sync_projects()
BEGIN
    DECLARE v_start_time TIMESTAMP;
    DECLARE v_rows_affected INT DEFAULT 0;

    SET v_start_time = CURRENT_TIMESTAMP;

    INSERT INTO enterprise_hr_dw.Dim_Project (project_id, project_code, project_name, budget_tier, status)
    SELECT 
        p.project_id,
        p.project_code,
        p.project_name,
        CASE 
            WHEN p.budget < 500000 THEN 'Small (<$500k)'
            WHEN p.budget BETWEEN 500000 AND 1500000 THEN 'Medium ($500k-$1.5M)'
            ELSE 'Large (>$1.5M)'
        END AS budget_tier,
        p.status
    FROM enterprise_hr_oltp.projects p
    LEFT JOIN enterprise_hr_dw.Dim_Project dp ON p.project_id = dp.project_id
    WHERE dp.project_id IS NULL;

    SET v_rows_affected = ROW_COUNT();

    INSERT INTO ETL_Execution_Log (
        pipeline_name, step_name, records_processed, records_inserted, status, 
        execution_start, execution_end, duration_seconds
    )
    VALUES (
        'Daily_Dimensional_Sync', 'sp_etl_sync_projects', v_rows_affected, v_rows_affected, 'SUCCESS',
        v_start_time, CURRENT_TIMESTAMP, TIMESTAMPDIFF(SECOND, v_start_time, CURRENT_TIMESTAMP)
    );

    SELECT 'Projects synchronized successfully' AS Result;
END$$

-- ----------------------------------------------------------------------------
-- 4. Stored Procedure: Core SCD Type 2 Employee Synchronization
-- ----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_etl_scd2_sync_employees$$
CREATE PROCEDURE sp_etl_scd2_sync_employees()
BEGIN
    DECLARE v_start_time TIMESTAMP;
    DECLARE v_expired_count INT DEFAULT 0;
    DECLARE v_inserted_count INT DEFAULT 0;

    SET v_start_time = CURRENT_TIMESTAMP;

    START TRANSACTION;

    -- STEP A: Expire active versions where tracked attributes (department, role, salary) have changed
    -- CTE identifying changed records between OLTP and DW active versions
    DROP TEMPORARY TABLE IF EXISTS tmp_scd2_changes;
    CREATE TEMPORARY TABLE tmp_scd2_changes AS
    SELECT 
        dw.employee_dim_id,
        dw.employee_id,
        dw.version AS old_version,
        oltp.first_name,
        oltp.last_name,
        oltp.gender,
        oltp.age,
        oltp.hire_date,
        oltp.department_id,
        d.department_name,
        oltp.job_role,
        oltp.education_field,
        oltp.monthly_income
    FROM enterprise_hr_dw.Dim_Employee dw
    INNER JOIN enterprise_hr_oltp.employees oltp ON dw.employee_id = oltp.employee_id
    INNER JOIN enterprise_hr_oltp.departments d ON oltp.department_id = d.department_id
    WHERE dw.is_current = 1
      AND (
          dw.department_name <> d.department_name
          OR dw.job_role <> oltp.job_role
          OR ABS(dw.monthly_income - oltp.monthly_income) > 100.00
      );

    -- Expire current records in Dim_Employee
    UPDATE enterprise_hr_dw.Dim_Employee dw
    INNER JOIN tmp_scd2_changes chg ON dw.employee_dim_id = chg.employee_dim_id
    SET dw.end_date = CURRENT_DATE,
        dw.is_current = 0;

    SET v_expired_count = ROW_COUNT();

    -- Insert new successor versions (Version = old_version + 1, start_date = CURRENT_DATE)
    INSERT INTO enterprise_hr_dw.Dim_Employee (
        employee_id, first_name, last_name, gender, age, hire_date,
        department_id, department_name, job_role, education_field, monthly_income,
        start_date, end_date, is_current, version
    )
    SELECT 
        chg.employee_id, chg.first_name, chg.last_name, chg.gender, chg.age, chg.hire_date,
        chg.department_id, chg.department_name, chg.job_role, chg.education_field, chg.monthly_income,
        CURRENT_DATE AS start_date,
        NULL AS end_date,
        1 AS is_current,
        chg.old_version + 1 AS version
    FROM tmp_scd2_changes chg;

    SET v_inserted_count = ROW_COUNT();

    -- STEP B: Insert brand new employees (not present in Dim_Employee at all)
    INSERT INTO enterprise_hr_dw.Dim_Employee (
        employee_id, first_name, last_name, gender, age, hire_date,
        department_id, department_name, job_role, education_field, monthly_income,
        start_date, end_date, is_current, version
    )
    SELECT 
        oltp.employee_id, oltp.first_name, oltp.last_name, oltp.gender, oltp.age, oltp.hire_date,
        oltp.department_id, d.department_name, oltp.job_role, oltp.education_field, oltp.monthly_income,
        oltp.hire_date AS start_date,
        NULL AS end_date,
        1 AS is_current,
        1 AS version
    FROM enterprise_hr_oltp.employees oltp
    INNER JOIN enterprise_hr_oltp.departments d ON oltp.department_id = d.department_id
    LEFT JOIN enterprise_hr_dw.Dim_Employee dw ON oltp.employee_id = dw.employee_id
    WHERE dw.employee_id IS NULL;

    SET v_inserted_count = v_inserted_count + ROW_COUNT();

    COMMIT;

    DROP TEMPORARY TABLE IF EXISTS tmp_scd2_changes;

    INSERT INTO ETL_Execution_Log (
        pipeline_name, step_name, records_processed, records_inserted, records_updated, status,
        execution_start, execution_end, duration_seconds
    )
    VALUES (
        'Daily_Dimensional_Sync', 'sp_etl_scd2_sync_employees', 
        (v_expired_count + v_inserted_count), v_inserted_count, v_expired_count, 'SUCCESS',
        v_start_time, CURRENT_TIMESTAMP, TIMESTAMPDIFF(SECOND, v_start_time, CURRENT_TIMESTAMP)
    );

    SELECT CONCAT('SCD2 Sync Completed: ', v_expired_count, ' expired versions, ', v_inserted_count, ' new versions created.') AS Result;
END$$

-- ----------------------------------------------------------------------------
-- 5. Stored Procedure: Load Fact_PerformanceReviews with Point-in-Time Key Resolution
-- ----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_etl_load_fact_performance$$
CREATE PROCEDURE sp_etl_load_fact_performance()
BEGIN
    DECLARE v_start_time TIMESTAMP;
    DECLARE v_inserted_count INT DEFAULT 0;

    SET v_start_time = CURRENT_TIMESTAMP;

    START TRANSACTION;

    -- Insert new reviews from OLTP into Fact table matching exact SCD2 surrogate key valid on review_date
    INSERT INTO enterprise_hr_dw.Fact_PerformanceReviews (
        employee_dim_id, department_dim_id, project_dim_id, date_dim_id,
        review_id, employee_id, performance_rating, monthly_income_at_review,
        percent_salary_hike, work_life_balance, job_satisfaction, environment_satisfaction,
        attrition_risk_score, tenure_at_review, promotion_given
    )
    SELECT 
        de.employee_dim_id,
        dd.department_dim_id,
        COALESCE(dp.project_dim_id, 0) AS project_dim_id,
        CAST(DATE_FORMAT(r.review_date, '%Y%m%d') AS UNSIGNED) AS date_dim_id,
        r.review_id,
        r.employee_id,
        r.performance_rating,
        r.monthly_income_at_review,
        r.percent_salary_hike,
        r.work_life_balance,
        r.job_satisfaction,
        r.environment_satisfaction,
        r.attrition_risk_score,
        r.tenure_at_review,
        r.promotion_given
    FROM enterprise_hr_oltp.performance_reviews r
    -- Match exact historical version of employee valid at appraisal time:
    INNER JOIN enterprise_hr_dw.Dim_Employee de 
        ON r.employee_id = de.employee_id
       AND r.review_date >= de.start_date
       AND (de.end_date IS NULL OR r.review_date < de.end_date)
    -- Match department dimension
    INNER JOIN enterprise_hr_dw.Dim_Department dd 
        ON r.department_id = dd.department_id
    -- Match primary project assignment if any
    LEFT JOIN (
        SELECT employee_id, MIN(project_id) AS project_id
        FROM enterprise_hr_oltp.employee_project_assignments
        GROUP BY employee_id
    ) pa ON r.employee_id = pa.employee_id
    LEFT JOIN enterprise_hr_dw.Dim_Project dp 
        ON pa.project_id = dp.project_id
    -- Exclude reviews already ingested
    LEFT JOIN enterprise_hr_dw.Fact_PerformanceReviews f 
        ON r.review_id = f.review_id
    WHERE f.review_id IS NULL;

    SET v_inserted_count = ROW_COUNT();

    COMMIT;

    INSERT INTO ETL_Execution_Log (
        pipeline_name, step_name, records_processed, records_inserted, status,
        execution_start, execution_end, duration_seconds
    )
    VALUES (
        'Daily_Fact_Sync', 'sp_etl_load_fact_performance', v_inserted_count, v_inserted_count, 'SUCCESS',
        v_start_time, CURRENT_TIMESTAMP, TIMESTAMPDIFF(SECOND, v_start_time, CURRENT_TIMESTAMP)
    );

    SELECT CONCAT('Fact_PerformanceReviews loaded with ', v_inserted_count, ' new review records.') AS Result;
END$$

-- ----------------------------------------------------------------------------
-- 6. Master Orchestrator Stored Procedure
-- ----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_run_full_etl$$
CREATE PROCEDURE sp_run_full_etl()
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        INSERT INTO ETL_Execution_Log (pipeline_name, step_name, status, error_message)
        VALUES ('Master_ETL_Orchestrator', 'sp_run_full_etl', 'FAILED', 'Unhandled SQL Exception during ETL execution');
        RESIGNAL;
    END;

    -- 1. Sync Calendar Dimension (2018 - 2030)
    CALL sp_populate_dim_date(2018, 2030);

    -- 2. Sync Conformed Dimensions
    CALL sp_etl_sync_departments();
    CALL sp_etl_sync_projects();

    -- 3. Execute SCD Type 2 Employee Dimension Sync
    CALL sp_etl_scd2_sync_employees();

    -- 4. Load Fact Performance Reviews
    CALL sp_etl_load_fact_performance();

    SELECT 'Full ETL Pipeline Executed Successfully!' AS MasterStatus;
END$$

DELIMITER ;
