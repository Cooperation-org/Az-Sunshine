# backend/transparency/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
from .views_soi import *
from .views_email import *
from .views_dashboard_optimized import *

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


urlpatterns = [
    # === RACE ANALYSIS ===
    path('races/ie-spending/', race_ie_spending, name='race-ie-spending'),
    path('races/top-donors/', race_top_donors, name='race-top-donors'),
    
    # === EMAIL CAMPAIGN ENDPOINTS (Phase 1 Requirement 1b) ===
    path('email/statistics/', email_statistics, name='email-statistics'),
    path('email/send-single/', send_single_email, name='send-single-email'),
    path('email/send-bulk/', send_bulk_emails, name='send-bulk-emails'),
    path('email-tracking/open/<str:tracking_id>/', track_email_open, name='email-track-open'),
    path('email-tracking/click/<str:tracking_id>/', track_email_click, name='email-track-click'),
    
    # === DASHBOARD - OPTIMIZED ENDPOINTS ===
    path('dashboard/summary/', dashboard_summary, name='dashboard-summary'),
    path('dashboard/summary-optimized/', dashboard_summary_optimized, name='dashboard-summary-optimized'),
    path('dashboard/charts-data/', dashboard_charts_data, name='dashboard-charts-data'),
    path('dashboard/recent-expenditures/', dashboard_recent_expenditures, name='dashboard-recent-expenditures'),
    path('dashboard/clear-cache/', clear_dashboard_cache, name='clear-dashboard-cache'),
    path('dashboard/charts-data-mv/', dashboard_charts_data_mv, name='dashboard-charts-mv'),
    path('dashboard/recent-expenditures-mv/', dashboard_recent_expenditures_mv, name='dashboard-recent-exp-mv'),
    path('dashboard/refresh-mv/', refresh_dashboard_materialized_views, name='dashboard-refresh-mv'),
    
    # === DATA VALIDATION ===
    path('validation/phase1/', validate_phase1_data, name='validate-phase1'),
    
    # === FRONTEND ADAPTERS ===
    path('donors/top/', donors_top, name='donors-top'),
    path('committees/top/', committees_top, name='committees-top'),
    path('expenditures/', expenditures_list, name='expenditures-list'),
    path('candidates/', candidates_list, name='candidates-list'),
    path('donors/', donors_list, name='donors-list'),
    
    # === SCRAPER TRIGGERS ===
    path('trigger-scrape/', trigger_scrape, name='trigger-scrape'),
    path('upload-scraped/', upload_scraped, name='upload-scraped'),
    
    # Router MUST come last
    path('', include(router.urls)),
]