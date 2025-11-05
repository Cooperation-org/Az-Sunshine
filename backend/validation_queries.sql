-- ============================================================
-- POSTGRESQL VALIDATION QUERIES FOR ARIZONA SUNSHINE PROJECT
-- Fixed to match Django model field names (using foreign key _id suffix)
-- ============================================================

-- ============================================================
-- 1. VERIFY ALL TABLES HAVE DATA
-- ============================================================

SELECT 
    'Counties' as table_name, COUNT(*) as row_count FROM "Counties"
UNION ALL
SELECT 'Parties', COUNT(*) FROM "Parties"
UNION ALL
SELECT 'Offices', COUNT(*) FROM "Offices"
UNION ALL
SELECT 'Cycles', COUNT(*) FROM "Cycles"
UNION ALL
SELECT 'EntityTypes', COUNT(*) FROM "EntityTypes"
UNION ALL
SELECT 'TransactionTypes', COUNT(*) FROM "TransactionTypes"
UNION ALL
SELECT 'Categories', COUNT(*) FROM "Categories"
UNION ALL
SELECT 'BallotMeasures', COUNT(*) FROM "BallotMeasures"
UNION ALL
SELECT 'Names (Entities)', COUNT(*) FROM "Names"
UNION ALL
SELECT 'Committees', COUNT(*) FROM "Committees"
UNION ALL
SELECT 'Transactions', COUNT(*) FROM "Transactions"
UNION ALL
SELECT 'Reports', COUNT(*) FROM "Reports"
ORDER BY table_name;

-- ============================================================
-- 2. BEN'S REQUIREMENT: CANDIDATE COMMITTEES
-- "create public-facing django-based transparency app and 
--  data models for candidates, races"
-- ============================================================

-- How many candidate committees do we have?
SELECT 
    'Total Committees' as metric,
    COUNT(*) as count
FROM "Committees"
UNION ALL
SELECT 
    'Candidate Committees',
    COUNT(*)
FROM "Committees"
WHERE candidate_id IS NOT NULL
UNION ALL
SELECT 
    'Candidates with Office',
    COUNT(*)
FROM "Committees"
WHERE candidate_id IS NOT NULL 
  AND candidate_office_id IS NOT NULL
UNION ALL
SELECT 
    'Candidates with Party',
    COUNT(*)
FROM "Committees"
WHERE candidate_id IS NOT NULL 
  AND candidate_party_id IS NOT NULL
UNION ALL
SELECT 
    'Candidates with Cycle',
    COUNT(*)
FROM "Committees"
WHERE candidate_id IS NOT NULL 
  AND election_cycle_id IS NOT NULL;

-- Sample of candidate committees
SELECT 
    c.committee_id,
    n.last_name || COALESCE(', ' || n.first_name, '') as candidate_name,
    o.name as office,
    p.name as party,
    cy.name as cycle,
    c.is_incumbent
FROM "Committees" c
JOIN "Names" n ON c.name_id = n.name_id
LEFT JOIN "Offices" o ON c.candidate_office_id = o.office_id
LEFT JOIN "Parties" p ON c.candidate_party_id = p.party_id
LEFT JOIN "Cycles" cy ON c.election_cycle_id = cy.cycle_id
WHERE c.candidate_id IS NOT NULL
ORDER BY cy.begin_date DESC NULLS LAST, o.name, n.last_name
LIMIT 20;

-- ============================================================
-- 3. BEN'S REQUIREMENT: INDEPENDENT EXPENDITURE TRACKING
-- "Aggregate by entity, race, and candidate"
-- "Pull donors (individual and super PAC) to relevant IEs"
-- ============================================================

-- Verify IE transactions are properly mapped
SELECT 
    'Total IE Transactions' as metric,
    COUNT(*) as count,
    SUM(amount) as total_amount
FROM "Transactions"
WHERE subject_committee_id IS NOT NULL
  AND deleted = false
UNION ALL
SELECT 
    'IE For Benefit',
    COUNT(*),
    SUM(amount)
FROM "Transactions"
WHERE subject_committee_id IS NOT NULL
  AND is_for_benefit = true
  AND deleted = false
UNION ALL
SELECT 
    'IE Against Benefit',
    COUNT(*),
    SUM(amount)
FROM "Transactions"
WHERE subject_committee_id IS NOT NULL
  AND is_for_benefit = false
  AND deleted = false;

-- Top 10 candidates by IE spending FOR them
SELECT 
    subject.committee_id,
    n.last_name || COALESCE(', ' || n.first_name, '') as candidate_name,
    o.name as office,
    p.name as party,
    COUNT(t.transaction_id) as num_ie_expenditures,
    SUM(t.amount) as total_ie_for
FROM "Transactions" t
JOIN "Committees" subject ON t.subject_committee_id = subject.committee_id
JOIN "Names" n ON subject.name_id = n.name_id
LEFT JOIN "Offices" o ON subject.candidate_office_id = o.office_id
LEFT JOIN "Parties" p ON subject.candidate_party_id = p.party_id
WHERE t.is_for_benefit = true
  AND t.deleted = false
GROUP BY subject.committee_id, n.last_name, n.first_name, o.name, p.name
ORDER BY total_ie_for DESC
LIMIT 10;

-- Top 10 candidates by IE spending AGAINST them
SELECT 
    subject.committee_id,
    n.last_name || COALESCE(', ' || n.first_name, '') as candidate_name,
    o.name as office,
    p.name as party,
    COUNT(t.transaction_id) as num_ie_expenditures,
    SUM(t.amount) as total_ie_against
FROM "Transactions" t
JOIN "Committees" subject ON t.subject_committee_id = subject.committee_id
JOIN "Names" n ON subject.name_id = n.name_id
LEFT JOIN "Offices" o ON subject.candidate_office_id = o.office_id
LEFT JOIN "Parties" p ON subject.candidate_party_id = p.party_id
WHERE t.is_for_benefit = false
  AND t.deleted = false
GROUP BY subject.committee_id, n.last_name, n.first_name, o.name, p.name
ORDER BY total_ie_against DESC
LIMIT 10;

-- ============================================================
-- 4. BEN'S REQUIREMENT: IE DONOR TRACKING
-- "Aggregate IE donors by race and candidate"
-- ============================================================

-- Top IE committees (those making independent expenditures)
SELECT 
    c.committee_id,
    n.last_name as committee_name,
    COUNT(DISTINCT t.subject_committee_id) as num_candidates_supported,
    COUNT(t.transaction_id) as num_ie_expenditures,
    SUM(t.amount) as total_ie_spending
FROM "Transactions" t
JOIN "Committees" c ON t.committee_id = c.committee_id
JOIN "Names" n ON c.name_id = n.name_id
WHERE t.subject_committee_id IS NOT NULL
  AND t.deleted = false
GROUP BY c.committee_id, n.last_name
ORDER BY total_ie_spending DESC
LIMIT 20;

-- Donors to IE committees (tracing the money)
WITH ie_committees AS (
    SELECT DISTINCT committee_id
    FROM "Transactions"
    WHERE subject_committee_id IS NOT NULL
)
SELECT 
    donor.name_id,
    donor.last_name || COALESCE(', ' || donor.first_name, '') as donor_name,
    donor.occupation,
    donor.employer,
    et.name as entity_type,
    COUNT(t.transaction_id) as num_contributions,
    SUM(t.amount) as total_contributed_to_ie_committees
FROM "Transactions" t
JOIN ie_committees ie ON t.committee_id = ie.committee_id
JOIN "Names" donor ON t.entity_id = donor.name_id
JOIN "EntityTypes" et ON donor.entity_type_id = et.entity_type_id
JOIN "TransactionTypes" tt ON t.transaction_type_id = tt.transaction_type_id
WHERE tt.income_expense_neutral = 1  -- Contributions only
  AND t.deleted = false
GROUP BY donor.name_id, donor.last_name, donor.first_name, 
         donor.occupation, donor.employer, et.name
ORDER BY total_contributed_to_ie_committees DESC
LIMIT 50;

-- ============================================================
-- 5. BEN'S REQUIREMENT: AGGREGATE BY RACE
-- "Aggregate by entity, race, and candidate"
-- ============================================================

-- IE spending by race (office + cycle)
SELECT 
    o.name as office,
    cy.name as cycle,
    COUNT(DISTINCT t.subject_committee_id) as num_candidates,
    COUNT(t.transaction_id) as num_ie_transactions,
    SUM(CASE WHEN t.is_for_benefit = true THEN t.amount ELSE 0 END) as ie_for_total,
    SUM(CASE WHEN t.is_for_benefit = false THEN t.amount ELSE 0 END) as ie_against_total,
    SUM(t.amount) as total_ie_spending
FROM "Transactions" t
JOIN "Committees" subject ON t.subject_committee_id = subject.committee_id
LEFT JOIN "Offices" o ON subject.candidate_office_id = o.office_id
LEFT JOIN "Cycles" cy ON subject.election_cycle_id = cy.cycle_id
WHERE t.deleted = false
GROUP BY o.name, cy.name
HAVING o.name IS NOT NULL AND cy.name IS NOT NULL
ORDER BY total_ie_spending DESC
LIMIT 20;

-- ============================================================
-- 6. BEN'S REQUIREMENT: GRASSROOTS THRESHOLD COMPARISON
-- "Compare direct IE spending to grassroots threshold"
-- "Compare total IE spending funded indirectly by donor to threshold"
-- ============================================================

-- Candidates where IE spending exceeds grassroots threshold ($5,000)
WITH candidate_ie AS (
    SELECT 
        subject.committee_id,
        n.last_name || COALESCE(', ' || n.first_name, '') as candidate_name,
        o.name as office,
        p.name as party,
        SUM(CASE WHEN t.is_for_benefit = true THEN t.amount ELSE 0 END) as ie_for,
        SUM(CASE WHEN t.is_for_benefit = false THEN t.amount ELSE 0 END) as ie_against,
        SUM(t.amount) as total_ie
    FROM "Transactions" t
    JOIN "Committees" subject ON t.subject_committee_id = subject.committee_id
    JOIN "Names" n ON subject.name_id = n.name_id
    LEFT JOIN "Offices" o ON subject.candidate_office_id = o.office_id
    LEFT JOIN "Parties" p ON subject.candidate_party_id = p.party_id
    WHERE t.deleted = false
    GROUP BY subject.committee_id, n.last_name, n.first_name, o.name, p.name
)
SELECT 
    *,
    CASE WHEN ie_for > 5000 THEN 'YES' ELSE 'NO' END as exceeds_threshold_for,
    CASE WHEN ie_against > 5000 THEN 'YES' ELSE 'NO' END as exceeds_threshold_against,
    ROUND(ie_for / 5000.0, 2) as times_threshold_for,
    ROUND(ie_against / 5000.0, 2) as times_threshold_against
FROM candidate_ie
WHERE ie_for > 5000 OR ie_against > 5000
ORDER BY total_ie DESC;

-- ============================================================
-- 7. DATA INTEGRITY CHECKS
-- ============================================================

-- Check for missing foreign keys
SELECT 
    'Committees with invalid name_id' as issue,
    COUNT(*) as count
FROM "Committees" c
LEFT JOIN "Names" n ON c.name_id = n.name_id
WHERE n.name_id IS NULL
UNION ALL
SELECT 
    'Transactions with invalid committee_id',
    COUNT(*)
FROM "Transactions" t
LEFT JOIN "Committees" c ON t.committee_id = c.committee_id
WHERE c.committee_id IS NULL
UNION ALL
SELECT 
    'Transactions with invalid entity_id (donor)',
    COUNT(*)
FROM "Transactions" t
LEFT JOIN "Names" n ON t.entity_id = n.name_id
WHERE n.name_id IS NULL
UNION ALL
SELECT 
    'IE Transactions with invalid subject_committee_id',
    COUNT(*)
FROM "Transactions" t
LEFT JOIN "Committees" c ON t.subject_committee_id = c.committee_id
WHERE t.subject_committee_id IS NOT NULL
  AND c.committee_id IS NULL;

-- Check for data completeness
SELECT 
    'Candidate committees missing office' as issue,
    COUNT(*) as count
FROM "Committees"
WHERE candidate_id IS NOT NULL
  AND candidate_office_id IS NULL
UNION ALL
SELECT 
    'Candidate committees missing party',
    COUNT(*)
FROM "Committees"
WHERE candidate_id IS NOT NULL
  AND candidate_party_id IS NULL
UNION ALL
SELECT 
    'Candidate committees missing cycle',
    COUNT(*)
FROM "Committees"
WHERE candidate_id IS NOT NULL
  AND election_cycle_id IS NULL
UNION ALL
SELECT 
    'Active committees with no transactions',
    COUNT(*)
FROM "Committees" c
WHERE c.termination_date IS NULL
  AND NOT EXISTS (
      SELECT 1 FROM "Transactions" t 
      WHERE t.committee_id = c.committee_id
        AND t.deleted = false
  );

-- ============================================================
-- 8. ADDITIONAL SANITY CHECKS
-- ============================================================

-- Check transaction amounts are reasonable
SELECT 
    'Transactions with zero amount' as issue,
    COUNT(*) as count
FROM "Transactions"
WHERE amount = 0 AND deleted = false
UNION ALL
SELECT 
    'Transactions with negative amount',
    COUNT(*)
FROM "Transactions"
WHERE amount < 0 AND deleted = false
UNION ALL
SELECT 
    'Transactions > $1M (unusually large)',
    COUNT(*)
FROM "Transactions"
WHERE amount > 1000000 AND deleted = false;

-- Check date ranges are sensible
SELECT 
    'Earliest transaction date' as metric,
    MIN(transaction_date)::text as value
FROM "Transactions"
WHERE deleted = false
UNION ALL
SELECT 
    'Latest transaction date',
    MAX(transaction_date)::text
FROM "Transactions"
WHERE deleted = false
UNION ALL
SELECT 
    'Future dated transactions (suspicious)',
    COUNT(*)::text
FROM "Transactions"
WHERE transaction_date > CURRENT_DATE AND deleted = false;

-- ============================================================
-- 9. PHASE 1 SUMMARY REPORT FOR BEN
-- ============================================================

SELECT '=== PHASE 1 DATA VALIDATION SUMMARY ===' as report_section
UNION ALL SELECT ''
UNION ALL SELECT 'Total Entities: ' || COUNT(*)::text FROM "Names"
UNION ALL SELECT 'Total Committees: ' || COUNT(*)::text FROM "Committees"
UNION ALL SELECT 'Candidate Committees: ' || COUNT(*)::text 
    FROM "Committees" WHERE candidate_id IS NOT NULL
UNION ALL SELECT 'Total Transactions: ' || COUNT(*)::text FROM "Transactions" WHERE deleted = false
UNION ALL SELECT 'IE Transactions: ' || COUNT(*)::text 
    FROM "Transactions" WHERE subject_committee_id IS NOT NULL AND deleted = false
UNION ALL SELECT ''
UNION ALL SELECT '=== IE SPENDING SUMMARY ==='
UNION ALL SELECT 'Total IE FOR candidates: $' || COALESCE(ROUND(SUM(amount), 2), 0)::text
    FROM "Transactions" WHERE is_for_benefit = true AND deleted = false AND subject_committee_id IS NOT NULL
UNION ALL SELECT 'Total IE AGAINST candidates: $' || COALESCE(ROUND(SUM(amount), 2), 0)::text
    FROM "Transactions" WHERE is_for_benefit = false AND deleted = false AND subject_committee_id IS NOT NULL
UNION ALL SELECT ''
UNION ALL SELECT '=== READY FOR PHASE 1? ==='
UNION ALL SELECT CASE 
    WHEN (SELECT COUNT(*) FROM "Committees" WHERE candidate_id IS NOT NULL) > 0
     AND (SELECT COUNT(*) FROM "Transactions" WHERE subject_committee_id IS NOT NULL) > 0
    THEN '✓ YES - Data mapped correctly for Phase 1'
    ELSE '✗ NO - Missing required data'
END;