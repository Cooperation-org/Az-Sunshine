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
        """Income minus expenses"""
        return self.get_total_income() - self.get_total_expenses()
    
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
        Returns total IE spending for/against this candidate
        """
        ie_for = Transaction.objects.filter(
            subject_committee=self,
            is_for_benefit=True,
            deleted=False
        ).aggregate(
            total=Sum('amount'),
            count=Count('transaction_id')
        )
        
        ie_against = Transaction.objects.filter(
            subject_committee=self,
            is_for_benefit=False,
            deleted=False
        ).aggregate(
            total=Sum('amount'),
            count=Count('transaction_id')
        )
        
        return {
            'for': {
                'total': ie_for['total'] or Decimal('0.00'),
                'count': ie_for['count'] or 0
            },
            'against': {
                'total': ie_against['total'] or Decimal('0.00'),
                'count': ie_against['count'] or 0
            },
            'net': (ie_for['total'] or Decimal('0.00')) - (ie_against['total'] or Decimal('0.00'))
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
    contact_date = models.DateField(null=True, blank=True, db_index=True, db_column='contacted_date')
    contacted_by = models.CharField(max_length=100, blank=True)
    
    # Pledge tracking
    pledge_received = models.BooleanField(default=False, db_index=True)
    pledge_date = models.DateField(null=True, blank=True, db_index=True, db_column='pledge_received_date')
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
# ==================== PHASE 1 AGGREGATION MANAGER ====================

class RaceAggregationManager:
    """
    Ben requires: "Aggregate by entity, race, and candidate"
    This provides race-level aggregations
    """
    
    @staticmethod
    def get_race_ie_spending(office, cycle, party=None):
        """
        Get all IE spending for a specific race (office + cycle)
        """
        filters = {
            'subject_committee__candidate_office': office,
            'subject_committee__election_cycle': cycle,
            'deleted': False,
            'subject_committee__isnull': False
        }
        
        if party:
            filters['subject_committee__candidate_party'] = party
        
        race_spending = Transaction.objects.filter(
            **filters
        ).values(
            'subject_committee__committee_id',
            'subject_committee__name__last_name',
            'subject_committee__name__first_name',
            'subject_committee__candidate_party__name',
            'is_for_benefit'
        ).annotate(
            total_ie=Sum('amount'),
            num_expenditures=Count('transaction_id')
        ).order_by('-total_ie')
        
        return race_spending
    
    @staticmethod
    def get_top_ie_donors_by_race(office, cycle, limit=20):
        """
        Ben requires: "Aggregate IE donors by race and candidate"
        Shows top donors impacting a specific race
        """
        # Get all candidates in this race
        candidates = Committee.objects.filter(
            candidate_office=office,
            election_cycle=cycle,
            candidate__isnull=False
        )
        
        # Get IE committees spending on this race
        ie_committees = Committee.objects.filter(
            transactions__subject_committee__in=candidates,
            transactions__deleted=False
        ).distinct()
        
        # Get donors to those IE committees
        top_donors = Transaction.objects.filter(
            committee__in=ie_committees,
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

