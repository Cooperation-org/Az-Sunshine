"""
Django management command to validate Phase 1 data mapping
against Ben's requirements

Usage:
    python manage.py validate_phase1_data
    python manage.py validate_phase1_data --detailed
"""

from django.core.management.base import BaseCommand
from django.db.models import Sum, Count, Q, F
from decimal import Decimal
from transparency.models import *


class Command(BaseCommand):
    help = 'Validate Phase 1 data mapping per Ben\'s requirements'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed breakdowns and sample data'
        )

    def handle(self, *args, **options):
        detailed = options['detailed']
        
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 70))
        self.stdout.write(self.style.SUCCESS('ARIZONA SUNSHINE - PHASE 1 DATA VALIDATION'))
        self.stdout.write(self.style.SUCCESS('Verifying data mapping per Ben\'s requirements'))
        self.stdout.write(self.style.SUCCESS('=' * 70 + '\n'))
        
        # Run all validation checks
        self.check_basic_data_loading()
        self.check_candidate_tracking()
        self.check_ie_spending_tracking()
        self.check_donor_tracking()
        self.check_race_aggregations()
        self.check_grassroots_threshold()
        self.check_data_integrity()
        
        if detailed:
            self.show_detailed_examples()
        
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 70))
        self.stdout.write(self.style.SUCCESS('VALIDATION COMPLETE'))
        self.stdout.write(self.style.SUCCESS('=' * 70 + '\n'))

    def check_basic_data_loading(self):
        """Verify all lookup tables and main tables have data"""
        self.stdout.write(self.style.WARNING('\n[1] BASIC DATA LOADING'))
        self.stdout.write('-' * 70)
        
        tables = [
            ('Counties', County),
            ('Parties', Party),
            ('Offices', Office),
            ('Cycles', Cycle),
            ('Entity Types', EntityType),
            ('Transaction Types', TransactionType),
            ('Expense Categories', ExpenseCategory),
            ('Report Types', ReportType),
            ('Report Names', ReportName),
            ('Ballot Measures', BallotMeasure),
            ('Entities (Names)', Entity),
            ('Committees', Committee),
            ('Transactions', Transaction),
            ('Reports', Report),
        ]
        
        all_ok = True
        for name, model in tables:
            count = model.objects.count()
            status = '✓' if count > 0 else '✗'
            color = self.style.SUCCESS if count > 0 else self.style.ERROR
            self.stdout.write(color(f'{status} {name:.<50} {count:>15,}'))
            if count == 0:
                all_ok = False
        
        if all_ok:
            self.stdout.write(self.style.SUCCESS('\n✓ All tables loaded successfully'))
        else:
            self.stdout.write(self.style.ERROR('\n✗ Some tables are empty!'))

    def check_candidate_tracking(self):
        """
        Ben's requirement: "create public-facing django-based transparency app 
        and data models for candidates, races"
        """
        self.stdout.write(self.style.WARNING('\n[2] CANDIDATE TRACKING'))
        self.stdout.write('-' * 70)
        
        total_committees = Committee.objects.count()
        candidate_committees = Committee.objects.filter(candidate__isnull=False).count()
        with_office = Committee.objects.filter(
            candidate__isnull=False,
            candidate_office__isnull=False
        ).count()
        with_party = Committee.objects.filter(
            candidate__isnull=False,
            candidate_party__isnull=False
        ).count()
        with_cycle = Committee.objects.filter(
            candidate__isnull=False,
            election_cycle__isnull=False
        ).count()
        
        self.stdout.write(f'Total Committees: {total_committees:,}')
        self.stdout.write(f'Candidate Committees: {candidate_committees:,}')
        self.stdout.write(f'  - With Office: {with_office:,}')
        self.stdout.write(f'  - With Party: {with_party:,}')
        self.stdout.write(f'  - With Cycle: {with_cycle:,}')
        
        if candidate_committees == 0:
            self.stdout.write(self.style.ERROR('\n✗ CRITICAL: No candidate committees found!'))
        elif with_office < candidate_committees * 0.9:
            self.stdout.write(self.style.WARNING(
                f'\n⚠ WARNING: {candidate_committees - with_office:,} candidates missing office info'
            ))
        else:
            self.stdout.write(self.style.SUCCESS('\n✓ Candidate tracking looks good'))

    def check_ie_spending_tracking(self):
        """
        Ben's requirement: "Aggregate by entity, race, and candidate"
        and "Track outside spending"
        """
        self.stdout.write(self.style.WARNING('\n[3] INDEPENDENT EXPENDITURE TRACKING'))
        self.stdout.write('-' * 70)
        
        ie_txns = Transaction.objects.filter(
            subject_committee__isnull=False,
            deleted=False
        )
        
        total_ie = ie_txns.count()
        ie_for = ie_txns.filter(is_for_benefit=True).count()
        ie_against = ie_txns.filter(is_for_benefit=False).count()
        
        amount_for = ie_txns.filter(is_for_benefit=True).aggregate(
            total=Sum('amount'))['total'] or Decimal('0.00')
        amount_against = ie_txns.filter(is_for_benefit=False).aggregate(
            total=Sum('amount'))['total'] or Decimal('0.00')
        
        candidates_with_ie = Committee.objects.filter(
            subject_of_ies__deleted=False
        ).distinct().count()
        
        ie_committees = Committee.objects.filter(
            transactions__subject_committee__isnull=False,
            transactions__deleted=False
        ).distinct().count()
        
        self.stdout.write(f'Total IE Transactions: {total_ie:,}')
        self.stdout.write(f'  - FOR candidates: {ie_for:,} (${amount_for:,.2f})')
        self.stdout.write(f'  - AGAINST candidates: {ie_against:,} (${amount_against:,.2f})')
        self.stdout.write(f'Candidates with IE spending: {candidates_with_ie:,}')
        self.stdout.write(f'Committees making IEs: {ie_committees:,}')
        
        if total_ie == 0:
            self.stdout.write(self.style.ERROR(
                '\n✗ CRITICAL: No IE transactions found! Check SubjectCommitteeID mapping'
            ))
        elif ie_for + ie_against != total_ie:
            self.stdout.write(self.style.WARNING(
                f'\n⚠ WARNING: {total_ie - ie_for - ie_against:,} IE transactions missing benefit flag'
            ))
        else:
            self.stdout.write(self.style.SUCCESS('\n✓ IE tracking looks good'))

    def check_donor_tracking(self):
        """
        Ben's requirement: "Pull donors (individual and super PAC) to relevant IEs"
        and "Aggregate IE donors by race and candidate"
        """
        self.stdout.write(self.style.WARNING('\n[4] DONOR TRACKING'))
        self.stdout.write('-' * 70)
        
        total_entities = Entity.objects.count()
        
        entities_as_donors = Entity.objects.filter(
            transactions__transaction_type__income_expense_neutral=1,
            transactions__deleted=False
        ).distinct().count()
        
        total_contributions = Transaction.objects.filter(
            transaction_type__income_expense_neutral=1,
            deleted=False
        ).count()
        
        contribution_amount = Transaction.objects.filter(
            transaction_type__income_expense_neutral=1,
            deleted=False
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Donors to IE committees
        ie_committee_ids = Committee.objects.filter(
            transactions__subject_committee__isnull=False
        ).distinct().values_list('committee_id', flat=True)
        
        donors_to_ie_committees = Entity.objects.filter(
            transactions__committee_id__in=ie_committee_ids,
            transactions__transaction_type__income_expense_neutral=1,
            transactions__deleted=False
        ).distinct().count()
        
        self.stdout.write(f'Total Entities: {total_entities:,}')
        self.stdout.write(f'Entities as donors: {entities_as_donors:,}')
        self.stdout.write(f'Total contribution transactions: {total_contributions:,}')
        self.stdout.write(f'Total contribution amount: ${contribution_amount:,.2f}')
        self.stdout.write(f'Donors to IE committees: {donors_to_ie_committees:,}')
        
        if entities_as_donors == 0:
            self.stdout.write(self.style.ERROR('\n✗ CRITICAL: No donor entities found!'))
        elif donors_to_ie_committees == 0:
            self.stdout.write(self.style.WARNING(
                '\n⚠ WARNING: No donors to IE committees tracked'
            ))
        else:
            self.stdout.write(self.style.SUCCESS('\n✓ Donor tracking looks good'))

    def check_race_aggregations(self):
        """
        Ben's requirement: "Aggregate by entity, race, and candidate"
        """
        self.stdout.write(self.style.WARNING('\n[5] RACE-LEVEL AGGREGATIONS'))
        self.stdout.write('-' * 70)
        
        # Count distinct races (office + cycle combinations)
        races = Committee.objects.filter(
            candidate__isnull=False,
            candidate_office__isnull=False,
            election_cycle__isnull=False
        ).values(
            'candidate_office__name',
            'election_cycle__name'
        ).distinct().count()
        
        # Races with IE spending
        races_with_ie = Committee.objects.filter(
            candidate__isnull=False,
            candidate_office__isnull=False,
            election_cycle__isnull=False,
            subject_of_ies__deleted=False
        ).values(
            'candidate_office__name',
            'election_cycle__name'
        ).distinct().count()
        
        self.stdout.write(f'Total races (office + cycle): {races:,}')
        self.stdout.write(f'Races with IE spending: {races_with_ie:,}')
        
        if races == 0:
            self.stdout.write(self.style.ERROR(
                '\n✗ CRITICAL: Cannot aggregate by race - missing office/cycle data'
            ))
        elif races_with_ie == 0:
            self.stdout.write(self.style.WARNING(
                '\n⚠ WARNING: No IE spending tracked at race level'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'\n✓ Can aggregate {races_with_ie:,} races with IE activity'
            ))

    def check_grassroots_threshold(self):
        """
        Ben's requirement: "Compare direct IE spending to grassroots threshold"
        and "Compare total IE spending funded indirectly by donor to threshold"
        """
        self.stdout.write(self.style.WARNING('\n[6] GRASSROOTS THRESHOLD COMPARISON'))
        self.stdout.write('-' * 70)
        
        THRESHOLD = Decimal('5000.00')
        
        # Candidates with IE spending over threshold
        candidates_over_threshold_for = Committee.objects.filter(
            subject_of_ies__is_for_benefit=True,
            subject_of_ies__deleted=False
        ).annotate(
            total_ie_for=Sum('subject_of_ies__amount')
        ).filter(
            total_ie_for__gt=THRESHOLD
        ).count()
        
        candidates_over_threshold_against = Committee.objects.filter(
            subject_of_ies__is_for_benefit=False,
            subject_of_ies__deleted=False
        ).annotate(
            total_ie_against=Sum('subject_of_ies__amount')
        ).filter(
            total_ie_against__gt=THRESHOLD
        ).count()
        
        self.stdout.write(f'Threshold: ${THRESHOLD:,.2f}')
        self.stdout.write(f'Candidates with IE FOR > threshold: {candidates_over_threshold_for:,}')
        self.stdout.write(f'Candidates with IE AGAINST > threshold: {candidates_over_threshold_against:,}')
        
        if candidates_over_threshold_for > 0 or candidates_over_threshold_against > 0:
            self.stdout.write(self.style.SUCCESS(
                '\n✓ Can identify candidates exceeding grassroots threshold'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                '\n⚠ No candidates exceed grassroots threshold (may be expected for test data)'
            ))

    def check_data_integrity(self):
        """Check for data integrity issues"""
        self.stdout.write(self.style.WARNING('\n[7] DATA INTEGRITY'))
        self.stdout.write('-' * 70)
        
        issues = []
        
        # Check for orphaned transactions
        orphaned = Transaction.objects.filter(committee__isnull=True).count()
        if orphaned > 0:
            issues.append(f'{orphaned:,} transactions with null committee')
        
        # Check for IE transactions without subject
        ie_no_subject = Transaction.objects.filter(
            transaction_type__name__icontains='independent expenditure',
            subject_committee__isnull=True
        ).count()
        if ie_no_subject > 0:
            issues.append(f'{ie_no_subject:,} IE transactions missing subject_committee')
        
        # Check for candidates without office
        candidates_no_office = Committee.objects.filter(
            candidate__isnull=False,
            candidate_office__isnull=True
        ).count()
        if candidates_no_office > 0:
            issues.append(f'{candidates_no_office:,} candidates missing office')
        
        # Check for the infamous Committee 1003
        if not Committee.objects.filter(committee_id=1003).exists():
            reports_need_1003 = Report.objects.filter(committee_id=1003).count()
            if reports_need_1003 > 0:
                issues.append(
                    f'Committee 1003 missing but {reports_need_1003:,} reports reference it'
                )
        
        if issues:
            self.stdout.write(self.style.WARNING('Issues found:'))
            for issue in issues:
                self.stdout.write(self.style.WARNING(f'  ⚠ {issue}'))
        else:
            self.stdout.write(self.style.SUCCESS('✓ No data integrity issues found'))

    def show_detailed_examples(self):
        """Show example queries demonstrating Ben's requirements"""
        self.stdout.write(self.style.WARNING('\n[8] DETAILED EXAMPLES'))
        self.stdout.write('-' * 70)
        
        # Top 5 candidates by IE spending FOR
        self.stdout.write('\nTop 5 Candidates by IE Spending FOR:')
        top_for = Committee.objects.filter(
            subject_of_ies__is_for_benefit=True,
            subject_of_ies__deleted=False
        ).annotate(
            total_ie=Sum('subject_of_ies__amount'),
            num_expenditures=Count('subject_of_ies')
        ).order_by('-total_ie')[:5]
        
        for i, committee in enumerate(top_for, 1):
            self.stdout.write(
                f'  {i}. {committee.name.full_name} - '
                f'${committee.total_ie:,.2f} ({committee.num_expenditures} expenditures)'
            )
        
        # Top 5 IE committees
        self.stdout.write('\nTop 5 IE Committees (making expenditures):')
        top_ie_committees = Committee.objects.filter(
            transactions__subject_committee__isnull=False,
            transactions__deleted=False
        ).annotate(
            total_spent=Sum('transactions__amount'),
            num_candidates=Count('transactions__subject_committee', distinct=True)
        ).order_by('-total_spent')[:5]
        
        for i, committee in enumerate(top_ie_committees, 1):
            self.stdout.write(
                f'  {i}. {committee.name.full_name} - '
                f'${committee.total_spent:,.2f} (targeting {committee.num_candidates} candidates)'
            )
        
        # Top 5 donors to IE committees
        self.stdout.write('\nTop 5 Donors to IE Committees:')
        ie_committee_ids = list(Committee.objects.filter(
            transactions__subject_committee__isnull=False
        ).distinct().values_list('committee_id', flat=True)[:100])  # Limit for performance
        
        if ie_committee_ids:
            top_donors = Entity.objects.filter(
                transactions__committee_id__in=ie_committee_ids,
                transactions__transaction_type__income_expense_neutral=1,
                transactions__deleted=False
            ).annotate(
                total_contributed=Sum('transactions__amount'),
                num_contributions=Count('transactions')
            ).order_by('-total_contributed')[:5]
            
            for i, donor in enumerate(top_donors, 1):
                self.stdout.write(
                    f'  {i}. {donor.full_name} - '
                    f'${donor.total_contributed:,.2f} ({donor.num_contributions} contributions)'
                )
        else:
            self.stdout.write('  No IE committee donors found')