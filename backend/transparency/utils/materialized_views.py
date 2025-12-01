# transparency/utils/materialized_views.py
from django.db import connection
from django.db.models import Sum, Count
from django.core.management.base import BaseCommand
import logging

logger = logging.getLogger(__name__)

class MaterializedViewManager:
    @staticmethod
    def create_dashboard_mv():
        """Create materialized view for dashboard aggregations"""
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS dashboard_aggregations AS
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
                    (SELECT COUNT(*) FROM candidate_soi WHERE pledge_received = true) as soi_pledged
                """)
    
    @staticmethod
    def create_race_ie_mv():
        """Create materialized view for race-level IE spending"""
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS race_ie_spending AS
                SELECT 
                    c.office_id,
                    o.name as office_name,
                    cy.cycle_id,
                    cy.name as cycle_name,
                    t.subject_committee_id,
                    sc.name_id as candidate_name_id,
                    t.is_for_benefit,
                    SUM(t.amount) as total_ie,
                    COUNT(t.transaction_id) as transaction_count
                FROM "Transactions" t
                JOIN "Committees" c ON t.subject_committee_id = c.committee_id
                JOIN "Offices" o ON c.candidate_office_id = o.office_id
                JOIN "Cycles" cy ON c.election_cycle_id = cy.cycle_id
                JOIN "Committees" sc ON t.subject_committee_id = sc.committee_id
                WHERE t.deleted = false AND t.subject_committee_id IS NOT NULL
                GROUP BY c.office_id, o.name, cy.cycle_id, cy.name, t.subject_committee_id, sc.name_id, t.is_for_benefit
            """)
    
    @staticmethod
    def refresh_all_views():
        """Refresh all materialized views"""
        with connection.cursor() as cursor:
            cursor.execute("REFRESH MATERIALIZED VIEW dashboard_aggregations")
            cursor.execute("REFRESH MATERIALIZED VIEW race_ie_spending")
            cursor.execute("REFRESH MATERIALIZED VIEW top_donors_mv")
        logger.info("All materialized views refreshed")

# Add to views.py - Update dashboard endpoints to use materialized views
@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_summary_optimized(request):
    """OPTIMIZED: Use materialized view for dashboard data"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM dashboard_aggregations")
            row = cursor.fetchone()
            
        if row:
            data = {
                'total_ie_spending': float(row[0] or 0),
                'candidate_committees': row[1] or 0,
                'num_expenditures': row[2] or 0,
                'soi_tracking': {
                    'total': row[3] or 0,
                    'uncontacted': row[4] or 0,
                    'pledged': row[5] or 0
                },
                'last_updated': timezone.now().isoformat(),
                'cached': False  # From MV, not cache
            }
            return Response(data)
    except Exception as e:
        logger.error(f"Materialized view error: {e}")
        # Fallback to original query
        return dashboard_summary_optimized(request)


@staticmethod
def create_benefit_breakdown_mv():
    """Create materialized view for IE benefit breakdown"""
    with connection.cursor() as cursor:
        cursor.execute("""
            CREATE MATERIALIZED VIEW IF NOT EXISTS ie_benefit_breakdown AS
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
            GROUP BY is_for_benefit
        """)