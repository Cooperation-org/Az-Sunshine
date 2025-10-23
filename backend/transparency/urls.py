# transparency/urls.py
from django.urls import path, include
from rest_framework import routers
from .views import (
    RaceViewSet,
    CandidateViewSet,
    IECommitteeViewSet,
    DonorEntityViewSet,
    ExpenditureViewSet,
    metrics_view,
)

router = routers.DefaultRouter()
router.register(r"races", RaceViewSet, basename="race")
router.register(r"candidates", CandidateViewSet, basename="candidate")
router.register(r"committees", IECommitteeViewSet, basename="committee")
router.register(r"donors", DonorEntityViewSet, basename="donor")
router.register(r"expenditures", ExpenditureViewSet, basename="expenditure")

urlpatterns = [
    path("api/", include(router.urls)),
    path("api/metrics/", metrics_view, name="metrics"),
]
