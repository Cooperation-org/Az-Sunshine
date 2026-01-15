"""
Import dark money research data from OpenSecrets, Tucson Star, and other sources.

This command populates the DarkMoneyDisclosure model with retroactive disclosures
of dark money funding sources discovered through investigative journalism and research.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from datetime import date

from transparency.models import (
    Committee, Entity, EntityType, Office, Cycle, DarkMoneyDisclosure
)


class Command(BaseCommand):
    help = 'Import dark money research data from OpenSecrets and investigative journalism'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be made'))

        # Research data compiled from agents
        dark_money_data = self.get_research_data()

        with transaction.atomic():
            created_count = 0
            updated_count = 0

            for record in dark_money_data:
                if dry_run:
                    self.stdout.write(f"Would create: {record['funding_source']} -> {record['ie_committee']} (${record['amount']:,.0f})")
                    continue

                # Get or create the IE committee
                ie_committee = self.get_or_create_committee(record['ie_committee'])

                # Get office if specified
                office = None
                if record.get('office_name'):
                    office = Office.objects.filter(name__icontains=record['office_name']).first()

                # Check if disclosure already exists
                existing = DarkMoneyDisclosure.objects.filter(
                    ie_committee=ie_committee,
                    funding_source_name=record['funding_source'],
                    election_year=record['election_year']
                ).first()

                if existing:
                    # Update existing record
                    existing.amount = Decimal(str(record['amount']))
                    existing.disclosure_source = record['disclosure_source']
                    existing.source_url = record.get('source_url', '')
                    existing.notes = record.get('notes', '')
                    existing.target_candidates = record.get('target_candidates', '')
                    existing.is_for_benefit = record.get('is_for_benefit', True)
                    existing.save()
                    updated_count += 1
                    self.stdout.write(f"Updated: {record['funding_source']} -> {record['ie_committee']}")
                else:
                    # Create new disclosure
                    DarkMoneyDisclosure.objects.create(
                        ie_committee=ie_committee,
                        funding_source_name=record['funding_source'],
                        amount=Decimal(str(record['amount'])),
                        election_year=record['election_year'],
                        office=office,
                        target_candidates=record.get('target_candidates', ''),
                        is_for_benefit=record.get('is_for_benefit', True),
                        disclosure_date=record.get('disclosure_date', date.today()),
                        disclosure_source=record['disclosure_source'],
                        source_url=record.get('source_url', ''),
                        notes=record.get('notes', '')
                    )
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"Created: {record['funding_source']} -> {record['ie_committee']} (${record['amount']:,.0f})"
                    ))

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(
                f'\nImport complete: {created_count} created, {updated_count} updated'
            ))

    def get_or_create_committee(self, committee_name):
        """Get or create a committee by name."""
        # First try to find existing committee by last_name (organizations use last_name for full name)
        entity = Entity.objects.filter(last_name__iexact=committee_name).first()

        if entity:
            committee = Committee.objects.filter(name=entity).first()
            if committee:
                return committee

        # Create new entity and committee
        if not entity:
            # Generate a unique entity_id (name_id in the model) - use 999 million range
            max_entity = Entity.objects.filter(name_id__gte=999000000).order_by('-name_id').first()
            if max_entity:
                new_entity_id = max_entity.name_id + 1
            else:
                new_entity_id = 999000001

            # Get or create an entity type for dark money groups
            entity_type, _ = EntityType.objects.get_or_create(
                entity_type_id=99,
                defaults={'name': 'Dark Money Group'}
            )

            entity = Entity.objects.create(
                name_id=new_entity_id,
                name_group_id=new_entity_id,
                last_name=committee_name,
                first_name='',
                entity_type=entity_type
            )
            self.stdout.write(f"  Created entity: {committee_name}")

        # Create committee - use 999 million range to avoid conflicts
        max_committee = Committee.objects.filter(committee_id__gte=999000000).order_by('-committee_id').first()
        if max_committee:
            new_committee_id = max_committee.committee_id + 1
        else:
            new_committee_id = 999000001

        committee = Committee.objects.create(
            committee_id=new_committee_id,
            name=entity
        )
        self.stdout.write(f"  Created committee: {committee_name}")

        return committee

    def get_research_data(self):
        """
        Compiled research data from OpenSecrets, Tucson Star, Arizona Mirror,
        Campaign Legal Center, and other investigative sources.
        """
        return [
            # === APS/PINNACLE WEST 2014 CORPORATION COMMISSION SCANDAL ===
            {
                'ie_committee': 'Arizona Free Enterprise Club',
                'funding_source': 'Pinnacle West Capital Corp (APS)',
                'amount': 5800000,
                'election_year': 2014,
                'office_name': 'Corporation Commissioner',
                'target_candidates': 'Tom Forese, Doug Little',
                'is_for_benefit': True,
                'disclosure_date': date(2019, 3, 29),
                'disclosure_source': 'Forced disclosure via Corporation Commission subpoena after 5 years of litigation. Commissioner Bob Burns led the investigation.',
                'source_url': 'https://tucson.com/news/local/aps-admits-spending-10-7-million-in-2014-to-elect-two-regulators-of-its-choice/article_bc6636af-c128-5765-8906-482b92a1bf20.html',
                'notes': 'Arizona Free Enterprise Club was the primary conduit for APS dark money. Also spent $733,000 supporting Justin Pierce (son of Commissioner Gary Pierce) for Secretary of State.'
            },
            {
                'ie_committee': 'Save Our Future Now',
                'funding_source': 'Pinnacle West Capital Corp (APS)',
                'amount': 3500000,
                'election_year': 2014,
                'office_name': 'Corporation Commissioner',
                'target_candidates': 'Tom Forese, Doug Little',
                'is_for_benefit': True,
                'disclosure_date': date(2019, 3, 29),
                'disclosure_source': 'Forced disclosure via Corporation Commission subpoena',
                'source_url': 'https://azmirror.com/2019/04/01/aps-docs-reveal-it-funded-2014-dark-money-effort-supporting-commissioners-son/',
                'notes': 'Direct funding from Pinnacle West. Also received $2.7M passed through from Arizona Free Enterprise Club.'
            },
            {
                'ie_committee': 'Arizona Cattle Feeders Association',
                'funding_source': 'Pinnacle West Capital Corp (APS)',
                'amount': 1400000,
                'election_year': 2014,
                'office_name': 'Corporation Commissioner',
                'target_candidates': 'Tom Forese, Doug Little',
                'is_for_benefit': True,
                'disclosure_date': date(2019, 3, 29),
                'disclosure_source': 'Forced disclosure via Corporation Commission subpoena',
                'source_url': 'https://www.phoenixnewtimes.com/news/dark-money-disclosures-aps-questions-utility-spending-forese-little-11263984/',
                'notes': 'Unusual recipient - cattle feeders association used as dark money conduit for Corporation Commission race.'
            },

            # === APS 2016 CORPORATION COMMISSION ===
            {
                'ie_committee': 'Arizona Coalition for Reliable Electricity (ACRE)',
                'funding_source': 'Pinnacle West Capital Corp (APS)',
                'amount': 4200000,
                'election_year': 2016,
                'office_name': 'Corporation Commissioner',
                'target_candidates': 'Boyd Dunn, Bob Burns, Andy Tobin',
                'is_for_benefit': True,
                'disclosure_date': date(2019, 4, 1),
                'disclosure_source': 'APS financial disclosures and investigative reporting',
                'source_url': 'https://energyandpolicy.org/arizona-regulator-investigation-unveils-arizona-public-service-companys-political-spending/',
                'notes': 'APS created this PAC specifically for 2016 ACC races. Goal was to maintain Republican control of the commission.'
            },

            # === APS 2018 PROPOSITION 127 ===
            {
                'ie_committee': 'Arizonans for Affordable Energy',
                'funding_source': 'Pinnacle West Capital Corp (APS)',
                'amount': 38000000,
                'election_year': 2018,
                'office_name': None,
                'target_candidates': 'Proposition 127 (Clean Energy Initiative)',
                'is_for_benefit': False,
                'disclosure_date': date(2018, 11, 6),
                'disclosure_source': 'Campaign finance filings - openly disclosed',
                'source_url': 'https://www.opensecrets.org/news/2024/11/outside-spending-on-2024-elections-shatters-records-fueled-by-billion-dollar-dark-money-infusion/',
                'notes': 'Unlike 2014, this spending was openly disclosed. APS spent nearly $40M to defeat renewable energy ballot initiative.'
            },

            # === LD2/LD3 2020 HERNANDEZ SIBLINGS ===
            {
                'ie_committee': 'Arizona Integrity PAC',
                'funding_source': 'Responsible Leadership for AZ (Realtors)',
                'amount': 109095,
                'election_year': 2020,
                'office_name': 'State Representative',
                'target_candidates': 'Daniel Hernandez, Alma Hernandez',
                'is_for_benefit': True,
                'disclosure_date': date(2020, 7, 28),
                'disclosure_source': 'Campaign finance filings via Arizona Secretary of State',
                'source_url': 'https://tucson.com/news/local/govt-and-politics/tim-stellers-opinion-outside-money-pushing-for-re-election-of-hernandez-siblings/article_31cdab94-4ec4-51b0-af54-02de2296a6ad.html',
                'notes': 'Arizona Integrity PAC spent $68,440 for Alma Hernandez, $40,655 for Daniel Hernandez. Funded by Realtors of AZ PAC ($500,000) and corporate interests including Southwest Gas and Pinnacle West.'
            },
            {
                'ie_committee': 'Better Leaders Better Arizona',
                'funding_source': 'Unite America (Kathryn Murdoch)',
                'amount': 97948,
                'election_year': 2020,
                'office_name': 'State Representative',
                'target_candidates': 'Daniel Hernandez, Alma Hernandez',
                'is_for_benefit': True,
                'disclosure_date': date(2020, 7, 28),
                'disclosure_source': 'Campaign finance filings and InfluenceWatch research',
                'source_url': 'https://www.influencewatch.org/political-party/unite-america/',
                'notes': 'Funded by Unite America, which received at least $9M from Kathryn Murdoch (daughter-in-law of Rupert Murdoch). Spent $49,192 for Daniel, $48,756 for Alma.'
            },

            # === 2024 FEDERAL RACES ===
            {
                'ie_committee': 'Progress Arizona',
                'funding_source': 'Multiple Democratic donors',
                'amount': 4267117,
                'election_year': 2024,
                'office_name': None,
                'target_candidates': 'Various Democratic candidates',
                'is_for_benefit': True,
                'disclosure_date': date(2024, 11, 1),
                'disclosure_source': 'OpenSecrets FEC filings',
                'source_url': 'https://www.opensecrets.org/political-action-committees-pacs/C00746107/summary/2024',
                'notes': 'Liberal Super PAC. 2023-2024 cycle fundraising. Previously known as ProgressNow Arizona.'
            },
            {
                'ie_committee': 'Americans for Prosperity Action',
                'funding_source': 'Koch Network / Stand Together Chamber of Commerce',
                'amount': 780000,
                'election_year': 2024,
                'office_name': 'State Representative',
                'target_candidates': 'Ben Toma, other GOP candidates',
                'is_for_benefit': True,
                'disclosure_date': date(2024, 11, 1),
                'disclosure_source': 'OpenSecrets reporting',
                'source_url': 'https://www.opensecrets.org/orgs/americans-for-prosperity/summary?id=D000024046',
                'notes': 'Arizona-specific spending from Koch network. AFP received $330M from Stand Together Chamber of Commerce nationally in 2024 cycle.'
            },
            {
                'ie_committee': 'Protect Progress',
                'funding_source': 'Cryptocurrency industry donors',
                'amount': 1400000,
                'election_year': 2024,
                'office_name': None,
                'target_candidates': 'Yassamin Ansari (AZ-03)',
                'is_for_benefit': True,
                'disclosure_date': date(2024, 8, 1),
                'disclosure_source': 'OpenSecrets / Brennan Center reporting',
                'source_url': 'https://www.brennancenter.org/our-work/analysis-opinion/arizona-races-funded-national-donors',
                'notes': 'Largest spender in AZ-03 Democratic primary. Crypto-funded Super PAC. Ansari won by 39 votes.'
            },
            {
                'ie_committee': 'LCV Victory Fund',
                'funding_source': 'League of Conservation Voters',
                'amount': 2800000,
                'election_year': 2024,
                'office_name': None,
                'target_candidates': 'Democratic candidates statewide',
                'is_for_benefit': True,
                'disclosure_date': date(2024, 11, 1),
                'disclosure_source': 'OpenSecrets FEC filings',
                'source_url': 'https://www.opensecrets.org/outside-spending/detail/2024?cmte=C00746107',
                'notes': 'Environmental advocacy Super PAC. Does not fully disclose all donors.'
            },

            # === HISTORICAL DARK MONEY CASES ===
            {
                'ie_committee': 'Center to Protect Patient Rights',
                'funding_source': 'Koch Brothers Network',
                'amount': 15000000,
                'election_year': 2012,
                'office_name': None,
                'target_candidates': 'California Propositions 30 and 32',
                'is_for_benefit': False,
                'disclosure_date': date(2013, 10, 24),
                'disclosure_source': 'California FPPC investigation - record $1M fine',
                'source_url': 'https://www.tucsonsentinel.com/local/report/102513_az_koch_dark_money/2-az-dark-money-groups-pay-record-1m-fine-calif/',
                'notes': 'Arizona-based dark money group funneled $18M to Americans for Responsible Leadership. Paid record $1M fine in California. Operated from PO box in Arizona.'
            },
            {
                'ie_committee': 'Our Southern Arizona',
                'funding_source': 'Don Diamond (land investor)',
                'amount': 175000,
                'election_year': 2016,
                'office_name': None,
                'target_candidates': 'Sharon Bronson (Pima County Supervisor)',
                'is_for_benefit': True,
                'disclosure_date': date(2016, 10, 1),
                'disclosure_source': 'Tim Steller investigative reporting - Tucson Star',
                'source_url': 'https://tucson.com/news/local/columnists/steller/article_f2d8a1c8-ef61-5983-a194-80fb9f5c1200.html',
                'notes': 'Pima County Supervisor race. Diamond disclosed as founder with $175,000. Other funders included Larry Hecker and Mark Irvin.'
            },
            {
                'ie_committee': 'America Revived PAC',
                'funding_source': 'Suspected: Jim Click, Hank Amos (not confirmed)',
                'amount': 200000,
                'election_year': 2016,
                'office_name': None,
                'target_candidates': 'Kim DeMarco (Pima County Supervisor)',
                'is_for_benefit': True,
                'disclosure_date': date(2016, 10, 1),
                'disclosure_source': 'Tim Steller investigative reporting',
                'source_url': 'https://tucson.com/news/local/columnists/steller/article_f2d8a1c8-ef61-5983-a194-80fb9f5c1200.html',
                'notes': 'Nathan Sproul (Lincoln Strategy Group) was treasurer. Original funders never confirmed.'
            },
        ]
