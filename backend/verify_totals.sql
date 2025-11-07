-- verify_totals.sql
-- SQL script to verify financial data accuracy in the database
-- Compatible with both SQLite and PostgreSQL
--
-- This script verifies:
-- 1. Total independent expenditures grouped by committee
-- 2. Total contributions grouped by donor entity
-- 3. Total support vs oppose amounts
--
-- Run this script and compare results with the frontend dashboard totals
--
-- USAGE:
--   SQLite:   sqlite3 db.sqlite3 < verify_totals.sql
--   PostgreSQL: psql -d your_database -f verify_totals.sql
--
-- Note: For PostgreSQL, you may need to uncomment the PostgreSQL-specific
--       versions of queries below and comment out the SQLite versions.

-- ============================================================================
-- QUERY 1: Total Independent Expenditures by Committee
-- ============================================================================
-- This matches the "Top 10 IE Committees by Spending" on the dashboard
-- Shows which committees made independent expenditures and total amounts
--
-- Expected: Should match the totals shown in Dashboard > Top 10 IE Committees

-- SQLite version (default):
SELECT 
    c.committee_id,
    COALESCE(
        CASE 
            WHEN n.first_name IS NOT NULL AND n.first_name != '' 
            THEN n.first_name || ' ' || n.last_name
            ELSE n.last_name
        END,
        'Unknown Committee'
    ) AS committee_name,
    SUM(t.amount) AS total_amount,
    COUNT(*) AS transaction_count
FROM 
    Transactions t
    INNER JOIN Committees c ON t.committee_id = c.committee_id
    INNER JOIN Names n ON c.name_id = n.name_id
WHERE 
    t.subject_committee_id IS NOT NULL
    AND t.deleted = 0  -- SQLite uses 0/1 for boolean
GROUP BY 
    c.committee_id, committee_name
ORDER BY 
    total_amount DESC
LIMIT 20;  -- Show top 20 for verification

-- PostgreSQL version (uncomment if using PostgreSQL and comment out SQLite version above):
/*
SELECT 
    c.committee_id,
    COALESCE(
        CASE 
            WHEN n.first_name IS NOT NULL AND n.first_name != '' 
            THEN n.first_name || ' ' || n.last_name
            ELSE n.last_name
        END,
        'Unknown Committee'
    ) AS committee_name,
    SUM(t.amount) AS total_amount,
    COUNT(*) AS transaction_count
FROM 
    "Transactions" t
    INNER JOIN "Committees" c ON t.committee_id = c.committee_id
    INNER JOIN "Names" n ON c.name_id = n.name_id
WHERE 
    t.subject_committee_id IS NOT NULL
    AND t.deleted = false  -- PostgreSQL uses true/false
GROUP BY 
    c.committee_id, committee_name
ORDER BY 
    total_amount DESC
LIMIT 20;
*/

-- ============================================================================
-- QUERY 2: Total Contributions by Donor Entity
-- ============================================================================
-- This matches the "Top 10 Donors" chart on the dashboard
-- Shows total contributions made by each donor/entity

-- SQLite version (default):
SELECT 
    e.name_id,
    COALESCE(
        CASE 
            WHEN e.first_name IS NOT NULL AND e.first_name != '' 
            THEN e.first_name || ' ' || e.last_name
            ELSE e.last_name
        END,
        'Unknown Donor'
    ) AS donor_name,
    et.name AS entity_type,
    SUM(t.amount) AS total_contribution,
    COUNT(*) AS contribution_count
FROM 
    Transactions t
    INNER JOIN Names e ON t.entity_id = e.name_id
    INNER JOIN TransactionTypes tt ON t.transaction_type_id = tt.transaction_type_id
    LEFT JOIN EntityTypes et ON e.entity_type_id = et.entity_type_id
WHERE 
    tt.income_expense_neutral = 1  -- 1 = contribution/income
    AND t.deleted = 0  -- SQLite uses 0/1 for boolean
GROUP BY 
    e.name_id, donor_name, entity_type
ORDER BY 
    total_contribution DESC
LIMIT 20;  -- Show top 20 for verification

-- PostgreSQL version (uncomment if using PostgreSQL and comment out SQLite version above):
/*
SELECT 
    e.name_id,
    COALESCE(
        CASE 
            WHEN e.first_name IS NOT NULL AND e.first_name != '' 
            THEN e.first_name || ' ' || e.last_name
            ELSE e.last_name
        END,
        'Unknown Donor'
    ) AS donor_name,
    et.name AS entity_type,
    SUM(t.amount) AS total_contribution,
    COUNT(*) AS contribution_count
FROM 
    "Transactions" t
    INNER JOIN "Names" e ON t.entity_id = e.name_id
    INNER JOIN "TransactionTypes" tt ON t.transaction_type_id = tt.transaction_type_id
    LEFT JOIN "EntityTypes" et ON e.entity_type_id = et.entity_type_id
WHERE 
    tt.income_expense_neutral = 1  -- 1 = contribution/income
    AND t.deleted = false  -- PostgreSQL uses true/false
GROUP BY 
    e.name_id, donor_name, entity_type
ORDER BY 
    total_contribution DESC
LIMIT 20;
*/

-- ============================================================================
-- QUERY 3: Total Support vs Oppose Amounts
-- ============================================================================
-- This matches the "Support vs Oppose" pie chart on the dashboard
-- Shows total spending for supporting candidates vs opposing candidates

SELECT 
    CASE 
        WHEN t.is_for_benefit = 1 THEN 'Support'
        WHEN t.is_for_benefit = 0 THEN 'Oppose'
        ELSE 'Unknown'
    END AS type,
    SUM(t.amount) AS total_amount,
    COUNT(*) AS transaction_count
FROM 
    Transactions t
WHERE 
    t.subject_committee_id IS NOT NULL
    AND t.deleted = 0  -- SQLite uses 0/1 for boolean
GROUP BY 
    type
ORDER BY 
    CASE type
        WHEN 'Support' THEN 1
        WHEN 'Oppose' THEN 2
        ELSE 3
    END;

-- PostgreSQL version (uncomment if using PostgreSQL and comment out SQLite version above):
/*
SELECT 
    CASE 
        WHEN t.is_for_benefit = true THEN 'Support'
        WHEN t.is_for_benefit = false THEN 'Oppose'
        ELSE 'Unknown'
    END AS type,
    SUM(t.amount) AS total_amount,
    COUNT(*) AS transaction_count
FROM 
    "Transactions" t
WHERE 
    t.subject_committee_id IS NOT NULL
    AND t.deleted = false  -- PostgreSQL uses true/false
GROUP BY 
    type
ORDER BY 
    CASE type
        WHEN 'Support' THEN 1
        WHEN 'Oppose' THEN 2
        ELSE 3
    END;
*/

-- ============================================================================
-- SUMMARY QUERIES (for quick verification)
-- ============================================================================

-- Total IE Spending (should match dashboard metric)
SELECT 
    'Total IE Spending' AS metric,
    SUM(amount) AS total_amount
FROM 
    Transactions
WHERE 
    subject_committee_id IS NOT NULL
    AND deleted = 0;

-- Total Contributions (overall)
SELECT 
    'Total Contributions' AS metric,
    SUM(amount) AS total_amount
FROM 
    Transactions t
    INNER JOIN TransactionTypes tt ON t.transaction_type_id = tt.transaction_type_id
WHERE 
    tt.income_expense_neutral = 1
    AND t.deleted = 0;

-- Support vs Oppose Summary (with percentages)
SELECT 
    CASE 
        WHEN is_for_benefit = 1 THEN 'Support'
        WHEN is_for_benefit = 0 THEN 'Oppose'
        ELSE 'Unknown'
    END AS type,
    SUM(amount) AS total_amount,
    ROUND(SUM(amount) * 100.0 / (SELECT SUM(amount) FROM Transactions WHERE subject_committee_id IS NOT NULL AND deleted = 0), 2) AS percentage
FROM 
    Transactions
WHERE 
    subject_committee_id IS NOT NULL
    AND deleted = 0
GROUP BY 
    type;

-- ============================================================================
-- VERIFICATION INSTRUCTIONS
-- ============================================================================
--
-- To verify these queries match the frontend dashboard:
--
-- 1. QUERY 1 (IE Expenditures by Committee):
--    - Compare with Dashboard > "Top 10 IE Committees by Spending" widget
--    - Top 10 rows should match the committee names and amounts shown
--    - Total amounts should match exactly
--
-- 2. QUERY 2 (Contributions by Donor):
--    - Compare with Dashboard > "Top 10 Donors" bar chart
--    - Top 10 rows should match the donor names and amounts shown
--    - Total contribution amounts should match exactly
--
-- 3. QUERY 3 (Support vs Oppose):
--    - Compare with Dashboard > "Support vs Oppose" pie chart
--    - Support total should match the green slice amount
--    - Oppose total should match the gray slice amount
--    - Percentages should match the labels shown (e.g., "65% Support")
--
-- 4. SUMMARY QUERIES:
--    - "Total IE Spending" should match Dashboard > "Total IE Spending" metric card
--    - "Total Contributions" shows overall contribution total (not shown on dashboard)
--    - Support vs Oppose Summary shows percentages for quick verification
--
-- If totals don't match:
--   1. Check that deleted=0/false filter is applied (no deleted transactions)
--   2. Verify subject_committee_id IS NOT NULL for IE queries
--   3. Verify income_expense_neutral = 1 for contribution queries
--   4. Check for NULL values in is_for_benefit (should be filtered or handled)
--
-- Expected behavior:
--   - All queries should return the same totals as shown in the frontend
--   - Frontend fetches data from API endpoints which use the same filters
--   - Any discrepancies indicate a data consistency issue that needs investigation

