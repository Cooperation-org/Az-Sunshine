# Arizona Sunshine Transparency Project - Backend Documentation

**Version:** 1.0.0 (Phase 1)  
**Last Updated:** November 6, 2025  
**Server:** az-sunshine  
**Environment:** Production

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Data Models](#data-models)
5. [Database Schema](#database-schema)
6. [Data Import Process](#data-import-process)
7. [API Reference](#api-reference)
8. [Deployment Guide](#deployment-guide)
9. [Query Cookbook](#query-cookbook)
10. [Data Validation](#data-validation)
11. [Maintenance & Operations](#maintenance-operations)
12. [Security](#security)
13. [Troubleshooting](#troubleshooting)

---

## 1. Executive Summary

### 1.1 Project Overview

The Arizona Sunshine Transparency Project is a Django-based web application designed to track and visualize campaign finance data, with a focus on Independent Expenditure (IE) spending and its impact on Arizona elections.

**Mission:** Make it easy to aggregate, visualize, and act on total IE spending for/against candidates, track contribution flows through PACs, and correlate contributions with political actions.

### 1.2 Phase 1 Scope

**Current Implementation (Phase 1):**
- ✅ Candidate Statement of Interest (SOI) tracking
- ✅ Independent Expenditure (IE) database
- ✅ Data models for candidates, races, IE committees, and donors
- ✅ RESTful API for data access
- ✅ Django Admin for manual tracking
- ✅ Aggregation queries for IE spending analysis

**Future Phases:**
- Phase 2: Automation of updates and email tracking
- Phase 3: Lobbyist database and vote correlations
- Phase 4: Financial disclosures and NLP processing

### 1.3 Key Metrics (Current Database)

```
Total Records: 12,631,191
├── Entities (Donors/People): 2,332,644
├── Transactions: 10,103,007
│   ├── Contributions: 9,197,061
│   ├── Expenses: 872,331
│   └── IE Transactions: 4,293
├── Reports: 189,601
├── Committees: 5,486
│   └── Candidate Committees: 3,298
├── Offices: 70
├── Cycles: 19
├── Counties: 15
├── Parties: 8
└── Transaction Types: 178
```

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Data Sources                            │
├─────────────────────────────────────────────────────────────┤
│  • AZ SOS Campaign Finance DB ($25/download)                │
│  • Statements of Interest (spider daily)                    │
│  • MDB Database → CSV Exports                               │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────┐
│              Import & Processing Layer                       │
├─────────────────────────────────────────────────────────────┤
│  Django Management Commands:                                 │
│  • claude_import_mdb_data.py (Claude-assisted validation)   │
│  • Bulk operations (5,000 records/batch)                    │
│  • Foreign key validation                                    │
│  • Duplicate detection                                       │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────┐
│                  PostgreSQL Database                         │
├─────────────────────────────────────────────────────────────┤
│  Database: transparency_db                                   │
│  User: transparency_user                                     │
│  Host: localhost:5432                                        │
│  Tables: 13 core tables + 32 indexes                        │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────┐
│                  Django Application                          │
├─────────────────────────────────────────────────────────────┤
│  • Django 5.0.7 + DRF 3.16.1                                │
│  • Models: 15 models with 32 indexes                        │
│  • Views: 668 lines (ViewSets + function views)             │
│  • Serializers: 373 lines                                    │
│  • URLs: 296 lines                                           │
│  • Admin: 246 lines (custom admin interfaces)               │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────┐
│                      API Layer                               │
├─────────────────────────────────────────────────────────────┤
│  Base URL: /api/v1/                                         │
│  • REST endpoints for all models                            │
│  • Custom aggregation endpoints                             │
│  • Django Admin: /admin/                                    │
│  • Health Check: /health/                                   │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────┐
│                  Frontend Clients                            │
├─────────────────────────────────────────────────────────────┤
│  • React/Vue dashboard (planned)                            │
│  • Django Admin (current)                                    │
│  • API consumers                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Server Environment

```yaml
Server: az-sunshine
OS: Ubuntu 24.04.3 LTS
Kernel: 6.8.0-87-generic
Architecture: x86_64
CPU Cores: 1
Memory: 1.9Gi
Disk: 24GB total, 420MB available

Python: 3.12.3
Virtual Environment: /opt/az_sunshine/venv
Project Path: /opt/az_sunshine/backend
```

### 2.3 Data Flow

```
[AZ SOS MDB Database]
        ↓
[CSV Export (transparency/utils/mdb_exports/)]
        ↓
[Claude-Assisted Import Validation]
        ↓
[Bulk Insert (5000/batch)]
        ↓
[PostgreSQL Database]
        ↓
[Django ORM]
        ↓
[DRF Serializers]
        ↓
[REST API Endpoints]
        ↓
[Frontend/Admin Interface]
```

---

## 3. Technology Stack

### 3.1 Core Dependencies

```python
# Backend Framework
Django==5.0.7
djangorestframework==3.16.1
django-cors-headers==4.4.0

# Database
psycopg2-binary==2.9.9  # PostgreSQL adapter

# AI/ML
anthropic==0.72.0  # Claude API for import validation

# Web Scraping (Future)
playwright==1.55.0
requests==2.32.5

# Data Processing
pandas==2.2.2
numpy==2.3.4

# Deployment
gunicorn==23.0.0  # WSGI server

# Visualization (Future)
matplotlib==3.9.2
plotly==5.24.1

# Utilities
python-dotenv==1.0.1
pytz==2025.2
```

### 3.2 Project Structure

```
/opt/az_sunshine/backend/
├── backend/                      # Django project settings
│   ├── __init__.py
│   ├── settings.py              # Main configuration (132 lines)
│   ├── urls.py                  # URL routing (60 lines)
│   ├── wsgi.py                  # WSGI configuration
│   └── asgi.py                  # ASGI configuration
│
├── transparency/                 # Main Django app
│   ├── models.py                # Data models (1009 lines)
│   ├── views.py                 # API views (668 lines)
│   ├── serializers.py           # DRF serializers (373 lines)
│   ├── urls.py                  # API routing (296 lines)
│   ├── admin.py                 # Django admin (246 lines)
│   ├── apps.py
│   ├── tests.py
│   │
│   ├── management/commands/     # Management commands
│   │   ├── claude_import_mdb_data.py  # Main import (831 lines)
│   │   ├── load_data_from_mdb.py
│   │   ├── map_mdb_to_app.py
│   │   ├── discover_soi_urls.py
│   │   └── validate_phase1_data.py
│   │
│   └── utils/                   # Utility scripts
│       ├── mdb_exports/         # CSV data directory (18 files)
│       ├── export_mdb_to_csv.py
│       ├── mdb_analyzer.py
│       └── claude_helper.py
│
├── manage.py                    # Django management script
├── requirements.txt             # Python dependencies
├── deployment_info.txt          # Server documentation
├── validation_queries.sql       # PostgreSQL validation queries
└── README.md                    # Project overview
```

---

## 4. Data Models

### 4.1 Model Hierarchy

```
Lookup Tables (Reference Data)
├── County (15 records)
├── Party (8 records)
├── Office (70 records)
├── Cycle (19 records)
├── EntityType (43 records)
├── TransactionType (178 records)
└── ExpenseCategory (71 records)

Core Entities
├── Entity (2.3M records) - Master table for people/orgs
├── BallotMeasure (49 records)
└── Committee (5,486 records) - Campaign committees

Transactions & Reports
├── Transaction (10.1M records) - All financial activity
└── Report (189K records) - Campaign finance reports

Phase 1 Tracking
└── CandidateStatementOfInterest (0 records) - SOI tracking
```

### 4.2 Entity Model (Master Table)

**Purpose:** Stores all people, businesses, PACs, and organizations involved in campaign finance.

```python
class Entity(models.Model):
    name_id = IntegerField(primary_key=True)
    name_group_id = IntegerField(db_index=True)
    entity_type = ForeignKey(EntityType)
    
    # Name fields
    last_name = CharField(max_length=255, db_index=True)
    first_name = CharField(max_length=255, db_index=True)
    middle_name = CharField(max_length=255)
    suffix = CharField(max_length=50)
    
    # Address
    address1, address2 = CharField(max_length=255)
    city = CharField(max_length=100, db_index=True)
    state = CharField(max_length=2, db_index=True)
    zip_code = CharField(max_length=10, db_index=True)
    county = ForeignKey(County)
    
    # For individuals
    occupation = CharField(max_length=255, db_index=True)
    employer = CharField(max_length=255, db_index=True)
```

**Key Methods:**
- `get_total_ie_impact_by_candidate()` - Traces indirect IE spending
- `get_contribution_summary()` - Aggregates all contributions

**Indexes:** 11 indexes for name, location, and employment searches

### 4.3 Committee Model

**Purpose:** Campaign committees for candidates, PACs, IE committees, and ballot measures.

```python
class Committee(models.Model):
    committee_id = IntegerField(primary_key=True)
    name = ForeignKey(Entity)  # Committee name
    
    # Leadership
    chairperson = ForeignKey(Entity)
    treasurer = ForeignKey(Entity)
    
    # Candidate committees
    candidate = ForeignKey(Entity)  # If this is candidate committee
    candidate_party = ForeignKey(Party)
    candidate_office = ForeignKey(Office)
    candidate_county = ForeignKey(County)
    is_incumbent = BooleanField()
    election_cycle = ForeignKey(Cycle)
    
    # PACs
    sponsor = ForeignKey(Entity)
    sponsor_type = CharField(max_length=100)
    
    # Ballot measures
    ballot_measure = ForeignKey(BallotMeasure)
    benefits_ballot_measure = BooleanField()
    
    # Dates
    organization_date = DateField()
    termination_date = DateField()  # NULL = active
```

**Key Methods (Phase 1 Requirements):**
- `get_ie_spending_summary()` - IE for/against totals
- `get_ie_spending_by_committee()` - IE breakdown by spender
- `get_ie_donors()` - Traces IE funding to original donors
- `compare_to_grassroots_threshold(threshold=5000)` - Grassroots analysis

**Statistics:**
- Total: 5,486 committees
- Candidate committees: 3,298 (60%)
- Active committees: 1,366 (25%)

### 4.4 Transaction Model

**Purpose:** All financial transactions - contributions, expenses, and independent expenditures.

```python
class Transaction(models.Model):
    transaction_id = IntegerField(primary_key=True)
    committee = ForeignKey(Committee)  # Who received/spent
    transaction_type = ForeignKey(TransactionType)
    transaction_date = DateField(db_index=True)
    amount = DecimalField(max_digits=12, decimal_places=2)
    
    # Donor/Payee
    entity = ForeignKey(Entity)
    
    # Independent Expenditures
    subject_committee = ForeignKey(Committee)  # Candidate targeted
    is_for_benefit = BooleanField()  # True=FOR, False=AGAINST
    
    # Categorization
    category = ForeignKey(ExpenseCategory)
    memo = TextField()
    
    # Amendment tracking
    modifies_transaction = ForeignKey('self')
    deleted = BooleanField(default=False)
```

**Transaction Type Categories:**
- `income_expense_neutral = 1` → Contributions (9.2M records)
- `income_expense_neutral = 2` → Expenses (872K records)
- `income_expense_neutral = 3` → Neutral adjustments

**IE Transactions:** 4,293 records with `subject_committee` populated

**Indexes:** 17 indexes for date, amount, committee, entity, and IE queries

### 4.5 CandidateStatementOfInterest Model (Phase 1)

**Purpose:** Track SOI filings and manual outreach for candidate pledge program.

```python
class CandidateStatementOfInterest(models.Model):
    candidate_name = CharField(max_length=255)
    office = ForeignKey(Office)
    email = EmailField()
    filing_date = DateField()
    
    # Tracking fields
    contact_status = CharField(choices=[
        ('uncontacted', 'Uncontacted'),
        ('contacted', 'Email Sent'),
        ('acknowledged', 'Acknowledged')
    ])
    contact_date = DateField()
    contacted_by = CharField(max_length=100)
    
    # Pledge tracking
    pledge_received = BooleanField(default=False)
    pledge_date = DateField()
    notes = TextField()
    
    # Link to Entity
    entity = ForeignKey(Entity)  # Once they become candidate
```

**Usage:** Django Admin interface for manual tracking

---

## 5. Database Schema

### 5.1 Table Relationships

```
┌──────────┐
│  County  │←───────┐
└──────────┘        │
                    │
┌──────────┐        │         ┌────────────┐
│  Party   │←───┐   │    ┌───→│  Entity    │
└──────────┘    │   │    │    │ (2.3M)     │
                │   │    │    └─────┬──────┘
┌──────────┐    │   │    │          │
│  Office  │←───┼───┼────┤          │ (chairperson)
└──────────┘    │   │    │          │ (treasurer)
                │   │    │          │ (candidate)
┌──────────┐    │   │    │          │ (sponsor)
│  Cycle   │←───┼───┼────┤          │
└──────────┘    │   │    │          ↓
                │   │    │    ┌────────────┐
┌────────────┐  │   │    └────│ Committee  │
│ EntityType │←─┤   │         │  (5.5K)    │
└────────────┘  │   │         └──────┬─────┘
                │   │                │
┌────────────┐  │   └────────────────┤
│Transaction │←─┤                    │
│   Type     │  │                    │ (committee)
└────────────┘  │                    │ (subject_committee)
                │                    ↓
┌────────────┐  │              ┌─────────────┐
│  Category  │←─┼──────────────│Transaction  │
└────────────┘  │              │   (10.1M)   │
                │              └──────┬──────┘
                │                     │
                └─────────────────────┘
                      (entity - donor/payee)
```

### 5.2 Index Strategy

**Total Indexes:** 32 indexes across all tables

**Performance-Critical Indexes:**

```sql
-- Transaction queries (most frequent)
CREATE INDEX idx_txn_committee_date ON "Transactions" (committee_id, transaction_date DESC);
CREATE INDEX idx_txn_entity_date ON "Transactions" (entity_id, transaction_date DESC);
CREATE INDEX idx_txn_ie_target ON "Transactions" (subject_committee_id, is_for_benefit);
CREATE INDEX idx_txn_deleted ON "Transactions" (deleted);

-- Committee searches
CREATE INDEX idx_committee_candidate ON "Committees" (candidate_id);
CREATE INDEX idx_committee_office_cycle ON "Committees" (candidate_office_id, election_cycle_id);
CREATE INDEX idx_committee_race ON "Committees" (candidate_party_id, candidate_office_id, election_cycle_id);

-- Entity/Donor searches
CREATE INDEX idx_entity_name ON "Names" (last_name, first_name);
CREATE INDEX idx_entity_employer ON "Names" (employer);
CREATE INDEX idx_entity_location ON "Names" (city, state);
```

### 5.3 Database Statistics

```sql
-- Run these to get current stats
SELECT 
    schemaname,
    tablename,
    n_live_tup AS row_count,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

**Expected Results:**
- Transactions table: ~415MB
- Names (Entity) table: ~XXX MB
- Reports table: ~25MB
- All indexes: ~XXX MB

---

## 6. Data Import Process

### 6.1 Import Overview

The import process uses a Claude-assisted management command that validates data quality and handles the complex relationships between 13 tables and 10+ million records.

**Import Command:**
```bash
cd /opt/az_sunshine/backend
source ../venv/bin/activate
python manage.py claude_import_mdb_data --csv-dir=./transparency/utils/mdb_exports
```

### 6.2 Import Sequence

```
1. Lookup Tables (must be first - foreign key dependencies)
   ├── Counties (15 records)
   ├── Parties (8 records)
   ├── Offices (70 records)
   ├── Cycles (19 records)
   ├── EntityTypes (43 records)
   ├── TransactionTypes (178 records)
   ├── Categories (71 records)
   ├── ReportTypes (10 records)
   └── ReportNames (249 records)

2. Ballot Measures (49 records)

3. Entities (2.3M records) - BULK OPERATION
   - Batch size: 5,000 records
   - Validates foreign keys to County, EntityType
   - Normalizes state codes

4. Committees (5.5K records) - BULK OPERATION
   - Validates all foreign keys exist
   - Links to: Entity (name), Party, Office, County, Cycle, BallotMeasure
   - Skips records with invalid FK references

5. Transactions (10.1M records) - BULK OPERATION, TWO-PASS
   - Pass 1: Import transactions, validate committee exists
   - Pass 2: Update modifies_transaction self-references
   - Validates subject_committee for IE transactions

6. Reports (189K records) - BULK OPERATION, TWO-PASS  
   - Pass 1: Import original reports
   - Pass 2: Import amended reports (validates original_report exists)
```

### 6.3 Bulk Import Strategy

**Why Bulk Operations?**
- Individual inserts: ~40 hours for 10M records
- Bulk inserts (5K batch): ~2-3 hours for 10M records
- 95%+ time savings

**Implementation:**

```python
# From claude_import_mdb_data.py
batch_size = 5000
entities_to_create = []

for row in csv_rows:
    entity = Entity(
        name_id=int(row['NameID']),
        last_name=row['LastName'],
        # ... all fields
    )
    entities_to_create.append(entity)
    
    if len(entities_to_create) >= batch_size:
        with transaction.atomic():
            Entity.objects.bulk_create(
                entities_to_create, 
                ignore_conflicts=True
            )
        entities_to_create = []
```

**Error Handling:**
- Foreign key validation before insert
- Invalid records logged and skipped
- Duplicate detection via `ignore_conflicts=True`
- Timeout protection (30 seconds per operation)

### 6.4 CSV Source Files

**Location:** `/opt/az_sunshine/backend/transparency/utils/mdb_exports/`

**Files (18 total):**
```
Transactions.csv         415,645,696 bytes    5,647,731 rows
Reports.csv               25,504,050 bytes      202,956 rows
Committees.csv               893,116 bytes        5,487 rows
TransactionTypes.csv           7,532 bytes          179 rows
ReportNames.csv                6,854 bytes          249 rows
BallotMeasures.csv             4,568 bytes           53 rows
Categories.csv                 1,296 bytes           72 rows
Cycles.csv                       936 bytes           20 rows
EntityTypes.csv                1,468 bytes           44 rows
Parties.csv                      142 bytes            9 rows
ReportTypes.csv                  283 bytes           10 rows
... (other reference tables with 0 bytes - exported separately)
```

**Note:** Counties.csv, Names.csv, and Offices.csv show 0 bytes in listing but contain data when re-exported.

### 6.5 Common Import Issues

**Issue 1: Committee FK Errors**
```
Transaction 12345: Committee 999 not found - SKIPPING
```
**Solution:** Committee doesn't exist in database. Check if committee was imported successfully.

**Issue 2: Null Date Errors**
```
Report 67890: Missing required dates (period_end=None) - SKIPPING
```
**Solution:** Report has NULL values in required date fields. These are skipped.

**Issue 3: Timeout During Statistics**
```
Error getting statistics: Operation timed out
```
**Solution:** Query taking too long. Not critical - data is fine. Run validation queries manually.

### 6.6 Post-Import Validation

**Run validation queries:**
```bash
psql -U transparency_user -d transparency_db -f validation_queries.sql > validation_results.txt
```

**Expected Results:**
```sql
-- Section 1: Record counts should match
Counties: 15
Parties: 8
Offices: 70
Cycles: 19
EntityTypes: 43
TransactionTypes: 178
Categories: 71
Entities: 2,332,644
Committees: 5,486
Transactions: 10,103,007
Reports: 189,601

-- Section 7: Data integrity - all should be 0
Committees with invalid name_id: 0
Transactions with invalid committee_id: 0
Transactions with invalid entity_id: 0
IE Transactions with invalid subject_committee_id: 0
```

---

## 7. API Reference

### 7.1 Base URL

```
Development: http://localhost:8000/api/v1/
Production: https://api.arizonasunshine.org/api/v1/ (TBD)
Admin Panel: http://localhost:8000/admin/
Health Check: http://localhost:8000/health/
```

### 7.2 Authentication

**Current:** Open API (no authentication required)

**Future:** Django REST Framework Token Authentication
```python
# Add to request headers:
Authorization: Token <your-api-token>
```

### 7.3 Common Query Parameters

All list endpoints support:
```
?page=1                    # Pagination (default: page 1)
?page_size=25              # Results per page (default: 25)
?search=keyword            # Full-text search
?ordering=-field_name      # Sort results (- for descending)
?field=value               # Filter by field value
```

### 7.4 Phase 1 Endpoints

#### 7.4.1 Candidate Statements of Interest

**List SOI Filings**
```http
GET /api/v1/candidate-soi/

Query params:
  status: uncontacted|contacted|acknowledged
  pledge_received: true|false
  office: <office_id>
  
Response 200:
{
  "count": 150,
  "next": "http://api/v1/candidate-soi/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "candidate_name": "Jane Smith",
      "office": {"id": 5, "name": "State Senate District 10"},
      "email": "jane@example.com",
      "filing_date": "2024-01-15",
      "contact_status": "uncontacted",
      "pledge_received": false,
      "notes": ""
    }
  ]
}
```

**Get Summary Stats**
```http
GET /api/v1/candidate-soi/summary_stats/

Response 200:
{
  "total_filings": 150,
  "uncontacted": 45,
  "contacted": 80,
  "acknowledged": 25,
  "pledges_received": 30,
  "pledge_rate": 0.20,
  "recent_filings_7days": 5
}
```

**Mark Candidate Contacted**
```http
POST /api/v1/candidate-soi/1/mark_contacted/
Content-Type: application/json

{
  "contacted_by": "John Doe"
}

Response 200:
{
  "id": 1,
  "contact_status": "contacted",
  "contact_date": "2024-11-06",
  "contacted_by": "John Doe"
}
```

#### 7.4.2 Committee Endpoints

**Get Committee Details**
```http
GET /api/v1/committees/1234/

Response 200:
{
  "committee_id": 1234,
  "name": "Friends of Jane Smith",
  "candidate": {
    "name_id": 5678,
    "full_name": "Jane Smith",
    "party": "Democratic",
    "office": "State Senate District 10",
    "cycle": "2024"
  },
  "is_active": true,
  "organization_date": "2023-01-15",
  "total_income": "125000.00",
  "total_expenses": "98000.00",
  "cash_balance": "27000.00"
}
```

**IE Spending Summary (Ben's Requirement 2a)**
```http
GET /api/v1/committees/1234/ie_spending_summary/

Response 200:
{
  "committee_id": 1234,
  "candidate_name": "Jane Smith",
  "office": "State Senate District 10",
  "party": "Democratic",
  "ie_spending": {
    "for": {
      "total": "45000.00",
      "count": 12
    },
    "against": {
      "total": "15000.00",
      "count": 5
    },
    "net": "30000.00"
  }
}
```

**IE Donors (Ben's Requirement 2c)**
```http
GET /api/v1/committees/1234/ie_donors/?limit=20

Response 200:
[
  {
    "entity__name_id": 9876,
    "entity__first_name": "John",
    "entity__last_name": "Doe",
    "entity__entity_type__name": "Individual",
    "total_contributed": "25000.00",
    "num_contributions": 3
  },
  ...
]
```

**Grassroots Threshold (Ben's Requirements 2d-2e)**
```http
GET /api/v1/committees/1234/grassroots_threshold/?threshold=5000

Response 200:
{
  "committee": {...},
  "comparison": {
    "ie_for_total": "45000.00",
    "ie_against_total": "15000.00",
    "ie_net": "30000.00",
    "threshold": "5000.00",
    "exceeds_threshold_for": true,
    "exceeds_threshold_against": true,
    "times_threshold_for": 9.0,
    "times_threshold_against": 3.0
  }
}
```

#### 7.4.3 Entity/Donor Endpoints

**Get Entity IE Impact (Ben's Requirement 2e)**
```http
GET /api/v1/entities/5678/ie_impact_by_candidate/

Response 200:
[
  {
    "subject_committee__committee_id": 1234,
    "subject_committee__name__first_name": "Jane",
    "subject_committee__name__last_name": "Smith",
    "subject_committee__candidate_office__name": "State Senate District 10",
    "is_for_benefit": true,
    "ie_total": "75000.00",
    "ie_count": 15
  },
  ...
]
```

**Top Donors**
```http
GET /api/v1/entities/top_donors/?limit=50&cycle=19

Response 200:
[
  {
    "entity__name_id": 1111,
    "entity__full_name": "John Doe",
    "entity__employer": "Acme Corporation",
    "entity__occupation": "CEO",
    "total_contributed": "250000.00",
    "num_contributions": 45,
    "committees_contributed_to": 12
  },
  ...
]
```

#### 7.4.4 Race Aggregation Endpoints (Ben's Requirements)

**Race IE Spending (Aggregate by Race)**
```http
GET /api/v1/races/ie-spending/?office=5&cycle=19

Query params (required):
  office: <office_id>
  cycle: <cycle_id>
  party: <party_id> (optional)

Response 200:
[
  {
    "subject_committee__committee_id": 1234,
    "subject_committee__name__first_name": "Jane",
    "subject_committee__name__last_name": "Smith",
    "subject_committee__candidate_party__name": "Democratic",
    "is_for_benefit": true,
    "total_ie": "125000.00",
    "num_expenditures": 25
  },
  {
    "subject_committee__committee_id": 5678,
    "subject_committee__name__first_name": "John",
    "subject_committee__name__last_name": "Johnson",
    "subject_committee__candidate_party__name": "Republican",
    "is_for_benefit": true,
    "total_ie": "98000.00",
    "num_expenditures": 18
  }
]
```

**Race Top Donors**
```http
GET /api/v1/races/top-donors/?office=5&cycle=19&limit=20

Response 200:
[
  {
    "entity__name_id": 2222,
    "entity__first_name": "Mary",
    "entity__last_name": "Johnson",
    "entity__occupation": "Attorney",
    "entity__employer": "Johnson Law Firm",
    "total_contributed": "150000.00",
    "num_contributions": 30
  },
  ...
]
```

#### 7.4.5 Dashboard & Validation

**Dashboard Summary**
```http
GET /api/v1/dashboard/summary/

Response 200:
{
  "database_stats": {
    "total_records": 12631191,
    "entities": 2332644,
    "committees": 5486,
    "transactions": 10103007,
    "reports": 189601
  },
  "phase1_stats": {
    "candidate_committees": 3298,
    "active_committees": 1366,
    "ie_transactions": 4293,
    "contributions": 9197061,
    "expenses": 872331
  },
  "soi_tracking": {
    "total_filings": 0,
    "uncontacted": 0,
    "pledges_received": 0
  }
}
```

**Phase 1 Data Validation**
```http
GET /api/v1/validation/phase1/

Response 200:
{
  "ie_tracking": {
    "total_ie_transactions": 4293,
    "ie_committees_count": 125,
    "candidates_with_ie_spending": 342,
    "ie_for_count": 2150,
    "ie_against_count": 2143
  },
  "candidate_tracking": {
    "total_committees": 5486,
    "candidate_committees": 3298,
    "candidates_with_office": 3298,
    "candidates_with_party": 3150,
    "candidates_with_cycle": 3298
  },
  "donor_tracking": {
    "total_entities": 2332644,
    "entities_with_contributions": 185000,
    "total_contribution_transactions": 9197061,
    "unique_donors": 185000
  },
  "data_integrity": [
    "No data integrity issues found"
  ]
}
```

---

## 8. Deployment Guide

### 8.1 Server Prerequisites

```bash
# System requirements
Ubuntu 24.04.3 LTS
Python 3.12.3
PostgreSQL 14+
1GB+ RAM (2GB recommended)
24GB+ disk space

# Required packages
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3-pip
sudo apt install -y postgresql postgresql-contrib
sudo apt install -y nginx
sudo apt install -y git
```

### 8.2 PostgreSQL Setup

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE transparency_db;
CREATE USER transparency_user WITH PASSWORD 'STORED_IN_VAULT';
ALTER ROLE transparency_user SET client_encoding TO 'utf8';
ALTER ROLE transparency_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE transparency_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE transparency_db TO transparency_user;

# Exit psql
\q

# Test connection
psql -U transparency_user -d transparency_db -h localhost
```

### 8.3 Application Setup

```bash
# Create project directory
sudo mkdir -p /opt/az_sunshine
sudo chown deploy:deploy /opt/az_sunshine

# Clone repository (if using git)
cd /opt/az_sunshine
git clone <repository-url> backend

# Or upload files directly
cd /opt/az_sunshine/backend

# Create virtual environment
python3.12 -m venv /opt/az_sunshine/venv

# Activate virtual environment
source /opt/az_sunshine/venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 8.4 Environment Configuration

**Create `.env` file:**
```bash
cd /opt/az_sunshine/backend
nano .env
```

**Required Environment Variables:**
```bash
# Django settings
DJANGO_SECRET_KEY=<generate-with-django>
DEBUG=False
ALLOWED_HOSTS=api.arizonasunshine.org,localhost,127.0.0.1

# Database
DB_NAME=transparency_db
DB_USER=transparency_user
DB_PASSWORD=<stored-in-vault>
DB_HOST=localhost
DB_PORT=5432

# API Keys
ANTHROPIC_API_KEY=<stored-in-vault>

# CORS (adjust as needed)
CORS_ALLOWED_ORIGINS=https://arizonasunshine.org,http://localhost:3000
```

**Generate Django Secret Key:**
```python
python manage.py shell
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
exit()
```

### 8.5 Database Migration

```bash
# Apply migrations
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser
# Username: admin
# Email: admin@arizonasunshine.org
# Password: <stored-in-vault>

# Collect static files
python manage.py collectstatic --noinput
```

### 8.6 Data Import

```bash
# Place CSV files in correct location
mkdir -p /opt/az_sunshine/backend/transparency/utils/mdb_exports
# Upload CSV files to this directory

# Run import (takes 2-3 hours for full dataset)
python manage.py claude_import_mdb_data --csv-dir=./transparency/utils/mdb_exports

# Validate import
psql -U transparency_user -d transparency_db -f validation_queries.sql > validation_results.txt
cat validation_results.txt
```

### 8.7 Gunicorn Configuration

**Create gunicorn config:**
```bash
nano /opt/az_sunshine/backend/gunicorn_config.py
```

```python
# gunicorn_config.py
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 50
errorlog = "/opt/az_sunshine/backend/logs/gunicorn-error.log"
accesslog = "/opt/az_sunshine/backend/logs/gunicorn-access.log"
loglevel = "info"
```

**Create systemd service:**
```bash
sudo nano /etc/systemd/system/gunicorn-az-sunshine.service
```

```ini
[Unit]
Description=Gunicorn daemon for Arizona Sunshine Transparency
After=network.target

[Service]
User=deploy
Group=deploy
WorkingDirectory=/opt/az_sunshine/backend
Environment="PATH=/opt/az_sunshine/venv/bin"
ExecStart=/opt/az_sunshine/venv/bin/gunicorn \
    --config /opt/az_sunshine/backend/gunicorn_config.py \
    backend.wsgi:application

[Install]
WantedBy=multi-user.target
```

**Start and enable service:**
```bash
sudo systemctl daemon-reload
sudo systemctl start gunicorn-az-sunshine
sudo systemctl enable gunicorn-az-sunshine
sudo systemctl status gunicorn-az-sunshine
```

### 8.8 Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/az-sunshine
```

```nginx
upstream az_sunshine_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.arizonasunshine.org;

    client_max_body_size 10M;

    location /static/ {
        alias /opt/az_sunshine/backend/staticfiles/;
    }

    location /media/ {
        alias /opt/az_sunshine/backend/media/;
    }

    location / {
        proxy_pass http://az_sunshine_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
}
```

**Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/az-sunshine /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 8.9 SSL/HTTPS Setup (Production)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d api.arizonasunshine.org

# Auto-renewal is configured automatically
# Test renewal:
sudo certbot renew --dry-run
```

---

## 9. Query Cookbook

### 9.1 Ben's Core Requirements - SQL Queries

#### Query 1: Top Candidates by IE Spending FOR Them

```sql
SELECT 
    subject.committee_id,
    n.last_name || COALESCE(', ' || n.first_name, '') as candidate_name,
    o.name as office,
    p.name as party,
    cy.name as cycle,
    COUNT(t.transaction_id) as num_ie_expenditures,
    SUM(t.amount) as total_ie_for
FROM "Transactions" t
JOIN "Committees" subject ON t.subject_committee_id = subject.committee_id
JOIN "Names" n ON subject.name_id = n.name_id
LEFT JOIN "Offices" o ON subject.candidate_office_id = o.office_id
LEFT JOIN "Parties" p ON subject.candidate_party_id = p.party_id
LEFT JOIN "Cycles" cy ON subject.election_cycle_id = cy.cycle_id
WHERE t.is_for_benefit = true
  AND t.deleted = false
  AND subject.candidate_id IS NOT NULL
GROUP BY subject.committee_id, n.last_name, n.first_name, o.name, p.name, cy.name
ORDER BY total_ie_for DESC
LIMIT 20;
```

#### Query 2: Top Candidates by IE Spending AGAINST Them

```sql
SELECT 
    subject.committee_id,
    n.last_name || COALESCE(', ' || n.first_name, '') as candidate_name,
    o.name as office,
    p.name as party,
    COUNT(t.transaction_id) as num_ie_expenditures,
    SUM(t.amount) as total_ie_against
FROM "Transactions" t
JOIN "Committees" subject ON t.subject_committee_id = subject.committee_id
JOIN "Names" n ON subject.name_id = n.name_id
LEFT JOIN "Offices" o ON subject.candidate_office_id = o.office_id
LEFT JOIN "Parties" p ON subject.candidate_party_id = p.party_id
WHERE t.is_for_benefit = false
  AND t.deleted = false
GROUP BY subject.committee_id, n.last_name, n.first_name, o.name, p.name
ORDER BY total_ie_against DESC
LIMIT 20;
```

#### Query 3: Top IE Committees (Those Making IE Spending)

```sql
SELECT 
    c.committee_id,
    n.last_name as committee_name,
    COUNT(DISTINCT t.subject_committee_id) as num_candidates_targeted,
    COUNT(t.transaction_id) as num_ie_expenditures,
    SUM(t.amount) as total_ie_spending
FROM "Transactions" t
JOIN "Committees" c ON t.committee_id = c.committee_id
JOIN "Names" n ON c.name_id = n.name_id
WHERE t.subject_committee_id IS NOT NULL
  AND t.deleted = false
GROUP BY c.committee_id, n.last_name
ORDER BY total_ie_spending DESC
LIMIT 20;
```

#### Query 4: Donors to IE Committees (Tracing the Money)

```sql
WITH ie_committees AS (
    SELECT DISTINCT committee_id
    FROM "Transactions"
    WHERE subject_committee_id IS NOT NULL
)
SELECT 
    donor.name_id,
    donor.last_name || COALESCE(', ' || donor.first_name, '') as donor_name,
    donor.occupation,
    donor.employer,
    et.name as entity_type,
    COUNT(t.transaction_id) as num_contributions,
    SUM(t.amount) as total_contributed_to_ie_committees
FROM "Transactions" t
JOIN ie_committees ie ON t.committee_id = ie.committee_id
JOIN "Names" donor ON t.entity_id = donor.name_id
JOIN "EntityTypes" et ON donor.entity_type_id = et.entity_type_id
JOIN "TransactionTypes" tt ON t.transaction_type_id = tt.transaction_type_id
WHERE tt.income_expense_neutral = 1
  AND t.deleted = false
GROUP BY donor.name_id, donor.last_name, donor.first_name, 
         donor.occupation, donor.employer, et.name
ORDER BY total_contributed_to_ie_committees DESC
LIMIT 50;
```

#### Query 5: IE Spending by Race (Office + Cycle)

```sql
SELECT 
    o.name as office,
    cy.name as cycle,
    COUNT(DISTINCT t.subject_committee_id) as num_candidates,
    COUNT(t.transaction_id) as num_ie_transactions,
    SUM(CASE WHEN t.is_for_benefit = true THEN t.amount ELSE 0 END) as ie_for_total,
    SUM(CASE WHEN t.is_for_benefit = false THEN t.amount ELSE 0 END) as ie_against_total,
    SUM(t.amount) as total_ie_spending
FROM "Transactions" t
JOIN "Committees" subject ON t.subject_committee_id = subject.committee_id
LEFT JOIN "Offices" o ON subject.candidate_office_id = o.office_id
LEFT JOIN "Cycles" cy ON subject.election_cycle_id = cy.cycle_id
WHERE t.deleted = false
GROUP BY o.name, cy.name
HAVING o.name IS NOT NULL AND cy.name IS NOT NULL
ORDER BY total_ie_spending DESC
LIMIT 20;
```

#### Query 6: Candidates Exceeding Grassroots Threshold ($5,000)

```sql
WITH candidate_ie AS (
    SELECT 
        subject.committee_id,
        n.last_name || COALESCE(', ' || n.first_name, '') as candidate_name,
        o.name as office,
        p.name as party,
        SUM(CASE WHEN t.is_for_benefit = true THEN t.amount ELSE 0 END) as ie_for,
        SUM(CASE WHEN t.is_for_benefit = false THEN t.amount ELSE 0 END) as ie_against,
        SUM(t.amount) as total_ie
    FROM "Transactions" t
    JOIN "Committees" subject ON t.subject_committee_id = subject.committee_id
    JOIN "Names" n ON subject.name_id = n.name_id
    LEFT JOIN "Offices" o ON subject.candidate_office_id = o.office_id
    LEFT JOIN "Parties" p ON subject.candidate_party_id = p.party_id
    WHERE t.deleted = false
    GROUP BY subject.committee_id, n.last_name, n.first_name, o.name, p.name
)
SELECT 
    *,
    CASE WHEN ie_for > 5000 THEN 'YES' ELSE 'NO' END as exceeds_threshold_for,
    CASE WHEN ie_against > 5000 THEN 'YES' ELSE 'NO' END as exceeds_threshold_against,
    ROUND(ie_for / 5000.0, 2) as times_threshold_for,
    ROUND(ie_against / 5000.0, 2) as times_threshold_against
FROM candidate_ie
WHERE ie_for > 5000 OR ie_against > 5000
ORDER BY total_ie DESC;
```

### 9.2 Django ORM Examples

#### Example 1: Get IE Spending for a Specific Candidate

```python
from transparency.models import Committee

# Get candidate committee
candidate = Committee.objects.get(committee_id=1234)

# Get IE spending summary
ie_summary = candidate.get_ie_spending_summary()

print(f"IE For: ${ie_summary['for']['total']:,.2f}")
print(f"IE Against: ${ie_summary['against']['total']:,.2f}")
print(f"Net IE: ${ie_summary['net']:,.2f}")
```

#### Example 2: Find Top Donors to IE Committees

```python
from transparency.models import Committee, Transaction

# Get IE spending breakdown
ie_spending = candidate.get_ie_spending_by_committee()

for item in ie_spending[:10]:
    print(f"{item['committee__name__last_name']}: ${item['total']:,.2f}")
```

#### Example 3: Trace Donor Impact Across Candidates

```python
from transparency.models import Entity

# Get a specific donor
donor = Entity.objects.get(name_id=5678)

# Get IE impact by candidate
impact = donor.get_total_ie_impact_by_candidate()

for candidate_impact in impact[:10]:
    print(f"Candidate: {candidate_impact['subject_committee__name__first_name']} "
          f"{candidate_impact['subject_committee__name__last_name']}")
    print(f"  Office: {candidate_impact['subject_committee__candidate_office__name']}")
    print(f"  IE Total: ${candidate_impact['ie_total']:,.2f}")
    print(f"  Support: {'FOR' if candidate_impact['is_for_benefit'] else 'AGAINST'}")
```

#### Example 4: Race-Level Aggregations

```python
from transparency.models import Office, Cycle, RaceAggregationManager

# Get specific race
office = Office.objects.get(name='Governor')
cycle = Cycle.objects.get(name='2024')

# Get IE spending for this race
race_spending = RaceAggregationManager.get_race_ie_spending(office, cycle)

for item in race_spending:
    print(f"{item['subject_committee__name__first_name']} "
          f"{item['subject_committee__name__last_name']}: "
          f"${item['total_ie']:,.2f}")

# Get top donors for this race
top_donors = RaceAggregationManager.get_top_ie_donors_by_race(office, cycle, limit=20)

for donor in top_donors:
    print(f"{donor['entity__first_name']} {donor['entity__last_name']}: "
          f"${donor['total_contributed']:,.2f}")
```

---

## 10. Data Validation

### 10.1 Post-Import Validation Checklist

**Run after every import:**

```bash
cd /opt/az_sunshine/backend
psql -U transparency_user -d transparency_db -f validation_queries.sql > validation_results.txt
```

**Expected Results:**

✅ **Record Counts Match Source:**
- Counties: 15
- Parties: 8  
- Offices: 70
- Entities: 2,332,644
- Committees: 5,486
- Transactions: 10,103,007

✅ **No Foreign Key Violations:**
- Committees with invalid name_id: 0
- Transactions with invalid committee_id: 0
- IE Transactions with invalid subject_committee_id: 0

✅ **Data Completeness:**
- Candidate committees with office: 3,298 / 3,298
- Candidate committees with party: 3,150+ / 3,298
- IE transactions have subject_committee: 4,293

✅ **No Orphaned Records:**
- Transactions without committee: 0
- Committees without name entity: 0

### 10.2 Phase 1 Validation (Django)

```python
from transparency.models import Phase1DataValidator

# Run all validations
ie_validation = Phase1DataValidator.validate_ie_tracking()
candidate_validation = Phase1DataValidator.validate_candidate_tracking()
donor_validation = Phase1DataValidator.validate_donor_tracking()
integrity_issues = Phase1DataValidator.check_data_integrity()

# Print results
print("IE Tracking:")
print(f"  Total IE Transactions: {ie_validation['total_ie_transactions']:,}")
print(f"  Candidates with IE: {ie_validation['candidates_with_ie_spending']:,}")

print("\nCandidate Tracking:")
print(f"  Candidate Committees: {candidate_validation['candidate_committees']:,}")
print(f"  With Office: {candidate_validation['candidates_with_office']:,}")

print("\nDonor Tracking:")
print(f"  Unique Donors: {donor_validation['unique_donors']:,}")

print("\nIntegrity Issues:")
for issue in integrity_issues:
    print(f"  {issue}")
```

### 10.3 Performance Validation

**Check query performance:**

```sql
-- Explain analyze key queries
EXPLAIN ANALYZE
SELECT * FROM "Transactions" 
WHERE committee_id = 1234 
  AND deleted = false 
ORDER BY transaction_date DESC 
LIMIT 100;

-- Should use: idx_txn_committee_date
-- Execution time: < 50ms

EXPLAIN ANALYZE
SELECT * FROM "Transactions"
WHERE subject_committee_id IS NOT NULL
  AND is_for_benefit = true
  AND deleted = false
LIMIT 1000;

-- Should use: idx_txn_ie_target or idx_txn_ie_active_amount  
-- Execution time: < 100ms
```

---

## 11. Maintenance & Operations

### 11.1 Regular Data Updates

**Frequency:** Monthly or quarterly (when AZ SOS releases new database)

**Process:**
```bash
# 1. Download new MDB database from AZ SOS ($25)
# 2. Export to CSV (using Access or mdb-tools)
# 3. Upload CSVs to server
scp *.csv deploy@az-sunshine:/opt/az_sunshine/backend/transparency/utils/mdb_exports/

# 4. SSH to server
ssh deploy@az-sunshine

# 5. Backup current database
pg_dump -U transparency_user transparency_db > backup_$(date +%Y%m%d).sql

# 6. Run import (adds new records, skips existing)
cd /opt/az_sunshine/backend
source ../venv/bin/activate
python manage.py claude_import_mdb_data

# 7. Validate
psql -U transparency_user -d transparency_db -f validation_queries.sql > validation_latest.txt

# 8. Restart services
sudo systemctl restart gunicorn-az-sunshine
```

### 11.2 Database Backups

**Daily Backup Script:**

```bash
#!/bin/bash
# /opt/az_sunshine/backup_database.sh

BACKUP_DIR="/opt/az_sunshine/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/transparency_db_$DATE.sql"

# Create backup directory if doesn't exist
mkdir -p $BACKUP_DIR

# Perform backup
pg_dump -U transparency_user transparency_db > $BACKUP_FILE

# Compress
gzip $BACKUP_FILE

# Delete backups older than 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

**Schedule with cron:**
```bash
crontab -e

# Add line:
0 2 * * * /opt/az_sunshine/backup_database.sh >> /opt/az_sunshine/backup.log 2>&1
```

### 11.3 Log Rotation

```bash
sudo nano /etc/logrotate.d/az-sunshine
```

```
/opt/az_sunshine/backend/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 deploy deploy
    sharedscripts
    postrotate
        systemctl reload gunicorn-az-sunshine > /dev/null 2>&1 || true
    endscript
}
```

### 11.4 Monitoring

**Health Check Endpoint:**
```bash
curl http://localhost:8000/health/
# {"status": "healthy", "timestamp": "2025-11-06T12:00:00Z"}
```

**Database Connection Test:**
```bash
python manage.py dbshell
# Should connect successfully
\q
```

**Service Status:**
```bash
sudo systemctl status gunicorn-az-sunshine
sudo systemctl status nginx
sudo systemctl status postgresql
```

---

## 12. Security

### 12.1 Sensitive Data Storage

**ALL sensitive data stored in vault:**
- Django SECRET_KEY
- Database password
- Anthropic API key
- Admin user passwords
- Any future API tokens

**Never commit to git:**
- `.env` files
- Database dumps
- Passwords in plain text
- API keys

### 12.2 Database Security

```sql
-- Verify user permissions
\du transparency_user

-- Should only have access to transparency_db
REVOKE ALL ON DATABASE postgres FROM transparency_user;
REVOKE ALL ON DATABASE template1 FROM transparency_user;
```

**PostgreSQL Configuration:**
```bash
sudo nano /etc/postgresql/14/main/pg_hba.conf

# Only allow local connections
local   transparency_db   transparency_user   md5
host    transparency_db   transparency_user   127.0.0.1/32   md5
```

### 12.3 Django Security Settings

**In production (`DEBUG=False`):**

```python
# backend/settings.py
DEBUG = False
ALLOWED_HOSTS = ['api.arizonasunshine.org', 'localhost']

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

### 12.4 API Rate Limiting (Future)

```python
# Add to settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}
```

---

## 13. Troubleshooting

### 13.1 Common Issues

#### Issue: Import times out during statistics

```
Error getting statistics: Operation timed out
```

**Solution:** Not critical. Query is taking too long. Data imported successfully. Skip statistics or run manually:

```bash
psql -U transparency_user -d transparency_db
SELECT COUNT(*) FROM "Transactions" WHERE deleted = false;
```

#### Issue: Committee FK errors during import

```
Transaction 12345: Committee 999 not found - SKIPPING
```

**Solution:** Check if committee was imported:
```sql
SELECT * FROM "Committees" WHERE committee_id = 999;
```

If missing, check CSV file has committee and re-import committees table.

#### Issue: Gunicorn won't start

```
sudo systemctl status gunicorn-az-sunshine
# Shows "failed" or "inactive"
```

**Solution:**
```bash
# Check logs
sudo journalctl -u gunicorn-az-sunshine -n 50

# Common causes:
# 1. Port 8000 already in use
sudo netstat -tulpn | grep 8000

# 2. Python dependencies missing
source /opt/az_sunshine/venv/bin/activate
pip install -r requirements.txt

# 3. Database connection failed
python manage.py dbshell
```

#### Issue: Django Admin CSS missing

```
# Static files not loading in admin
```

**Solution:**
```bash
python manage.py collectstatic --noinput
sudo systemctl restart nginx
```

#### Issue: 502 Bad Gateway

**Solution:**
```bash
# Check if Gunicorn is running
sudo systemctl status gunicorn-az-sunshine

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Restart both services
sudo systemctl restart gunicorn-az-sunshine
sudo systemctl restart nginx
```

### 13.2 Debug Mode

**For troubleshooting only - NEVER in production:**

```python
# backend/settings.py
DEBUG = True

# Restart
sudo systemctl restart gunicorn-az-sunshine
```

**Remember to turn off:**
```python
DEBUG = False
```

### 13.3 Useful Commands

```bash
# Django shell
python manage.py shell

# Database shell
python manage.py dbshell

# Check migrations
python manage.py showmigrations

# Create superuser
python manage.py createsuperuser

# Test email (future)
python manage.py sendtestemail admin@arizonasunshine.org

# Check for issues
python manage.py check

# Validate models
python manage.py validate
```

---

## Appendices

### A. Glossary

- **IE**: Independent Expenditure - Political spending not coordinated with candidates
- **SOI**: Statement of Interest - Candidate filing declaring intent to run
- **PAC**: Political Action Committee
- **Super PAC**: Independent-expenditure-only committee
- **Committee**: Campaign finance entity (candidate committee, PAC, etc.)
- **Entity**: Master record for person or organization
- **Grassroots Threshold**: $5,000 (Arizona reporting threshold)
- **MDB**: Microsoft Access Database (source data format from AZ SOS)
- **DRF**: Django REST Framework
- **ORM**: Object-Relational Mapping (Django's database abstraction layer)
- **Bulk Operations**: Database inserts in batches for performance
- **Foreign Key (FK)**: Database relationship between tables

### B. External Data Sources

**Primary Data Source:**
- **AZ SOS Campaign Finance Database**
  - URL: https://azsos.gov/services/database-purchasing
  - Cost: $25 per download
  - Format: Microsoft Access (.mdb)
  - Update Frequency: Monthly/Quarterly
  - Contact: Arizona Secretary of State Elections Division

**Statements of Interest:**
- URL: https://azsos.gov/elections/candidates/statements-interest
- Data Source: https://apps.arizona.vote/electioninfo/SOI/71
- Scraping: Daily (planned in Phase 2)

**See The Money Arizona:**
- URL: https://seethemoney.az.gov/
- Note: Individual transaction lookup, not bulk download

### C. Contact Information

**Project Team:**
- **Client**: Ben (Arizona Sunshine Project)
- **Developer**: Deploy User (deploy@az-sunshine)
- **Server**: az-sunshine (Ubuntu 24.04.3 LTS)

**Technical Support:**
- Django Issues: https://docs.djangoproject.com/
- PostgreSQL: https://www.postgresql.org/docs/
- DRF: https://www.django-rest-framework.org/

**Vault Access:**
- Credentials stored in secure vault
- Access controlled by project administrators

### D. File Locations Reference

```
Project Root: /opt/az_sunshine/backend/

Configuration:
├── backend/settings.py          # Django configuration
├── backend/urls.py              # Main URL routing
├── .env                         # Environment variables (SECURE)
├── requirements.txt             # Python dependencies
└── gunicorn_config.py          # Gunicorn settings

Application:
├── transparency/models.py       # Data models (1009 lines)
├── transparency/views.py        # API views (668 lines)
├── transparency/serializers.py  # DRF serializers (373 lines)
├── transparency/urls.py         # API routing (296 lines)
└── transparency/admin.py        # Django admin (246 lines)

Data:
├── transparency/utils/mdb_exports/  # CSV files (18 files, ~416MB)
└── staticfiles/                     # Static assets

Management Commands:
├── transparency/management/commands/claude_import_mdb_data.py
├── transparency/management/commands/validate_phase1_data.py
└── transparency/management/commands/discover_soi_urls.py

Documentation:
├── deployment_info.txt          # Server information
├── validation_queries.sql       # PostgreSQL validation
├── validation_results.txt       # Validation output
└── README.md                    # Project overview

Logs (create if not exists):
├── logs/gunicorn-access.log
├── logs/gunicorn-error.log
└── logs/django.log

Backups:
└── backups/                     # Database backups (create if not exists)

Virtual Environment:
└── /opt/az_sunshine/venv/       # Python packages
```

### E. Database Table Reference

| Table Name | Django Model | Primary Key | Record Count | Purpose |
|------------|--------------|-------------|--------------|---------|
| Counties | County | county_id | 15 | Arizona counties |
| Parties | Party | party_id | 8 | Political parties |
| Offices | Office | office_id | 70 | Elected offices |
| Cycles | Cycle | cycle_id | 19 | Election cycles |
| EntityTypes | EntityType | entity_type_id | 43 | Entity classifications |
| TransactionTypes | TransactionType | transaction_type_id | 178 | Transaction types |
| Categories | ExpenseCategory | category_id | 71 | Expense categories |
| ReportTypes | ReportType | report_type_id | 10 | Report types |
| ReportNames | ReportName | report_name_id | 249 | Report period names |
| BallotMeasures | BallotMeasure | ballot_measure_id | 49 | Ballot initiatives |
| Names | Entity | name_id | 2,332,644 | People & organizations |
| Committees | Committee | committee_id | 5,486 | Campaign committees |
| Transactions | Transaction | transaction_id | 10,103,007 | Financial transactions |
| Reports | Report | report_id | 189,601 | Campaign finance reports |
| candidate_soi | CandidateStatementOfInterest | id | 0 | SOI tracking (Phase 1) |

### F. Environment Variables Reference

**Required Variables:**

```bash
# Django Core
DJANGO_SECRET_KEY=<generated-secret-key>         # VAULT
DEBUG=False                                       # Production: False
ALLOWED_HOSTS=api.domain.org,localhost

# Database
DB_NAME=transparency_db
DB_USER=transparency_user
DB_PASSWORD=<database-password>                   # VAULT
DB_HOST=localhost
DB_PORT=5432

# External APIs
ANTHROPIC_API_KEY=<claude-api-key>               # VAULT

# CORS (adjust for frontend domain)
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://arizonasunshine.org

# Email (future)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=<email-address>                  # VAULT
EMAIL_HOST_PASSWORD=<email-password>             # VAULT
```

**Optional Variables:**

```bash
# Logging
LOG_LEVEL=INFO

# Performance
DATABASE_CONN_MAX_AGE=600

# Sentry (future)
SENTRY_DSN=<sentry-dsn>                          # VAULT
```

### G. API Response Format Standards

**Success Response:**
```json
{
  "count": 100,
  "next": "http://api/v1/endpoint/?page=2",
  "previous": null,
  "results": [...]
}
```

**Error Response:**
```json
{
  "error": "Error message",
  "detail": "Detailed error information",
  "code": "error_code"
}
```

**HTTP Status Codes:**
- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Permission denied
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

### H. Performance Benchmarks

**Query Performance Targets:**

| Query Type | Target Time | Index Used |
|------------|-------------|------------|
| Committee by ID | < 10ms | Primary key |
| Transactions by committee | < 50ms | idx_txn_committee_date |
| IE transactions | < 100ms | idx_txn_ie_target |
| Entity search by name | < 50ms | idx_entity_name |
| Top donors aggregation | < 500ms | Multiple indexes |
| Race IE spending | < 1000ms | Combined indexes |

**Import Performance:**

| Operation | Records | Time | Method |
|-----------|---------|------|--------|
| Lookup tables | ~1,000 | 1-2 min | Individual inserts |
| Entities | 2.3M | 30-45 min | Bulk (5K batch) |
| Committees | 5.5K | 2-3 min | Bulk (5K batch) |
| Transactions | 10.1M | 90-120 min | Bulk (5K batch), 2-pass |
| Reports | 189K | 15-20 min | Bulk (5K batch), 2-pass |
| **Total Import** | **12.6M** | **2-3 hours** | Optimized bulk |

### I. Future Enhancements (Phases 2-4)

**Phase 2: Automations**
- [ ] Automated data updates from AZ SOS
- [ ] Duplicate detection and removal
- [ ] Automated email sending to candidates
- [ ] Email open/click tracking
- [ ] Time-series visualizations

**Phase 3: Lobbyist & Vote Correlations**
- [ ] Lobbyist database integration
- [ ] Arizona Legislature bill scraping
- [ ] Request to Speak (RTS) data import
- [ ] Vote record tracking
- [ ] IE spending vs. voting pattern correlation

**Phase 4: Financial Disclosures & NLP**
- [ ] PDF financial disclosure parsing
- [ ] Campaign website scraping
- [ ] Social media monitoring
- [ ] NLP/LLM processing of statements
- [ ] Automated policy position extraction

### J. Testing Checklist

**Pre-Deployment Testing:**

```bash
# 1. Database connectivity
python manage.py dbshell

# 2. Migrations up to date
python manage.py showmigrations

# 3. Static files collected
python manage.py collectstatic --dry-run

# 4. Admin panel accessible
# Visit: http://localhost:8000/admin/

# 5. API endpoints responding
curl http://localhost:8000/api/v1/committees/
curl http://localhost:8000/api/v1/dashboard/summary/

# 6. Health check
curl http://localhost:8000/health/

# 7. Data validation
python manage.py validate_phase1_data

# 8. Query performance
psql -U transparency_user -d transparency_db -f validation_queries.sql
```

**Post-Deployment Verification:**

```bash
# 1. Services running
sudo systemctl status gunicorn-az-sunshine
sudo systemctl status nginx
sudo systemctl status postgresql

# 2. Logs clean
sudo tail -f /var/log/nginx/error.log
tail -f /opt/az_sunshine/backend/logs/gunicorn-error.log

# 3. Database accessible remotely (if needed)
psql -U transparency_user -h <server-ip> -d transparency_db

# 4. SSL certificate valid (production)
curl -I https://api.arizonasunshine.org/health/
```

### K. Development Workflow

**Local Development Setup:**

```bash
# 1. Clone repository
git clone <repository-url>
cd az-sunshine-backend

# 2. Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create local .env
cp .env.example .env
# Edit .env with local settings

# 5. Setup local database
createdb transparency_db_local

# 6. Run migrations
python manage.py migrate

# 7. Create superuser
python manage.py createsuperuser

# 8. Load sample data (optional)
python manage.py loaddata sample_data.json

# 9. Run development server
python manage.py runserver

# 10. Access application
# API: http://localhost:8000/api/v1/
# Admin: http://localhost:8000/admin/
```

**Making Changes:**

```bash
# 1. Create feature branch
git checkout -b feature/new-feature

# 2. Make changes to code

# 3. Run tests (when implemented)
python manage.py test

# 4. Check for issues
python manage.py check

# 5. Commit changes
git add .
git commit -m "Description of changes"

# 6. Push to remote
git push origin feature/new-feature

# 7. Deploy to server
# SSH to server and pull changes
ssh deploy@az-sunshine
cd /opt/az_sunshine/backend
git pull origin main
source ../venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
sudo systemctl restart gunicorn-az-sunshine
```

### L. Useful SQL Queries for Reporting

**Top Contributors Overall:**
```sql
SELECT 
    n.name_id,
    n.last_name || ', ' || COALESCE(n.first_name, '') as name,
    n.occupation,
    n.employer,
    COUNT(t.transaction_id) as num_contributions,
    SUM(t.amount) as total_contributed
FROM "Transactions" t
JOIN "Names" n ON t.entity_id = n.name_id
JOIN "TransactionTypes" tt ON t.transaction_type_id = tt.transaction_type_id
WHERE tt.income_expense_neutral = 1
  AND t.deleted = false
GROUP BY n.name_id, n.last_name, n.first_name, n.occupation, n.employer
ORDER BY total_contributed DESC
LIMIT 100;
```

**Active Committees with Financials:**
```sql
SELECT 
    c.committee_id,
    n.last_name as committee_name,
    o.name as office,
    p.name as party,
    (SELECT SUM(amount) FROM "Transactions" t1 
     WHERE t1.committee_id = c.committee_id 
       AND t1.transaction_type_id IN (SELECT transaction_type_id FROM "TransactionTypes" WHERE income_expense_neutral = 1)
       AND t1.deleted = false) as total_income,
    (SELECT SUM(amount) FROM "Transactions" t2 
     WHERE t2.committee_id = c.committee_id 
       AND t2.transaction_type_id IN (SELECT transaction_type_id FROM "TransactionTypes" WHERE income_expense_neutral = 2)
       AND t2.deleted = false) as total_expenses
FROM "Committees" c
JOIN "Names" n ON c.name_id = n.name_id
LEFT JOIN "Offices" o ON c.candidate_office_id = o.office_id
LEFT JOIN "Parties" p ON c.candidate_party_id = p.party_id
WHERE c.termination_date IS NULL
  AND c.candidate_id IS NOT NULL
ORDER BY total_income DESC NULLS LAST;
```

**Recent Large Contributions (> $1,000):**
```sql
SELECT 
    t.transaction_date,
    t.amount,
    donor.last_name || ', ' || COALESCE(donor.first_name, '') as donor_name,
    donor.occupation,
    donor.employer,
    committee.last_name as committee_name,
    o.name as office
FROM "Transactions" t
JOIN "Names" donor ON t.entity_id = donor.name_id
JOIN "Committees" c ON t.committee_id = c.committee_id
JOIN "Names" committee ON c.name_id = committee.name_id
LEFT JOIN "Offices" o ON c.candidate_office_id = o.office_id
JOIN "TransactionTypes" tt ON t.transaction_type_id = tt.transaction_type_id
WHERE tt.income_expense_neutral = 1
  AND t.amount > 1000
  AND t.deleted = false
  AND t.transaction_date > CURRENT_DATE - INTERVAL '90 days'
ORDER BY t.transaction_date DESC, t.amount DESC;
```

### M. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-06 | Initial documentation for Phase 1 deployment |
| | | - Data models complete (15 models) |
| | | - Import process documented |
| | | - API endpoints functional |
| | | - Database optimized with 32 indexes |
| | | - 12.6M records imported successfully |

---

## Quick Reference Card

### Essential Commands

```bash
# Start/Stop Services
sudo systemctl start gunicorn-az-sunshine
sudo systemctl stop gunicorn-az-sunshine
sudo systemctl restart gunicorn-az-sunshine
sudo systemctl status gunicorn-az-sunshine

# Activate Virtual Environment
cd /opt/az_sunshine/backend
source ../venv/bin/activate

# Database Backup
pg_dump -U transparency_user transparency_db > backup_$(date +%Y%m%d).sql

# Import Data
python manage.py claude_import_mdb_data

# Validate Data
psql -U transparency_user -d transparency_db -f validation_queries.sql

# Django Admin
python manage.py createsuperuser
python manage.py collectstatic

# Check Logs
tail -f /opt/az_sunshine/backend/logs/gunicorn-error.log
sudo tail -f /var/log/nginx/error.log
```

### Key URLs

```
Production API: https://api.arizonasunshine.org/api/v1/
Admin Panel: https://api.arizonasunshine.org/admin/
Health Check: https://api.arizonasunshine.org/health/

Local Development: http://localhost:8000/api/v1/
Local Admin: http://localhost:8000/admin/
```

### Important Paths

```
Project: /opt/az_sunshine/backend/
Virtual Env: /opt/az_sunshine/venv/
CSV Data: /opt/az_sunshine/backend/transparency/utils/mdb_exports/
Logs: /opt/az_sunshine/backend/logs/
Backups: /opt/az_sunshine/backups/
```

### Database Info

```
Database: transparency_db
User: transparency_user
Host: localhost
Port: 5432
Records: 12,631,191
```

---

## Documentation Maintenance

**This documentation should be updated when:**
- New features are added
- API endpoints change
- Database schema modifications occur
- Deployment process changes
- New phases are implemented
- Performance optimizations are made

**Update Instructions:**
1. Edit this markdown file
2. Increment version number
3. Add entry to Version History
4. Commit to repository
5. Regenerate PDF if needed

**Documentation Location:**
- Master: `/opt/az_sunshine/backend/BACKEND_DOCUMENTATION.md`
- PDF: `/opt/az_sunshine/backend/BACKEND_DOCUMENTATION.pdf`
- Repository: `docs/BACKEND_DOCUMENTATION.md`

---

**END OF DOCUMENTATION**

*Arizona Sunshine Transparency Project - Making campaign finance data accessible and actionable.*

For questions or issues, contact the project team or refer to the troubleshooting section.