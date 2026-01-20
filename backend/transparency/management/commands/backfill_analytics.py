"""
Management command to backfill advanced analytics data from existing SiteVisit records.
This populates UserSession, CandidateView, and HourlyTrafficPattern tables.
"""

from django.core.management.base import BaseCommand
from django.db import transaction, models
from django.db.models import Count, Avg, Q
from django.db.models.functions import ExtractHour, ExtractWeekDay, TruncDate
from django.utils import timezone
from datetime import timedelta
from collections import defaultdict
import hashlib


class Command(BaseCommand):
    help = 'Backfill advanced analytics data from existing SiteVisit records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days of data to backfill (default: 90)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing analytics data before backfilling'
        )

    def handle(self, *args, **options):
        from transparency.models import (
            SiteVisit, UserSession, CandidateView,
            HourlyTrafficPattern, ContentPerformance, Committee
        )

        days = options['days']
        clear = options['clear']

        self.stdout.write(f"Backfilling analytics data for the last {days} days...")

        if clear:
            self.stdout.write("Clearing existing analytics data...")
            UserSession.objects.all().delete()
            CandidateView.objects.all().delete()
            HourlyTrafficPattern.objects.all().delete()
            ContentPerformance.objects.all().delete()

        cutoff = timezone.now() - timedelta(days=days)
        visits = SiteVisit.objects.filter(timestamp__gte=cutoff).order_by('timestamp')

        total = visits.count()
        self.stdout.write(f"Processing {total} visits...")

        # Group visits by session
        sessions = defaultdict(list)
        for visit in visits.iterator():
            sessions[visit.session_id].append(visit)

        self.stdout.write(f"Found {len(sessions)} unique sessions")

        # Create UserSession records
        session_count = 0
        candidate_view_count = 0

        with transaction.atomic():
            for session_id, session_visits in sessions.items():
                if not session_visits:
                    continue

                first_visit = session_visits[0]
                last_visit = session_visits[-1]

                # Build pages list
                pages = [v.path for v in session_visits]
                page_count = len(pages)

                # Calculate duration
                duration = int((last_visit.timestamp - first_visit.timestamp).total_seconds())

                # Determine engagement score
                if page_count >= 5 and duration >= 180:
                    engagement = 'power_user'
                elif page_count >= 3 or duration >= 60:
                    engagement = 'engaged'
                elif page_count >= 2:
                    engagement = 'interested'
                else:
                    engagement = 'casual'

                # Parse referrer
                referrer_source = ''
                referrer_medium = 'direct'
                if first_visit.referrer:
                    from urllib.parse import urlparse
                    try:
                        parsed = urlparse(first_visit.referrer)
                        referrer_source = parsed.netloc
                        if 'google' in referrer_source or 'bing' in referrer_source:
                            referrer_medium = 'organic'
                        elif any(s in referrer_source for s in ['facebook', 'twitter', 'linkedin', 't.co']):
                            referrer_medium = 'social'
                        else:
                            referrer_medium = 'referral'
                    except:
                        pass

                # Create session record
                UserSession.objects.update_or_create(
                    session_id=session_id,
                    defaults={
                        'visitor_id': first_visit.visitor_id,
                        'started_at': first_visit.timestamp,
                        'ended_at': last_visit.timestamp if page_count > 1 else None,
                        'duration_seconds': duration,
                        'page_count': page_count,
                        'pages_visited': pages[:100],  # Limit to prevent huge JSON
                        'entry_page': first_visit.path,
                        'exit_page': last_visit.path,
                        'referrer': first_visit.referrer[:500] if first_visit.referrer else '',
                        'referrer_domain': referrer_source[:100],
                        'utm_medium': referrer_medium,
                        'device_type': first_visit.device_type,
                        'browser': first_visit.browser[:50] if first_visit.browser else '',
                        'country': first_visit.country[:100] if first_visit.country else '',
                        'country_code': first_visit.country_code[:10] if first_visit.country_code else '',
                        'region': first_visit.region[:100] if first_visit.region else '',
                        'city': first_visit.city[:100] if first_visit.city else '',
                        'engagement_score': engagement,
                        'is_bot': False,
                        'is_bounced': page_count == 1,
                    }
                )
                session_count += 1

                # Create CandidateView records for candidate page visits
                for visit in session_visits:
                    if '/candidate/' in visit.path:
                        try:
                            parts = visit.path.strip('/').split('/')
                            candidate_idx = parts.index('candidate') + 1
                            if candidate_idx < len(parts) and parts[candidate_idx].isdigit():
                                candidate_id = int(parts[candidate_idx])
                                committee = Committee.objects.filter(id=candidate_id).first()
                                if committee:
                                    CandidateView.objects.get_or_create(
                                        session_id=session_id,
                                        candidate_id=candidate_id,
                                        defaults={
                                            'visitor_id': visit.visitor_id,
                                            'candidate_name': committee.name[:255],
                                            'district': committee.district[:100] if committee.district else '',
                                            'timestamp': visit.timestamp,
                                            'viewed_ie_spending': False,
                                        }
                                    )
                                    candidate_view_count += 1
                        except (ValueError, IndexError):
                            pass

                if session_count % 100 == 0:
                    self.stdout.write(f"  Processed {session_count} sessions...")

        self.stdout.write(self.style.SUCCESS(f"Created {session_count} UserSession records"))
        self.stdout.write(self.style.SUCCESS(f"Created {candidate_view_count} CandidateView records"))

        # Generate hourly traffic patterns
        self.stdout.write("Generating hourly traffic patterns...")

        # Group by date and hour
        hourly_data = SiteVisit.objects.filter(
            timestamp__gte=cutoff
        ).annotate(
            visit_date=TruncDate('timestamp'),
            hour=ExtractHour('timestamp')
        ).values('visit_date', 'hour').annotate(
            visits=Count('id'),
            unique_visitors=Count('visitor_id', distinct=True),
            desktop_count=Count('id', filter=Q(device_type='desktop')),
            mobile_count=Count('id', filter=Q(device_type='mobile')),
            tablet_count=Count('id', filter=Q(device_type='tablet')),
        ).order_by('visit_date', 'hour')

        pattern_count = 0
        with transaction.atomic():
            for data in hourly_data:
                HourlyTrafficPattern.objects.update_or_create(
                    date=data['visit_date'],
                    hour=data['hour'],
                    defaults={
                        'visits': data['visits'],
                        'unique_visitors': data['unique_visitors'],
                        'page_views': data['visits'],
                        'desktop': data['desktop_count'],
                        'mobile': data['mobile_count'],
                        'tablet': data['tablet_count'],
                    }
                )
                pattern_count += 1

        self.stdout.write(self.style.SUCCESS(f"Created {pattern_count} HourlyTrafficPattern records"))

        # Generate content performance
        self.stdout.write("Generating content performance data...")

        content_data = SiteVisit.objects.filter(
            timestamp__gte=cutoff
        ).exclude(
            path__startswith='/api/'
        ).exclude(
            path__startswith='/static/'
        ).values('path').annotate(
            views=Count('id'),
            unique_visitors=Count('visitor_id', distinct=True),
            avg_time=Avg('time_on_page')
        ).order_by('-views')[:100]

        content_count = 0
        with transaction.atomic():
            for data in content_data:
                ContentPerformance.objects.update_or_create(
                    path=data['path'][:500],
                    date=timezone.now().date(),
                    defaults={
                        'views': data['views'],
                        'unique_visitors': data['unique_visitors'],
                        'avg_time_on_page': int(data['avg_time'] or 0),
                        'bounce_rate': 0.0,
                        'exit_rate': 0.0,
                    }
                )
                content_count += 1

        self.stdout.write(self.style.SUCCESS(f"Created {content_count} ContentPerformance records"))

        # Summary
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("Analytics backfill complete!"))
        self.stdout.write(f"  UserSessions: {UserSession.objects.count()}")
        self.stdout.write(f"  CandidateViews: {CandidateView.objects.count()}")
        self.stdout.write(f"  HourlyPatterns: {HourlyTrafficPattern.objects.count()}")
        self.stdout.write(f"  ContentPerformance: {ContentPerformance.objects.count()}")
