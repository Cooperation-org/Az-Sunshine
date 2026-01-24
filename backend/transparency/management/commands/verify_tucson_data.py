"""
Verify database against known political spending data from tucson.com.

This script checks if key spending records documented by Arizona Daily Star
are present in our database.

Usage:
    python manage.py verify_tucson_data
"""

import json
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db.models import Sum, Q
from transparency.models import Committee, Transaction, Office, Cycle, Entity


class Command(BaseCommand):
    help = 'Verify database against tucson.com documented spending'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Verifying database against tucson.com data...\n'))

        issues = []
        verified = []

        # =================================================================
        # 1. APS DARK MONEY - CORPORATION COMMISSION 2014
        # Expected: $10.7 million total from APS via dark money groups
        # =================================================================
        self.stdout.write(self.style.WARNING('1. Checking Corporation Commission 2014 Dark Money...'))

        corp_comm_offices = Office.objects.filter(
            Q(name__icontains='Corporation Commission') | Q(name__icontains='Corp Comm')
        )

        if corp_comm_offices.exists():
            self.stdout.write(f"   Found offices: {[o.name for o in corp_comm_offices]}")

            # Check for known dark money committees
            dark_money_committees = [
                'Arizona Free Enterprise Club',  # $5.9M
                'Save Our Future Now',  # $3.5M
                'Arizona Cattle Feeders',  # $1.4M
            ]

            for committee_name in dark_money_committees:
                found = Committee.objects.filter(
                    Q(name__last_name__icontains=committee_name) |
                    Q(name__first_name__icontains=committee_name)
                )
                if found.exists():
                    self.stdout.write(self.style.SUCCESS(f"   Found: {committee_name}"))
                    verified.append(f"Corporation Commission 2014: {committee_name}")
                else:
                    self.stdout.write(self.style.ERROR(f"   MISSING: {committee_name}"))
                    issues.append({
                        'category': 'Corporation Commission 2014 Dark Money',
                        'missing': committee_name,
                        'expected_amount': '$5.9M' if 'Free Enterprise' in committee_name else '$3.5M' if 'Save Our' in committee_name else '$1.4M',
                        'source': 'tucson.com - APS admits spending $10.7 million'
                    })
        else:
            self.stdout.write(self.style.ERROR("   MISSING: Corporation Commission office not found"))
            issues.append({
                'category': 'Corporation Commission 2014',
                'missing': 'Corporation Commission office',
                'note': 'Entire office category missing from database'
            })

        # =================================================================
        # 2. GOVERNOR RACES - RGA SPENDING
        # Expected: $8.8M+ from RGA in 2018, $11M+ in 2022
        # =================================================================
        self.stdout.write(self.style.WARNING('\n2. Checking Governor Race Outside Spending...'))

        gov_offices = Office.objects.filter(name__icontains='Governor')

        if gov_offices.exists():
            self.stdout.write(f"   Found offices: {[o.name for o in gov_offices]}")

            # Check for RGA
            rga = Committee.objects.filter(
                Q(name__last_name__icontains='Republican Governors') |
                Q(name__first_name__icontains='RGA')
            )
            if rga.exists():
                self.stdout.write(self.style.SUCCESS(f"   Found RGA: {rga.count()} records"))
                verified.append("Governor races: Republican Governors Association")
            else:
                self.stdout.write(self.style.ERROR("   MISSING: Republican Governors Association"))
                issues.append({
                    'category': 'Governor Races',
                    'missing': 'Republican Governors Association (RGA)',
                    'expected_amount': '$8.8M (2018), $11M+ (2022)',
                    'source': 'tucson.com - RGA spending on Arizona governor races'
                })
        else:
            self.stdout.write(self.style.ERROR("   MISSING: Governor office not found"))
            issues.append({
                'category': 'Governor Races',
                'missing': 'Governor office',
                'note': 'Governor office category missing'
            })

        # =================================================================
        # 3. CD2 FEDERAL RACE - Already documented as missing
        # =================================================================
        self.stdout.write(self.style.WARNING('\n3. Checking Federal Congressional Races...'))

        federal_offices = Office.objects.filter(
            Q(name__icontains='Congress') & Q(office_type='FEDERAL') |
            Q(name__icontains='U.S. House') |
            Q(name__icontains='US House')
        )

        if federal_offices.exists():
            self.stdout.write(self.style.SUCCESS(f"   Found federal offices: {federal_offices.count()}"))
            verified.append("Federal Congressional offices exist")
        else:
            self.stdout.write(self.style.ERROR("   MISSING: No federal Congressional offices"))
            issues.append({
                'category': 'Federal Races',
                'missing': 'U.S. House of Representatives offices',
                'expected_data': [
                    'CD2 2018: $800K+ (Women Vote!, DCCC, Progress Tomorrow)',
                    'CD2 2012-2014: $7.6M+ in ads (Barber vs McSally)',
                    'CD6 2022-2024: Millions in Super PAC spending'
                ],
                'source': 'tucson.com - Multiple articles on CD2/CD6 spending'
            })

        # =================================================================
        # 4. US SENATE RACES
        # Expected: $133.7M total in 2020 (Kelly vs McSally)
        # =================================================================
        self.stdout.write(self.style.WARNING('\n4. Checking US Senate Races...'))

        senate_offices = Office.objects.filter(
            Q(name__icontains='Senate') & Q(office_type='FEDERAL') |
            Q(name__icontains='U.S. Senate') |
            Q(name__icontains='US Senate')
        )

        if senate_offices.exists():
            self.stdout.write(self.style.SUCCESS(f"   Found Senate offices: {senate_offices.count()}"))
            verified.append("US Senate offices exist")
        else:
            self.stdout.write(self.style.ERROR("   MISSING: No US Senate offices"))
            issues.append({
                'category': 'Federal Races',
                'missing': 'U.S. Senate offices',
                'expected_data': [
                    '2018 Sinema vs McSally: $90M total, $58M outside',
                    '2020 Kelly vs McSally: $133.7M - RECORD',
                    '2022 Kelly vs Masters: $31.7M IE spending'
                ],
                'source': 'tucson.com - Arizona Senate race articles'
            })

        # =================================================================
        # 5. KEY CANDIDATES CHECK
        # =================================================================
        self.stdout.write(self.style.WARNING('\n5. Checking Key Candidates Mentioned in tucson.com...'))

        key_candidates = [
            ('Katie Hobbs', 'Governor 2022'),
            ('Doug Ducey', 'Governor 2014/2018'),
            ('Kari Lake', 'Governor 2022'),
            ('Ann Kirkpatrick', 'CD2 2018'),
            ('Martha McSally', 'CD2/Senate'),
            ('Mark Kelly', 'Senate 2020'),
            ('Kyrsten Sinema', 'Senate 2018'),
            ('Tom Forese', 'Corp Commission 2014'),
            ('Doug Little', 'Corp Commission 2014'),
        ]

        for candidate_name, race_info in key_candidates:
            parts = candidate_name.split()
            first_name = parts[0] if len(parts) > 0 else ''
            last_name = parts[-1] if len(parts) > 1 else parts[0]

            found = Committee.objects.filter(
                Q(candidate__last_name__icontains=last_name) |
                Q(name__last_name__icontains=last_name)
            ).filter(
                Q(candidate__first_name__icontains=first_name) |
                Q(name__first_name__icontains=first_name)
            )

            if found.exists():
                self.stdout.write(self.style.SUCCESS(f"   Found: {candidate_name} ({found.count()} records)"))
                verified.append(f"Candidate: {candidate_name}")
            else:
                self.stdout.write(self.style.ERROR(f"   MISSING: {candidate_name} ({race_info})"))
                issues.append({
                    'category': 'Missing Candidates',
                    'missing': candidate_name,
                    'race': race_info,
                    'source': 'tucson.com'
                })

        # =================================================================
        # 6. KEY OUTSIDE SPENDING GROUPS
        # =================================================================
        self.stdout.write(self.style.WARNING('\n6. Checking Key Outside Spending Groups...'))

        outside_groups = [
            ('Americans for Prosperity', '$650K+ CD2 2014'),
            ('House Majority PAC', 'Pro-Democrat spending'),
            ('Senate Majority PAC', 'Pro-Democrat spending'),
            ('NRCC', 'National Republican Congressional Committee'),
            ('DCCC', 'Democratic Congressional Campaign Committee'),
            ('Congressional Leadership Fund', 'Pro-GOP Super PAC'),
            ("Emily's List", 'Women Vote! affiliate'),
        ]

        for group_name, description in outside_groups:
            found = Committee.objects.filter(
                Q(name__last_name__icontains=group_name) |
                Q(name__first_name__icontains=group_name)
            )

            if found.exists():
                self.stdout.write(self.style.SUCCESS(f"   Found: {group_name} ({found.count()} records)"))
                verified.append(f"Outside group: {group_name}")
            else:
                self.stdout.write(self.style.ERROR(f"   MISSING: {group_name} - {description}"))
                issues.append({
                    'category': 'Missing Outside Groups',
                    'missing': group_name,
                    'description': description,
                    'source': 'tucson.com'
                })

        # =================================================================
        # SUMMARY REPORT
        # =================================================================
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('\nVERIFICATION SUMMARY'))
        self.stdout.write('=' * 60)

        self.stdout.write(f"\nVerified items: {len(verified)}")
        for v in verified[:10]:
            self.stdout.write(f"  ✓ {v}")
        if len(verified) > 10:
            self.stdout.write(f"  ... and {len(verified) - 10} more")

        self.stdout.write(self.style.ERROR(f"\nIssues found: {len(issues)}"))

        # Group issues by category
        categories = {}
        for issue in issues:
            cat = issue.get('category', 'Other')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(issue)

        for cat, cat_issues in categories.items():
            self.stdout.write(self.style.WARNING(f"\n{cat}:"))
            for issue in cat_issues:
                self.stdout.write(f"  ✗ {issue.get('missing', 'Unknown')}")
                if 'expected_amount' in issue:
                    self.stdout.write(f"    Expected: {issue['expected_amount']}")
                if 'expected_data' in issue:
                    for item in issue['expected_data']:
                        self.stdout.write(f"    - {item}")

        # Save report
        report = {
            'verified_count': len(verified),
            'issues_count': len(issues),
            'verified': verified,
            'issues': issues,
            'categories': list(categories.keys())
        }

        with open('tucson_verification_report.json', 'w') as f:
            json.dump(report, f, indent=2)

        self.stdout.write(f"\n\nFull report saved to: tucson_verification_report.json")

        if issues:
            self.stdout.write(self.style.WARNING('\n⚠️  ACTION NEEDED: Review missing data above'))
            self.stdout.write('These are records documented by tucson.com that Ben may check.')
