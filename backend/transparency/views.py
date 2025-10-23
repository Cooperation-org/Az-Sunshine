from rest_framework import viewsets, filters
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.db.models import Sum, F, Value, DecimalField
from django.db.models.functions import Coalesce

from .models import (
    Race,
    Candidate,
    Party,
    IECommittee,
    DonorEntity,
    Expenditure,
    Contribution,
    ContactLog,
)
from .serializers import (
    RaceSerializer,
    CandidateSerializer,
    PartySerializer,
    IECommitteeSerializer,
    DonorEntitySerializer,
    ExpenditureSerializer,
    ContributionSerializer,
    ContactLogSerializer,
)

# =====================
#  ViewSets
# =====================

class RaceViewSet(viewsets.ModelViewSet):
    """API endpoint for managing election races."""
    queryset = Race.objects.all()
    serializer_class = RaceSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "office", "district"]


class PartyViewSet(viewsets.ModelViewSet):
    """API endpoint for political parties."""
    queryset = Party.objects.all()
    serializer_class = PartySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]


class CandidateViewSet(viewsets.ModelViewSet):
    """API endpoint for candidates."""
    queryset = Candidate.objects.select_related("race", "party").all()
    serializer_class = CandidateSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "race__name", "external_id", "party__name"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]


class IECommitteeViewSet(viewsets.ModelViewSet):
    """API endpoint for Independent Expenditure Committees."""
    queryset = IECommittee.objects.all()
    serializer_class = IECommitteeSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "ein", "committee_type"]
    ordering_fields = ["name"]

    @action(detail=False, methods=["get"])
    def top(self, request):
        """
        Return top 10 IE Committees by total spending.
        Aligned with Transparency Project Phase 1 goal: 
        aggregating IE spending by entity.
        """
        qs = (
            Expenditure.objects.values("ie_committee__name")
            .annotate(
                total=Coalesce(
                    Sum("amount", output_field=DecimalField(max_digits=20, decimal_places=2)),
                    Value(0, output_field=DecimalField(max_digits=20, decimal_places=2))
                )
            )
            .exclude(ie_committee__name__isnull=True)
            .order_by("-total")[:10]
        )
        data = [{"name": row["ie_committee__name"], "total": float(row["total"])} for row in qs]
        return Response(data)


class DonorEntityViewSet(viewsets.ModelViewSet):
    """API endpoint for donor entities."""
    queryset = DonorEntity.objects.all()
    serializer_class = DonorEntitySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "entity_type"]
    ordering_fields = ["name"]

    @action(detail=False, methods=["get"])
    def top(self, request):
        """
        Return top 10 donors by total contributions.
        Helps identify key funders behind IE spending.
        """
        qs = (
            Contribution.objects.values("donor__name")
            .annotate(
                total_contribution=Coalesce(
                    Sum("amount", output_field=DecimalField(max_digits=20, decimal_places=2)),
                    Value(0, output_field=DecimalField(max_digits=20, decimal_places=2))
                )
            )
            .exclude(donor__name__isnull=True)
            .order_by("-total_contribution")[:10]
        )
        data = [
            {
                "name": row["donor__name"],
                "total_contribution": float(row["total_contribution"]),
            }
            for row in qs
        ]
        return Response(data)


class ExpenditureViewSet(viewsets.ModelViewSet):
    """API endpoint for Independent Expenditure records."""
    queryset = Expenditure.objects.select_related("candidate", "race", "ie_committee").all()
    serializer_class = ExpenditureSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["candidate__name", "ie_committee__name", "candidate_name", "purpose"]
    ordering_fields = ["date", "amount"]
    ordering = ["-date"]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("candidate_id"):
            qs = qs.filter(candidate__id=params["candidate_id"])
        if params.get("committee_id"):
            qs = qs.filter(ie_committee__id=params["committee_id"])
        if params.get("race_id"):
            qs = qs.filter(race__id=params["race_id"])
        if params.get("party_id"):
            qs = qs.filter(candidate__party__id=params["party_id"])
        return qs

    @action(detail=False, methods=["get"])
    def summary_by_candidate(self, request):
        """
        Summarize expenditures by candidate and race.
        Supports visualization of IE influence by candidate.
        """
        qs = (
            Expenditure.objects.annotate(
                candidate_label=Coalesce("candidate__name", "candidate_name", Value("Unknown")),
                race_label=Coalesce("race__name", Value("")),
            )
            .values("candidate_label", "race_label")
            .annotate(
                total=Coalesce(
                    Sum("amount", output_field=DecimalField(max_digits=20, decimal_places=2)),
                    Value(0, output_field=DecimalField(max_digits=20, decimal_places=2))
                )
            )
            .order_by("-total")
        )
        formatted = []
        for row in qs:
            name = row["candidate_label"] or "Unknown"
            if row["race_label"]:
                name = f"{name} – {row['race_label']}"
            formatted.append({"name": name, "total": float(row["total"])})
        return Response(formatted)

    @action(detail=False, methods=["get"])
    def support_oppose_by_candidate(self, request):
        """
        Aggregate expenditures by support vs oppose stance.
        Useful for tracking candidate advocacy balance.
        """
        qs = (
            Expenditure.objects.annotate(
                support_label=Coalesce("support_oppose", Value("Unknown"))
            )
            .values("support_label")
            .annotate(
                total=Coalesce(
                    Sum("amount", output_field=DecimalField(max_digits=20, decimal_places=2)),
                    Value(0, output_field=DecimalField(max_digits=20, decimal_places=2))
                )
            )
            .order_by("-total")
        )
        data = [
            {"support_oppose": row["support_label"], "total": float(row["total"])} for row in qs
        ]
        return Response(data)


class ContributionViewSet(viewsets.ModelViewSet):
    """API endpoint for contributions (donor → committee)."""
    queryset = Contribution.objects.select_related("donor", "committee").all()
    serializer_class = ContributionSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["donor__name", "committee__name"]
    ordering_fields = ["amount", "date"]


class ContactLogViewSet(viewsets.ModelViewSet):
    """API endpoint for candidate outreach tracking."""
    queryset = ContactLog.objects.select_related("candidate").all()
    serializer_class = ContactLogSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["candidate__name", "contacted_by", "note"]
    ordering_fields = ["created_at"]


# =====================
#  Metrics Endpoint
# =====================

@api_view(["GET"])
def metrics_view(request):
    """
    Aggregated summary metrics for the Arizona Sunshine dashboard.
    Provides totals and counts for expenditures and candidates.
    """
    total_expenditures = Expenditure.objects.aggregate(
        total=Coalesce(
            Sum("amount", output_field=DecimalField(max_digits=20, decimal_places=2)),
            Value(0, output_field=DecimalField(max_digits=20, decimal_places=2))
        )
    )["total"] or 0

    num_candidates = Candidate.objects.count()
    num_expenditures = Expenditure.objects.count()

    data = {
        "total_expenditures": float(total_expenditures),
        "num_candidates": num_candidates,
        "num_expenditures": num_expenditures,
        "candidates": list(Candidate.objects.values("id", "name")[:50]),
    }
    return Response(data)
