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
            cursor.execute("SELECT * FROM dashboard_aggregations")
            row = cursor.fetchone()
            
            if row:
                response_data = {
                    'total_ie_spending': abs(float(row[0] or 0)),  # Use abs() for negative values
                    'candidate_committees': row[1] or 0,
                    'num_expenditures': row[2] or 0,
                    'soi_tracking': {
                        'total_filings': row[3] or 0,
                        'uncontacted': row[4] or 0,
                        'pledged': row[5] or 0,
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
    OPTIMIZED: Fetch dashboard charts data from materialized views
    FIXED: Handle negative amounts with abs()
    WITH FALLBACK: Use regular queries if materialized views don't exist
    """
    cache_key = 'dashboard_charts_mv_v1'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        logger.info("✅ Returning cached dashboard charts (MV)")
        return Response(cached_data)
    
    logger.info("🔄 Loading fresh dashboard charts from materialized views...")
    
    try:
        with connection.cursor() as cursor:
            # IE Benefit Breakdown - Try MV first, fallback to query
            try:
                cursor.execute("""
                    SELECT 
                        is_for_benefit,
                        transaction_count,
                        ABS(total_amount) as total_amount,
                        percentage
                    FROM ie_benefit_breakdown
                    ORDER BY is_for_benefit DESC
                """)
                benefit_rows = cursor.fetchall()
            except Exception as mv_error:
                logger.warning(f"⚠️ MV not found, using fallback query: {mv_error}")
                cursor.execute("""
                    SELECT 
                        is_for_benefit,
                        COUNT(*) as transaction_count,
                        ABS(COALESCE(SUM(amount), 0)) as total_amount,
                        ROUND(
                            100.0 * COALESCE(SUM(ABS(amount)), 0) / NULLIF(
                                (SELECT SUM(ABS(amount)) FROM "Transactions" 
                                 WHERE subject_committee_id IS NOT NULL AND deleted = false AND is_for_benefit IS NOT NULL), 
                                0
                            ), 
                            1
                        ) as percentage
                    FROM "Transactions"
                    WHERE subject_committee_id IS NOT NULL 
                        AND deleted = false
                        AND is_for_benefit IS NOT NULL
                    GROUP BY is_for_benefit
                    ORDER BY is_for_benefit DESC
                """)
                benefit_rows = cursor.fetchall()
            
            # Initialize with zeros
            for_benefit_data = {'total': 0, 'count': 0, 'percentage': 0}
            not_for_benefit_data = {'total': 0, 'count': 0, 'percentage': 0}
            
            # Process results
            for row in benefit_rows:
                is_for_benefit, count, total, percentage = row
                data = {
                    'total': float(total or 0),
                    'count': int(count or 0),
                    'percentage': float(percentage or 0)
                }
                
                if is_for_benefit:
                    for_benefit_data = data
                else:
                    not_for_benefit_data = data
            
            logger.info(f"📊 For Benefit: ${for_benefit_data['total']:,.2f} ({for_benefit_data['percentage']}%)")
            logger.info(f"📊 Not For Benefit: ${not_for_benefit_data['total']:,.2f} ({not_for_benefit_data['percentage']}%)")
            
            # Top 10 IE Committees - Try MV first, fallback to query
            try:
                cursor.execute("""
                    SELECT 
                        committee,
                        committee_id,
                        ABS(total_spending) as total_spending
                    FROM top_ie_committees_mv
                    ORDER BY ABS(total_spending) DESC
                    LIMIT 10
                """)
                top_committees = []
                for row in cursor.fetchall():
                    top_committees.append({
                        'committee': row[0],
                        'committee_id': row[1],
                        'total_spending': float(row[2] or 0)
                    })
            except Exception as mv_error:
                logger.warning(f"⚠️ MV not found, using fallback query: {mv_error}")
                cursor.execute("""
                    SELECT 
                        COALESCE(n.last_name || ', ' || n.first_name, n.last_name, 'Unknown') as committee,
                        c.committee_id,
                        ABS(COALESCE(SUM(t.amount), 0)) as total_spending
                    FROM "Committees" c
                    LEFT JOIN "Names" n ON c.name_id = n.name_id
                    LEFT JOIN "Transactions" t ON c.committee_id = t.committee_id
                    WHERE t.subject_committee_id IS NOT NULL 
                        AND t.deleted = false
                    GROUP BY c.committee_id, n.last_name, n.first_name
                    HAVING COUNT(t.transaction_id) > 0
                    ORDER BY ABS(COALESCE(SUM(t.amount), 0)) DESC
                    LIMIT 10
                """)
                top_committees = []
                for row in cursor.fetchall():
                    top_committees.append({
                        'committee': row[0],
                        'committee_id': row[1],
                        'total_spending': float(row[2] or 0)
                    })
            
            # Top 10 Donors - Try MV first, fallback to query
            try:
                cursor.execute("""
                    SELECT 
                        entity_name,
                        entity_id,
                        ABS(total_contributed) as total_contributed
                    FROM top_donors_mv
                    ORDER BY ABS(total_contributed) DESC
                    LIMIT 10
                """)
                top_donors = []
                for row in cursor.fetchall():
                    top_donors.append({
                        'entity_name': row[0],
                        'entity_id': row[1],
                        'total_contributed': float(row[2] or 0)
                    })
            except Exception as mv_error:
                logger.warning(f"⚠️ MV not found, using fallback query: {mv_error}")
                cursor.execute("""
                    SELECT 
                        COALESCE(e.last_name || ', ' || e.first_name, e.last_name, 'Unknown') as entity_name,
                        e.name_id as entity_id,
                        ABS(COALESCE(SUM(t.amount), 0)) as total_contributed
                    FROM "Names" e
                    LEFT JOIN "Transactions" t ON e.name_id = t.entity_id
                    LEFT JOIN "TransactionTypes" tt ON t.transaction_type_id = tt.transaction_type_id
                    WHERE tt.income_expense_neutral = 1  -- Contributions only
                        AND t.deleted = false
                    GROUP BY e.name_id, e.last_name, e.first_name
                    HAVING COUNT(t.transaction_id) > 0
                    ORDER BY ABS(COALESCE(SUM(t.amount), 0)) DESC
                    LIMIT 10
                """)
                top_donors = []
                for row in cursor.fetchall():
                    top_donors.append({
                        'entity_name': row[0],
                        'entity_id': row[1],
                        'total_contributed': float(row[2] or 0)
                    })
            
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
            
            logger.info(f"✅ Dashboard charts loaded - {len(top_committees)} committees, {len(top_donors)} donors")
            return Response(response_data)
            
    except Exception as e:
        logger.error(f"❌ Error loading dashboard charts: {e}", exc_info=True)
        return Response({
            'is_for_benefit_breakdown': {
                'for_benefit': {'total': 0, 'count': 0, 'percentage': 0},
                'not_for_benefit': {'total': 0, 'count': 0, 'percentage': 0}
            },
            'top_ie_committees': [],
            'top_donors': []
        })


@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_recent_expenditures_mv(request):
    """
    OPTIMIZED: Latest 10 expenditures with minimal data
    FIXED: Handle negative amounts
    """
    cache_key = 'dashboard_recent_exp_v1'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return Response(cached_data)
    
    try:
        with connection.cursor() as cursor:
            # FIXED: Use ABS() for amounts
            cursor.execute("""
                SELECT 
                    t.transaction_date,
                    ABS(t.amount) as amount,
                    t.is_for_benefit,
                    cn.last_name || COALESCE(', ' || cn.first_name, '') as committee_name,
                    sn.last_name || COALESCE(', ' || sn.first_name, '') as candidate_name
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
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'date': row[0].isoformat() if row[0] else None,
                    'amount': float(row[1] or 0),
                    'is_for_benefit': row[2],
                    'committee': row[3] or 'Unknown',
                    'candidate': row[4] or 'Unknown'
                })
        
        response_data = {'results': results}
        cache.set(cache_key, response_data, timeout=300)
        
        logger.info(f"✅ Loaded {len(results)} recent expenditures")
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Recent expenditures error: {e}", exc_info=True)
        return Response({'results': []})


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_dashboard_materialized_views(request):
    """
    Refresh all dashboard materialized views
    POST /api/v1/dashboard/refresh-mv/
    """
    try:
        with connection.cursor() as cursor:
            logger.info("🔄 Refreshing dashboard materialized views...")
            
            # Check if materialized views exist first
            cursor.execute("""
                SELECT matviewname 
                FROM pg_matviews 
                WHERE schemaname = 'public' 
                AND matviewname IN (
                    'dashboard_aggregations',
                    'ie_benefit_breakdown',
                    'top_donors_mv',
                    'top_ie_committees_mv'
                )
            """)
            existing_views = [row[0] for row in cursor.fetchall()]
            
            if not existing_views:
                logger.error("❌ No materialized views found. Run create_dashboard_views first.")
                return Response({
                    'success': False,
                    'error': 'Materialized views not found. Please create them first.',
                    'hint': 'Run: python manage.py create_dashboard_views'
                }, status=400)
            
            # Refresh existing views
            if 'dashboard_aggregations' in existing_views:
                cursor.execute('REFRESH MATERIALIZED VIEW CONCURRENTLY dashboard_aggregations')
            if 'ie_benefit_breakdown' in existing_views:
                cursor.execute('REFRESH MATERIALIZED VIEW CONCURRENTLY ie_benefit_breakdown')
            if 'top_donors_mv' in existing_views:
                cursor.execute('REFRESH MATERIALIZED VIEW CONCURRENTLY top_donors_mv')
            if 'top_ie_committees_mv' in existing_views:
                cursor.execute('REFRESH MATERIALIZED VIEW CONCURRENTLY top_ie_committees_mv')
            
            logger.info(f"✅ Refreshed {len(existing_views)} materialized views")
        
        # Clear cache
        cache.delete('dashboard_summary_v1')
        cache.delete('dashboard_charts_mv_v1')
        cache.delete('dashboard_recent_exp_v1')
        
        return Response({
            'success': True,
            'message': f'Refreshed {len(existing_views)} materialized views successfully',
            'views_refreshed': existing_views,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error refreshing views: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)