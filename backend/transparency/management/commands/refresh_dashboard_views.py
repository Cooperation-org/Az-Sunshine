from django.core.management.base import BaseCommand
from django.db import connection
from django.core.cache import cache
import logging
import time

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Refresh all dashboard materialized views'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Refreshing all dashboard materialized views...\n'))

        total_start = time.time()

        # Views that can be refreshed concurrently (have unique indexes)
        concurrent_views = [
            'ie_benefit_breakdown',
            'mv_dashboard_top_donors',
            'mv_dashboard_top_ie_committees',
            'top_donors_mv',
            'top_ie_committees_mv',
            'mv_committee_ie_summary'
        ]

        # Views without unique indexes (must refresh non-concurrently)
        non_concurrent_views = [
            'mv_dashboard_support_oppose',
            'mv_dashboard_recent_expenditures',
            'dashboard_aggregations'
        ]

        try:
            with connection.cursor() as cursor:
                # Refresh concurrent views
                for view in concurrent_views:
                    start = time.time()
                    self.stdout.write(f'Refreshing {view}...', ending=' ')
                    try:
                        cursor.execute(f'REFRESH MATERIALIZED VIEW CONCURRENTLY {view}')
                        elapsed = time.time() - start
                        self.stdout.write(self.style.SUCCESS(f'Done in {elapsed:.2f}s'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error: {e}'))

                # Refresh non-concurrent views
                for view in non_concurrent_views:
                    start = time.time()
                    self.stdout.write(f'Refreshing {view}...', ending=' ')
                    try:
                        cursor.execute(f'REFRESH MATERIALIZED VIEW {view}')
                        elapsed = time.time() - start
                        self.stdout.write(self.style.SUCCESS(f'Done in {elapsed:.2f}s'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error: {e}'))

            # Clear Django cache
            self.stdout.write('\n🗑️  Clearing Django cache...', ending=' ')
            cache.delete('dashboard_summary_v1')
            cache.delete('dashboard_charts_fast_v2')
            cache.delete('dashboard_recent_exp_v1')
            self.stdout.write(self.style.SUCCESS('Done'))

            total_elapsed = time.time() - total_start
            self.stdout.write(self.style.SUCCESS(f'\nAll views refreshed successfully in {total_elapsed:.2f}s!'))
            self.stdout.write(self.style.SUCCESS('Dashboard should now load instantly!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nError refreshing views: {e}'))
            logger.error(f"Error refreshing materialized views: {e}", exc_info=True)