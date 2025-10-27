# transparency/urls.py
from django.urls import path, include
from rest_framework import routers
from .views import (
    RaceViewSet,
    CandidateViewSet,
    PartyViewSet,
    IECommitteeViewSet,
    DonorEntityViewSet,
    ExpenditureViewSet,
    ContributionViewSet,
    ContactLogViewSet,
    metrics_view,
)

router = routers.DefaultRouter()
router.register(r"races", RaceViewSet, basename="race")
router.register(r"candidates", CandidateViewSet, basename="candidate")
router.register(r"parties", PartyViewSet, basename="party")
router.register(r"committees", IECommitteeViewSet, basename="committee")
router.register(r"donors", DonorEntityViewSet, basename="donor")
router.register(r"expenditures", ExpenditureViewSet, basename="expenditure")
router.register(r"contributions", ContributionViewSet, basename="contribution")
router.register(r"contactlogs", ContactLogViewSet, basename="contactlog")

urlpatterns = [
    path("api/", include(router.urls)),
    path("api/metrics/", metrics_view, name="metrics"),
]
