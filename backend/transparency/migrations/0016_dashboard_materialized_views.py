# Generated migration for dashboard materialized views
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('transparency', '0015_merge_20251129_1334'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE MATERIALIZED VIEW IF NOT EXISTS mv_dashboard_top_donors AS
            SELECT 
                n.name_id as entity_id,
                CONCAT(COALESCE(n.first_name, ''), ' ', COALESCE(n.last_name, '')) as entity_name,
                COALESCE(et.name, 'Unknown') as entity_type,
                SUM(ABS(t.amount)) as total_contributed,
                COUNT(t.transaction_id) as contribution_count
            FROM "Names" n
            LEFT JOIN "EntityTypes" et ON n.entity_type_id = et.entity_type_id
            INNER JOIN "Transactions" t ON t.entity_id = n.name_id
            INNER JOIN "TransactionTypes" tt ON t.transaction_type_id = tt.transaction_type_id
            WHERE tt.income_expense_neutral = 1
                AND t.deleted = FALSE
            GROUP BY n.name_id, n.first_name, n.last_name, et.name
            ORDER BY total_contributed DESC
            LIMIT 10;
            
            CREATE UNIQUE INDEX IF NOT EXISTS mv_dashboard_top_donors_idx 
            ON mv_dashboard_top_donors(entity_id);
            """,
            reverse_sql="DROP MATERIALIZED VIEW IF EXISTS mv_dashboard_top_donors CASCADE;"
        ),
        
        migrations.RunSQL(
            sql="""
            CREATE MATERIALIZED VIEW IF NOT EXISTS mv_dashboard_top_ie_committees AS
            SELECT 
                c.committee_id as committee_id,
                CONCAT(COALESCE(n.first_name, ''), ' ', COALESCE(n.last_name, '')) as committee_name,
                SUM(ABS(t.amount)) as total_spent,
                COUNT(t.transaction_id) as expenditure_count
            FROM "Committees" c
            INNER JOIN "Names" n ON c.name_id = n.name_id
            INNER JOIN "Transactions" t ON t.committee_id = c.committee_id
            WHERE t.subject_committee_id IS NOT NULL
                AND t.deleted = FALSE
            GROUP BY c.committee_id, n.first_name, n.last_name
            ORDER BY total_spent DESC
            LIMIT 10;
            
            CREATE UNIQUE INDEX IF NOT EXISTS mv_dashboard_top_ie_committees_idx 
            ON mv_dashboard_top_ie_committees(committee_id);
            """,
            reverse_sql="DROP MATERIALIZED VIEW IF EXISTS mv_dashboard_top_ie_committees CASCADE;"
        ),
        
        migrations.RunSQL(
            sql="""
            CREATE MATERIALIZED VIEW IF NOT EXISTS mv_dashboard_support_oppose AS
            SELECT 
                SUM(CASE WHEN t.is_for_benefit = TRUE THEN ABS(t.amount) ELSE 0 END) as total_for_benefit,
                SUM(CASE WHEN t.is_for_benefit = FALSE THEN ABS(t.amount) ELSE 0 END) as total_not_for_benefit,
                COUNT(CASE WHEN t.is_for_benefit = TRUE THEN 1 END) as count_for_benefit,
                COUNT(CASE WHEN t.is_for_benefit = FALSE THEN 1 END) as count_not_for_benefit
            FROM "Transactions" t
            WHERE t.subject_committee_id IS NOT NULL
                AND t.is_for_benefit IS NOT NULL
                AND t.deleted = FALSE;
            """,
            reverse_sql="DROP MATERIALIZED VIEW IF EXISTS mv_dashboard_support_oppose CASCADE;"
        ),
        
        migrations.RunSQL(
            sql="""
            CREATE MATERIALIZED VIEW IF NOT EXISTS mv_dashboard_recent_expenditures AS
            SELECT 
                t.transaction_id as id,
                t.amount as amount,
                t.transaction_date as expenditure_date,
                t.memo as purpose,
                t.is_for_benefit as is_for_benefit,
                CONCAT(COALESCE(cn.first_name, ''), ' ', COALESCE(cn.last_name, '')) as committee_name,
                CONCAT(COALESCE(scn.first_name, ''), ' ', COALESCE(scn.last_name, '')) as subject_committee_name,
                CONCAT(COALESCE(scn.first_name, ''), ' ', COALESCE(scn.last_name, '')) as candidate_name
            FROM "Transactions" t
            LEFT JOIN "Committees" c ON t.committee_id = c.committee_id
            LEFT JOIN "Names" cn ON c.name_id = cn.name_id
            LEFT JOIN "Committees" sc ON t.subject_committee_id = sc.committee_id
            LEFT JOIN "Names" scn ON sc.name_id = scn.name_id
            WHERE t.subject_committee_id IS NOT NULL
                AND t.deleted = FALSE
            ORDER BY t.transaction_date DESC NULLS LAST, t.transaction_id DESC
            LIMIT 50;
            
            CREATE INDEX IF NOT EXISTS mv_dashboard_recent_expenditures_date_idx 
            ON mv_dashboard_recent_expenditures(expenditure_date DESC NULLS LAST);
            """,
            reverse_sql="DROP MATERIALIZED VIEW IF EXISTS mv_dashboard_recent_expenditures CASCADE;"
        ),
    ]
