from django.db import models

class Race(models.Model):
    name = models.CharField(max_length=200)
    office = models.CharField(max_length=200, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    is_fake = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Candidate(models.Model):
    SOURCE_CHOICES = [
        ('AZ_SOS', 'Arizona SOS'),
        ('COUNTY', 'County'),
        ('OTHER', 'Other'),
    ]
    name = models.CharField(max_length=255)
    race = models.ForeignKey(Race, on_delete=models.SET_NULL, null=True, blank=True)
    email = models.EmailField(blank=True, null=True)
    filing_date = models.DateField(blank=True, null=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='AZ_SOS')
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
    name = models.CharField(max_length=255)
    committee_type = models.CharField(max_length=100, blank=True, null=True)
    ein = models.CharField(max_length=100, blank=True, null=True)
    is_fake = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class DonorEntity(models.Model):
    name = models.CharField(max_length=255)
    entity_type = models.CharField(max_length=100, blank=True, null=True)
    total_contribution = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    is_fake = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Expenditure(models.Model):
    ie_committee = models.ForeignKey(IECommittee, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    date = models.DateField(null=True, blank=True)
    race = models.ForeignKey(Race, on_delete=models.SET_NULL, null=True, blank=True)
    candidate_name = models.CharField(max_length=255, blank=True, null=True)
    purpose = models.TextField(blank=True, null=True)
    raw = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_fake = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.ie_committee} -> {self.amount} on {self.date}"


class Contribution(models.Model):
    donor = models.ForeignKey(DonorEntity, on_delete=models.CASCADE)
    committee = models.ForeignKey(IECommittee, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    date = models.DateField(null=True, blank=True)
    raw = models.JSONField(blank=True, null=True)
    is_fake = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.donor} -> {self.committee} : {self.amount}"


class ContactLog(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    contacted_by = models.CharField(max_length=255, blank=True, null=True)
    method = models.CharField(max_length=50, default='email')
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_fake = models.BooleanField(default=False)

    def __str__(self):
        return f"Contact: {self.candidate} @ {self.created_at}"
