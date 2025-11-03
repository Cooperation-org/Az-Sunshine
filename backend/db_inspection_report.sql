-- ============================================================================
-- DATABASE INSPECTION SCRIPT FOR ARIZONA SUNSHINE TRANSPARENCY PROJECT
-- This script verifies all raw MDB data and mapped application data
-- ============================================================================

\echo '======================================================================='
\echo 'ARIZONA SUNSHINE - DATABASE INSPECTION REPORT'
\echo '======================================================================='
\echo ''

-- ============================================================================
-- SECTION 1: RAW MDB DATA COUNTS
-- ============================================================================
\echo '1. RAW MDB DATA SUMMARY'
\echo '======================='
\echo ''

\echo '→ Lookup Tables (Reference Data):'
SELECT 'Entity Types' as table_name, COUNT(*) as record_count FROM mdb_entity_types
UNION ALL
SELECT 'Transaction Types', COUNT(*) FROM mdb_transaction_types
UNION ALL
SELECT 'Offices', COUNT(*) FROM mdb_offices
UNION ALL
SELECT 'Categories', COUNT(*) FROM mdb_categories
UNION ALL
SELECT 'Parties', COUNT(*) FROM mdb_parties;

\echo ''
\echo '→ Main Raw Data Tables:'
SELECT 'Names (All Entities)' as table_name, COUNT(*) as record_count FROM mdb_names
UNION ALL
SELECT 'Committees', COUNT(*) FROM mdb_committees
UNION ALL
SELECT 'Transactions', COUNT(*) FROM mdb_transactions;

\echo ''

-- ============================================================================
-- SECTION 2: APPLICATION DATA COUNTS
-- ============================================================================
\echo '2. APPLICATION DATA SUMMARY'
\echo '==========================='
\echo ''

SELECT 'Parties' as table_name, COUNT(*) as record_count FROM transparency_party
UNION ALL
SELECT 'Races', COUNT(*) FROM transparency_race
UNION ALL
SELECT 'Candidates', COUNT(*) FROM transparency_candidate
UNION ALL
SELECT 'IE Committees', COUNT(*) FROM transparency_iecommittee
UNION ALL
SELECT 'Donor Entities', COUNT(*) FROM transparency_donorentity
UNION ALL
SELECT 'Contributions', COUNT(*) FROM transparency_contribution
UNION ALL
SELECT 'Expenditures', COUNT(*) FROM transparency_expenditure;

\echo ''

-- ============================================================================
-- SECTION 3: DATA QUALITY - SOURCE REFERENCES
-- ============================================================================
\echo '3. DATA QUALITY - SOURCE REFERENCE VERIFICATION'
\echo '================================================'
\echo ''

\echo '→ Candidates linked to source MDB data:'
SELECT 
    COUNT(*) as total_candidates,
    COUNT(source_mdb_committee_id) as with_committee_link,
    COUNT(source_mdb_candidate_name_id) as with_name_link,
    COUNT(*) - COUNT(source_mdb_committee_id) as missing_committee_link,
    COUNT(*) - COUNT(source_mdb_candidate_name_id) as missing_name_link
FROM transparency_candidate;

\echo ''
\echo '→ IE Committees linked to source MDB data:'
SELECT 
    COUNT(*) as total_ie_committees,
    COUNT(source_mdb_committee_id) as with_committee_link,
    COUNT(source_mdb_committee_name_id) as with_name_link
FROM transparency_iecommittee;

\echo ''
\echo '→ Donors linked to source MDB data:'
SELECT 
    COUNT(*) as total_donors,
    COUNT(source_mdb_name_id) as with_name_link
FROM transparency_donorentity;

\echo ''
\echo '→ Contributions linked to source MDB data:'
SELECT 
    COUNT(*) as total_contributions,
    COUNT(source_mdb_transaction_id) as with_transaction_link,
    COUNT(donor_id) as with_donor_link,
    COUNT(committee_id) as with_committee_link
FROM transparency_contribution;

\echo ''
\echo '→ Expenditures linked to source MDB data:'
SELECT 
    COUNT(*) as total_expenditures,
    COUNT(source_mdb_transaction_id) as with_transaction_link,
    COUNT(ie_committee_id) as with_committee_link,
    COUNT(candidate_id) as with_candidate_link
FROM transparency_expenditure;

\echo ''

-- ============================================================================
-- SECTION 4: RAW DATA BREAKDOWN
-- ============================================================================
\echo '4. RAW DATA DETAILED BREAKDOWN'
\echo '==============================='
\echo ''

\echo '→ Names by Entity Type:'
SELECT 
    et."EntityTypeName",
    COUNT(*) as count
FROM mdb_names n
LEFT JOIN mdb_entity_types et ON n."EntityTypeID" = et."EntityTypeID"
GROUP BY et."EntityTypeName"
ORDER BY count DESC
LIMIT 20;

\echo ''
\echo '→ Committees Breakdown:'
SELECT 
    CASE 
        WHEN "CandidateNameID" IS NOT NULL THEN 'Candidate Committee'
        ELSE 'Non-Candidate Committee'
    END as committee_type,
    COUNT(*) as count
FROM mdb_committees
GROUP BY committee_type;

\echo ''
\echo '→ Transactions by Type (Top 20):'
SELECT 
    tt."TransactionTypeName",
    tt."IncomeExpenseNeutralID",
    CASE 
        WHEN tt."IncomeExpenseNeutralID" = 1 THEN 'Income'
        WHEN tt."IncomeExpenseNeutralID" = 2 THEN 'Expense'
        WHEN tt."IncomeExpenseNeutralID" = 3 THEN 'Neutral'
        ELSE 'Unknown'
    END as transaction_category,
    COUNT(*) as count,
    SUM(t."Amount") as total_amount
FROM mdb_transactions t
LEFT JOIN mdb_transaction_types tt ON t."TransactionTypeID" = tt."TransactionTypeID"
WHERE t."Deleted" = 0
GROUP BY tt."TransactionTypeName", tt."IncomeExpenseNeutralID"
ORDER BY count DESC
LIMIT 20;

\echo ''

-- ============================================================================
-- SECTION 5: SAMPLE CANDIDATE DATA
-- ============================================================================
\echo '5. SAMPLE CANDIDATE DATA (Verification)'
\echo '========================================'
\echo ''

\echo '→ Sample Candidates with Complete Information:'
SELECT 
    c.id,
    c.name as candidate_name,
    c.source,
    p.name as party,
    r.name as race,
    c.filing_date,
    CASE WHEN c.source_mdb_committee_id IS NOT NULL THEN 'Yes' ELSE 'No' END as has_mdb_link
FROM transparency_candidate c
LEFT JOIN transparency_party p ON c.party_id = p.id
LEFT JOIN transparency_race r ON c.race_id = r.id
ORDER BY c.id
LIMIT 10;

\echo ''
\echo '→ Candidates by Party:'
SELECT 
    COALESCE(p.name, 'No Party') as party,
    COUNT(*) as candidate_count
FROM transparency_candidate c
LEFT JOIN transparency_party p ON c.party_id = p.id
GROUP BY p.name
ORDER BY candidate_count DESC;

\echo ''
\echo '→ Candidates by Race/Office:'
SELECT 
    COALESCE(r.name, 'No Race') as race,
    COUNT(*) as candidate_count
FROM transparency_candidate c
LEFT JOIN transparency_race r ON c.race_id = r.id
GROUP BY r.name
ORDER BY candidate_count DESC
LIMIT 15;

\echo ''

-- ============================================================================
-- SECTION 6: SAMPLE IE COMMITTEE DATA
-- ============================================================================
\echo '6. SAMPLE IE COMMITTEE DATA'
\echo '==========================='
\echo ''

\echo '→ Sample IE Committees:'
SELECT 
    id,
    name,
    committee_type,
    CASE WHEN source_mdb_committee_id IS NOT NULL THEN 'Yes' ELSE 'No' END as has_mdb_link
FROM transparency_iecommittee
ORDER BY id
LIMIT 10;

\echo ''
\echo '→ IE Committees by Type:'
SELECT 
    COALESCE(committee_type, 'Unknown Type') as type,
    COUNT(*) as count
FROM transparency_iecommittee
GROUP BY committee_type
ORDER BY count DESC
LIMIT 15;

\echo ''

-- ============================================================================
-- SECTION 7: SAMPLE DONOR DATA
-- ============================================================================
\echo '7. SAMPLE DONOR DATA'
\echo '===================='
\echo ''

\echo '→ Sample Donors:'
SELECT 
    id,
    name,
    entity_type,
    total_contribution,
    CASE WHEN source_mdb_name_id IS NOT NULL THEN 'Yes' ELSE 'No' END as has_mdb_link
FROM transparency_donorentity
ORDER BY total_contribution DESC
LIMIT 10;

\echo ''
\echo '→ Donors by Entity Type:'
SELECT 
    COALESCE(entity_type, 'Unknown') as type,
    COUNT(*) as count
FROM transparency_donorentity
GROUP BY entity_type
ORDER BY count DESC;

\echo ''

-- ============================================================================
-- SECTION 8: CONTRIBUTIONS ANALYSIS
-- ============================================================================
\echo '8. CONTRIBUTIONS ANALYSIS'
\echo '========================='
\echo ''

\echo '→ Contributions by Year:'
SELECT 
    COALESCE(year::text, 'Unknown') as year,
    COUNT(*) as contribution_count,
    SUM(amount) as total_amount,
    AVG(amount) as avg_amount,
    MIN(amount) as min_amount,
    MAX(amount) as max_amount
FROM transparency_contribution
GROUP BY year
ORDER BY year DESC;

\echo ''
\echo '→ Sample Large Contributions:'
SELECT 
    c.id,
    d.name as donor,
    cm.name as committee,
    c.amount,
    c.date,
    c.year
FROM transparency_contribution c
LEFT JOIN transparency_donorentity d ON c.donor_id = d.id
LEFT JOIN transparency_iecommittee cm ON c.committee_id = cm.id
WHERE c.amount > 1000
ORDER BY c.amount DESC
LIMIT 10;

\echo ''
\echo '→ Contributions with Missing Links:'
SELECT 
    COUNT(*) as total,
    COUNT(*) - COUNT(donor_id) as missing_donor,
    COUNT(*) - COUNT(committee_id) as missing_committee,
    COUNT(*) - COUNT(date) as missing_date
FROM transparency_contribution;

\echo ''

-- ============================================================================
-- SECTION 9: EXPENDITURES ANALYSIS (IE SPENDING)
-- ============================================================================
\echo '9. INDEPENDENT EXPENDITURES ANALYSIS'
\echo '====================================='
\echo ''

\echo '→ IE Expenditures by Year:'
SELECT 
    COALESCE(year::text, 'Unknown') as year,
    COUNT(*) as expenditure_count,
    SUM(amount) as total_amount,
    AVG(amount) as avg_amount
FROM transparency_expenditure
GROUP BY year
ORDER BY year DESC;

\echo ''
\echo '→ Sample IE Expenditures:'
SELECT 
    e.id,
    ie.name as ie_committee,
    c.name as candidate,
    e.amount,
    e.date,
    e.purpose
FROM transparency_expenditure e
LEFT JOIN transparency_iecommittee ie ON e.ie_committee_id = ie.id
LEFT JOIN transparency_candidate c ON e.candidate_id = c.id
ORDER BY e.amount DESC
LIMIT 10;

\echo ''
\echo '→ IE Expenditures with Missing Links:'
SELECT 
    COUNT(*) as total,
    COUNT(*) - COUNT(ie_committee_id) as missing_committee,
    COUNT(*) - COUNT(candidate_id) as missing_candidate,
    COUNT(*) - COUNT(date) as missing_date
FROM transparency_expenditure;

\echo ''

-- ============================================================================
-- SECTION 10: DATA INTEGRITY CHECKS
-- ============================================================================
\echo '10. DATA INTEGRITY CHECKS'
\echo '========================='
\echo ''

\echo '→ Orphaned Records Check:'
\echo '  Candidates without race:'
SELECT COUNT(*) as count FROM transparency_candidate WHERE race_id IS NULL;

\echo '  Candidates without party:'
SELECT COUNT(*) as count FROM transparency_candidate WHERE party_id IS NULL;

\echo '  Contributions without donor:'
SELECT COUNT(*) as count FROM transparency_contribution WHERE donor_id IS NULL;

\echo '  Contributions without committee:'
SELECT COUNT(*) as count FROM transparency_contribution WHERE committee_id IS NULL;

\echo '  Expenditures without IE committee:'
SELECT COUNT(*) as count FROM transparency_expenditure WHERE ie_committee_id IS NULL;

\echo '  Expenditures without candidate:'
SELECT COUNT(*) as count FROM transparency_expenditure WHERE candidate_id IS NULL;

\echo ''

-- ============================================================================
-- SECTION 11: MAPPING VERIFICATION - SPOT CHECK
-- ============================================================================
\echo '11. MAPPING VERIFICATION - SPOT CHECK'
\echo '====================================='
\echo ''

\echo '→ Sample Candidate with Full Source Trace:'
SELECT 
    'Application Data' as data_level,
    c.id as app_id,
    c.name as app_name,
    c.source,
    c.external_id
FROM transparency_candidate c
WHERE c.source_mdb_committee_id IS NOT NULL
LIMIT 1

UNION ALL

SELECT 
    'MDB Committee',
    mc."CommitteeID",
    NULL,
    NULL,
    'committee_' || mc."CommitteeID"
FROM transparency_candidate c
JOIN mdb_committees mc ON c.source_mdb_committee_id = mc."CommitteeID"
WHERE c.source_mdb_committee_id IS NOT NULL
LIMIT 1

UNION ALL

SELECT 
    'MDB Candidate Name',
    mn."NameID",
    mn."FirstName" || ' ' || mn."LastName",
    NULL,
    NULL
FROM transparency_candidate c
JOIN mdb_names mn ON c.source_mdb_candidate_name_id = mn."NameID"
WHERE c.source_mdb_candidate_name_id IS NOT NULL
LIMIT 1;

\echo ''

-- ============================================================================
-- SECTION 12: SUMMARY STATISTICS
-- ============================================================================
\echo '12. FINAL SUMMARY STATISTICS'
\echo '============================'
\echo ''

\echo '→ Overall Data Summary:'
SELECT 
    'Total Raw Names' as metric,
    COUNT(*)::text as value
FROM mdb_names

UNION ALL

SELECT 
    'Total Raw Committees',
    COUNT(*)::text
FROM mdb_committees

UNION ALL

SELECT 
    'Total Raw Transactions',
    COUNT(*)::text
FROM mdb_transactions

UNION ALL

SELECT 
    'Total Mapped Candidates',
    COUNT(*)::text
FROM transparency_candidate

UNION ALL

SELECT 
    'Total Mapped IE Committees',
    COUNT(*)::text
FROM transparency_iecommittee

UNION ALL

SELECT 
    'Total Mapped Donors',
    COUNT(*)::text
FROM transparency_donorentity

UNION ALL

SELECT 
    'Total Mapped Contributions',
    COUNT(*)::text
FROM transparency_contribution

UNION ALL

SELECT 
    'Total Mapped IE Expenditures',
    COUNT(*)::text
FROM transparency_expenditure

UNION ALL

SELECT 
    'Total Contribution Amount',
    '$' || TO_CHAR(SUM(amount), 'FM999,999,999,999.00')
FROM transparency_contribution

UNION ALL

SELECT 
    'Total IE Expenditure Amount',
    '$' || TO_CHAR(SUM(amount), 'FM999,999,999,999.00')
FROM transparency_expenditure;

\echo ''
\echo '======================================================================='
\echo 'END OF DATABASE INSPECTION REPORT'
\echo '======================================================================='