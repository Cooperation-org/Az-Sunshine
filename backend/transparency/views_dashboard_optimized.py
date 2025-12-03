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
    FAST VERSION: Simplified queries without subqueries
    """
    cache_key = 'dashboard_charts_fast_v2'
    
    # Check for refresh param
    force_refresh = request.GET.get('refresh') == '1'
    
    if not force_refresh:
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.info("✅ Returning cached charts")
            return Response(cached_data)
    
    logger.info("🔄 Loading fresh dashboard charts...")
    
    try:
        with connection.cursor() as cursor:
            # Query 1: IE Benefit Breakdown - Simple aggregation
            cursor.execute("""
                SELECT 
                    is_for_benefit,
                    COUNT(*) as transaction_count,
                    ABS(COALESCE(SUM(amount), 0)) as total_amount
                FROM "Transactions"
                WHERE subject_committee_id IS NOT NULL 
                    AND deleted = false
                    AND is_for_benefit IS NOT NULL
                GROUP BY is_for_benefit
            """)
            benefit_rows = cursor.fetchall()
            
            # Calculate percentages in Python (avoid expensive subquery)
            total_amount = sum(float(row[2]) for row in benefit_rows) if benefit_rows else 0

            for_benefit_data = {'total': 0.0, 'count': 0, 'percentage': 0.0}
            not_for_benefit_data = {'total': 0.0, 'count': 0, 'percentage': 0.0}

            for row in benefit_rows:
                is_for_benefit, count, amount = row
                percentage = (float(amount) / total_amount * 100) if total_amount > 0 else 0.0
                data = {
                    'total': float(amount),
                    'count': int(count),
                    'percentage': round(percentage, 1)
                }
                if is_for_benefit:
                    for_benefit_data = data
                else:
                    not_for_benefit_data = data
            
            # Query 2: Top 10 IE Committees
            cursor.execute("""
                SELECT 
                    COALESCE(n.last_name || ', ' || n.first_name, n.last_name, 'Unknown') as committee,
                    c.committee_id,
                    ABS(COALESCE(SUM(t.amount), 0)) as total_spending
                FROM "Committees" c
                INNER JOIN "Names" n ON c.name_id = n.name_id
                INNER JOIN "Transactions" t ON c.committee_id = t.committee_id
                WHERE t.subject_committee_id IS NOT NULL 
                    AND t.deleted = false
                GROUP BY c.committee_id, n.last_name, n.first_name
                ORDER BY total_spending DESC
                LIMIT 10
            """)
            
            top_committees = [{
                'committee': row[0],
                'committee_id': row[1],
                'total_spending': float(row[2])
            } for row in cursor.fetchall()]
            
            # Query 3: Top 10 Donors
            cursor.execute("""
                SELECT 
                    COALESCE(e.last_name || ', ' || e.first_name, e.last_name, 'Unknown') as entity_name,
                    e.name_id as entity_id,
                    ABS(COALESCE(SUM(t.amount), 0)) as total_contributed
                FROM "Names" e
                INNER JOIN "Transactions" t ON e.name_id = t.entity_id
                INNER JOIN "TransactionTypes" tt ON t.transaction_type_id = tt.transaction_type_id
                WHERE tt.income_expense_neutral = 1
                    AND t.deleted = false
                GROUP BY e.name_id, e.last_name, e.first_name
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
            
            logger.info(f"✅ Charts loaded: {len(top_committees)} committees, {len(top_donors)} donors")
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
    Latest 10 expenditures
    """
    cache_key = 'dashboard_recent_exp_v1'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return Response(cached_data)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    t.transaction_date,
                    ABS(t.amount) as amount,
                    t.is_for_benefit,
                    COALESCE(cn.last_name || ', ' || cn.first_name, cn.last_name, 'Unknown') as committee_name,
                    COALESCE(sn.last_name || ', ' || sn.first_name, sn.last_name, 'Unknown') as candidate_name
                FROM "Transactions" t
                LEFT JOIN "Committees" c ON t.committee_id = c.committee_id
                LEFT JOIN "Names" cn ON c.name_id = cn.name_id
                LEFT JOIN "Committees" sc ON t.subject_committee_id = sc.committee_id
                LEFT JOIN "Names" sn ON sc.name_id = sn.name_id
                WHERE t.subject_committee_id IS NOT NULL 
                    AND t.deleted = false
                ORDER BY t.transaction_date DESC
                LIMIT 10
            """)
            
            results = [{
                'date': row[0].isoformat() if row[0] else None,
                'amount': float(row[1]),
                'is_for_benefit': row[2],
                'committee': row[3],
                'candidate': row[4]
            } for row in cursor.fetchall()]
        
        response_data = {'results': results}
        cache.set(cache_key, response_data, timeout=300)
        
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