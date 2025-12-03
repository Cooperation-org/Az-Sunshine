from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('transparency', '0017_transaction_dashboard_indexes'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE MATERIALIZED VIEW IF NOT EXISTS mv_donor_stats AS
                SELECT
                    n.name_id,
                    n.first_name || ' ' || n.last_name as full_name,
                    COALESCE(SUM(t.amount), 0) as total_contribution,
                    COUNT(t.transaction_id) as num_contributions,
                    COUNT(DISTINCT t.committee_id) as linked_committees
                FROM "Names" n
                LEFT JOIN "Transactions" t ON t.entity_id = n.name_id
                    AND t.transaction_type_id IN (
                        SELECT transaction_type_id
                        FROM "TransactionTypes"
                        WHERE income_expense_neutral = 1
                    )
                    AND t.deleted = FALSE
                GROUP BY n.name_id, n.first_name, n.last_name;

                CREATE INDEX IF NOT EXISTS idx_mv_donor_stats_name_id
                    ON mv_donor_stats(name_id);

                CREATE INDEX IF NOT EXISTS idx_mv_donor_stats_total
                    ON mv_donor_stats(total_contribution DESC);
            """,
            reverse_sql="""
                DROP MATERIALIZED VIEW IF EXISTS mv_donor_stats CASCADE;
            """
        ),
    ]
