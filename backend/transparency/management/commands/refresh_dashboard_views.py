from django.core.management.base import BaseCommand
from django.db import connection
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Refresh all dashboard materialized views'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔄 Refreshing dashboard materialized views...'))
        
        try:
            with connection.cursor() as cursor:
                # Refresh IE benefit breakdown
                self.stdout.write('Refreshing ie_benefit_breakdown...')
                cursor.execute('REFRESH MATERIALIZED VIEW CONCURRENTLY ie_benefit_breakdown')
                
                # Refresh top committees
                self.stdout.write('Refreshing top_ie_committees_mv...')
                cursor.execute('REFRESH MATERIALIZED VIEW CONCURRENTLY top_ie_committees_mv')
                
                # Refresh top donors
                self.stdout.write('Refreshing top_donors_mv...')
                cursor.execute('REFRESH MATERIALIZED VIEW CONCURRENTLY top_donors_mv')
                
            self.stdout.write(self.style.SUCCESS('✅ All views refreshed successfully!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error refreshing views: {e}'))
            logger.error(f"Error refreshing materialized views: {e}", exc_info=True)