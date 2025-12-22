# views_ad_buys.py - Ad Buy tracking with volunteer crowdsourced reporting
# Phase 2: Race View Implementation

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from django.db.models import Sum, Q
from .models import AdBuy, Committee
from .serializers import AdBuySerializer, AdBuyCreateSerializer


class AdBuyPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class AdBuyViewSet(viewsets.ModelViewSet):
    """
    Ad Buy tracking with volunteer crowdsourced reporting

    List/Retrieve: Public (verified ads only)
    Create: Public (volunteer submissions)
    Update/Delete/Verify: Admin only
    """
    queryset = AdBuy.objects.all()
    serializer_class = AdBuySerializer
    pagination_class = AdBuyPagination

    def get_permissions(self):
        """
        Public can view verified ads and submit new ones
        Admins can do everything
        """
        if self.action in ['list', 'retrieve', 'create', 'stats']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == 'create':
            return AdBuyCreateSerializer
        return AdBuySerializer

    def get_queryset(self):
        queryset = AdBuy.objects.select_related(
            'ie_committee', 'ie_committee__name',
            'candidate', 'candidate__name', 'candidate__candidate_office',
            'verified_by'
        )

        # Public users only see verified ads
        if not (self.request.user and self.request.user.is_staff):
            queryset = queryset.filter(verified=True, rejected=False)

        # Filter by candidate
        candidate_id = self.request.query_params.get('candidate_id')
        if candidate_id:
            queryset = queryset.filter(candidate_id=candidate_id)

        # Filter by office + cycle (for race view)
        office_id = self.request.query_params.get('office_id')
        cycle_id = self.request.query_params.get('cycle_id')
        if office_id and cycle_id:
            queryset = queryset.filter(
                candidate__candidate_office_id=office_id,
                candidate__election_cycle_id=cycle_id
            )

        # Filter by platform
        platform = self.request.query_params.get('platform')
        if platform:
            queryset = queryset.filter(platform=platform)

        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(ad_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(ad_date__lte=date_to)

        # Admin-only filters
        if self.request.user and self.request.user.is_staff:
            status_filter = self.request.query_params.get('status')
            if status_filter == 'pending':
                queryset = queryset.filter(verified=False, rejected=False)
            elif status_filter == 'rejected':
                queryset = queryset.filter(rejected=True)

        return queryset.order_by('-ad_date', '-reported_at')

    def perform_create(self, serializer):
        """Handle volunteer submission"""
        serializer.save(
            verified=False,
            rejected=False
        )

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def pending_review(self, request):
        """Admin queue: Get all pending ad buys"""
        pending = self.get_queryset().filter(
            verified=False,
            rejected=False
        ).order_by('reported_at')

        page = self.paginate_queryset(pending)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(pending, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def verify(self, request, pk=None):
        """Admin action: Verify an ad buy"""
        ad_buy = self.get_object()

        # Update fields from request
        ad_buy.verified = True
        ad_buy.verified_at = timezone.now()
        ad_buy.verified_by = request.user
        ad_buy.rejected = False

        # Admin can update IE committee/candidate links
        if 'ie_committee_id' in request.data:
            ad_buy.ie_committee_id = request.data['ie_committee_id']
        if 'candidate_id' in request.data:
            ad_buy.candidate_id = request.data['candidate_id']
        if 'admin_notes' in request.data:
            ad_buy.admin_notes = request.data['admin_notes']

        ad_buy.save()

        serializer = self.get_serializer(ad_buy)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reject(self, request, pk=None):
        """Admin action: Reject an ad buy"""
        ad_buy = self.get_object()

        ad_buy.rejected = True
        ad_buy.verified = False
        ad_buy.rejection_reason = request.data.get('reason', '')
        ad_buy.save()

        serializer = self.get_serializer(ad_buy)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get ad buy statistics for a race"""
        office_id = request.query_params.get('office_id')
        cycle_id = request.query_params.get('cycle_id')

        if not office_id or not cycle_id:
            return Response(
                {'error': 'office_id and cycle_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = self.get_queryset().filter(
            candidate__candidate_office_id=office_id,
            candidate__election_cycle_id=cycle_id,
            verified=True,
            rejected=False
        )

        stats = {
            'total_ads': queryset.count(),
            'by_platform': {},
            'by_candidate': {},
            'total_estimated_spend': 0
        }

        # Group by platform
        platform_choices = dict(AdBuy._meta.get_field('platform').choices)
        for platform_code in platform_choices.keys():
            count = queryset.filter(platform=platform_code).count()
            if count > 0:
                stats['by_platform'][platform_code] = {
                    'count': count,
                    'label': platform_choices[platform_code]
                }

        # Group by candidate
        candidates_data = queryset.values(
            'candidate__name__last_name',
            'candidate__name__first_name',
            'candidate_id'
        ).distinct()

        for cand in candidates_data:
            cand_name = f"{cand['candidate__name__first_name']} {cand['candidate__name__last_name']}" if cand['candidate__name__first_name'] else cand['candidate__name__last_name']
            cand_ads = queryset.filter(candidate_id=cand['candidate_id'])

            stats['by_candidate'][cand_name] = {
                'candidate_id': cand['candidate_id'],
                'support': cand_ads.filter(support_oppose='support').count(),
                'oppose': cand_ads.filter(support_oppose='oppose').count(),
                'neutral': cand_ads.filter(support_oppose='neutral').count(),
            }

        # Estimated spend
        total = queryset.aggregate(
            total=Sum('approximate_spend')
        )['total']
        stats['total_estimated_spend'] = float(total or 0)

        return Response(stats)
