from django.db import models


class Party(models.Model):
    """Represents a political party (e.g., Democratic, Republican, Independent)."""
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Race(models.Model):
    """Represents an electoral race (e.g., Governor, State Senate District 3)."""
    name = models.CharField(max_length=200)
    office = models.CharField(max_length=200, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    is_fake = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Candidate(models.Model):
    """Represents an election candidate."""
    SOURCE_CHOICES = [
        ("AZ_SOS", "Arizona SOS"),
        ("COUNTY", "County"),
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

    def __str__(self):
        return self.name


class DonorEntity(models.Model):
    """Represents a donor or organization contributing funds to committees."""
    name = models.CharField(max_length=255)
    entity_type = models.CharField(max_length=100, blank=True, null=True)
    total_contribution = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    is_fake = models.BooleanField(default=False)

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
