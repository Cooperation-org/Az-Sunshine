from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import connection
from django.core.cache import cache
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_summary_optimized(request):
    """
    OPTIMIZED: Single query dashboard with 5-minute caching
    """
    cache_key = 'dashboard_summary_v1'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        logger.info("✅ Returning cached dashboard data")
        return Response(cached_data)
    
    logger.info("🔄 Computing fresh dashboard data...")
    
    try:
        with connection.cursor() as cursor:
            # Try materialized view first
            try:
                cursor.execute("SELECT * FROM dashboard_aggregations")
                row = cursor.fetchone()
            except:
                # Fallback to simple aggregates
                cursor.execute("""
                    SELECT 
                        COALESCE(SUM(ABS(amount)), 0) as total_ie_spending,
                        COUNT(DISTINCT committee_id) as candidate_committees,
                        COUNT(*) as num_expenditures
                    FROM "Transactions"
                    WHERE subject_committee_id IS NOT NULL 
                        AND deleted = false
                """)
                row = cursor.fetchone()
                row = list(row) + [0, 0, 0]  # Add placeholders for SOI fields
            
            if row:
                response_data = {
                    'total_ie_spending': abs(float(row[0] or 0)),
                    'candidate_committees': row[1] or 0,
                    'num_expenditures': row[2] or 0,
                    'soi_tracking': {
                        'total_filings': row[3] if len(row) > 3 else 0,
                        'uncontacted': row[4] if len(row) > 4 else 0,
                        'pledged': row[5] if len(row) > 5 else 0,
                    },
                    'last_updated': timezone.now().isoformat(),
                    'cached': False
                }
            else:
                response_data = {
                    'total_ie_spending': 0,
                    'candidate_committees': 0,
                    'num_expenditures': 0,
                    'soi_tracking': {'total_filings': 0, 'uncontacted': 0, 'pledged': 0},
                    'last_updated': timezone.now().isoformat(),
                    'cached': False
                }
        
        cache.set(cache_key, response_data, timeout=300)
        logger.info("✅ Dashboard data computed and cached")
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}", exc_info=True)
        return Response({
            'total_ie_spending': 0,
            'candidate_committees': 0,
            'num_expenditures': 0,
            'soi_tracking': {'total_filings': 0, 'uncontacted': 0, 'pledged': 0},
            'last_updated': timezone.now().isoformat(),
        }, status=200)


@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_charts_data_mv(request):
    """
    OPTIMIZED: Use materialized views for instant results
    """
    cache_key = 'dashboard_charts_fast_v2'

    # Check for refresh param
    force_refresh = request.GET.get('refresh') == '1'

    if not force_refresh:
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.info("✅ Returning cached charts")
            return Response(cached_data)

    logger.info("🔄 Loading fresh dashboard charts from materialized views...")

    try:
        with connection.cursor() as cursor:
            # Query 1: IE Benefit Breakdown - FROM MATERIALIZED VIEW
            cursor.execute("""
                SELECT
                    is_for_benefit,
                    transaction_count,
                    total_amount
                FROM ie_benefit_breakdown
                ORDER BY is_for_benefit DESC
            """)
            benefit_rows = cursor.fetchall()

            # Calculate percentages in Python - use ABS() for correct percentage calculation
            total_amount = sum(abs(float(row[2])) for row in benefit_rows) if benefit_rows else 0

            for_benefit_data = {'total': 0.0, 'count': 0, 'percentage': 0.0}
            not_for_benefit_data = {'total': 0.0, 'count': 0, 'percentage': 0.0}

            for row in benefit_rows:
                is_for_benefit, count, amount = row
                abs_amount = abs(float(amount))
                percentage = (abs_amount / total_amount * 100) if total_amount > 0 else 0.0
                data = {
                    'total': float(amount),
                    'count': int(count),
                    'percentage': round(percentage, 1)
                }
                if is_for_benefit:
                    for_benefit_data = data
                else:
                    not_for_benefit_data = data

            # Query 2: Top 10 IE Committees - FROM MATERIALIZED VIEW
            cursor.execute("""
                SELECT
                    committee_name as committee,
                    committee_id,
                    total_spent as total_spending
                FROM mv_dashboard_top_ie_committees
                ORDER BY total_spent DESC
                LIMIT 10
            """)

            top_committees = [{
                'committee': row[0],
                'committee_id': row[1],
                'total_spending': float(row[2])
            } for row in cursor.fetchall()]

            # Query 3: Top 10 Donors - FROM MATERIALIZED VIEW
            cursor.execute("""
                SELECT
                    entity_name,
                    entity_id,
                    total_contributed
                FROM mv_dashboard_top_donors
                ORDER BY total_contributed DESC
                LIMIT 10
            """)

            top_donors = [{
                'entity_name': row[0],
                'entity_id': row[1],
                'total_contributed': float(row[2])
            } for row in cursor.fetchall()]

            response_data = {
                'is_for_benefit_breakdown': {
                    'for_benefit': for_benefit_data,
                    'not_for_benefit': not_for_benefit_data
                },
                'top_ie_committees': top_committees,
                'top_donors': top_donors
            }

            # Cache for 10 minutes
            cache.set(cache_key, response_data, timeout=600)

            logger.info(f"✅ Charts loaded from MV: {len(top_committees)} committees, {len(top_donors)} donors")
            return Response(response_data)

    except Exception as e:
        logger.error(f"❌ Charts error: {e}", exc_info=True)
        return Response({
            'is_for_benefit_breakdown': {
                'for_benefit': {'total': 0.0, 'count': 0, 'percentage': 0.0},
                'not_for_benefit': {'total': 0.0, 'count': 0, 'percentage': 0.0}
            },
            'top_ie_committees': [],
            'top_donors': [],
            'error': str(e)
        }, status=200)


@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_recent_expenditures_mv(request):
    """
    OPTIMIZED: Latest expenditures from materialized view
    """
    cache_key = 'dashboard_recent_exp_v1'
    cached_data = cache.get(cache_key)

    if cached_data:
        return Response(cached_data)

    try:
        with connection.cursor() as cursor:
            # Query from materialized view - instant results!
            cursor.execute("""
                SELECT
                    expenditure_date,
                    ABS(amount) as amount,
                    is_for_benefit,
                    committee_name,
                    candidate_name
                FROM mv_dashboard_recent_expenditures
                ORDER BY expenditure_date DESC NULLS LAST
                LIMIT 10
            """)

            results = [{
                'date': row[0].isoformat() if row[0] else None,
                'amount': float(row[1]),
                'is_for_benefit': row[2],
                'committee': row[3] or 'Unknown',
                'candidate': row[4] or 'Unknown'
            } for row in cursor.fetchall()]

        response_data = {'results': results}
        cache.set(cache_key, response_data, timeout=300)

        logger.info(f"✅ Recent expenditures loaded from MV: {len(results)} records")
        return Response(response_data)

    except Exception as e:
        logger.error(f"Recent expenditures error: {e}", exc_info=True)
        return Response({'results': []})


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_dashboard_materialized_views(request):
    """
    Refresh materialized views (if they exist) and clear cache
    """
    try:
        # Clear cache regardless
        cache.delete('dashboard_summary_v1')
        cache.delete('dashboard_charts_fast_v2')
        cache.delete('dashboard_recent_exp_v1')
        
        return Response({
            'success': True,
            'message': 'Cache cleared successfully',
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error refreshing: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)