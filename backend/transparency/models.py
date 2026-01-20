# models.py for Arizona Sunshine Transparency Project
# Complete models with comprehensive indexing for performance

from django.db import models
from django.db.models import Sum, Count, Q
from decimal import Decimal

# ==================== LOOKUP TABLES ====================

class County(models.Model):
    """Arizona counties (15 total)"""
    county_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50, unique=True, db_index=True)
    
    class Meta:
        db_table = 'Counties'
        ordering = ['name']
        verbose_name_plural = 'Counties'
        indexes = [
            models.Index(fields=['name'], name='idx_county_name'),
        ]
    
    def __str__(self):
        return self.name


class Party(models.Model):
    """Political parties"""
    party_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100, unique=True, db_index=True)
    abbreviation = models.CharField(max_length=10, blank=True, db_index=True)
    
    class Meta:
        db_table = 'Parties'
        verbose_name_plural = 'Parties'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name'], name='idx_party_name'),
            models.Index(fields=['abbreviation'], name='idx_party_abbr'),
        ]
    
    def __str__(self):
        return self.name


class Office(models.Model):
    """Elected offices candidates run for"""
    office_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200, db_index=True)
    office_type = models.CharField(max_length=50, blank=True, db_index=True)
    
    class Meta:
        db_table = 'Offices'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name'], name='idx_office_name'),
            models.Index(fields=['office_type'], name='idx_office_type'),
            models.Index(fields=['office_type', 'name'], name='idx_office_type_name'),
        ]
    
    def __str__(self):
        return self.name


class Cycle(models.Model):
    """Election cycles"""
    cycle_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=10, db_index=True)
    begin_date = models.DateTimeField(null=True, blank=True, db_index=True)
    end_date = models.DateTimeField(null=True, blank=True, db_index=True)
    
    class Meta:
        db_table = 'Cycles'
        ordering = ['-begin_date']  # Most recent first
        indexes = [
            models.Index(fields=['name'], name='idx_cycle_name'),
            models.Index(fields=['-begin_date'], name='idx_cycle_begin_desc'),
            models.Index(fields=['begin_date', 'end_date'], name='idx_cycle_dates'),
        ]
    
    def __str__(self):
        return self.name


class EntityType(models.Model):
    """Types of entities (individual, business, committee, etc)"""
    entity_type_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100, db_index=True)
    
    class Meta:
        db_table = 'EntityTypes'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name'], name='idx_entitytype_name'),
        ]
    
    def __str__(self):
        return self.name


class TransactionType(models.Model):
    """Types of financial transactions"""
    transaction_type_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200, db_index=True)
    income_expense_neutral = models.IntegerField(db_index=True)
    
    class Meta:
        db_table = 'TransactionTypes'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name'], name='idx_txn_type_name'),
            models.Index(fields=['income_expense_neutral'], name='idx_txn_type_category'),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def is_contribution(self):
        return self.income_expense_neutral == 1
    
    @property
    def is_expense(self):
        return self.income_expense_neutral == 2


class ExpenseCategory(models.Model):
    """Categories for expenses (TV, Radio, Mailers, etc)"""
    category_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100, db_index=True)
    
    class Meta:
        db_table = 'Categories'
        verbose_name_plural = 'Expense Categories'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name'], name='idx_category_name'),
        ]
    
    def __str__(self):
        return self.name


# ==================== CORE ENTITIES ====================

class Entity(models.Model):
    """Master entity table: people, businesses, committees, etc"""
    name_id = models.IntegerField(primary_key=True)
    name_group_id = models.IntegerField(db_index=True)
    entity_type = models.ForeignKey(EntityType, on_delete=models.PROTECT, db_index=True)
    
    # Name fields (works for both people and organizations)
    last_name = models.CharField(max_length=255, db_index=True)
    first_name = models.CharField(max_length=255, blank=True, db_index=True)
    middle_name = models.CharField(max_length=255, blank=True)
    suffix = models.CharField(max_length=50, blank=True)
    
    # Address
    address1 = models.CharField(max_length=255, blank=True)
    address2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True, db_index=True)
    state = models.CharField(max_length=2, blank=True, db_index=True)
    zip_code = models.CharField(max_length=10, blank=True, db_index=True)
    county = models.ForeignKey(County, null=True, blank=True, on_delete=models.SET_NULL, db_index=True)
    
    # For individuals
    occupation = models.CharField(max_length=255, blank=True, db_index=True)
    employer = models.CharField(max_length=255, blank=True, db_index=True)
    
    class Meta:
        db_table = 'Names'
        ordering = ['last_name', 'first_name']
        indexes = [
            # Name searches
            models.Index(fields=['last_name', 'first_name'], name='idx_entity_name'),
            models.Index(fields=['first_name', 'last_name'], name='idx_entity_name_reverse'),
            
            # Grouping and filtering
            models.Index(fields=['name_group_id'], name='idx_entity_group'),
            models.Index(fields=['entity_type', 'last_name'], name='idx_entity_type_lastname'),
            
            # Location searches
            models.Index(fields=['city', 'state'], name='idx_entity_location'),
            models.Index(fields=['state', 'city'], name='idx_entity_state_city'),
            models.Index(fields=['zip_code'], name='idx_entity_zip'),
            
            # Employment searches
            models.Index(fields=['employer'], name='idx_entity_employer'),
            models.Index(fields=['occupation'], name='idx_entity_occupation'),
        ]
    
    def __str__(self):
        return self.full_name
    
    @property
    def full_name(self):
        """Return formatted full name"""
        if self.first_name:
            name = f"{self.first_name} {self.last_name}"
            if self.suffix:
                name += f" {self.suffix}"
            return name
        return self.last_name
    
    # ==================== PHASE 1 METHODS ====================
    
    def get_total_ie_impact_by_candidate(self):
        """
        Shows which candidates this donor/entity is impacting through IE spending
        Ben requires: "Compare total IE spending funded indirectly by a given donor"
        """
        # Direct IE spending by committees this entity contributed to
        committees_donated_to = Committee.objects.filter(
            transactions__entity=self,
            transactions__transaction_type__income_expense_neutral=1,
            transactions__deleted=False
        ).distinct()
        
        # IE spending by those committees
        ie_impact = Transaction.objects.filter(
            committee__in=committees_donated_to,
            subject_committee__isnull=False,
            deleted=False
        ).values(
            'subject_committee__committee_id',
            'subject_committee__name__last_name',
            'subject_committee__name__first_name',
            'subject_committee__candidate_office__name',
            'is_for_benefit'
        ).annotate(
            ie_total=Sum('amount'),
            ie_count=Count('transaction_id')
        ).order_by('-ie_total')
        
        return ie_impact
    
    def get_contribution_summary(self):
        """Total contributions made by this entity"""
        return self.transactions.filter(
            transaction_type__income_expense_neutral=1,
            deleted=False
        ).aggregate(
            total=Sum('amount'),
            count=Count('transaction_id')
        )


class BallotMeasure(models.Model):
    """Ballot initiatives and propositions"""
    ballot_measure_id = models.IntegerField(primary_key=True)
    sos_identifier = models.CharField(max_length=50, unique=True, db_index=True)
    measure_number = models.CharField(max_length=10, blank=True, null=True, db_index=True)
    short_title = models.CharField(max_length=500, db_index=True)
    official_title = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'BallotMeasures'
        ordering = ['-sos_identifier']
        indexes = [
            models.Index(fields=['sos_identifier'], name='idx_ballot_sos_id'),
            models.Index(fields=['measure_number'], name='idx_ballot_number'),
            models.Index(fields=['short_title'], name='idx_ballot_title'),
        ]
    
    def __str__(self):
        return f"{self.sos_identifier}: {self.short_title}"
    
    @property
    def election_year(self):
        """Extract year from SOS identifier"""
        parts = self.sos_identifier.split('-')
        return int(parts[-1]) if len(parts) >= 3 else None
    
    @property
    def measure_type(self):
        """C=Constitutional, I=Initiative, R=Referendum"""
        return self.sos_identifier[0] if self.sos_identifier else None


class Committee(models.Model):
    """Campaign committees (candidates, PACs, IE committees, ballot measures)"""
    committee_id = models.IntegerField(primary_key=True)
    name = models.ForeignKey(Entity, related_name='committee', on_delete=models.PROTECT, db_index=True)
    
    # Leadership
    chairperson = models.ForeignKey(Entity, related_name='chaired_committees', 
                                   null=True, blank=True, on_delete=models.SET_NULL, db_index=True)
    treasurer = models.ForeignKey(Entity, related_name='treasured_committees',
                                 null=True, blank=True, on_delete=models.SET_NULL, db_index=True)
    
    # If this is a candidate committee
    candidate = models.ForeignKey(Entity, related_name='candidate_committees',
                                 null=True, blank=True, on_delete=models.SET_NULL, db_index=True)
    candidate_party = models.ForeignKey(Party, null=True, blank=True, on_delete=models.SET_NULL, db_index=True)
    candidate_office = models.ForeignKey(Office, null=True, blank=True, on_delete=models.SET_NULL, db_index=True)
    candidate_county = models.ForeignKey(County, null=True, blank=True, 
                                        related_name='candidate_committees',
                                        on_delete=models.SET_NULL, db_index=True)
    is_incumbent = models.BooleanField(default=False, db_index=True)
    election_cycle = models.ForeignKey(Cycle, null=True, blank=True, on_delete=models.SET_NULL, db_index=True)
    
    # If this is a sponsored PAC
    sponsor = models.ForeignKey(Entity, related_name='sponsored_committees',
                               null=True, blank=True, on_delete=models.SET_NULL, db_index=True)
    sponsor_type = models.CharField(max_length=100, blank=True, db_index=True)
    sponsor_relationship = models.CharField(max_length=255, blank=True)
    
    # Ballot measure (if applicable)
    ballot_measure = models.ForeignKey(BallotMeasure, null=True, blank=True,
                                      related_name='committees',
                                      on_delete=models.SET_NULL, db_index=True)
    benefits_ballot_measure = models.BooleanField(default=False)
    
    # Dates
    organization_date = models.DateField(null=True, blank=True, db_index=True)
    termination_date = models.DateField(null=True, blank=True, db_index=True)
    
    # Address
    physical_address1 = models.CharField(max_length=255, blank=True)
    physical_address2 = models.CharField(max_length=255, blank=True)
    physical_city = models.CharField(max_length=100, blank=True, db_index=True)
    physical_state = models.CharField(max_length=2, blank=True, db_index=True)
    physical_zip_code = models.CharField(max_length=10, blank=True)
    
    # Financial institutions
    financial_institution1 = models.CharField(max_length=255, blank=True)
    financial_institution2 = models.CharField(max_length=255, blank=True)
    financial_institution3 = models.CharField(max_length=255, blank=True)
    
    class Meta:
        db_table = 'Committees'
        ordering = ['name']
        indexes = [
            # Committee searches
            models.Index(fields=['name'], name='idx_committee_name'),
            
            # Candidate committees
            models.Index(fields=['candidate'], name='idx_committee_candidate'),
            models.Index(fields=['candidate_office', 'candidate_party'], name='idx_committee_office_party'),
            models.Index(fields=['candidate_office', 'election_cycle'], name='idx_committee_office_cycle'),
            models.Index(fields=['is_incumbent'], name='idx_committee_incumbent'),
            
            # Active/terminated
            models.Index(fields=['organization_date'], name='idx_committee_org_date'),
            models.Index(fields=['termination_date'], name='idx_committee_term_date'),
            
            # Sponsored committees
            models.Index(fields=['sponsor', 'sponsor_type'], name='idx_committee_sponsor'),
            
            # Ballot measures
            models.Index(fields=['ballot_measure'], name='idx_committee_ballot'),
            
            # Election cycles
            models.Index(fields=['election_cycle'], name='idx_committee_cycle'),
            
            # Combined indexes for common queries
            models.Index(fields=['candidate_party', 'candidate_office', 'election_cycle'], 
                        name='idx_committee_race'),
        ]
    
    def __str__(self):
        return f"{self.name.full_name} ({self.committee_id})"
    
    @property
    def is_candidate_committee(self):
        return self.candidate is not None
    
    @property
    def is_active(self):
        return self.termination_date is None
    
    def get_total_income(self):
        """Calculate total contributions received"""
        return self.transactions.filter(
            transaction_type__income_expense_neutral=1,
            deleted=False
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    def get_total_expenses(self):
        """Calculate total expenditures"""
        return self.transactions.filter(
            transaction_type__income_expense_neutral=2,
            deleted=False
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    def get_cash_balance(self):
        """
        Income minus expenses.
        FIXED: Single query to avoid race condition between income/expense reads.
        """
        # Single atomic query using conditional aggregation
        totals = self.transactions.filter(deleted=False).aggregate(
            income=Sum('amount', filter=Q(transaction_type__income_expense_neutral=1)),
            expenses=Sum('amount', filter=Q(transaction_type__income_expense_neutral=2))
        )
        income = totals['income'] or Decimal('0.00')
        expenses = totals['expenses'] or Decimal('0.00')
        return income - expenses
    
    def get_ie_for(self):
        """Independent expenditures supporting this committee"""
        return Transaction.objects.filter(
            subject_committee=self,
            is_for_benefit=True,
            deleted=False
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    def get_ie_against(self):
        """Independent expenditures opposing this committee"""
        return Transaction.objects.filter(
            subject_committee=self,
            is_for_benefit=False,
            deleted=False
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # ==================== PHASE 1 METHODS ====================
    
    def get_ie_spending_summary(self):
        """
        Ben requires: "Aggregate by entity, race, and candidate"
        Returns total IE spending for/against this candidate.
        FIXED: Single query to avoid race condition.
        FIXED: Explicitly handles NULL is_for_benefit values.
        FIXED: Filter by income_expense_neutral=2 (expenses only) to exclude Pay a Bill entries.
        FIXED: Use Abs() since expenses are stored as negative values.
        """
        from django.db.models.functions import Abs

        # Single atomic query using conditional aggregation
        # NOTE: is_for_benefit=True means "for", is_for_benefit=False means "against"
        # NULL values are excluded from both counts (edge case handling)
        # Filter by income_expense_neutral=2 to only count actual expenses (not Pay a Bill)
        totals = Transaction.objects.filter(
            subject_committee=self,
            deleted=False,
            is_for_benefit__isnull=False,
            transaction_type__income_expense_neutral=2  # Only actual expenses
        ).aggregate(
            for_total=Sum(Abs('amount'), filter=Q(is_for_benefit=True)),
            for_count=Count('transaction_id', filter=Q(is_for_benefit=True)),
            against_total=Sum(Abs('amount'), filter=Q(is_for_benefit=False)),
            against_count=Count('transaction_id', filter=Q(is_for_benefit=False))
        )

        ie_for_total = totals['for_total'] or Decimal('0.00')
        ie_against_total = totals['against_total'] or Decimal('0.00')

        return {
            'for': {
                'total': ie_for_total,
                'count': totals['for_count'] or 0
            },
            'against': {
                'total': ie_against_total,
                'count': totals['against_count'] or 0
            },
            'net': ie_for_total - ie_against_total
        }
    
    def get_ie_spending_by_committee(self):
        """
        Ben requires: "Pull donors (individual and super PAC) to relevant IEs"
        Returns IE spending breakdown by which committees spent
        """
        ie_spending = Transaction.objects.filter(
            subject_committee=self,
            deleted=False,
            subject_committee__isnull=False
        ).values(
            'committee__name__last_name',
            'committee__committee_id',
            'is_for_benefit'
        ).annotate(
            total=Sum('amount'),
            count=Count('transaction_id')
        ).order_by('-total')
        
        return ie_spending
    
    def get_ie_donors(self):
        """
        Ben requires: "Aggregate IE donors by race and candidate"
        Traces IE spending back to original donors
        """
        # Get all committees that spent on this candidate
        ie_committees = Committee.objects.filter(
            transactions__subject_committee=self,
            transactions__deleted=False
        ).distinct()
        
        # Get contributions to those IE committees
        donors = Transaction.objects.filter(
            committee__in=ie_committees,
            transaction_type__income_expense_neutral=1,  # Contributions
            deleted=False
        ).values(
            'entity__name_id',
            'entity__last_name',
            'entity__first_name',
            'entity__entity_type__name'
        ).annotate(
            total_contributed=Sum('amount'),
            num_contributions=Count('transaction_id')
        ).order_by('-total_contributed')
        
        return donors
    
    def compare_to_grassroots_threshold(self, threshold=5000):
        """
        Ben requires: "Compare direct IE spending to grassroots threshold"
        and "Compare total IE spending funded indirectly by a given donor"
        
        Default AZ grassroots threshold is typically $5,000
        """
        ie_summary = self.get_ie_spending_summary()
        
        return {
            'ie_for_total': ie_summary['for']['total'],
            'ie_against_total': ie_summary['against']['total'],
            'ie_net': ie_summary['net'],
            'threshold': Decimal(str(threshold)),
            'exceeds_threshold_for': ie_summary['for']['total'] > threshold,
            'exceeds_threshold_against': ie_summary['against']['total'] > threshold,
            'times_threshold_for': float(ie_summary['for']['total'] / Decimal(str(threshold))) if threshold else 0,
            'times_threshold_against': float(ie_summary['against']['total'] / Decimal(str(threshold))) if threshold else 0,
        }


# ==================== TRANSACTIONS ====================

class Transaction(models.Model):
    """All financial transactions (contributions and expenses)"""
    transaction_id = models.IntegerField(primary_key=True)
    committee = models.ForeignKey(Committee, related_name='transactions', on_delete=models.PROTECT, db_index=True)
    transaction_type = models.ForeignKey(TransactionType, on_delete=models.PROTECT, db_index=True)
    transaction_date = models.DateField(db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, db_index=True)
    
    # Donor (for contributions) or Payee (for expenses)
    entity = models.ForeignKey(Entity, related_name='transactions', on_delete=models.PROTECT, db_index=True)
    
    # For independent expenditures
    subject_committee = models.ForeignKey(Committee, related_name='subject_of_ies',
                                         null=True, blank=True, on_delete=models.SET_NULL, db_index=True)
    is_for_benefit = models.BooleanField(null=True, blank=True, db_index=True)
    
    # Expense categorization
    category = models.ForeignKey(ExpenseCategory, null=True, blank=True, on_delete=models.SET_NULL, db_index=True)
    
    # Metadata
    memo = models.TextField(blank=True)
    account_type = models.CharField(max_length=50, blank=True)
    
    # Amendment tracking
    modifies_transaction = models.ForeignKey('self', null=True, blank=True, 
                                            related_name='amendments',
                                            on_delete=models.SET_NULL, db_index=True)
    deleted = models.BooleanField(default=False, db_index=True)
    
    class Meta:
        db_table = 'Transactions'
        ordering = ['-transaction_date', '-amount']  # Most recent, largest first
        indexes = [
            # Basic queries
            models.Index(fields=['committee', '-transaction_date'], name='idx_txn_committee_date'),
            models.Index(fields=['entity', '-transaction_date'], name='idx_txn_entity_date'),
            models.Index(fields=['transaction_type'], name='idx_txn_type'),
            models.Index(fields=['-transaction_date'], name='idx_txn_date_desc'),
            
            # Amount queries (largest contributions/expenses)
            models.Index(fields=['-amount'], name='idx_txn_amount_desc'),
            models.Index(fields=['amount'], name='idx_txn_amount_asc'),
            
            # Independent expenditures
            models.Index(fields=['subject_committee', 'is_for_benefit'], name='idx_txn_ie_target'),
            models.Index(fields=['subject_committee', '-amount'], name='idx_txn_ie_amount'),
            models.Index(fields=['is_for_benefit', '-amount'], name='idx_txn_ie_benefit'),
            
            # Category analysis
            models.Index(fields=['category', '-amount'], name='idx_txn_category_amount'),
            
            # Active transactions only
            models.Index(fields=['deleted'], name='idx_txn_deleted'),
            models.Index(fields=['deleted', '-transaction_date'], name='idx_txn_active_date'),
            
            # Combined indexes for common queries
            models.Index(fields=['committee', 'transaction_type', '-transaction_date'], 
                        name='idx_txn_comm_type_date'),
            models.Index(fields=['transaction_type', 'deleted', '-amount'], 
                        name='idx_txn_type_active_amount'),
            models.Index(fields=['subject_committee', 'deleted', '-amount'], 
                        name='idx_txn_ie_active_amount'),
            
            # Date range queries
            models.Index(fields=['transaction_date', 'committee'], name='idx_txn_date_committee'),
            models.Index(fields=['transaction_date', 'entity'], name='idx_txn_date_entity'),

            # Dashboard optimization indexes
            models.Index(fields=['deleted', 'subject_committee', 'is_for_benefit'],
                        name='idx_txn_dash_ie_benefit'),
            models.Index(fields=['transaction_type', 'deleted', 'entity', '-amount'],
                        name='idx_txn_dash_donors'),
        ]
    
    def __str__(self):
        return f"Transaction {self.transaction_id}: {self.amount}"
    
    @property
    def is_contribution(self):
        return self.transaction_type.is_contribution
    
    @property
    def is_expense(self):
        return self.transaction_type.is_expense
    
    @property
    def is_ie_spending(self):
        """Is this independent expenditure?"""
        return self.subject_committee is not None


# ==================== REPORTING ====================

class ReportType(models.Model):
    """Types of campaign finance reports"""
    report_type_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    
    class Meta:
        db_table = 'ReportTypes'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name'], name='idx_report_type_name'),
            models.Index(fields=['is_active'], name='idx_report_type_active'),
        ]
    
    def __str__(self):
        return self.name


class ReportName(models.Model):
    """Standard reporting period names"""
    report_name_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100, db_index=True)
    
    class Meta:
        db_table = 'ReportNames'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name'], name='idx_report_name'),
        ]
    
    def __str__(self):
        return self.name


class Report(models.Model):
    """Campaign finance reports filed with AZ SOS"""
    report_id = models.IntegerField(primary_key=True)
    committee = models.ForeignKey(Committee, related_name='reports', on_delete=models.CASCADE, db_index=True)
    cycle = models.ForeignKey(Cycle, on_delete=models.CASCADE, db_index=True)
    report_type = models.ForeignKey(ReportType, on_delete=models.CASCADE, db_index=True)
    report_name = models.ForeignKey(ReportName, on_delete=models.CASCADE, db_index=True)
    
    # Date ranges
    report_period_begin = models.DateTimeField(db_index=True)
    report_period_end = models.DateTimeField(db_index=True)
    filing_period_begin = models.DateTimeField()
    filing_period_end = models.DateTimeField(db_index=True)
    filing_datetime = models.DateTimeField(db_index=True)
    
    # Amendment tracking
    original_report = models.ForeignKey('self', null=True, blank=True,
                                       related_name='amendments',
                                       on_delete=models.SET_NULL, db_index=True)
    
    class Meta:
        db_table = 'Reports'
        ordering = ['-filing_datetime']  # Most recent first
        indexes = [
            # Basic queries
            models.Index(fields=['committee', '-filing_datetime'], name='idx_report_comm_filed'),
            models.Index(fields=['cycle'], name='idx_report_cycle'),
            models.Index(fields=['-filing_datetime'], name='idx_report_filed_desc'),
            
            # Period searches
            models.Index(fields=['report_period_begin', 'report_period_end'], name='idx_report_period'),
            models.Index(fields=['filing_period_end', 'filing_datetime'], name='idx_report_deadline'),
            
            # Combined queries
            models.Index(fields=['committee', 'cycle', 'report_type'], name='idx_report_comm_cycle_type'),
            models.Index(fields=['cycle', 'report_type'], name='idx_report_cycle_type'),
            
            # Amendments
            models.Index(fields=['original_report'], name='idx_report_original'),
        ]
    
    def __str__(self):
        return f"Report {self.report_id}: {self.committee.name.full_name}"
    
    @property
    def is_amendment(self):
        return self.original_report is not None
    
    @property
    def is_late(self):
        """Was this report filed after the deadline?"""
        return self.filing_datetime > self.filing_period_end


# ==================== PHASE 1: CANDIDATE TRACKING ====================

class CandidateStatementOfInterest(models.Model):
    """Phase 1: Track SOI filings and candidate outreach"""
    candidate_name = models.CharField(max_length=255, db_index=True)
    office = models.ForeignKey(Office, on_delete=models.CASCADE, db_index=True)
    email = models.EmailField(blank=True, db_index=True)
    phone = models.CharField(max_length=100, blank=True, db_index=True)  # NEW FIELD
    filing_date = models.DateField(db_index=True)
    party = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    source_url = models.URLField(max_length=500, null=True, blank=True, db_index=True)  # ADD THIS LINE
    
    # Manual tracking via Django admin
    contact_status = models.CharField(
        max_length=20,
        choices=[
            ('uncontacted', 'Uncontacted'),
            ('contacted', 'Email Sent'),
            ('acknowledged', 'Acknowledged'),
        ],
        default='uncontacted',
        db_index=True
    )
    contact_date = models.DateField(null=True, blank=True, db_index=True)
    contacted_by = models.CharField(max_length=100, blank=True)
    
    # Pledge tracking
    pledge_received = models.BooleanField(default=False, db_index=True)
    pledge_date = models.DateField(null=True, blank=True, db_index=True)
    notes = models.TextField(blank=True)
    
    # Link to Entity if they become a candidate committee
    entity = models.ForeignKey('Entity', null=True, blank=True, 
                              related_name='soi_filings',
                              on_delete=models.SET_NULL, db_index=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'candidate_soi'
        ordering = ['-filing_date']
        unique_together = ['candidate_name', 'office', 'filing_date']
        verbose_name = 'Candidate Statement of Interest'
        verbose_name_plural = 'Candidate Statements of Interest'
        indexes = [
            # Search and filter
            models.Index(fields=['candidate_name'], name='idx_soi_name'),
            models.Index(fields=['office', '-filing_date'], name='idx_soi_office_date'),
            models.Index(fields=['-filing_date'], name='idx_soi_date_desc'),
            
            # Status tracking
            models.Index(fields=['contact_status'], name='idx_soi_status'),
            models.Index(fields=['contact_status', '-filing_date'], name='idx_soi_status_date'),
            models.Index(fields=['pledge_received'], name='idx_soi_pledge'),
            
            # Combined queries
            models.Index(fields=['office', 'contact_status'], name='idx_soi_office_status'),
            models.Index(fields=['contact_status', 'pledge_received'], name='idx_soi_status_pledge'),
            
            # Phone search
            models.Index(fields=['phone'], name='idx_soi_phone'),
        ]
    
    def __str__(self):
        return f"{self.candidate_name} - {self.office.name}"


class AdBuy(models.Model):
    """
    Ad Buy tracking with volunteer crowdsourced reporting
    Phase 2 Requirement: Track ad buys correlated with IE spending
    """
    # Image upload
    image = models.ImageField(
        upload_to='ad_buys/%Y/%m/%d/',
        help_text='Screenshot/photo of the ad'
    )

    # Ad details
    url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text='URL where ad appeared (if online)'
    )
    ad_date = models.DateField(
        db_index=True,
        help_text='Date ad was observed'
    )
    platform = models.CharField(
        max_length=100,
        choices=[
            ('tv', 'Television'),
            ('radio', 'Radio'),
            ('digital', 'Digital/Online'),
            ('print', 'Print/Newspaper'),
            ('mail', 'Direct Mail'),
            ('billboard', 'Billboard/Outdoor'),
            ('other', 'Other'),
        ],
        db_index=True
    )

    # Financial details
    paid_for_by = models.CharField(
        max_length=255,
        help_text='Committee/organization that paid for ad'
    )
    approximate_spend = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Estimated cost (if known)'
    )
    how_known = models.CharField(
        max_length=50,
        choices=[
            ('disclaimer', 'Shown in disclaimer'),
            ('research', 'Found via research'),
            ('estimate', 'Estimated'),
            ('unknown', 'Unknown'),
        ],
        default='disclaimer'
    )

    # Linked to IE spending
    ie_committee = models.ForeignKey(
        'Committee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ad_buys',
        help_text='IE committee that paid for this ad',
        db_index=True
    )
    candidate = models.ForeignKey(
        'Committee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ads_about_candidate',
        help_text='Candidate this ad is about',
        db_index=True
    )
    support_oppose = models.CharField(
        max_length=10,
        choices=[
            ('support', 'Support'),
            ('oppose', 'Oppose'),
            ('neutral', 'Neutral/Informational'),
        ],
        db_index=True
    )

    # Volunteer reporting
    reported_by = models.CharField(
        max_length=255,
        help_text='Name/email of volunteer who reported this'
    )
    reported_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    # Admin review
    verified = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Has this been reviewed and approved by admin?'
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True
    )
    verified_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_ad_buys'
    )
    rejected = models.BooleanField(
        default=False,
        db_index=True
    )
    rejection_reason = models.TextField(blank=True)

    # Admin notes
    admin_notes = models.TextField(blank=True)

    # Metadata
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ad_buys'
        ordering = ['-ad_date', '-reported_at']
        verbose_name = 'Ad Buy'
        verbose_name_plural = 'Ad Buys'
        indexes = [
            models.Index(fields=['-ad_date'], name='idx_adbuy_date_desc'),
            models.Index(fields=['verified', '-ad_date'], name='idx_adbuy_verified_date'),
            models.Index(fields=['candidate', '-ad_date'], name='idx_adbuy_candidate_date'),
            models.Index(fields=['ie_committee', '-ad_date'], name='idx_adbuy_ie_date'),
            models.Index(fields=['platform', '-ad_date'], name='idx_adbuy_platform_date'),
            models.Index(fields=['verified', 'rejected'], name='idx_adbuy_status'),
        ]

    def __str__(self):
        return f"Ad Buy: {self.paid_for_by} - {self.ad_date}"

    @property
    def is_pending_review(self):
        return not self.verified and not self.rejected


# ==================== PHASE 1 AGGREGATION MANAGER ====================

class RaceAggregationManager:
    """
    Ben requires: "Aggregate by entity, race, and candidate"
    This provides race-level aggregations
    """
    
    @staticmethod
    def get_race_ie_spending(office, cycle, party=None, date_from=None, date_to=None):
        """
        Get all IE spending for a specific race (office + cycle)
        Consolidates FOR and AGAINST spending per candidate
        Returns absolute values for proper display

        Filter by transaction dates within the cycle, not committee's election_cycle.
        This ensures candidates running in a cycle are included even if their
        committee registration shows a different cycle.

        Optional date_from/date_to parameters allow filtering for Primary Only view.
        """
        from django.db.models.functions import Abs

        # Use custom dates if provided, otherwise use cycle dates
        effective_date_from = date_from if date_from else cycle.begin_date
        effective_date_to = date_to if date_to else cycle.end_date

        filters = {
            'subject_committee__candidate_office': office,
            'deleted': False,
            'subject_committee__isnull': False,
            'transaction_date__gte': effective_date_from,
            'transaction_date__lte': effective_date_to,
            'transaction_type__income_expense_neutral': 2,  # Only count actual expenses (not Pay a Bill)
        }

        if party:
            filters['subject_committee__candidate_party'] = party

        # Aggregate IE FOR and AGAINST separately per candidate
        # Use Abs() since expenses are stored as negative values
        race_spending = Transaction.objects.filter(
            **filters
        ).values(
            'subject_committee__committee_id',
            'subject_committee__name__last_name',
            'subject_committee__name__first_name',
            'subject_committee__candidate_party__name',
        ).annotate(
            ie_for=Sum(Abs('amount'), filter=Q(is_for_benefit=True)),
            ie_against=Sum(Abs('amount'), filter=Q(is_for_benefit=False)),
            num_expenditures=Count('transaction_id')
        ).annotate(
            # Calculate totals from the absolute values
            total_ie=Sum(Abs('amount'))
        ).order_by('-total_ie')

        return race_spending
    
    @staticmethod
    def get_top_ie_donors_by_race(office, cycle, limit=20):
        """
        Ben requires: "Aggregate IE donors by race and candidate"
        Shows top donors impacting a specific race

        Optimized to avoid slow subqueries by materializing intermediate results.
        """
        # Step 1: Get candidate committee IDs (materialize to list)
        candidate_ids = list(Committee.objects.filter(
            candidate_office=office,
            election_cycle=cycle,
            candidate__isnull=False
        ).values_list('committee_id', flat=True))

        if not candidate_ids:
            return []

        # Step 2: Get IE committee IDs that spent on these candidates (materialize)
        ie_committee_ids = list(Transaction.objects.filter(
            subject_committee_id__in=candidate_ids,
            deleted=False
        ).values_list('committee_id', flat=True).distinct()[:100])  # Limit to top 100 IE committees

        if not ie_committee_ids:
            return []

        # Step 3: Get top donors to those IE committees
        top_donors = Transaction.objects.filter(
            committee_id__in=ie_committee_ids,
            transaction_type__income_expense_neutral=1,
            deleted=False
        ).values(
            'entity__name_id',
            'entity__last_name',
            'entity__first_name',
            'entity__occupation',
            'entity__employer'
        ).annotate(
            total_contributed=Sum('amount'),
            num_contributions=Count('transaction_id')
        ).order_by('-total_contributed')[:limit]

        return top_donors


# ==================== PHASE 1 DATA VALIDATION ====================

class Phase1DataValidator:
    """
    Validation queries to ensure data is correctly mapped
    per Ben's requirements
    """
    
    @staticmethod
    def validate_ie_tracking():
        """Verify IE spending is tracked correctly"""
        return {
            'total_ie_transactions': Transaction.objects.filter(
                subject_committee__isnull=False,
                deleted=False
            ).count(),
            
            'ie_committees_count': Committee.objects.filter(
                transactions__subject_committee__isnull=False
            ).distinct().count(),
            
            'candidates_with_ie_spending': Committee.objects.filter(
                subject_of_ies__deleted=False
            ).distinct().count(),
            
            'ie_for_count': Transaction.objects.filter(
                subject_committee__isnull=False,
                is_for_benefit=True,
                deleted=False
            ).count(),
            
            'ie_against_count': Transaction.objects.filter(
                subject_committee__isnull=False,
                is_for_benefit=False,
                deleted=False
            ).count(),
        }
    
    @staticmethod
    def validate_candidate_tracking():
        """Verify candidate committees are properly identified"""
        return {
            'total_committees': Committee.objects.count(),
            'candidate_committees': Committee.objects.filter(
                candidate__isnull=False
            ).count(),
            'candidates_with_office': Committee.objects.filter(
                candidate__isnull=False,
                candidate_office__isnull=False
            ).count(),
            'candidates_with_party': Committee.objects.filter(
                candidate__isnull=False,
                candidate_party__isnull=False
            ).count(),
            'candidates_with_cycle': Committee.objects.filter(
                candidate__isnull=False,
                election_cycle__isnull=False
            ).count(),
        }
    
    @staticmethod
    def validate_donor_tracking():
        """Verify donor entities are properly tracked"""
        return {
            'total_entities': Entity.objects.count(),
            'entities_with_contributions': Entity.objects.filter(
                transactions__transaction_type__income_expense_neutral=1,
                transactions__deleted=False
            ).distinct().count(),
            'total_contribution_transactions': Transaction.objects.filter(
                transaction_type__income_expense_neutral=1,
                deleted=False
            ).count(),
            'unique_donors': Transaction.objects.filter(
                transaction_type__income_expense_neutral=1,
                deleted=False
            ).values('entity').distinct().count(),
        }
    
    @staticmethod
    def check_data_integrity():
        """
        Check for data integrity issues that would prevent
        Ben's required aggregations from working
        """
        issues = []
        
        # Check for IE transactions without subject_committee
        ie_without_subject = Transaction.objects.filter(
            transaction_type__name__icontains='independent expenditure',
            subject_committee__isnull=True
        ).count()
        if ie_without_subject > 0:
            issues.append(f"{ie_without_subject} IE transactions missing subject_committee")
        
        # Check for candidate committees without office
        candidates_no_office = Committee.objects.filter(
            candidate__isnull=False,
            candidate_office__isnull=True
        ).count()
        if candidates_no_office > 0:
            issues.append(f"{candidates_no_office} candidate committees missing office")
        
        # Check for orphaned transactions
        orphaned_txn = Transaction.objects.filter(
            committee__isnull=True
        ).count()
        if orphaned_txn > 0:
            issues.append(f"{orphaned_txn} transactions with null committee")
        
        return issues if issues else ["No data integrity issues found"]



# Add to models.py after CandidateStatementOfInterest
class EmailTemplate(models.Model):
    """Email templates for SOI outreach"""
    name = models.CharField(max_length=200)
    category = models.CharField(
        max_length=50,
        choices=[
            ('soi_initial', 'Initial SOI Request'),
            ('soi_followup', 'SOI Follow-up'),
            ('pledge_reminder', 'Pledge Reminder'),
            ('general', 'General'),
        ],
        default='general',
        db_index=True
    )
    subject = models.TextField()
    body = models.TextField()
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'email_templates'
        ordering = ['name']
        indexes = [
            models.Index(fields=['category', 'is_active'], name='idx_template_cat_active'),
        ]
    
    def __str__(self):
        return self.name

class EmailCampaign(models.Model):
    """Email campaign tracking"""
    name = models.CharField(max_length=200)
    template = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE)
    candidates = models.ManyToManyField(CandidateStatementOfInterest, through='EmailLog')
    scheduled_for = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('scheduled', 'Scheduled'),
            ('sending', 'Sending'),
            ('sent', 'Sent'),
            ('cancelled', 'Cancelled'),
        ],
        default='draft'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'email_campaigns'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    
    
    
class EmailLog(models.Model):
    """Individual email sending logs"""
    campaign = models.ForeignKey(EmailCampaign, on_delete=models.CASCADE, null=True, blank=True)
    candidate = models.ForeignKey(CandidateStatementOfInterest, on_delete=models.CASCADE)
    template = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE)
    tracking_id = models.CharField(max_length=64, unique=True, db_index=True, null=True, blank=True)
    subject = models.TextField()
    body = models.TextField()
    sent_at = models.DateTimeField(null=True, blank=True, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('sending', 'Sending'),
            ('sent', 'Sent'),
            ('failed', 'Failed'),
            ('bounced', 'Bounced'),
        ],
        default='sending',
        db_index=True
    )
    error_message = models.TextField(blank=True)
    opened_at = models.DateTimeField(null=True, blank=True, db_index=True)
    clicked_at = models.DateTimeField(null=True, blank=True, db_index=True)
    
    class Meta:
        db_table = 'email_logs'
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['tracking_id'], name='idx_emaillog_tracking'),
            models.Index(fields=['status', 'sent_at'], name='idx_emaillog_status_sent'),
            models.Index(fields=['campaign', 'status'], name='idx_emaillog_campaign_status'),
        ]
    
    def __str__(self):
        return f"Email to {self.candidate.candidate_name}"


# ==================== AUTHENTICATION & USER PROFILE ====================

class UserProfile(models.Model):
    """Extended user profile for 2FA support"""
    user = models.OneToOneField(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='profile'
    )

    # 2FA fields
    totp_secret = models.CharField(
        max_length=32,
        blank=True,
        help_text='TOTP secret for two-factor authentication'
    )
    is_2fa_enabled = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Has the user enabled 2FA?'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'
        ordering = ['-created_at']
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        indexes = [
            models.Index(fields=['user', 'is_2fa_enabled'], name='idx_profile_user_2fa'),
        ]

    def __str__(self):
        return f"Profile for {self.user.username}"


# ==================== SOI SCRAPE JOB TRACKING ====================

class SOIScrapeJob(models.Model):
    """Track SOI scraping jobs triggered via laptop agent"""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    job_id = models.CharField(max_length=36, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Results
    candidates_found = models.IntegerField(default=0)
    candidates_created = models.IntegerField(default=0)
    candidates_updated = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)

    # Metadata
    triggered_by = models.CharField(max_length=100, default='web')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'soi_scrape_jobs'
        ordering = ['-created_at']

    def __str__(self):
        return f"SOI Scrape {self.job_id} - {self.status}"


# ==================== DARK MONEY DISCLOSURE TRACKING ====================

class DarkMoneyDisclosure(models.Model):
    """
    Track retroactive disclosures of dark money funding sources.

    When dark money groups are later forced to reveal their funding sources
    (e.g., through lawsuits, investigations, or voluntary disclosure),
    this model tracks that information to provide historical context.

    Example: APS revealed in 2019 that they funded $10.7M to Arizona Public
    Service Partners / Save Our Future Arizona for the 2014 Corporation
    Commission race, which wasn't disclosed at the time.
    """

    # The IE committee that spent the dark money
    ie_committee = models.ForeignKey(
        Committee,
        on_delete=models.CASCADE,
        related_name='dark_money_disclosures',
        help_text='The IE committee that received/spent the dark money'
    )

    # The actual funding source revealed later
    funding_source_name = models.CharField(
        max_length=255,
        help_text='Name of the entity that was the actual funding source'
    )
    funding_source_entity = models.ForeignKey(
        Entity,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dark_money_funded',
        help_text='Link to Entity if they exist in our database'
    )

    # Financial details
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text='Amount contributed by the funding source'
    )

    # Election context
    election_year = models.IntegerField(
        db_index=True,
        help_text='Year of the election this spending was for'
    )
    office = models.ForeignKey(
        Office,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Office/race this spending was targeting'
    )

    # Target candidates (who the IE spending was for/against)
    target_candidates = models.TextField(
        blank=True,
        help_text='Names of candidates targeted (comma-separated)'
    )
    is_for_benefit = models.BooleanField(
        null=True,
        blank=True,
        help_text='True if spending supported candidates, False if opposed'
    )

    # Disclosure details
    disclosure_date = models.DateField(
        db_index=True,
        help_text='Date the funding source was publicly revealed'
    )
    disclosure_source = models.TextField(
        help_text='How the disclosure came about (lawsuit, investigation, etc.)'
    )
    source_url = models.URLField(
        max_length=500,
        blank=True,
        help_text='URL to news article or document about the disclosure'
    )

    # Metadata
    notes = models.TextField(
        blank=True,
        help_text='Additional context about this disclosure'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dark_money_disclosures'
        ordering = ['-disclosure_date', '-amount']
        verbose_name = 'Dark Money Disclosure'
        verbose_name_plural = 'Dark Money Disclosures'
        indexes = [
            models.Index(fields=['election_year'], name='idx_darkmoney_year'),
            models.Index(fields=['ie_committee'], name='idx_darkmoney_committee'),
            models.Index(fields=['disclosure_date'], name='idx_darkmoney_disclosed'),
            models.Index(fields=['election_year', 'office'], name='idx_darkmoney_race'),
        ]

    def __str__(self):
        return f"{self.funding_source_name} -> {self.ie_committee.name.full_name} (${self.amount:,.0f})"


# ==================== SITE ANALYTICS ====================

class SiteVisit(models.Model):
    """
    Individual page visit tracking (Google Analytics-like)
    Captures visitor information, location, and behavior
    """
    # Visit identification
    session_id = models.CharField(max_length=64, db_index=True)
    visitor_id = models.CharField(max_length=64, db_index=True, blank=True, help_text='Persistent visitor ID from cookie')

    # Page information
    path = models.CharField(max_length=500, db_index=True)
    page_title = models.CharField(max_length=200, blank=True)
    referrer = models.URLField(max_length=1000, blank=True)

    # Visitor information
    ip_address = models.GenericIPAddressField(db_index=True)
    user_agent = models.TextField(blank=True)
    device_type = models.CharField(max_length=20, blank=True, db_index=True)  # desktop, mobile, tablet
    browser = models.CharField(max_length=50, blank=True, db_index=True)
    os = models.CharField(max_length=50, blank=True, db_index=True)

    # Geolocation (derived from IP)
    country = models.CharField(max_length=100, blank=True, db_index=True)
    country_code = models.CharField(max_length=2, blank=True, db_index=True)
    region = models.CharField(max_length=100, blank=True)  # State/Province
    city = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # Timing
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    time_on_page = models.IntegerField(null=True, blank=True, help_text='Seconds spent on page')

    # User (if authenticated)
    user = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='site_visits'
    )

    class Meta:
        db_table = 'site_visits'
        ordering = ['-timestamp']
        verbose_name = 'Site Visit'
        verbose_name_plural = 'Site Visits'
        indexes = [
            models.Index(fields=['timestamp', 'path'], name='idx_visit_time_path'),
            models.Index(fields=['country_code'], name='idx_visit_country'),
            models.Index(fields=['device_type'], name='idx_visit_device'),
            models.Index(fields=['session_id'], name='idx_visit_session'),
            models.Index(fields=['-timestamp'], name='idx_visit_recent'),
        ]

    def __str__(self):
        return f"{self.path} - {self.ip_address} ({self.timestamp})"


class DailyAnalytics(models.Model):
    """
    Aggregated daily analytics for fast dashboard queries
    Updated periodically via management command or celery task
    """
    date = models.DateField(primary_key=True)

    # Traffic metrics
    total_visits = models.IntegerField(default=0)
    unique_visitors = models.IntegerField(default=0)
    page_views = models.IntegerField(default=0)

    # Top pages (JSON)
    top_pages = models.JSONField(default=dict, help_text='{"path": count, ...}')

    # Geographic breakdown (JSON)
    countries = models.JSONField(default=dict, help_text='{"country_code": count, ...}')
    regions = models.JSONField(default=dict, help_text='{"region": count, ...}')

    # Device breakdown
    desktop_visits = models.IntegerField(default=0)
    mobile_visits = models.IntegerField(default=0)
    tablet_visits = models.IntegerField(default=0)

    # Browser breakdown (JSON)
    browsers = models.JSONField(default=dict, help_text='{"browser": count, ...}')

    # Traffic sources (JSON)
    referrers = models.JSONField(default=dict, help_text='{"referrer": count, ...}')

    # Timing
    avg_time_on_site = models.FloatField(null=True, blank=True, help_text='Average seconds per session')

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'daily_analytics'
        ordering = ['-date']
        verbose_name = 'Daily Analytics'
        verbose_name_plural = 'Daily Analytics'

    def __str__(self):
        return f"Analytics for {self.date}: {self.total_visits} visits"


# =============================================================================
# ADVANCED ANALYTICS MODELS
# =============================================================================

class UserSession(models.Model):
    """
    Track complete user sessions for journey analysis.
    A session groups multiple page visits together.
    """
    session_id = models.CharField(max_length=64, primary_key=True)
    visitor_id = models.CharField(max_length=64, db_index=True)

    # Session timing
    started_at = models.DateTimeField(db_index=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(default=0)

    # Journey data
    page_count = models.IntegerField(default=0)
    pages_visited = models.JSONField(default=list, help_text='Ordered list of pages visited')
    entry_page = models.CharField(max_length=500, blank=True)
    exit_page = models.CharField(max_length=500, blank=True)

    # Engagement scoring
    engagement_score = models.CharField(max_length=20, default='casual', choices=[
        ('casual', 'Casual'),         # 1 page, <30 sec
        ('interested', 'Interested'), # 2-5 pages, 1-3 min
        ('engaged', 'Engaged'),       # 5+ pages, 3+ min
        ('power_user', 'Power User'), # Multiple sessions, advanced features
    ])

    # Visitor context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_type = models.CharField(max_length=20, blank=True)
    browser = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=100, blank=True)
    country_code = models.CharField(max_length=2, blank=True)
    city = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)

    # Referrer info
    referrer = models.URLField(max_length=1000, blank=True)
    referrer_domain = models.CharField(max_length=255, blank=True, db_index=True)
    utm_source = models.CharField(max_length=100, blank=True, db_index=True)
    utm_medium = models.CharField(max_length=100, blank=True)
    utm_campaign = models.CharField(max_length=100, blank=True)

    # Flags
    is_bot = models.BooleanField(default=False)
    is_bounced = models.BooleanField(default=False, help_text='Single page visit')

    class Meta:
        db_table = 'user_sessions'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['visitor_id'], name='idx_session_visitor'),
            models.Index(fields=['started_at'], name='idx_session_started'),
            models.Index(fields=['engagement_score'], name='idx_session_engagement'),
            models.Index(fields=['referrer_domain'], name='idx_session_referrer'),
        ]

    def __str__(self):
        return f"Session {self.session_id[:8]}... ({self.page_count} pages)"


class SearchQuery(models.Model):
    """
    Track user search queries for search analytics.
    """
    query = models.CharField(max_length=500, db_index=True)
    normalized_query = models.CharField(max_length=500, db_index=True, help_text='Lowercase, trimmed')

    # Context
    session_id = models.CharField(max_length=64, blank=True, db_index=True)
    visitor_id = models.CharField(max_length=64, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    # Results
    results_count = models.IntegerField(default=0)
    had_results = models.BooleanField(default=True)
    clicked_result = models.BooleanField(default=False)
    clicked_position = models.IntegerField(null=True, blank=True, help_text='Position of clicked result')

    # Timing
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    response_time_ms = models.IntegerField(null=True, blank=True)

    # Search type
    search_type = models.CharField(max_length=50, default='general', choices=[
        ('general', 'General Search'),
        ('candidate', 'Candidate Search'),
        ('committee', 'Committee Search'),
        ('transaction', 'Transaction Search'),
    ])

    class Meta:
        db_table = 'search_queries'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['normalized_query', '-timestamp'], name='idx_search_query_time'),
            models.Index(fields=['had_results'], name='idx_search_no_results'),
        ]

    def __str__(self):
        return f'"{self.query}" ({self.results_count} results)'


class CandidateView(models.Model):
    """
    Track views of individual candidates for interest heatmap.
    """
    candidate = models.ForeignKey(
        'Entity', on_delete=models.CASCADE, related_name='candidate_views',
        null=True, blank=True
    )
    candidate_name = models.CharField(max_length=255, db_index=True)
    office = models.CharField(max_length=255, blank=True)
    district = models.CharField(max_length=100, blank=True, db_index=True)

    # View context
    session_id = models.CharField(max_length=64, blank=True)
    visitor_id = models.CharField(max_length=64, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    # Geographic
    country = models.CharField(max_length=100, blank=True)
    country_code = models.CharField(max_length=2, blank=True)
    region = models.CharField(max_length=100, blank=True, db_index=True)
    city = models.CharField(max_length=100, blank=True)

    # Engagement
    time_on_page = models.IntegerField(null=True, blank=True, help_text='Seconds')
    scrolled_to_bottom = models.BooleanField(default=False)
    clicked_donation_link = models.BooleanField(default=False)
    viewed_ie_spending = models.BooleanField(default=False)

    # Source
    referrer = models.URLField(max_length=1000, blank=True)
    referrer_domain = models.CharField(max_length=255, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'candidate_views'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['candidate_name', '-timestamp'], name='idx_candview_name_time'),
            models.Index(fields=['district'], name='idx_candview_district'),
            models.Index(fields=['region'], name='idx_candview_region'),
        ]

    def __str__(self):
        return f"View: {self.candidate_name} ({self.timestamp.date()})"


class ReferrerStats(models.Model):
    """
    Aggregated referrer statistics for traffic source analysis.
    """
    domain = models.CharField(max_length=255, db_index=True)
    full_url = models.URLField(max_length=1000, blank=True)

    # Classification
    source_type = models.CharField(max_length=50, default='other', choices=[
        ('social', 'Social Media'),
        ('search', 'Search Engine'),
        ('news', 'News Site'),
        ('direct', 'Direct'),
        ('email', 'Email'),
        ('other', 'Other'),
    ])
    platform = models.CharField(max_length=50, blank=True, help_text='twitter, facebook, google, etc.')

    # Metrics
    visit_count = models.IntegerField(default=0)
    unique_visitors = models.IntegerField(default=0)
    last_seen = models.DateTimeField(auto_now=True)
    first_seen = models.DateTimeField(auto_now_add=True)

    # Quality metrics
    avg_pages_per_session = models.FloatField(default=1.0)
    avg_session_duration = models.FloatField(default=0)
    bounce_rate = models.FloatField(default=0, help_text='Percentage 0-100')

    class Meta:
        db_table = 'referrer_stats'
        ordering = ['-visit_count']
        indexes = [
            models.Index(fields=['source_type', '-visit_count'], name='idx_ref_type_count'),
        ]

    def __str__(self):
        return f"{self.domain} ({self.visit_count} visits)"


class APIUsage(models.Model):
    """
    Track API endpoint usage for API analytics.
    """
    endpoint = models.CharField(max_length=500, db_index=True)
    method = models.CharField(max_length=10, default='GET')

    # Request context
    ip_address = models.GenericIPAddressField(db_index=True)
    user_agent = models.TextField(blank=True)
    api_key = models.CharField(max_length=100, blank=True, db_index=True)
    user = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True
    )

    # Response
    status_code = models.IntegerField(default=200)
    response_time_ms = models.IntegerField(null=True, blank=True)
    response_size_bytes = models.IntegerField(null=True, blank=True)

    # Rate limiting
    is_rate_limited = models.BooleanField(default=False)

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'api_usage'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['endpoint', '-timestamp'], name='idx_api_endpoint_time'),
            models.Index(fields=['ip_address', '-timestamp'], name='idx_api_ip_time'),
        ]

    def __str__(self):
        return f"{self.method} {self.endpoint} ({self.status_code})"


class ContentPerformance(models.Model):
    """
    Track content performance metrics by page/section.
    """
    path = models.CharField(max_length=500, db_index=True)
    content_type = models.CharField(max_length=50, default='page', choices=[
        ('page', 'Page'),
        ('candidate_profile', 'Candidate Profile'),
        ('committee_profile', 'Committee Profile'),
        ('ie_spending', 'IE Spending'),
        ('dark_money', 'Dark Money'),
        ('race_analysis', 'Race Analysis'),
        ('document', 'Document/PDF'),
    ])

    # Date for daily aggregation
    date = models.DateField(db_index=True)

    # Metrics
    views = models.IntegerField(default=0)
    unique_visitors = models.IntegerField(default=0)
    avg_time_on_page = models.FloatField(default=0, help_text='Seconds')
    bounce_rate = models.FloatField(default=0, help_text='Percentage 0-100')
    scroll_depth_avg = models.FloatField(default=0, help_text='Percentage 0-100')

    # Engagement
    total_clicks = models.IntegerField(default=0)
    shares = models.IntegerField(default=0)
    downloads = models.IntegerField(default=0)

    class Meta:
        db_table = 'content_performance'
        unique_together = ['path', 'date']
        ordering = ['-date', '-views']
        indexes = [
            models.Index(fields=['content_type', '-date'], name='idx_content_type_date'),
        ]

    def __str__(self):
        return f"{self.path} ({self.date}): {self.views} views"


class AnomalyAlert(models.Model):
    """
    Store detected anomalies and alerts.
    """
    alert_type = models.CharField(max_length=50, choices=[
        ('traffic_spike', 'Unusual Traffic Spike'),
        ('traffic_drop', 'Unusual Traffic Drop'),
        ('bot_attack', 'Potential Bot Attack'),
        ('geo_anomaly', 'Geographic Anomaly'),
        ('error_spike', 'Error Rate Spike'),
        ('candidate_viral', 'Candidate Going Viral'),
        ('api_abuse', 'API Abuse Detected'),
    ])

    severity = models.CharField(max_length=20, default='medium', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ])

    # Alert details
    title = models.CharField(max_length=200)
    description = models.TextField()
    metric_name = models.CharField(max_length=100, blank=True)
    expected_value = models.FloatField(null=True, blank=True)
    actual_value = models.FloatField(null=True, blank=True)
    threshold = models.FloatField(null=True, blank=True)

    # Context
    related_path = models.CharField(max_length=500, blank=True)
    related_ip = models.GenericIPAddressField(null=True, blank=True)
    related_country = models.CharField(max_length=100, blank=True)

    # Status
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    # Timing
    detected_at = models.DateTimeField(auto_now_add=True, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'anomaly_alerts'
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['alert_type', '-detected_at'], name='idx_alert_type_time'),
            models.Index(fields=['severity', 'is_acknowledged'], name='idx_alert_severity'),
        ]

    def __str__(self):
        return f"[{self.severity.upper()}] {self.title}"


class HourlyTrafficPattern(models.Model):
    """
    Aggregated hourly traffic for time-based pattern analysis.
    """
    date = models.DateField(db_index=True)
    hour = models.IntegerField()  # 0-23

    visits = models.IntegerField(default=0)
    unique_visitors = models.IntegerField(default=0)
    page_views = models.IntegerField(default=0)

    # Device breakdown
    desktop = models.IntegerField(default=0)
    mobile = models.IntegerField(default=0)
    tablet = models.IntegerField(default=0)

    class Meta:
        db_table = 'hourly_traffic'
        unique_together = ['date', 'hour']
        ordering = ['-date', '-hour']

    def __str__(self):
        return f"{self.date} {self.hour}:00 - {self.visits} visits"
