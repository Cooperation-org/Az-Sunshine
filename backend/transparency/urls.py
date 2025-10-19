from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (CandidateViewSet, RaceViewSet, IECommitteeViewSet, DonorEntityViewSet,
                    ExpenditureViewSet, ContributionViewSet, ContactLogViewSet)

router = DefaultRouter()
router.register(r'candidates', CandidateViewSet)
router.register(r'races', RaceViewSet)
router.register(r'iecommittees', IECommitteeViewSet)
router.register(r'donors', DonorEntityViewSet)
router.register(r'expenditures', ExpenditureViewSet)
router.register(r'contributions', ContributionViewSet)
router.register(r'contacts', ContactLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
