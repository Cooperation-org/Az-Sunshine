"""
Advanced Analytics API Views

Provides endpoints for:
1. User Journey Tracking
2. Candidate Interest Heatmap
3. Search Analytics
4. Referrer Intelligence
5. Engagement Scoring
6. Geographic Intelligence
7. Time-Based Patterns
8. API Usage Analytics
9. Content Performance
10. Alerts & Anomalies
"""

from django.db.models import Count, Avg, Sum, F, Q, Min, Max, ExpressionWrapper, FloatField, IntegerField, Case, When, Value
from django.db.models.functions import TruncDate, TruncHour, ExtractHour, ExtractWeekDay
from django.utils import timezone
from django.core.cache import cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.response import Response
from datetime import timedelta
from collections import defaultdict
from urllib.parse import urlparse
import re

from .models import (
    SiteVisit, UserSession, SearchQuery, CandidateView,
    ReferrerStats, APIUsage, ContentPerformance, AnomalyAlert,
    HourlyTrafficPattern, DailyAnalytics, Entity, Committee
)


# =============================================================================
# 1. USER JOURNEY TRACKING
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAdminUser])
def user_journeys(request):
    """
    Get user journey analytics including funnels and session paths.

    Query params:
    - days: Number of days to analyze (default: 30)
    - limit: Max sessions to return (default: 100)
    """
    days = int(request.GET.get('days', 30))
    limit = int(request.GET.get('limit', 100))
    since = timezone.now() - timedelta(days=days)

    # Get sessions with journey data
    sessions = UserSession.objects.filter(
        started_at__gte=since
    ).order_by('-started_at')[:limit]

    # Calculate funnel metrics
    total_sessions = UserSession.objects.filter(started_at__gte=since).count()
    bounced_sessions = UserSession.objects.filter(started_at__gte=since, is_bounced=True).count()
    engaged_sessions = UserSession.objects.filter(
        started_at__gte=since,
        engagement_score__in=['engaged', 'power_user']
    ).count()

    # Common paths analysis
    path_sequences = defaultdict(int)
    for session in sessions:
        if session.pages_visited and len(session.pages_visited) >= 2:
            # Get first 3 pages as a path
            path = ' → '.join(session.pages_visited[:3])
            path_sequences[path] += 1

    top_paths = sorted(path_sequences.items(), key=lambda x: -x[1])[:20]

    # Entry/Exit page analysis
    entry_pages = UserSession.objects.filter(
        started_at__gte=since,
        entry_page__isnull=False
    ).exclude(entry_page='').values('entry_page').annotate(
        count=Count('session_id')
    ).order_by('-count')[:10]

    exit_pages = UserSession.objects.filter(
        started_at__gte=since,
        exit_page__isnull=False
    ).exclude(exit_page='').values('exit_page').annotate(
        count=Count('session_id')
    ).order_by('-count')[:10]

    # Engagement distribution
    engagement_dist = UserSession.objects.filter(
        started_at__gte=since
    ).values('engagement_score').annotate(
        count=Count('session_id')
    ).order_by('engagement_score')

    return Response({
        'summary': {
            'total_sessions': total_sessions,
            'bounced_sessions': bounced_sessions,
            'bounce_rate': round((bounced_sessions / total_sessions * 100) if total_sessions > 0 else 0, 1),
            'engaged_sessions': engaged_sessions,
            'engagement_rate': round((engaged_sessions / total_sessions * 100) if total_sessions > 0 else 0, 1),
        },
        'top_paths': [{'path': p[0], 'count': p[1]} for p in top_paths],
        'entry_pages': list(entry_pages),
        'exit_pages': list(exit_pages),
        'engagement_distribution': list(engagement_dist),
        'recent_sessions': [
            {
                'session_id': s.session_id[:8] + '...',
                'pages_visited': s.pages_visited[:5] if s.pages_visited else [],
                'page_count': s.page_count,
                'duration_seconds': s.duration_seconds,
                'engagement_score': s.engagement_score,
                'entry_page': s.entry_page,
                'exit_page': s.exit_page,
                'referrer_domain': s.referrer_domain,
                'country': s.country,
                'device_type': s.device_type,
                'started_at': s.started_at.isoformat(),
            }
            for s in sessions[:20]
        ]
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def funnel_analysis(request):
    """
    Analyze conversion funnels.

    Query params:
    - days: Number of days (default: 30)
    - funnel: Predefined funnel name or custom comma-separated pages
    """
    days = int(request.GET.get('days', 30))
    funnel_name = request.GET.get('funnel', 'candidate_research')
    since = timezone.now() - timedelta(days=days)

    # Predefined funnels
    funnels = {
        'candidate_research': ['/', '/candidates', '/candidate/'],
        'ie_analysis': ['/', '/ie-spending', '/candidate/'],
        'search_to_profile': ['/', '/search', '/candidate/'],
    }

    funnel_steps = funnels.get(funnel_name, funnel_name.split(','))

    # Analyze funnel
    sessions = UserSession.objects.filter(started_at__gte=since)

    step_counts = []
    for i, step in enumerate(funnel_steps):
        count = 0
        for session in sessions:
            if session.pages_visited:
                # Check if any page in session starts with the step
                if any(p.startswith(step) or step in p for p in session.pages_visited):
                    # Also check if previous steps were completed
                    if i == 0:
                        count += 1
                    else:
                        prev_steps_done = all(
                            any(p.startswith(s) or s in p for p in session.pages_visited)
                            for s in funnel_steps[:i]
                        )
                        if prev_steps_done:
                            count += 1

        step_counts.append({
            'step': step,
            'count': count,
            'drop_off': step_counts[-1]['count'] - count if step_counts else 0,
            'conversion_rate': round((count / step_counts[0]['count'] * 100) if step_counts and step_counts[0]['count'] > 0 else 100, 1)
        })

    return Response({
        'funnel_name': funnel_name,
        'steps': step_counts,
        'overall_conversion': round((step_counts[-1]['count'] / step_counts[0]['count'] * 100) if step_counts and step_counts[0]['count'] > 0 else 0, 1)
    })


# =============================================================================
# 2. CANDIDATE INTEREST HEATMAP
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAdminUser])
def candidate_heatmap(request):
    """
    Get candidate interest heatmap data.

    Query params:
    - days: Number of days (default: 30)
    - limit: Max candidates (default: 50)
    """
    days = int(request.GET.get('days', 30))
    limit = int(request.GET.get('limit', 50))
    since = timezone.now() - timedelta(days=days)

    # Get top viewed candidates
    top_candidates = CandidateView.objects.filter(
        timestamp__gte=since
    ).values('candidate_name', 'district', 'office').annotate(
        views=Count('id'),
        unique_visitors=Count('visitor_id', distinct=True),
        avg_time=Avg('time_on_page'),
        ie_views=Count('id', filter=Q(viewed_ie_spending=True)),
    ).order_by('-views')[:limit]

    # Views by district
    by_district = CandidateView.objects.filter(
        timestamp__gte=since,
        district__isnull=False
    ).exclude(district='').values('district').annotate(
        views=Count('id'),
        unique_candidates=Count('candidate_name', distinct=True)
    ).order_by('-views')[:20]

    # Trending candidates (comparing this week vs last week)
    this_week = timezone.now() - timedelta(days=7)
    last_week_start = timezone.now() - timedelta(days=14)
    last_week_end = timezone.now() - timedelta(days=7)

    this_week_views = dict(
        CandidateView.objects.filter(
            timestamp__gte=this_week
        ).values('candidate_name').annotate(count=Count('id')).values_list('candidate_name', 'count')
    )

    last_week_views = dict(
        CandidateView.objects.filter(
            timestamp__gte=last_week_start,
            timestamp__lt=last_week_end
        ).values('candidate_name').annotate(count=Count('id')).values_list('candidate_name', 'count')
    )

    trending = []
    for name, this_count in this_week_views.items():
        last_count = last_week_views.get(name, 0)
        if last_count > 0:
            change = ((this_count - last_count) / last_count) * 100
        else:
            change = 100 if this_count > 5 else 0  # Only flag as trending if > 5 views

        if change > 50:  # More than 50% increase
            trending.append({
                'candidate_name': name,
                'this_week': this_count,
                'last_week': last_count,
                'change_percent': round(change, 1)
            })

    trending.sort(key=lambda x: -x['change_percent'])

    # Geographic interest
    geo_interest = CandidateView.objects.filter(
        timestamp__gte=since
    ).values('region', 'candidate_name').annotate(
        views=Count('id')
    ).order_by('-views')[:50]

    return Response({
        'top_candidates': list(top_candidates),
        'by_district': list(by_district),
        'trending': trending[:10],
        'geographic_interest': list(geo_interest),
        'period_days': days
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def candidate_viral_alerts(request):
    """
    Check for candidates experiencing viral traffic spikes.
    """
    # Compare last 24 hours to previous 7-day average
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    last_week = now - timedelta(days=7)

    # Get 24h views per candidate
    recent_views = dict(
        CandidateView.objects.filter(
            timestamp__gte=last_24h
        ).values('candidate_name').annotate(
            count=Count('id')
        ).values_list('candidate_name', 'count')
    )

    # Get 7-day daily average per candidate
    weekly_views = CandidateView.objects.filter(
        timestamp__gte=last_week,
        timestamp__lt=last_24h
    ).values('candidate_name').annotate(
        total=Count('id')
    )

    weekly_avg = {v['candidate_name']: v['total'] / 6 for v in weekly_views}  # 6 days before last 24h

    viral_candidates = []
    for name, recent in recent_views.items():
        avg = weekly_avg.get(name, 1)
        if recent > avg * 3 and recent > 10:  # 3x spike and at least 10 views
            viral_candidates.append({
                'candidate_name': name,
                'views_24h': recent,
                'daily_average': round(avg, 1),
                'spike_factor': round(recent / avg, 1) if avg > 0 else 0
            })

    viral_candidates.sort(key=lambda x: -x['spike_factor'])

    return Response({
        'viral_candidates': viral_candidates[:10],
        'checked_at': now.isoformat()
    })


# =============================================================================
# 3. SEARCH ANALYTICS
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAdminUser])
def search_analytics(request):
    """
    Get search analytics data.

    Query params:
    - days: Number of days (default: 30)
    """
    days = int(request.GET.get('days', 30))
    since = timezone.now() - timedelta(days=days)

    # Total search stats
    total_searches = SearchQuery.objects.filter(timestamp__gte=since).count()
    unique_queries = SearchQuery.objects.filter(timestamp__gte=since).values('normalized_query').distinct().count()
    no_results = SearchQuery.objects.filter(timestamp__gte=since, had_results=False).count()
    clicked = SearchQuery.objects.filter(timestamp__gte=since, clicked_result=True).count()

    # Top searches
    top_searches = SearchQuery.objects.filter(
        timestamp__gte=since
    ).values('normalized_query').annotate(
        count=Count('id'),
        avg_results=Avg('results_count'),
        click_rate=ExpressionWrapper(
            Avg(Case(When(clicked_result=True, then=Value(1)), default=Value(0), output_field=IntegerField())) * 100,
            output_field=FloatField()
        )
    ).order_by('-count')[:20]

    # Searches with no results (content gaps)
    content_gaps = SearchQuery.objects.filter(
        timestamp__gte=since,
        had_results=False
    ).values('normalized_query').annotate(
        count=Count('id')
    ).order_by('-count')[:20]

    # Trending searches (last 7 days vs previous 7 days)
    this_week = timezone.now() - timedelta(days=7)
    last_week_start = timezone.now() - timedelta(days=14)

    this_week_searches = dict(
        SearchQuery.objects.filter(
            timestamp__gte=this_week
        ).values('normalized_query').annotate(count=Count('id')).values_list('normalized_query', 'count')
    )

    last_week_searches = dict(
        SearchQuery.objects.filter(
            timestamp__gte=last_week_start,
            timestamp__lt=this_week
        ).values('normalized_query').annotate(count=Count('id')).values_list('normalized_query', 'count')
    )

    trending = []
    for query, this_count in this_week_searches.items():
        last_count = last_week_searches.get(query, 0)
        if this_count > 3:  # At least 3 searches
            if last_count > 0:
                change = ((this_count - last_count) / last_count) * 100
            else:
                change = 100

            trending.append({
                'query': query,
                'this_week': this_count,
                'last_week': last_count,
                'change_percent': round(change, 1)
            })

    trending.sort(key=lambda x: -x['this_week'])

    # Search by type
    by_type = SearchQuery.objects.filter(
        timestamp__gte=since
    ).values('search_type').annotate(
        count=Count('id')
    ).order_by('-count')

    return Response({
        'summary': {
            'total_searches': total_searches,
            'unique_queries': unique_queries,
            'no_results_count': no_results,
            'no_results_rate': round((no_results / total_searches * 100) if total_searches > 0 else 0, 1),
            'click_through_rate': round((clicked / total_searches * 100) if total_searches > 0 else 0, 1),
        },
        'top_searches': list(top_searches),
        'content_gaps': list(content_gaps),
        'trending_searches': trending[:15],
        'by_type': list(by_type),
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def track_search(request):
    """
    Track a search query (called from frontend).

    Body:
    - query: Search query string
    - results_count: Number of results
    - search_type: Type of search (candidate, committee, etc.)
    - session_id: Session ID (optional)
    """
    query = request.data.get('query', '').strip()
    if not query:
        return Response({'error': 'Query required'}, status=400)

    SearchQuery.objects.create(
        query=query,
        normalized_query=query.lower().strip(),
        results_count=request.data.get('results_count', 0),
        had_results=request.data.get('results_count', 0) > 0,
        search_type=request.data.get('search_type', 'general'),
        session_id=request.data.get('session_id', ''),
        visitor_id=request.data.get('visitor_id', ''),
        ip_address=get_client_ip(request),
        response_time_ms=request.data.get('response_time_ms'),
    )

    return Response({'status': 'tracked'})


# =============================================================================
# 4. REFERRER INTELLIGENCE
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAdminUser])
def referrer_intelligence(request):
    """
    Get referrer/traffic source analytics.

    Query params:
    - days: Number of days (default: 30)
    """
    days = int(request.GET.get('days', 30))
    since = timezone.now() - timedelta(days=days)

    # Analyze from SiteVisit data
    referrers = SiteVisit.objects.filter(
        timestamp__gte=since,
        referrer__isnull=False
    ).exclude(referrer='')

    # Parse and classify referrers
    referrer_data = defaultdict(lambda: {'count': 0, 'visitors': set()})

    for visit in referrers.values('referrer', 'visitor_id', 'ip_address'):
        ref = visit['referrer']
        try:
            parsed = urlparse(ref)
            domain = parsed.netloc.lower().replace('www.', '')
        except:
            domain = 'unknown'

        referrer_data[domain]['count'] += 1
        visitor = visit['visitor_id'] or visit['ip_address']
        if visitor:
            referrer_data[domain]['visitors'].add(visitor)

    # Classify sources
    social_domains = ['twitter.com', 'x.com', 'facebook.com', 'linkedin.com', 'reddit.com', 'instagram.com']
    search_domains = ['google.com', 'bing.com', 'duckduckgo.com', 'yahoo.com']
    news_domains = ['azcentral.com', 'tucson.com', 'azcapitoltimes.com', 'kjzz.org']

    by_source_type = defaultdict(int)
    top_referrers = []

    for domain, data in referrer_data.items():
        # Classify
        if domain in social_domains or any(s in domain for s in ['twitter', 'facebook', 't.co']):
            source_type = 'social'
        elif domain in search_domains or 'google' in domain:
            source_type = 'search'
        elif domain in news_domains or 'news' in domain:
            source_type = 'news'
        elif not domain or domain == 'unknown':
            source_type = 'direct'
        else:
            source_type = 'other'

        by_source_type[source_type] += data['count']

        top_referrers.append({
            'domain': domain,
            'visits': data['count'],
            'unique_visitors': len(data['visitors']),
            'source_type': source_type
        })

    top_referrers.sort(key=lambda x: -x['visits'])

    # UTM campaign tracking
    utm_campaigns = UserSession.objects.filter(
        started_at__gte=since,
        utm_source__isnull=False
    ).exclude(utm_source='').values(
        'utm_source', 'utm_medium', 'utm_campaign'
    ).annotate(
        sessions=Count('session_id'),
        visitors=Count('visitor_id', distinct=True)
    ).order_by('-sessions')[:20]

    return Response({
        'by_source_type': dict(by_source_type),
        'top_referrers': top_referrers[:30],
        'utm_campaigns': list(utm_campaigns),
        'total_referred_visits': sum(d['count'] for d in referrer_data.values()),
    })


# =============================================================================
# 5. ENGAGEMENT SCORING
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAdminUser])
def engagement_metrics(request):
    """
    Get engagement scoring metrics.

    Query params:
    - days: Number of days (default: 30)
    """
    days = int(request.GET.get('days', 30))
    since = timezone.now() - timedelta(days=days)

    # Engagement distribution
    distribution = UserSession.objects.filter(
        started_at__gte=since
    ).values('engagement_score').annotate(
        count=Count('session_id'),
        avg_duration=Avg('duration_seconds'),
        avg_pages=Avg('page_count')
    ).order_by('engagement_score')

    # Calculate overall metrics
    total = UserSession.objects.filter(started_at__gte=since).count()

    engaged_count = UserSession.objects.filter(
        started_at__gte=since,
        engagement_score__in=['engaged', 'power_user']
    ).count()

    # Engagement by device
    by_device = UserSession.objects.filter(
        started_at__gte=since
    ).values('device_type', 'engagement_score').annotate(
        count=Count('session_id')
    ).order_by('device_type', 'engagement_score')

    # Engagement by referrer source
    by_source = UserSession.objects.filter(
        started_at__gte=since
    ).values('referrer_domain', 'engagement_score').annotate(
        count=Count('session_id')
    ).order_by('-count')[:50]

    # Power users (visitors with multiple engaged sessions)
    power_users = UserSession.objects.filter(
        started_at__gte=since,
        engagement_score__in=['engaged', 'power_user']
    ).values('visitor_id').annotate(
        sessions=Count('session_id'),
        total_pages=Sum('page_count'),
        total_time=Sum('duration_seconds')
    ).filter(sessions__gte=2).order_by('-sessions')[:20]

    return Response({
        'distribution': list(distribution),
        'summary': {
            'total_sessions': total,
            'engaged_sessions': engaged_count,
            'engagement_rate': round((engaged_count / total * 100) if total > 0 else 0, 1),
        },
        'by_device': list(by_device),
        'by_source': list(by_source),
        'power_users': list(power_users),
    })


# =============================================================================
# 6. GEOGRAPHIC INTELLIGENCE
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAdminUser])
def geographic_intelligence(request):
    """
    Get geographic analytics data.

    Query params:
    - days: Number of days (default: 30)
    """
    days = int(request.GET.get('days', 30))
    since = timezone.now() - timedelta(days=days)

    # Arizona regions (approximated by city)
    az_regions = {
        'Phoenix Metro': ['Phoenix', 'Scottsdale', 'Mesa', 'Tempe', 'Chandler', 'Gilbert', 'Glendale', 'Peoria', 'Surprise'],
        'Tucson Metro': ['Tucson', 'Oro Valley', 'Marana', 'Sahuarita'],
        'Northern AZ': ['Flagstaff', 'Prescott', 'Sedona', 'Cottonwood'],
        'Eastern AZ': ['Sierra Vista', 'Douglas', 'Bisbee', 'Safford'],
        'Western AZ': ['Yuma', 'Lake Havasu City', 'Bullhead City', 'Kingman'],
    }

    # By country
    by_country = SiteVisit.objects.filter(
        timestamp__gte=since
    ).values('country', 'country_code').annotate(
        visits=Count('id'),
        unique_visitors=Count('visitor_id', distinct=True)
    ).order_by('-visits')[:20]

    # Arizona cities
    az_cities = SiteVisit.objects.filter(
        timestamp__gte=since,
        country_code='US',
        region__icontains='Arizona'
    ).values('city').annotate(
        visits=Count('id'),
        unique_visitors=Count('visitor_id', distinct=True)
    ).order_by('-visits')[:30]

    # Map cities to regions
    region_visits = defaultdict(lambda: {'visits': 0, 'cities': set()})
    for city_data in az_cities:
        city = city_data['city']
        for region, cities in az_regions.items():
            if city in cities:
                region_visits[region]['visits'] += city_data['visits']
                region_visits[region]['cities'].add(city)
                break
        else:
            region_visits['Other AZ']['visits'] += city_data['visits']
            region_visits['Other AZ']['cities'].add(city)

    az_region_data = [
        {'region': r, 'visits': d['visits'], 'cities': list(d['cities'])}
        for r, d in region_visits.items()
    ]
    az_region_data.sort(key=lambda x: -x['visits'])

    # Out of state interest
    out_of_state = SiteVisit.objects.filter(
        timestamp__gte=since,
        country_code='US'
    ).exclude(
        Q(region__icontains='Arizona') | Q(region__isnull=True) | Q(region='')
    ).values('region').annotate(
        visits=Count('id')
    ).order_by('-visits')[:15]

    # International interest
    international = SiteVisit.objects.filter(
        timestamp__gte=since
    ).exclude(
        country_code='US'
    ).values('country', 'country_code').annotate(
        visits=Count('id')
    ).order_by('-visits')[:15]

    return Response({
        'by_country': list(by_country),
        'arizona_regions': az_region_data,
        'arizona_cities': list(az_cities),
        'out_of_state': list(out_of_state),
        'international': list(international),
    })


# =============================================================================
# 7. TIME-BASED PATTERNS
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAdminUser])
def time_patterns(request):
    """
    Get time-based traffic patterns.

    Query params:
    - days: Number of days (default: 30)
    """
    days = int(request.GET.get('days', 30))
    since = timezone.now() - timedelta(days=days)

    # Hourly patterns
    hourly = SiteVisit.objects.filter(
        timestamp__gte=since
    ).annotate(
        hour=ExtractHour('timestamp')
    ).values('hour').annotate(
        visits=Count('id'),
        unique_visitors=Count('visitor_id', distinct=True)
    ).order_by('hour')

    # Day of week patterns
    by_weekday = SiteVisit.objects.filter(
        timestamp__gte=since
    ).annotate(
        weekday=ExtractWeekDay('timestamp')
    ).values('weekday').annotate(
        visits=Count('id'),
        unique_visitors=Count('visitor_id', distinct=True)
    ).order_by('weekday')

    weekday_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    by_weekday_named = [
        {
            'day': weekday_names[d['weekday'] - 1] if d['weekday'] else 'Unknown',
            'visits': d['visits'],
            'unique_visitors': d['unique_visitors']
        }
        for d in by_weekday
    ]

    # Daily trend
    daily = SiteVisit.objects.filter(
        timestamp__gte=since
    ).annotate(
        date=TruncDate('timestamp')
    ).values('date').annotate(
        visits=Count('id'),
        unique_visitors=Count('visitor_id', distinct=True)
    ).order_by('date')

    # Peak hours
    hourly_list = list(hourly)
    if hourly_list:
        peak_hour = max(hourly_list, key=lambda x: x['visits'])
        quiet_hour = min(hourly_list, key=lambda x: x['visits'])
    else:
        peak_hour = quiet_hour = None

    return Response({
        'hourly': list(hourly),
        'by_weekday': by_weekday_named,
        'daily_trend': list(daily),
        'peak_hour': peak_hour,
        'quiet_hour': quiet_hour,
    })


# =============================================================================
# 8. API USAGE ANALYTICS
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAdminUser])
def api_usage_analytics(request):
    """
    Get API usage analytics.

    Query params:
    - days: Number of days (default: 30)
    """
    days = int(request.GET.get('days', 30))
    since = timezone.now() - timedelta(days=days)

    # Top endpoints
    top_endpoints = APIUsage.objects.filter(
        timestamp__gte=since
    ).values('endpoint', 'method').annotate(
        calls=Count('id'),
        avg_response_time=Avg('response_time_ms'),
        error_count=Count('id', filter=Q(status_code__gte=400))
    ).order_by('-calls')[:20]

    # Top consumers by IP
    top_consumers = APIUsage.objects.filter(
        timestamp__gte=since
    ).values('ip_address').annotate(
        calls=Count('id'),
        unique_endpoints=Count('endpoint', distinct=True)
    ).order_by('-calls')[:20]

    # Error rates
    total_calls = APIUsage.objects.filter(timestamp__gte=since).count()
    error_calls = APIUsage.objects.filter(timestamp__gte=since, status_code__gte=400).count()
    rate_limited = APIUsage.objects.filter(timestamp__gte=since, is_rate_limited=True).count()

    # Status code distribution
    status_dist = APIUsage.objects.filter(
        timestamp__gte=since
    ).values('status_code').annotate(
        count=Count('id')
    ).order_by('status_code')

    # Response time percentiles (approximate)
    response_times = APIUsage.objects.filter(
        timestamp__gte=since,
        response_time_ms__isnull=False
    ).values_list('response_time_ms', flat=True)

    rt_list = sorted(list(response_times))
    if rt_list:
        p50 = rt_list[len(rt_list) // 2]
        p95 = rt_list[int(len(rt_list) * 0.95)]
        p99 = rt_list[int(len(rt_list) * 0.99)]
    else:
        p50 = p95 = p99 = 0

    return Response({
        'summary': {
            'total_calls': total_calls,
            'error_rate': round((error_calls / total_calls * 100) if total_calls > 0 else 0, 2),
            'rate_limited_calls': rate_limited,
            'response_time_p50': p50,
            'response_time_p95': p95,
            'response_time_p99': p99,
        },
        'top_endpoints': list(top_endpoints),
        'top_consumers': list(top_consumers),
        'status_distribution': list(status_dist),
    })


# =============================================================================
# 9. CONTENT PERFORMANCE
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAdminUser])
def content_performance(request):
    """
    Get content performance analytics.

    Query params:
    - days: Number of days (default: 30)
    - content_type: Filter by content type (optional)
    """
    days = int(request.GET.get('days', 30))
    content_type = request.GET.get('content_type')
    since = timezone.now() - timedelta(days=days)

    # Build query
    query = ContentPerformance.objects.filter(date__gte=since.date())
    if content_type:
        query = query.filter(content_type=content_type)

    # Aggregate by path
    by_path = query.values('path', 'content_type').annotate(
        total_views=Sum('views'),
        total_unique=Sum('unique_visitors'),
        avg_time=Avg('avg_time_on_page'),
        avg_bounce=Avg('bounce_rate'),
        total_downloads=Sum('downloads')
    ).order_by('-total_views')[:30]

    # By content type
    by_type = query.values('content_type').annotate(
        total_views=Sum('views'),
        avg_time=Avg('avg_time_on_page'),
        avg_bounce=Avg('bounce_rate')
    ).order_by('-total_views')

    # Candidate profiles performance
    candidate_content = query.filter(
        content_type='candidate_profile'
    ).values('path').annotate(
        total_views=Sum('views'),
        avg_time=Avg('avg_time_on_page')
    ).order_by('-total_views')[:20]

    # Daily trend
    daily_trend = query.values('date').annotate(
        views=Sum('views')
    ).order_by('date')

    return Response({
        'top_content': list(by_path),
        'by_type': list(by_type),
        'candidate_profiles': list(candidate_content),
        'daily_trend': list(daily_trend),
    })


# =============================================================================
# 10. ALERTS & ANOMALIES
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAdminUser])
def anomaly_alerts(request):
    """
    Get anomaly alerts.

    Query params:
    - days: Number of days (default: 7)
    - severity: Filter by severity (optional)
    - acknowledged: Filter by acknowledgment status (optional)
    """
    days = int(request.GET.get('days', 7))
    severity = request.GET.get('severity')
    acknowledged = request.GET.get('acknowledged')
    since = timezone.now() - timedelta(days=days)

    query = AnomalyAlert.objects.filter(detected_at__gte=since)

    if severity:
        query = query.filter(severity=severity)
    if acknowledged is not None:
        query = query.filter(is_acknowledged=acknowledged.lower() == 'true')

    alerts = query.order_by('-detected_at')[:50]

    # Count by type
    by_type = AnomalyAlert.objects.filter(
        detected_at__gte=since
    ).values('alert_type').annotate(count=Count('id'))

    # Count by severity
    by_severity = AnomalyAlert.objects.filter(
        detected_at__gte=since
    ).values('severity').annotate(count=Count('id'))

    unacknowledged = AnomalyAlert.objects.filter(
        detected_at__gte=since,
        is_acknowledged=False
    ).count()

    return Response({
        'alerts': [
            {
                'id': a.id,
                'alert_type': a.alert_type,
                'severity': a.severity,
                'title': a.title,
                'description': a.description,
                'detected_at': a.detected_at.isoformat(),
                'is_acknowledged': a.is_acknowledged,
                'related_path': a.related_path,
                'actual_value': a.actual_value,
                'expected_value': a.expected_value,
            }
            for a in alerts
        ],
        'summary': {
            'total': len(alerts),
            'unacknowledged': unacknowledged,
        },
        'by_type': list(by_type),
        'by_severity': list(by_severity),
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def acknowledge_alert(request, alert_id):
    """
    Acknowledge an anomaly alert.
    """
    try:
        alert = AnomalyAlert.objects.get(id=alert_id)
        alert.is_acknowledged = True
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.save()
        return Response({'status': 'acknowledged'})
    except AnomalyAlert.DoesNotExist:
        return Response({'error': 'Alert not found'}, status=404)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def run_anomaly_detection(request):
    """
    Run anomaly detection and create alerts.
    """
    now = timezone.now()
    alerts_created = []

    # 1. Traffic spike detection
    today_visits = SiteVisit.objects.filter(
        timestamp__date=now.date()
    ).count()

    # Get 7-day average
    week_ago = now - timedelta(days=7)
    daily_avg = SiteVisit.objects.filter(
        timestamp__gte=week_ago,
        timestamp__lt=now.replace(hour=0, minute=0, second=0)
    ).count() / 7

    if daily_avg > 0 and today_visits > daily_avg * 2:
        alert, created = AnomalyAlert.objects.get_or_create(
            alert_type='traffic_spike',
            detected_at__date=now.date(),
            defaults={
                'severity': 'medium' if today_visits < daily_avg * 3 else 'high',
                'title': f'Traffic spike detected: {today_visits} visits today',
                'description': f'Today\'s traffic ({today_visits}) is {round(today_visits/daily_avg, 1)}x the 7-day average ({round(daily_avg)})',
                'expected_value': daily_avg,
                'actual_value': today_visits,
            }
        )
        if created:
            alerts_created.append(alert.title)

    # 2. Bot detection (many requests from single IP)
    suspicious_ips = SiteVisit.objects.filter(
        timestamp__gte=now - timedelta(hours=1)
    ).values('ip_address').annotate(
        count=Count('id')
    ).filter(count__gte=100)  # 100+ requests in 1 hour

    for ip_data in suspicious_ips:
        alert, created = AnomalyAlert.objects.get_or_create(
            alert_type='bot_attack',
            related_ip=ip_data['ip_address'],
            detected_at__gte=now - timedelta(hours=1),
            defaults={
                'severity': 'high',
                'title': f'Potential bot: {ip_data["ip_address"]}',
                'description': f'{ip_data["count"]} requests in the last hour from this IP',
                'actual_value': ip_data['count'],
            }
        )
        if created:
            alerts_created.append(alert.title)

    # 3. Geographic anomaly (sudden foreign traffic)
    foreign_traffic = SiteVisit.objects.filter(
        timestamp__gte=now - timedelta(hours=24)
    ).exclude(country_code='US').count()

    total_traffic = SiteVisit.objects.filter(
        timestamp__gte=now - timedelta(hours=24)
    ).count()

    if total_traffic > 0:
        foreign_pct = (foreign_traffic / total_traffic) * 100
        if foreign_pct > 30:  # More than 30% foreign traffic
            alert, created = AnomalyAlert.objects.get_or_create(
                alert_type='geo_anomaly',
                detected_at__date=now.date(),
                defaults={
                    'severity': 'medium',
                    'title': f'Unusual foreign traffic: {round(foreign_pct)}%',
                    'description': f'{foreign_traffic} of {total_traffic} visits in the last 24h are from outside the US',
                    'actual_value': foreign_pct,
                    'threshold': 30,
                }
            )
            if created:
                alerts_created.append(alert.title)

    return Response({
        'status': 'completed',
        'alerts_created': alerts_created,
        'checked_at': now.isoformat()
    })


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_client_ip(request):
    """Get the client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# =============================================================================
# COMBINED DASHBOARD ENDPOINT
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAdminUser])
def advanced_analytics_dashboard(request):
    """
    Get combined advanced analytics dashboard data.

    Query params:
    - days: Number of days (default: 30)
    """
    days = int(request.GET.get('days', 30))
    since = timezone.now() - timedelta(days=days)

    # Quick summary stats
    total_sessions = UserSession.objects.filter(started_at__gte=since).count()
    total_searches = SearchQuery.objects.filter(timestamp__gte=since).count()
    total_candidate_views = CandidateView.objects.filter(timestamp__gte=since).count()
    unacknowledged_alerts = AnomalyAlert.objects.filter(
        detected_at__gte=since,
        is_acknowledged=False
    ).count()

    # Engagement distribution
    engagement = UserSession.objects.filter(
        started_at__gte=since
    ).values('engagement_score').annotate(count=Count('session_id'))

    # Top 5 searched terms
    top_searches = SearchQuery.objects.filter(
        timestamp__gte=since
    ).values('normalized_query').annotate(
        count=Count('id')
    ).order_by('-count')[:5]

    # Top 5 viewed candidates
    top_candidates = CandidateView.objects.filter(
        timestamp__gte=since
    ).values('candidate_name').annotate(
        views=Count('id')
    ).order_by('-views')[:5]

    # Recent alerts
    recent_alerts = AnomalyAlert.objects.filter(
        detected_at__gte=since
    ).order_by('-detected_at')[:5]

    return Response({
        'summary': {
            'total_sessions': total_sessions,
            'total_searches': total_searches,
            'total_candidate_views': total_candidate_views,
            'unacknowledged_alerts': unacknowledged_alerts,
        },
        'engagement_distribution': list(engagement),
        'top_searches': list(top_searches),
        'top_candidates': list(top_candidates),
        'recent_alerts': [
            {
                'id': a.id,
                'alert_type': a.alert_type,
                'severity': a.severity,
                'title': a.title,
                'detected_at': a.detected_at.isoformat(),
            }
            for a in recent_alerts
        ],
    })


# =============================================================================
# FRONTEND TRACKING ENDPOINTS
# =============================================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def track_pageview(request):
    """
    Track a page view from the frontend.
    Called by the React usePageTracking hook.
    """
    try:
        data = request.data
        path = data.get('path', '')[:500]
        referrer = data.get('referrer', '')[:1000]
        visitor_id = data.get('visitor_id', '')[:64]
        session_id = data.get('session_id', '')[:64]
        page_count = int(data.get('page_count', 1))
        title = data.get('title', '')[:200]
        candidate_id = data.get('candidate_id')

        # Get client IP
        ip_address = get_client_ip(request)

        # Get user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

        # Parse device type
        ua_lower = user_agent.lower()
        if 'mobile' in ua_lower or 'android' in ua_lower and 'tablet' not in ua_lower:
            device_type = 'mobile'
        elif 'tablet' in ua_lower or 'ipad' in ua_lower:
            device_type = 'tablet'
        else:
            device_type = 'desktop'

        # Parse browser
        if 'edg' in ua_lower:
            browser = 'Edge'
        elif 'chrome' in ua_lower:
            browser = 'Chrome'
        elif 'firefox' in ua_lower:
            browser = 'Firefox'
        elif 'safari' in ua_lower:
            browser = 'Safari'
        else:
            browser = 'Other'

        # Create or update SiteVisit
        SiteVisit.objects.create(
            session_id=session_id[:64] if session_id else '',
            visitor_id=visitor_id[:64] if visitor_id else '',
            path=path,
            page_title=title,
            referrer=referrer,
            ip_address=ip_address,
            user_agent=user_agent,
            device_type=device_type,
            browser=browser,
        )

        # Create or update UserSession
        now = timezone.now()
        session_timeout = timedelta(minutes=30)

        session = UserSession.objects.filter(
            session_id=session_id,
            ended_at__isnull=True,
            started_at__gte=now - session_timeout
        ).first()

        # Parse referrer domain
        referrer_domain = ''
        if referrer:
            try:
                parsed = urlparse(referrer)
                referrer_domain = parsed.netloc[:100]
            except:
                pass

        if session:
            # Update existing session
            pages = session.pages_visited or []
            if path not in pages[-5:]:
                pages.append(path)
            session.pages_visited = pages
            session.page_count = len(pages)
            session.exit_page = path
            session.duration_seconds = int((now - session.started_at).total_seconds())
            session.is_bounced = False

            # Update engagement score
            if session.page_count >= 5 and session.duration_seconds >= 180:
                session.engagement_score = 'power_user'
            elif session.page_count >= 3 or session.duration_seconds >= 60:
                session.engagement_score = 'engaged'
            elif session.page_count >= 2:
                session.engagement_score = 'interested'

            session.save()
        else:
            # Create new session
            UserSession.objects.create(
                session_id=session_id,
                visitor_id=visitor_id,
                started_at=now,
                page_count=1,
                pages_visited=[path],
                entry_page=path,
                exit_page=path,
                referrer=referrer[:500] if referrer else '',
                referrer_domain=referrer_domain,
                utm_source=data.get('utm_source', '')[:100],
                utm_medium=data.get('utm_medium', '')[:100],
                utm_campaign=data.get('utm_campaign', '')[:200],
                device_type=device_type,
                browser=browser,
                is_bot=False,
                is_bounced=True,
                engagement_score='casual',
            )

        # Track candidate view if applicable
        if candidate_id:
            try:
                committee = Committee.objects.filter(id=int(candidate_id)).first()
                if committee:
                    CandidateView.objects.create(
                        session_id=session_id,
                        visitor_id=visitor_id,
                        candidate_id=int(candidate_id),
                        candidate_name=committee.name[:255],
                        district=committee.district[:100] if committee.district else '',
                        timestamp=now,
                        viewed_ie_spending=False,
                    )
            except (ValueError, TypeError):
                pass

        return Response({'status': 'tracked'})

    except Exception as e:
        # Silent fail - don't break frontend
        return Response({'status': 'error', 'message': str(e)}, status=200)


@api_view(['POST'])
@permission_classes([AllowAny])
def track_engagement(request):
    """
    Track engagement metrics (time on page, etc.) from the frontend.
    """
    try:
        data = request.data
        path = data.get('path', '')[:500]
        visitor_id = data.get('visitor_id', '')[:64]
        session_id = data.get('session_id', '')[:64]
        time_on_page = int(data.get('time_on_page', 0))

        if session_id and time_on_page > 0:
            # Update session duration
            session = UserSession.objects.filter(session_id=session_id).first()
            if session:
                session.duration_seconds = max(session.duration_seconds or 0, time_on_page)
                session.ended_at = timezone.now()

                # Update engagement score
                if session.page_count >= 5 and session.duration_seconds >= 180:
                    session.engagement_score = 'power_user'
                elif session.page_count >= 3 or session.duration_seconds >= 60:
                    session.engagement_score = 'engaged'
                elif session.page_count >= 2:
                    session.engagement_score = 'interested'

                session.save()

            # Update content performance (update time on page)
            today = timezone.now().date()
            perf, created = ContentPerformance.objects.get_or_create(
                path=path,
                date=today,
                defaults={
                    'views': 1,
                    'unique_visitors': 1,
                    'avg_time_on_page': time_on_page,
                }
            )
            if not created:
                # Update average time
                perf.views += 1
                perf.avg_time_on_page = (
                    (perf.avg_time_on_page * (perf.views - 1) + time_on_page) / perf.views
                )
                perf.save()

        return Response({'status': 'tracked'})

    except Exception as e:
        return Response({'status': 'error', 'message': str(e)}, status=200)


@api_view(['POST'])
@permission_classes([AllowAny])
def track_candidate_view(request):
    """
    Track a detailed candidate view from the frontend.
    """
    try:
        data = request.data
        candidate_id = data.get('candidate_id')
        candidate_name = data.get('candidate_name', '')[:255]
        visitor_id = data.get('visitor_id', '')[:64]
        session_id = data.get('session_id', '')[:64]
        viewed_ie_spending = data.get('viewed_ie_spending', False)

        if candidate_id:
            CandidateView.objects.update_or_create(
                session_id=session_id,
                candidate_id=int(candidate_id),
                defaults={
                    'visitor_id': visitor_id,
                    'candidate_name': candidate_name,
                    'timestamp': timezone.now(),
                    'viewed_ie_spending': viewed_ie_spending,
                }
            )

        return Response({'status': 'tracked'})

    except Exception as e:
        return Response({'status': 'error', 'message': str(e)}, status=200)
