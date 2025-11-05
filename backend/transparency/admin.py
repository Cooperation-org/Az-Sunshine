from django.contrib import admin
from .models import (
    County,
    Party,
    Office,
    Cycle,
    EntityType,
    TransactionType,
    ExpenseCategory,
    Entity,
    BallotMeasure,
    Committee,
    Transaction,
    ReportType,
    ReportName,
    Report,
    CandidateStatementOfInterest,
)

# ============================================================
# INLINE ADMINS
# ============================================================

class TransactionInline(admin.TabularInline):
    model = Transaction
    fk_name = "committee"
    extra = 0
    fields = ("transaction_date", "amount", "transaction_type", "entity", "deleted")
    readonly_fields = ("transaction_date", "amount", "transaction_type", "entity", "deleted")
    can_delete = False
    show_change_link = True
    autocomplete_fields = ("entity", "transaction_type")


class ReportInline(admin.TabularInline):
    model = Report
    fk_name = "committee"
    extra = 0
    fields = ("report_id", "cycle", "report_type", "report_name", "filing_datetime")
    readonly_fields = ("report_id", "cycle", "report_type", "report_name", "filing_datetime")
    can_delete = False
    show_change_link = True


# ============================================================
# MAIN ADMIN CLASSES
# ============================================================

@admin.register(Committee)
class CommitteeAdmin(admin.ModelAdmin):
    list_display = (
        "committee_id",
        "name",
        "candidate",
        "candidate_party",
        "candidate_office",
        "election_cycle",
        "is_incumbent",
        "is_active",
    )
    list_filter = (
        "is_incumbent",
        "candidate_party",
        "candidate_office",
        "election_cycle",
        "ballot_measure",
    )
    search_fields = (
        "name__last_name",
        "name__first_name",
        "candidate__last_name",
        "candidate__first_name",
    )
    ordering = ("name__last_name",)
    list_per_page = 50
    inlines = [TransactionInline, ReportInline]
    autocomplete_fields = (
        "name",
        "candidate",
        "candidate_party",
        "candidate_office",
        "candidate_county",
        "sponsor",
        "ballot_measure",
        "election_cycle",
    )


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_id",
        "committee",
        "entity",
        "transaction_type",
        "transaction_date",
        "amount",
        "deleted",
    )
    list_filter = ("deleted", "transaction_type", "category")
    search_fields = (
        "committee__name__last_name",
        "committee__name__first_name",
        "entity__last_name",
        "entity__first_name",
        "entity__organization_name",
    )
    ordering = ("-transaction_date",)
    list_per_page = 100
    autocomplete_fields = ("committee", "entity", "transaction_type", "subject_committee")


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = ("name_id", "full_name", "entity_type", "city", "state", "employer")
    search_fields = ("last_name", "first_name", "employer", "city")
    list_filter = ("entity_type", "state", "county")
    ordering = ("last_name",)
    list_per_page = 50
    autocomplete_fields = ("entity_type", "county")


@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ("party_id", "name", "abbreviation")
    search_fields = ("name", "abbreviation")
    ordering = ("name",)
    list_per_page = 50


@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ("office_id", "name", "office_type")
    search_fields = ("name", "office_type")
    ordering = ("name",)
    list_per_page = 50


@admin.register(Cycle)
class CycleAdmin(admin.ModelAdmin):
    list_display = ("cycle_id", "name", "begin_date", "end_date")
    ordering = ("-begin_date",)
    list_per_page = 20
    search_fields = ("name",)


@admin.register(EntityType)
class EntityTypeAdmin(admin.ModelAdmin):
    list_display = ("entity_type_id", "name")
    search_fields = ("name",)
    ordering = ("name",)
    list_per_page = 50


@admin.register(TransactionType)
class TransactionTypeAdmin(admin.ModelAdmin):
    list_display = ("transaction_type_id", "name", "income_expense_neutral")
    list_filter = ("income_expense_neutral",)
    search_fields = ("name",)
    ordering = ("transaction_type_id",)
    list_per_page = 50


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ("category_id", "name")
    search_fields = ("name",)
    ordering = ("name",)
    list_per_page = 50


@admin.register(County)
class CountyAdmin(admin.ModelAdmin):
    list_display = ("county_id", "name")
    search_fields = ("name",)
    ordering = ("name",)
    list_per_page = 20


@admin.register(BallotMeasure)
class BallotMeasureAdmin(admin.ModelAdmin):
    list_display = ("ballot_measure_id", "sos_identifier", "measure_number", "short_title")
    search_fields = ("sos_identifier", "short_title")
    ordering = ("-sos_identifier",)
    list_per_page = 50


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        "report_id",
        "committee",
        "cycle",
        "report_type",
        "report_name",
        "filing_datetime",
    )
    list_filter = ("cycle", "report_type")
    search_fields = ("committee__name__last_name", "committee__name__first_name")
    ordering = ("-filing_datetime",)
    list_per_page = 50
    autocomplete_fields = ("committee", "cycle", "report_type", "report_name")


@admin.register(ReportType)
class ReportTypeAdmin(admin.ModelAdmin):
    list_display = ("report_type_id", "name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    ordering = ("name",)
    list_per_page = 50


@admin.register(ReportName)
class ReportNameAdmin(admin.ModelAdmin):
    list_display = ("report_name_id", "name")
    search_fields = ("name",)
    ordering = ("name",)
    list_per_page = 50


@admin.register(CandidateStatementOfInterest)
class CandidateStatementOfInterestAdmin(admin.ModelAdmin):
    list_display = (
        "candidate_name",
        "office",
        "filing_date",
        "contact_status",
        "pledge_received",
        "entity",
    )
    list_filter = ("contact_status", "pledge_received", "office")
    search_fields = ("candidate_name", "email")
    ordering = ("-filing_date",)
    list_per_page = 50
    autocomplete_fields = ("office", "entity")


list_display = (
    "candidate_name", "office", "email",
    "filing_date", "contact_status",
    "pledge_received", "pledge_date", "contacted_by"
)
list_filter = ("office", "contact_status", "pledge_received")
search_fields = ("candidate_name", "email")
date_hierarchy = "filing_date"
