from django.contrib import admin
from .models import Candidate, Race, IECommittee, DonorEntity, Expenditure, Contribution, ContactLog

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('name', 'race', 'email', 'contacted', 'filing_date', 'source')
    list_filter = ('contacted', 'source', 'race')
    search_fields = ('name', 'email')

admin.site.register(Race)
admin.site.register(IECommittee)
admin.site.register(DonorEntity)

@admin.register(Expenditure)
class ExpenditureAdmin(admin.ModelAdmin):
    list_display = ('ie_committee','amount','date','candidate_name')
    search_fields = ('candidate_name','ie_committee__name')
    list_filter = ('date','ie_committee')

@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ('donor','committee','amount','date')
    search_fields = ('donor__name','committee__name')

@admin.register(ContactLog)
class ContactLogAdmin(admin.ModelAdmin):
    list_display = ('candidate','contacted_by','method','created_at')
