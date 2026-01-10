# backend/transparency/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
from .views_soi import *
from .views_email import *
from .views_dashboard_optimized import *
from .views_dashboard_extreme import dashboard_extreme, dashboard_streaming, refresh_extreme_cache, dashboard_spending_trends
from .views_admin import DataImportViewSet, ScraperViewSet, SOSViewSet, SeeTheMoneyViewSet
from .views_ad_buys import AdBuyViewSet
from .views_validation import (
    data_quality_metrics,
    duplicate_entities,
    race_validation,
    external_comparison,
    merge_entities
)
from .views_auth import (
    register,
    login,
    setup_2fa,
    enable_2fa,
    verify_2fa,
    disable_2fa,
    get_current_user,
    logout,
    refresh_token
)
from .views_primary_race import (
    primary_race_detail,
    available_primary_races
)
from .views_candidate_aggregate import (
    candidate_aggregate,
    candidate_aggregate_ie_spending
)

app_name = 'transparency'

router = DefaultRouter()
router.register(r'candidate-soi', CandidateSOIViewSet, basename='candidate-soi')
router.register(r'committees', CommitteeViewSet, basename='committee')
router.register(r'entities', EntityViewSet, basename='entity')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'offices', OfficeViewSet, basename='office')
router.register(r'cycles', CycleViewSet, basename='cycle')
router.register(r'parties', PartyViewSet, basename='party')
router.register(r'email-templates', EmailTemplateViewSet, basename='email-template')
router.register(r'email-campaigns', EmailCampaignViewSet, basename='email-campaign')
router.register(r'email-logs', EmailLogViewSet, basename='email-log')
router.register(r'ad-buys', AdBuyViewSet, basename='ad-buy')

# Phase 1 Admin Tools
router.register(r'admin/imports', DataImportViewSet, basename='admin-imports')
router.register(r'admin/scrapers', ScraperViewSet, basename='admin-scrapers')
router.register(r'admin/sos', SOSViewSet, basename='admin-sos')
router.register(r'admin/seethemoney', SeeTheMoneyViewSet, basename='admin-seethemoney')  # FREE!


urlpatterns = [
    # === AUTHENTICATION ===
    path('auth/register/', register, name='auth-register'),
    path('auth/login/', login, name='auth-login'),
    path('auth/logout/', logout, name='auth-logout'),
    path('auth/refresh/', refresh_token, name='auth-refresh'),
    path('auth/me/', get_current_user, name='auth-me'),
    path('auth/2fa-setup/', setup_2fa, name='auth-2fa-setup'),
    path('auth/2fa-enable/', enable_2fa, name='auth-2fa-enable'),
    path('auth/2fa-verify/', verify_2fa, name='auth-2fa-verify'),
    path('auth/2fa-disable/', disable_2fa, name='auth-2fa-disable'),

    # === RACE ANALYSIS ===
    path('races/ie-spending/', race_ie_spending, name='race-ie-spending'),
    path('races/top-donors/', race_top_donors, name='race-top-donors'),
    path('races/money-flow/', races_money_flow, name='races-money-flow'),
    path('races/detailed-money-flow/', races_detailed_money_flow, name='races-detailed-money-flow'),

    # === PRIMARY RACE VIEW (Golda Demo) ===
    path('races/primary/', primary_race_detail, name='primary-race-detail'),
    path('races/primary/available/', available_primary_races, name='available-primary-races'),

    # === VISUALIZATIONS ===
    path('committees/top_by_ie/', committees_top_by_ie, name='committees-top-by-ie'),
    
    # === EMAIL CAMPAIGN ENDPOINTS (Phase 1 Requirement 1b) ===
    path('email/statistics/', email_statistics, name='email-statistics'),
    path('email/send-single/', send_single_email, name='send-single-email'),
    path('email/send-bulk/', send_bulk_emails, name='send-bulk-emails'),
    path('email-tracking/open/<str:tracking_id>/', track_email_open, name='email-track-open'),
    path('email-tracking/click/<str:tracking_id>/', track_email_click, name='email-track-click'),
    
    # === DASHBOARD - EXTREME MODE (FASTEST: Single unified endpoint) ===
    path('dashboard/extreme/', dashboard_extreme, name='dashboard-extreme'),
    path('dashboard/streaming/', dashboard_streaming, name='dashboard-streaming'),
    path('dashboard/refresh-extreme/', refresh_extreme_cache, name='refresh-extreme-cache'),
    path('dashboard/spending-trends/', dashboard_spending_trends, name='dashboard-spending-trends'),

    # === DASHBOARD - OPTIMIZED ENDPOINTS (Use MV versions for performance) ===
    path('dashboard/summary-optimized/', dashboard_summary_optimized, name='dashboard-summary-optimized'),
    path('dashboard/charts-data/', dashboard_charts_data_mv, name='dashboard-charts-data'),
    path('dashboard/recent-expenditures/', dashboard_recent_expenditures_mv, name='dashboard-recent-expenditures'),
    path('dashboard/refresh-mv/', refresh_dashboard_materialized_views, name='dashboard-refresh-mv'),
    
    # === DASHBOARD - Legacy endpoints (slower, non-optimized) ===
    path('dashboard/summary/', dashboard_summary, name='dashboard-summary'),
    path('dashboard/charts-data-old/', dashboard_charts_data, name='dashboard-charts-data-old'),
    path('dashboard/recent-expenditures-old/', dashboard_recent_expenditures, name='dashboard-recent-expenditures-old'),
    path('dashboard/clear-cache/', clear_dashboard_cache, name='clear-dashboard-cache'),
    
    # === SOI Management URLs (Phase 1) ===
    path('soi/dashboard-stats/', soi_dashboard_stats, name='soi-dashboard-stats'),
    path('soi/candidates/', soi_candidates_list, name='soi-candidates-list'),
    path('candidate-soi/<int:pk>/mark_contacted/', mark_candidate_contacted, name='mark-candidate-contacted'),
    path('candidate-soi/<int:pk>/mark_pledge_received/', mark_pledge_received, name='mark-pledge-received'),
    
    # === DATA VALIDATION ===
    path('validation/phase1/', validate_phase1_data, name='validate-phase1'),
    path('validation/quality-metrics/', data_quality_metrics, name='validation-quality-metrics'),
    path('validation/duplicates/', duplicate_entities, name='validation-duplicates'),
    path('validation/race/', race_validation, name='validation-race'),
    path('validation/external-comparison/', external_comparison, name='validation-external'),
    path('validation/merge-entities/', merge_entities, name='validation-merge'),
    
    # === CANDIDATE AGGREGATE (combines data from multiple committees per candidate) ===
    path('candidates/<int:committee_id>/aggregate/', candidate_aggregate, name='candidate-aggregate'),
    path('candidates/<int:committee_id>/aggregate/ie_spending/', candidate_aggregate_ie_spending, name='candidate-aggregate-ie'),

    # === FRONTEND ADAPTERS ===
    path('donors/top/', donors_top, name='donors-top'),
    path('committees/top/', committees_top, name='committees-top'),
    path('expenditures/', expenditures_list, name='expenditures-list'),
    path('candidates/', candidates_list, name='candidates-list'),
    path('donors/', donors_list, name='donors-list'),
    
    # === SCRAPER TRIGGERS ===
    path('trigger-scrape/', trigger_scrape, name='trigger-scrape'),
    path('upload-scraped/', upload_scraped, name='upload-scraped'),
    path('scraper-status/', scraper_status, name='scraper-status'),
    path('scraper-complete/', scraper_complete, name='scraper-complete'),
    
    # Router MUST come last
    path('', include(router.urls)),
]