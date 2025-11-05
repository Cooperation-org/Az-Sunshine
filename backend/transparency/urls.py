
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    # ViewSets
    CandidateSOIViewSet,
    CommitteeViewSet,
    EntityViewSet,
    TransactionViewSet,
    OfficeViewSet,
    CycleViewSet,
    
    # Function-based views
    race_ie_spending,
    race_top_donors,
    validate_phase1_data,
    dashboard_summary,
)

# App name for namespacing
app_name = 'transparency'

# Create router for ViewSets
router = DefaultRouter()
router.register(r'candidate-soi', CandidateSOIViewSet, basename='candidate-soi')
router.register(r'committees', CommitteeViewSet, basename='committee')
router.register(r'entities', EntityViewSet, basename='entity')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'offices', OfficeViewSet, basename='office')
router.register(r'cycles', CycleViewSet, basename='cycle')

# URL patterns
urlpatterns = [
    # ==================== ROUTER ENDPOINTS ====================
    # Include all ViewSet routes
    path('', include(router.urls)),
    
    # ==================== PHASE 1: CANDIDATE TRACKING ====================
    # Handled by CandidateSOIViewSet:
    # GET /api/candidate-soi/ - List all SOI filings
    # GET /api/candidate-soi/{id}/ - Get specific SOI
    # POST /api/candidate-soi/ - Create new SOI (manual entry)
    # PUT/PATCH /api/candidate-soi/{id}/ - Update SOI
    # GET /api/candidate-soi/uncontacted/ - List uncontacted candidates
    # GET /api/candidate-soi/pending_pledges/ - List pending pledges
    # GET /api/candidate-soi/summary_stats/ - Dashboard stats
    # POST /api/candidate-soi/{id}/mark_contacted/ - Mark as contacted
    # POST /api/candidate-soi/{id}/mark_pledge_received/ - Mark pledge received
    
    # ==================== PHASE 1: COMMITTEE/CANDIDATE ENDPOINTS ====================
    # Handled by CommitteeViewSet:
    # GET /api/committees/ - List all committees
    # GET /api/committees/{id}/ - Get committee details
    # GET /api/committees/{id}/ie_spending_summary/ - IE for/against summary
    # GET /api/committees/{id}/ie_spending_by_committee/ - IE breakdown by committee
    # GET /api/committees/{id}/ie_donors/ - Donors to IE committees
    # GET /api/committees/{id}/grassroots_threshold/ - Grassroots comparison
    # GET /api/committees/{id}/financial_summary/ - Overall financials
    
    # ==================== PHASE 1: ENTITY/DONOR ENDPOINTS ====================
    # Handled by EntityViewSet:
    # GET /api/entities/ - List entities (donors/individuals)
    # GET /api/entities/{id}/ - Get entity details
    # GET /api/entities/{id}/ie_impact_by_candidate/ - IE impact per candidate
    # GET /api/entities/{id}/contribution_summary/ - Contribution summary
    # GET /api/entities/top_donors/ - Top donors list
    
    # ==================== PHASE 1: TRANSACTION ENDPOINTS ====================
    # Handled by TransactionViewSet:
    # GET /api/transactions/ - List all transactions
    # GET /api/transactions/{id}/ - Get transaction details
    # GET /api/transactions/ie_transactions/ - IE transactions only
    # GET /api/transactions/large_contributions/ - Large contributions
    
    # ==================== PHASE 1: RACE AGGREGATION ====================
    # Custom function-based views for race-level aggregations
    path('races/ie-spending/', race_ie_spending, name='race-ie-spending'),
    path('races/top-donors/', race_top_donors, name='race-top-donors'),
    
    # ==================== PHASE 1: DASHBOARD & VALIDATION ====================
    path('dashboard/summary/', dashboard_summary, name='dashboard-summary'),
    path('validation/phase1/', validate_phase1_data, name='validate-phase1'),
    
    
]

"""
PHASE 1 API ENDPOINT DOCUMENTATION
====================================

BASE URL: /api/

Query Parameter Conventions:
- All list endpoints support pagination: ?page=1&page_size=25
- Date filters: ?date_from=2024-01-01&date_to=2024-12-31
- Search: ?search=keyword
- Filtering: ?status=value&field=value
- Ordering: ?order_by=-field_name (prefix with - for descending)

====================================
1. CANDIDATE STATEMENT OF INTEREST
====================================

List SOI Filings:
GET /api/candidate-soi/
Query params:
  - status: uncontacted|contacted|acknowledged
  - pledge_received: true|false
  - office: office_id
  - date_from: YYYY-MM-DD
  - date_to: YYYY-MM-DD

Get Specific SOI:
GET /api/candidate-soi/{id}/

Uncontacted Candidates:
GET /api/candidate-soi/uncontacted/

Pending Pledges:
GET /api/candidate-soi/pending_pledges/

Summary Stats:
GET /api/candidate-soi/summary_stats/
Returns: {total_filings, uncontacted, contacted, acknowledged, 
          pledges_received, pledge_rate, recent_filings_7days}

Mark Contacted:
POST /api/candidate-soi/{id}/mark_contacted/
Body: {"contacted_by": "John Doe"}

Mark Pledge Received:
POST /api/candidate-soi/{id}/mark_pledge_received/
Body: {"notes": "Optional notes"}

====================================
2. COMMITTEES (CANDIDATES & PACs)
====================================

List Committees:
GET /api/committees/
Query params:
  - candidates_only: true|false
  - office: office_id
  - party: party_id
  - cycle: cycle_id
  - active_only: true|false

Get Committee Details:
GET /api/committees/{id}/

IE Spending Summary (Requirement 2a):
GET /api/committees/{id}/ie_spending_summary/
Returns: {committee_id, candidate_name, office, party, ie_spending: {for, against, net}}

IE Spending by Committee (Requirement 2b):
GET /api/committees/{id}/ie_spending_by_committee/
Returns: List of committees that spent IE money on this candidate

IE Donors (Requirement 2c):
GET /api/committees/{id}/ie_donors/
Returns: Donors to IE committees spending on this candidate

Grassroots Threshold (Requirements 2d-2e):
GET /api/committees/{id}/grassroots_threshold/?threshold=5000
Returns: Comparison to grassroots threshold

Financial Summary:
GET /api/committees/{id}/financial_summary/
Returns: {total_income, total_expenses, cash_balance, ie_for, ie_against}

====================================
3. ENTITIES (DONORS/INDIVIDUALS)
====================================

List Entities:
GET /api/entities/
Query params:
  - search: name search
  - entity_type: entity_type_id
  - city: city name
  - state: state code

Get Entity Details:
GET /api/entities/{id}/

IE Impact by Candidate (Requirement 2e):
GET /api/entities/{id}/ie_impact_by_candidate/
Returns: Total IE spending funded indirectly by this donor

Contribution Summary:
GET /api/entities/{id}/contribution_summary/
Returns: {total, count}

Top Donors:
GET /api/entities/top_donors/?limit=50&cycle=123
Returns: Top donors by contribution amount

====================================
4. TRANSACTIONS
====================================

List Transactions:
GET /api/transactions/
Query params:
  - committee: committee_id
  - entity: entity_id
  - type: contributions|expenses
  - ie_only: true|false
  - subject_committee: committee_id
  - date_from: YYYY-MM-DD
  - date_to: YYYY-MM-DD
  - amount_min: decimal
  - amount_max: decimal
  - order_by: field_name (default: -transaction_date)

Get Transaction Details:
GET /api/transactions/{id}/

IE Transactions Only:
GET /api/transactions/ie_transactions/

Large Contributions:
GET /api/transactions/large_contributions/?threshold=1000

====================================
5. RACE AGGREGATIONS (Ben's Requirements)
====================================

Race IE Spending (Aggregate by race):
GET /api/races/ie-spending/?office=123&cycle=456&party=789
Required params: office, cycle
Optional: party
Returns: IE spending for all candidates in this race

Race Top Donors:
GET /api/races/top-donors/?office=123&cycle=456&limit=20
Required params: office, cycle
Optional: limit (default 20)
Returns: Top donors impacting this race

====================================
6. LOOKUP/REFERENCE DATA
====================================

List Offices:
GET /api/offices/

List Election Cycles:
GET /api/cycles/

====================================
7. DASHBOARD & VALIDATION
====================================

Dashboard Summary:
GET /api/dashboard/summary/
Returns: High-level stats for Phase 1 dashboard

Phase 1 Data Validation:
GET /api/validation/phase1/
Returns: Data integrity checks and validation stats

====================================
EXAMPLE FRONTEND USAGE
====================================

// Get uncontacted candidates
fetch('/api/candidate-soi/uncontacted/')
  .then(res => res.json())
  .then(data => console.log(data));

// Get IE spending for a candidate
fetch('/api/committees/123/ie_spending_summary/')
  .then(res => res.json())
  .then(data => console.log(data));

// Get top donors for Governor race in 2024
fetch('/api/races/top-donors/?office=1&cycle=202')
  .then(res => res.json())
  .then(data => console.log(data));

// Check grassroots threshold
fetch('/api/committees/123/grassroots_threshold/?threshold=5000')
  .then(res => res.json())
  .then(data => {
    if (data.comparison.exceeds_threshold_for) {
      console.log('Candidate exceeds grassroots threshold');
    }
  });

// Get dashboard stats
fetch('/api/dashboard/summary/')
  .then(res => res.json())
  .then(data => console.log(data));
"""