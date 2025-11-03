from django.db import models


# ============================================================================
# RAW MDB MODELS - Must be defined FIRST (referenced by application models)
# ============================================================================

class MDB_EntityType(models.Model):
    """Lookup table for entity types (Individual, Business, Candidate, PAC, etc.)"""
    entity_type_id = models.IntegerField(primary_key=True, db_column='EntityTypeID')
    entity_type_name = models.CharField(max_length=255, db_column='EntityTypeName')
    
    class Meta:
        db_table = 'mdb_entity_types'
        
    def __str__(self):
        return self.entity_type_name


class MDB_TransactionType(models.Model):
    """Lookup table for transaction types (contributions, expenditures, etc.)"""
    transaction_type_id = models.IntegerField(primary_key=True, db_column='TransactionTypeID')
    transaction_type_name = models.CharField(max_length=255, db_column='TransactionTypeName')
    income_expense_neutral_id = models.IntegerField(null=True, blank=True, db_column='IncomeExpenseNeutralID')
    
    class Meta:
        db_table = 'mdb_transaction_types'
        
    def __str__(self):
        return self.transaction_type_name


class MDB_Office(models.Model):
    """Lookup table for political offices"""
    office_id = models.IntegerField(primary_key=True, db_column='OfficeID')
    office_name = models.CharField(max_length=255, db_column='OfficeName')
    
    class Meta:
        db_table = 'mdb_offices'
        
    def __str__(self):
        return self.office_name


class MDB_Category(models.Model):
    """Lookup table for expenditure categories"""
    category_id = models.IntegerField(primary_key=True, db_column='CategoryID')
    category_name = models.CharField(max_length=255, db_column='CategoryName')
    
    class Meta:
        db_table = 'mdb_categories'
        
    def __str__(self):
        return self.category_name


class MDB_Party(models.Model):
    """Raw Parties table"""
    party_id = models.IntegerField(primary_key=True, db_column='PartyID')
    party_name = models.CharField(max_length=255, db_column='PartyName')
    
    class Meta:
        db_table = 'mdb_parties'
        
    def __str__(self):
        return self.party_name


class MDB_Name(models.Model):
    """Raw Names table - contains ALL entities (donors, candidates, committee officers, etc.)"""
    name_id = models.IntegerField(primary_key=True, db_column='NameID')
    name_group_id = models.IntegerField(null=True, blank=True, db_column='NameGroupID')
    entity_type_id = models.IntegerField(null=True, blank=True, db_column='EntityTypeID')
    last_name = models.CharField(max_length=255, blank=True, null=True, db_column='LastName')
    first_name = models.CharField(max_length=255, blank=True, null=True, db_column='FirstName')
    middle_name = models.CharField(max_length=255, blank=True, null=True, db_column='MiddleName')
    suffix = models.CharField(max_length=50, blank=True, null=True, db_column='Suffix')
    address1 = models.CharField(max_length=255, blank=True, null=True, db_column='Address1')
    address2 = models.CharField(max_length=255, blank=True, null=True, db_column='Address2')
    city = models.CharField(max_length=100, blank=True, null=True, db_column='City')
    state = models.CharField(max_length=50, blank=True, null=True, db_column='State')
    zip_code = models.CharField(max_length=20, blank=True, null=True, db_column='ZipCode')
    county_id = models.IntegerField(null=True, blank=True, db_column='CountyID')
    occupation = models.CharField(max_length=255, blank=True, null=True, db_column='Occupation')
    employer = models.CharField(max_length=255, blank=True, null=True, db_column='Employer')
    
    class Meta:
        db_table = 'mdb_names'
        
    def __str__(self):
        if self.first_name:
            return f"{self.first_name} {self.last_name}"
        return self.last_name or f"Name {self.name_id}"


class MDB_Committee(models.Model):
    """Raw Committees table"""
    committee_id = models.IntegerField(primary_key=True, db_column='CommitteeID')
    name_id = models.IntegerField(null=True, blank=True, db_column='NameID')
    chairperson_name_id = models.IntegerField(null=True, blank=True, db_column='ChairpersonNameID')
    treasurer_name_id = models.IntegerField(null=True, blank=True, db_column='TreasurerNameID')
    candidate_name_id = models.IntegerField(null=True, blank=True, db_column='CandidateNameID')
    designee_name_id = models.IntegerField(null=True, blank=True, db_column='DesigneeNameID')
    sponsor_name_id = models.IntegerField(null=True, blank=True, db_column='SponsorNameID')
    ballot_measure_id = models.IntegerField(null=True, blank=True, db_column='BallotMeasureID')
    physical_address1 = models.CharField(max_length=255, blank=True, null=True, db_column='PhysicalAddress1')
    physical_address2 = models.CharField(max_length=255, blank=True, null=True, db_column='PhysicalAddress2')
    physical_city = models.CharField(max_length=100, blank=True, null=True, db_column='PhysicalCity')
    physical_state = models.CharField(max_length=2, blank=True, null=True, db_column='PhysicalState')
    physical_zip_code = models.CharField(max_length=20, blank=True, null=True, db_column='PhysicalZipCode')
    sponsor_type = models.CharField(max_length=100, blank=True, null=True, db_column='SponsorType')
    sponsor_relationship = models.CharField(max_length=100, blank=True, null=True, db_column='SponsorRelationship')
    organization_date = models.CharField(max_length=100, blank=True, null=True, db_column='OrganizationDate')
    termination_date = models.CharField(max_length=100, blank=True, null=True, db_column='TerminationDate')
    benefits_ballot_measure = models.IntegerField(null=True, blank=True, db_column='BenefitsBallotMeasure')
    financial_institution1 = models.CharField(max_length=255, blank=True, null=True, db_column='FinancialInstitution1')
    financial_institution2 = models.CharField(max_length=255, blank=True, null=True, db_column='FinancialInstitution2')
    financial_institution3 = models.CharField(max_length=255, blank=True, null=True, db_column='FinancialInstitution3')
    candidate_party_id = models.IntegerField(null=True, blank=True, db_column='CandidatePartyID')
    candidate_office_id = models.IntegerField(null=True, blank=True, db_column='CandidateOfficeID')
    candidate_county_id = models.IntegerField(null=True, blank=True, db_column='CandidateCountyID')
    candidate_is_incumbent = models.IntegerField(null=True, blank=True, db_column='CandidateIsIncumbent')
    candidate_cycle_id = models.IntegerField(null=True, blank=True, db_column='CandidateCycleID')
    candidate_other_party_name = models.CharField(max_length=100, blank=True, null=True, db_column='CandidateOtherPartyName')
    
    class Meta:
        db_table = 'mdb_committees'
        
    def __str__(self):
        return f"Committee {self.committee_id}"


class MDB_Transaction(models.Model):
    """Raw Transactions table - all financial transactions"""
    transaction_id = models.IntegerField(primary_key=True, db_column='TransactionID')
    modifies_transaction_id = models.IntegerField(null=True, blank=True, db_column='ModifiesTransactionID')
    transaction_type_id = models.IntegerField(null=True, blank=True, db_column='TransactionTypeID')
    committee_id = models.IntegerField(null=True, blank=True, db_column='CommitteeID')
    transaction_date = models.CharField(max_length=100, blank=True, null=True, db_column='TransactionDate')
    amount = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True, db_column='Amount')
    name_id = models.IntegerField(null=True, blank=True, db_column='NameID')
    is_for_benefit = models.IntegerField(null=True, blank=True, db_column='IsForBenefit')
    subject_committee_id = models.IntegerField(null=True, blank=True, db_column='SubjectCommitteeID')
    memo = models.TextField(blank=True, null=True, db_column='Memo')
    category_id = models.IntegerField(null=True, blank=True, db_column='CategoryID')
    account_type = models.CharField(max_length=100, blank=True, null=True, db_column='AccountType')
    deleted = models.IntegerField(null=True, blank=True, db_column='Deleted')
    
    class Meta:
        db_table = 'mdb_transactions'
        
    def __str__(self):
        return f"Transaction {self.transaction_id}: ${self.amount}"


# ============================================================================
# APPLICATION MODELS - Your models with SOURCE REFERENCES added
# ============================================================================

class Party(models.Model):
    """Represents a political party (e.g., Democratic, Republican, Independent)."""
    name = models.CharField(max_length=255, unique=True)
    
    # SOURCE REFERENCE - Link back to raw MDB data
    source_mdb_party = models.ForeignKey(
        MDB_Party, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='app_parties',
        help_text="Original MDB Party record"
    )

    def __str__(self):
        return self.name


class Race(models.Model):
    """Represents an electoral race (e.g., Governor, State Senate District 3)."""
    name = models.CharField(max_length=200)
    office = models.CharField(max_length=200, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    is_fake = models.BooleanField(default=False)
    
    # SOURCE REFERENCE - Link back to raw MDB office data
    source_mdb_office = models.ForeignKey(
        MDB_Office,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='app_races',
        help_text="Original MDB Office record"
    )

    def __str__(self):
        return self.name


class Candidate(models.Model):
    """Represents an election candidate."""
    SOURCE_CHOICES = [
        ("AZ_SOS", "Arizona SOS"),
        ("COUNTY", "County"),
        ("MDB", "CFS Export MDB"),
        ("OTHER", "Other"),
    ]

    name = models.CharField(max_length=255)
    race = models.ForeignKey(Race, on_delete=models.SET_NULL, null=True, blank=True, related_name="candidates")
    party = models.ForeignKey("Party", on_delete=models.SET_NULL, null=True, blank=True, related_name="candidates")

    email = models.EmailField(blank=True, null=True)
    filing_date = models.DateField(blank=True, null=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="AZ_SOS")
    contacted = models.BooleanField(default=False)
    contacted_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    external_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    is_fake = models.BooleanField(default=False)

    # SOURCE REFERENCES - Link back to raw MDB data
    source_mdb_committee = models.ForeignKey(
        MDB_Committee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='app_candidates',
        help_text="Original MDB Committee record (candidate committee)"
    )
    source_mdb_candidate_name = models.ForeignKey(
        MDB_Name,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='app_candidates',
        help_text="Original MDB Name record (the candidate's name)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class IECommittee(models.Model):
    """Independent Expenditure (IE) committees — entities that spend money on candidates."""
    name = models.CharField(max_length=255)
    committee_type = models.CharField(max_length=100, blank=True, null=True)
    ein = models.CharField(max_length=100, blank=True, null=True)
    is_fake = models.BooleanField(default=False)
    
    # SOURCE REFERENCES - Link back to raw MDB data
    source_mdb_committee = models.ForeignKey(
        MDB_Committee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='app_ie_committees',
        help_text="Original MDB Committee record"
    )
    source_mdb_committee_name = models.ForeignKey(
        MDB_Name,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='app_ie_committees',
        help_text="Original MDB Name record (committee's name)"
    )

    def __str__(self):
        return self.name


class DonorEntity(models.Model):
    """Represents a donor or organization contributing funds to committees."""
    name = models.CharField(max_length=255)
    entity_type = models.CharField(max_length=100, blank=True, null=True)
    total_contribution = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    is_fake = models.BooleanField(default=False)
    
    # SOURCE REFERENCE - Link back to raw MDB data
    source_mdb_name = models.ForeignKey(
        MDB_Name,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='app_donors',
        help_text="Original MDB Name record"
    )

    def __str__(self):
        return self.name


class Expenditure(models.Model):
    """Tracks independent expenditures made by committees in support or opposition of candidates."""
    ie_committee = models.ForeignKey(IECommittee, on_delete=models.SET_NULL, null=True, blank=True, related_name="expenditures")
    candidate = models.ForeignKey(Candidate, on_delete=models.SET_NULL, null=True, blank=True, related_name="expenditures")
    race = models.ForeignKey(Race, on_delete=models.SET_NULL, null=True, blank=True, related_name="expenditures")

    amount = models.DecimalField(max_digits=18, decimal_places=2)
    date = models.DateField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True, db_index=True)
    purpose = models.TextField(blank=True, null=True)
    support_oppose = models.CharField(max_length=20, blank=True, null=True)
    candidate_name = models.CharField(max_length=255, blank=True, null=True)

    raw = models.JSONField(blank=True, null=True)
    is_fake = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # SOURCE REFERENCE - Link back to raw MDB data
    source_mdb_transaction = models.ForeignKey(
        MDB_Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='app_expenditures',
        help_text="Original MDB Transaction record"
    )

    def __str__(self):
        return f"{self.ie_committee or 'Unknown Committee'} → {self.amount} ({self.year or 'N/A'})"


class Contribution(models.Model):
    """Tracks financial contributions made by donors to committees."""
    donor = models.ForeignKey(
        DonorEntity,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contributions"
    )
    committee = models.ForeignKey(
        IECommittee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contributions"
    )
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    date = models.DateField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True, db_index=True)
    raw = models.JSONField(blank=True, null=True)
    is_fake = models.BooleanField(default=False)
    
    # SOURCE REFERENCE - Link back to raw MDB data
    source_mdb_transaction = models.ForeignKey(
        MDB_Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='app_contributions',
        help_text="Original MDB Transaction record"
    )

    def __str__(self):
        donor_name = self.donor.name if self.donor else "Unknown Donor"
        committee_name = self.committee.name if self.committee else "Unknown Committee"
        return f"{donor_name} → {committee_name} : {self.amount} ({self.year or 'N/A'})"


class ContactLog(models.Model):
    """Tracks communications with candidates."""
    STATUS_CHOICES = [
        ("not_contacted", "Not Contacted"),
        ("contacted", "Contacted"),
        ("responded", "Responded"),
        ("pledged", "Pledged"),
    ]

    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="contact_logs")
    contacted_by = models.CharField(max_length=255, blank=True, null=True)
    method = models.CharField(max_length=50, default="email")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="not_contacted")
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    pledged_at = models.DateTimeField(null=True, blank=True)
    is_fake = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.candidate} - {self.status}"


class StatementOfInterest(models.Model):
    """Stores candidate Statements of Interest (SOI) data scraped from AZ SOS."""
    unique_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    office = models.CharField(max_length=255, blank=True, null=True)
    party = models.CharField(max_length=100, blank=True, null=True)
    county = models.CharField(max_length=100, blank=True, null=True)
    date_filed = models.CharField(max_length=100, blank=True, null=True)

    raw_data = models.JSONField(blank=True, null=True, help_text="Raw JSON data from the source")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name or 'Unknown'} ({self.office or 'No Office'})"
