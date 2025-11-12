"""
Fixed URLs Configuration
File: transparency/urls.py

Change this line in your urls.py:
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
from .views_soi import *
# ADD THIS IMPORT:
from .views_soi_webhook import *

app_name = 'transparency'

router = DefaultRouter()
router.register(r'candidate-soi', CandidateSOIViewSet, basename='candidate-soi')
router.register(r'committees', CommitteeViewSet, basename='committee')
router.register(r'entities', EntityViewSet, basename='entity')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'offices', OfficeViewSet, basename='office')
router.register(r'cycles', CycleViewSet, basename='cycle')

urlpatterns = [
    # === DIRECT SCRAPING (USE THIS FOR NOW) ===
    # This runs the scraper directly on the VPS without webhook
    
    # === STATUS ENDPOINTS ===
    # Use the EXISTING status endpoints from views_soi.py
    path('soi/webhook/status/', scraping_status, name='soi-webhook-status'),  # Reuse existing endpoint
    path('soi/webhook/history/', scraping_history, name='soi-webhook-history'),  # Reuse existing endpoint
    
    # === EXISTING SOI ENDPOINTS ===
    path('soi/scrape/trigger/', trigger_scraping, name='trigger-scraping'),
    path('soi/scrape/status/', scraping_status, name='scraping-status'),
    path('soi/scrape/history/', scraping_history, name='scraping-history'),
    path('soi/dashboard-stats/', soi_dashboard_stats, name='soi-dashboard-stats'),
    path('soi/candidates/', soi_candidates_list, name='soi-candidates-list'),
    path('soi/trigger-local/', trigger_scraping, name='trigger-local-scraping'),  # Use the working one
    
    # Backward compatibility
    path('soi_candidates/', soi_candidates_list, name='soi-candidates-alias'),

    # === EXISTING API ENDPOINTS ===
    path('races/ie-spending/', race_ie_spending, name='race-ie-spending'),
    path('races/top-donors/', race_top_donors, name='race-top-donors'),
    path('dashboard/summary/', dashboard_summary, name='dashboard-summary'),
    path('validation/phase1/', validate_phase1_data, name='validate-phase1'),
    path('donors/top/', donors_top, name='donors-top'),
    path('committees/top/', committees_top, name='committees-top'),
    path('expenditures/', expenditures_list, name='expenditures-list'),
    path('candidates/', candidates_list, name='candidates-list'),
    path('donors/', donors_list, name='donors-list'),

    # Router MUST come last
    path('', include(router.urls)),
]