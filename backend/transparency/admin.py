from django.contrib import admin
from .models import Race, Candidate, IECommittee, DonorEntity, Expenditure, Contribution, ContactLog


@admin.register(Race)
class RaceAdmin(admin.ModelAdmin):
    list_display = ("name", "office", "district", "is_fake")
    search_fields = ("name", "office", "district")
    list_filter = ("is_fake",)


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "race",
        "email",
        "filing_date",
        "source",
        "contacted",
        "contacted_at",
        "is_fake",
        "created_at",
        "updated_at",
    )
    list_filter = ("source", "contacted", "is_fake")
    search_fields = ("name", "email", "external_id")
    readonly_fields = ("created_at", "updated_at", "contacted_at")
    ordering = ("-created_at",)


@admin.register(IECommittee)
class IECommitteeAdmin(admin.ModelAdmin):
    list_display = ("name", "committee_type", "ein", "is_fake")
    search_fields = ("name", "ein")
    list_filter = ("committee_type", "is_fake")


@admin.register(DonorEntity)
class DonorEntityAdmin(admin.ModelAdmin):
    list_display = ("name", "entity_type", "total_contribution", "is_fake")
    search_fields = ("name",)
    list_filter = ("entity_type", "is_fake")


@admin.register(Expenditure)
class ExpenditureAdmin(admin.ModelAdmin):
    list_display = (
        "ie_committee",
        "amount",
        "date",
        "race",
        "candidate_name",
        "purpose",
        "is_fake",
        "created_at",
    )
    search_fields = ("candidate_name", "purpose", "ie_committee__name")
    list_filter = ("is_fake", "race", "date")
    readonly_fields = ("created_at",)
    ordering = ("-date",)


@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ("donor", "committee", "amount", "date", "is_fake")
    search_fields = ("donor__name", "committee__name")
    list_filter = ("is_fake", "date")


@admin.register(ContactLog)
class ContactLogAdmin(admin.ModelAdmin):
    list_display = (
        "candidate",
        "contacted_by",
        "method",
        "note",
        "created_at",
        "is_fake",
    )
    search_fields = ("candidate__name", "contacted_by", "note")
    list_filter = ("method", "is_fake")
    readonly_fields = ("created_at",)
