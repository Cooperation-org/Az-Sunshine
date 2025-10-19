from celery import shared_task
from django.core.management import call_command

@shared_task
def run_scrape_soi():
    call_command('scrape_soi')
