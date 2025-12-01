from django.core.management.base import BaseCommand
from django.db import connection
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Create all dashboard materialized views'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔄 Creating dashboard materialized views...'))
        
        try:
            with connection.cursor() as cursor:
                # 1. Create IE Benefit Breakdown View
                self.stdout.write('Creating ie_benefit_breakdown...')
                cursor.execute("""
                    DROP MATERIALIZED VIEW IF EXISTS ie_benefit_breakdown CASCADE;
                    
                    CREATE MATERIALIZED VIEW ie_benefit_breakdown AS
                    SELECT 
                        is_for_benefit,
                        COUNT(*) as transaction_count,
                        COALESCE(SUM(amount), 0) as total_amount,
                        ROUND(
                            100.0 * COALESCE(SUM(amount), 0) / NULLIF(
                                (SELECT SUM(amount) FROM "Transactions" 
                                 WHERE subject_committee_id IS NOT NULL AND deleted = false), 
                                0
                            ), 
                            1
                        ) as percentage
                    FROM "Transactions"
                    WHERE subject_committee_id IS NOT NULL 
                        AND deleted = false
                        AND is_for_benefit IS NOT NULL
                    GROUP BY is_for_benefit;
                    
                    CREATE UNIQUE INDEX idx_ie_benefit_unique ON ie_benefit_breakdown(is_for_benefit);
                """)
                self.stdout.write(self.style.SUCCESS('  ✅ ie_benefit_breakdown created'))
                
                # 2. Create Top IE Committees View (if not exists)
                self.stdout.write('Creating top_ie_committees_mv...')
                cursor.execute("""
                    DROP MATERIALIZED VIEW IF EXISTS top_ie_committees_mv CASCADE;
                    
                    CREATE MATERIALIZED VIEW top_ie_committees_mv AS
                    SELECT 
                        c.committee_id,
                        COALESCE(n.last_name || ', ' || n.first_name, n.last_name, 'Unknown') as committee,
                        COALESCE(SUM(t.amount), 0) as total_spending,
                        COUNT(t.transaction_id) as transaction_count
                    FROM "Committees" c
                    LEFT JOIN "Names" n ON c.name_id = n.name_id
                    LEFT JOIN "Transactions" t ON c.committee_id = t.committee_id
                    WHERE t.subject_committee_id IS NOT NULL 
                        AND t.deleted = false
                    GROUP BY c.committee_id, n.last_name, n.first_name
                    HAVING COUNT(t.transaction_id) > 0
                    ORDER BY total_spending DESC;
                    
                    CREATE UNIQUE INDEX idx_top_committees_unique ON top_ie_committees_mv(committee_id);
                """)
                self.stdout.write(self.style.SUCCESS('  ✅ top_ie_committees_mv created'))
                
                # 3. Create Top Donors View (if not exists)
                self.stdout.write('Creating top_donors_mv...')
                cursor.execute("""
                    DROP MATERIALIZED VIEW IF EXISTS top_donors_mv CASCADE;
                    
                    CREATE MATERIALIZED VIEW top_donors_mv AS
                    SELECT 
                        e.name_id as entity_id,
                        COALESCE(e.last_name || ', ' || e.first_name, e.last_name, 'Unknown') as entity_name,
                        COALESCE(SUM(t.amount), 0) as total_contributed,
                        COUNT(t.transaction_id) as contribution_count
                    FROM "Names" e
                    LEFT JOIN "Transactions" t ON e.name_id = t.entity_id
                    LEFT JOIN "TransactionTypes" tt ON t.transaction_type_id = tt.transaction_type_id
                    WHERE tt.income_expense_neutral = 1  -- Contributions only
                        AND t.deleted = false
                    GROUP BY e.name_id, e.last_name, e.first_name
                    HAVING COUNT(t.transaction_id) > 0
                    ORDER BY total_contributed DESC;
                    
                    CREATE UNIQUE INDEX idx_top_donors_unique ON top_donors_mv(entity_id);
                """)
                self.stdout.write(self.style.SUCCESS('  ✅ top_donors_mv created'))
                
                # 4. Create Dashboard Aggregations View
                self.stdout.write('Creating dashboard_aggregations...')
                cursor.execute("""
                    DROP MATERIALIZED VIEW IF EXISTS dashboard_aggregations CASCADE;
                    
                    CREATE MATERIALIZED VIEW dashboard_aggregations AS
                    SELECT 
                        -- IE Spending totals
                        (SELECT COALESCE(SUM(amount), 0) 
                         FROM "Transactions" 
                         WHERE subject_committee_id IS NOT NULL AND deleted = false) as total_ie_spending,
                        
                        -- Candidate counts
                        (SELECT COUNT(*) FROM "Committees" WHERE candidate_id IS NOT NULL) as candidate_committees,
                        
                        -- IE transaction count
                        (SELECT COUNT(*) FROM "Transactions" 
                         WHERE subject_committee_id IS NOT NULL AND deleted = false) as num_expenditures,
                        
                        -- SOI stats
                        (SELECT COUNT(*) FROM candidate_soi) as soi_total,
                        (SELECT COUNT(*) FROM candidate_soi WHERE contact_status = 'uncontacted') as soi_uncontacted,
                        (SELECT COUNT(*) FROM candidate_soi WHERE pledge_received = true) as soi_pledged;
                    
                    CREATE UNIQUE INDEX idx_dashboard_agg_unique ON dashboard_aggregations((1));
                """)
                self.stdout.write(self.style.SUCCESS('  ✅ dashboard_aggregations created'))
                
            self.stdout.write(self.style.SUCCESS('\n✅ All materialized views created successfully!'))
            self.stdout.write('\n📊 View summary:')
            
            # Show row counts
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM ie_benefit_breakdown")
                count = cursor.fetchone()[0]
                self.stdout.write(f'  • ie_benefit_breakdown: {count} rows')
                
                cursor.execute("SELECT COUNT(*) FROM top_ie_committees_mv")
                count = cursor.fetchone()[0]
                self.stdout.write(f'  • top_ie_committees_mv: {count} rows')
                
                cursor.execute("SELECT COUNT(*) FROM top_donors_mv")
                count = cursor.fetchone()[0]
                self.stdout.write(f'  • top_donors_mv: {count} rows')
                
                cursor.execute("SELECT COUNT(*) FROM dashboard_aggregations")
                count = cursor.fetchone()[0]
                self.stdout.write(f'  • dashboard_aggregations: {count} row')
            
            self.stdout.write('\n💡 Run "python manage.py refresh_dashboard_views" to update data')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error creating views: {e}'))
            logger.error(f"Error creating materialized views: {e}", exc_info=True)
            raise