from django.urls import path, include
from rest_framework import routers
from .views import RaceViewSet, CandidateViewSet, IECommitteeViewSet, DonorEntityViewSet, ExpenditureViewSet

router = routers.DefaultRouter()
router.register(r"races", RaceViewSet)
router.register(r"candidates", CandidateViewSet)
router.register(r"committees", IECommitteeViewSet)
router.register(r"donors", DonorEntityViewSet)
router.register(r"expenditures", ExpenditureViewSet)

urlpatterns = [
    path("api/", include(router.urls)),
]
