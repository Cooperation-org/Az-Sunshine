from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from .models import Candidate, Race, IECommittee, DonorEntity, Expenditure, Contribution, ContactLog
from .serializers import (CandidateSerializer, RaceSerializer, IECommitteeSerializer,
                          DonorEntitySerializer, ExpenditureSerializer, ContributionSerializer, ContactLogSerializer)
from django.utils import timezone
from django.shortcuts import render



def home(request):
    return render(request, "home.html")

def docs(request):
    return render(request, "docs.html")

def contact(request):
    return render(request, "contact.html")


class CandidateViewSet(viewsets.ModelViewSet):
    queryset = Candidate.objects.all().select_related('race')
    serializer_class = CandidateSerializer
    filterset_fields = ['contacted','source','race__id']

    @action(detail=True, methods=['post'])
    def mark_contacted(self, request, pk=None):
        candidate = self.get_object()
        candidate.contacted = True
        candidate.contacted_at = timezone.now()
        candidate.save()
        return Response({'status':'contacted'})

class RaceViewSet(viewsets.ModelViewSet):
    queryset = Race.objects.all()
    serializer_class = RaceSerializer

class IECommitteeViewSet(viewsets.ModelViewSet):
    queryset = IECommittee.objects.all()
    serializer_class = IECommitteeSerializer

class DonorEntityViewSet(viewsets.ModelViewSet):
    queryset = DonorEntity.objects.all()
    serializer_class = DonorEntitySerializer

class ExpenditureViewSet(viewsets.ModelViewSet):
    queryset = Expenditure.objects.all().select_related('ie_committee','race')
    serializer_class = ExpenditureSerializer
    filterset_fields = ['ie_committee','race','date']

    @action(detail=False, methods=['get'])
    def summary_by_race(self, request):
        qs = Expenditure.objects.values('race__id','race__name').annotate(total=Sum('amount')).order_by('-total')
        return Response(qs)

class ContributionViewSet(viewsets.ModelViewSet):
    queryset = Contribution.objects.all()
    serializer_class = ContributionSerializer

class ContactLogViewSet(viewsets.ModelViewSet):
    queryset = ContactLog.objects.all()
    serializer_class = ContactLogSerializer
