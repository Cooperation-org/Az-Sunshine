from django.core.management.base import BaseCommand
from transparency.models import Race, Candidate, IECommittee, DonorEntity, Expenditure
from datetime import date
from decimal import Decimal


class Command(BaseCommand):
    help = "Load dummy data for Phase 1"

    def handle(self, *args, **options):
        Expenditure.objects.all().delete()
        Candidate.objects.all().delete()
        IECommittee.objects.all().delete()
        DonorEntity.objects.all().delete()
        Race.objects.all().delete()

        gov = Race.objects.create(name="Governor", year=2024)
        sen = Race.objects.create(name="State Senate", year=2024)

        alice = Candidate.objects.create(name="Alice Johnson", race=gov, email="alice@gov.com")
        bob = Candidate.objects.create(name="Bob Martinez", race=sen, email="bob@senate.com")
        carla = Candidate.objects.create(name="Carla Lopez", race=sen, email="carla@domain.com")

        freedom_pac = IECommittee.objects.create(name="Freedom PAC", committee_type="Super PAC", filing_id="PAC123")
        future_fund = IECommittee.objects.create(name="Future Fund", committee_type="PAC", filing_id="PAC456")

        john = DonorEntity.objects.create(name="John Smith", entity_type="Individual", address="123 Main St")
        acme = DonorEntity.objects.create(name="ACME Corp", entity_type="Corporation", address="45 Industry Way")

        Expenditure.objects.create(
            committee=freedom_pac, candidate=alice, donor=john,
            amount=Decimal("15000.00"), date=date(2024, 5, 12),
            purpose="TV ads", support_oppose="Support"
        )
        Expenditure.objects.create(
            committee=future_fund, candidate=alice, donor=acme,
            amount=Decimal("8000.00"), date=date(2024, 5, 20),
            purpose="Mailers", support_oppose="Oppose"
        )
        Expenditure.objects.create(
            committee=freedom_pac, candidate=bob, donor=acme,
            amount=Decimal("12000.00"), date=date(2024, 6, 14),
            purpose="Online ads", support_oppose="Support"
        )
        Expenditure.objects.create(
            committee=future_fund, candidate=carla, donor=john,
            amount=Decimal("4200.00"), date=date(2024, 6, 5),
            purpose="Billboards", support_oppose="Support"
        )

        self.stdout.write(self.style.SUCCESS("Dummy data loaded"))
