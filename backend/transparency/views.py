from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from .models import Race, Candidate, IECommittee, DonorEntity, Expenditure, Contribution, ContactLog
from .serializers import (
    RaceSerializer,
    CandidateSerializer,
    IECommitteeSerializer,
    DonorEntitySerializer,
    ExpenditureSerializer,
)


class RaceViewSet(viewsets.ModelViewSet):
    queryset = Race.objects.all()
    serializer_class = RaceSerializer
    filter_backends = [filters.SearchFilter]
    # Race model has no 'year' field in your pasted model — avoid searching a non-existent field
    search_fields = ["name", "office", "district"]


class CandidateViewSet(viewsets.ModelViewSet):
    queryset = Candidate.objects.select_related("race").all()
    serializer_class = CandidateSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "race__name", "external_id"]


class IECommitteeViewSet(viewsets.ModelViewSet):
    queryset = IECommittee.objects.all()
    serializer_class = IECommitteeSerializer
    filter_backends = [filters.SearchFilter]
    # filing_id was removed from model; keep searchable fields that exist
    search_fields = ["name", "ein", "committee_type"]


class DonorEntityViewSet(viewsets.ModelViewSet):
    queryset = DonorEntity.objects.all()
    serializer_class = DonorEntitySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "entity_type"]


class ExpenditureViewSet(viewsets.ModelViewSet):
    queryset = Expenditure.objects.select_related("candidate", "race", "ie_committee").all()
    serializer_class = ExpenditureSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["candidate__name", "ie_committee__name", "candidate_name", "purpose"]
    ordering_fields = ["date", "amount"]
    ordering = ["-date"]

    def get_queryset(self):
        qs = super().get_queryset()
        candidate_id = self.request.query_params.get("candidate_id")
        committee_id = self.request.query_params.get("committee_id")
        race_id = self.request.query_params.get("race_id")

        if candidate_id:
            qs = qs.filter(candidate__id=candidate_id)
        if committee_id:
            qs = qs.filter(ie_committee__id=committee_id)
        if race_id:
            qs = qs.filter(race__id=race_id)

        return qs

    @action(detail=False, methods=["get"])
    def summary_by_candidate(self, request):
        """
        Returns list of { label, total } where label is "Candidate – Race"
        Uses candidate_name (raw text) if present; otherwise uses linked candidate.name.
        """
        # Coalesce candidate_name with candidate__name to handle null FK
        data = (
            Expenditure.objects.annotate(
                candidate_label=Coalesce("candidate_name", "candidate__name", Value("Unknown"))
            )
            .values("candidate_label", "race__name")
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )

        formatted = []
        for row in data:
            candidate_label = row.get("candidate_label") or "Unknown"
            race_name = row.get("race__name") or ""
            label = f"{candidate_label} – {race_name}" if race_name else candidate_label
            formatted.append({"label": label, "total": row["total"]})

        return Response(formatted)

    @action(detail=False, methods=["get"])
    def support_oppose_by_candidate(self, request):
        """
        Returns aggregated totals by candidate (via candidate FK) and support/oppose opinion.
        If candidate FK is null, entries will show candidate as null in the response.
        """
        data = (
            Expenditure.objects.values("candidate__name", "support_oppose")
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )
        return Response(data)
