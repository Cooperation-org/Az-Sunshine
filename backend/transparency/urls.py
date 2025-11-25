# transparency/urls.py - ADD THESE NEW ROUTES

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
from .views_soi import *
from .views_soi_webhook import *
# from .views import trigger_scrape, upload_scraped


app_name = 'transparency'

router = DefaultRouter()
router.register(r'candidate-soi', CandidateSOIViewSet, basename='candidate-soi')
router.register(r'committees', CommitteeViewSet, basename='committee')
router.register(r'entities', EntityViewSet, basename='entity')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'offices', OfficeViewSet, basename='office')
router.register(r'cycles', CycleViewSet, basename='cycle')
router.register(r'parties', PartyViewSet, basename='party')

urlpatterns = [
    # === SOI ENDPOINTS ===
    path('soi/webhook/status/', scraping_status, name='soi-webhook-status'),
    path('soi/webhook/history/', scraping_history, name='soi-webhook-history'),
    path('soi/scrape/trigger/', trigger_scraping, name='trigger-scraping'),
    path('soi/scrape/status/', scraping_status, name='scraping-status'),
    path('soi/scrape/history/', scraping_history, name='scraping-history'),
    path('soi/dashboard-stats/', soi_dashboard_stats, name='soi-dashboard-stats'),
    path('soi/candidates/', soi_candidates_list, name='soi-candidates-list'),
    path('soi/trigger-local/', trigger_scraping, name='trigger-local-scraping'),
    path('soi_candidates/', soi_candidates_list, name='soi-candidates-alias'),

    # === RACE ANALYSIS ===
    path('races/ie-spending/', race_ie_spending, name='race-ie-spending'),
    path('races/top-donors/', race_top_donors, name='race-top-donors'),
    
    # === DASHBOARD - OPTIMIZED ENDPOINTS ===
    path('dashboard/summary/', dashboard_summary, name='dashboard-summary'),  # Keep old one for compatibility
    path('dashboard/summary-optimized/', dashboard_summary_optimized, name='dashboard-summary-optimized'),  # NEW
    path('dashboard/charts-data/', dashboard_charts_data, name='dashboard-charts-data'),  # NEW
    path('dashboard/recent-expenditures/', dashboard_recent_expenditures, name='dashboard-recent-expenditures'),  # NEW
    path('dashboard/clear-cache/', clear_dashboard_cache, name='clear-dashboard-cache'),  # NEW
    
    # === DATA VALIDATION ===
    path('validation/phase1/', validate_phase1_data, name='validate-phase1'),
    
    # === FRONTEND ADAPTERS ===
    path('donors/top/', donors_top, name='donors-top'),
    path('committees/top/', committees_top, name='committees-top'),
    path('expenditures/', expenditures_list, name='expenditures-list'),
    path('candidates/', candidates_list, name='candidates-list'),
    path('donors/', donors_list, name='donors-list'),
    
    path("trigger-scrape/", trigger_scrape),
    path("upload-scraped/", upload_scraped),
    
    
    
    path('soi/candidates/', soi_candidates_list, name='soi-candidates-list'),
    path('soi/dashboard-stats/', soi_dashboard_stats, name='soi-dashboard-stats'),
    
    # === EXISTING ROUTES ===
    path('soi/webhook/status/', scraping_status, name='soi-webhook-status'),
    path('soi/webhook/history/', scraping_history, name='soi-webhook-history'),
    path('soi/scrape/trigger/', trigger_scraping, name='trigger-scraping'),
    # ... rest of your existing routes
    
    # === FASTAPI TRIGGERS ===
    path('trigger-scrape/', trigger_scrape, name='trigger-scrape'),
    path('upload-scraped/', upload_scraped, name='upload-scraped'),
    

    # Router MUST come last
    path('', include(router.urls)),
]