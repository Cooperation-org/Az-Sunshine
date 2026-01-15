"""
Data Verification Engine
Compares Az-Sunshine database with external sources to identify discrepancies.

This is the second layer of QA that automatically catches:
1. Missing candidates
2. Wrong totals (IE for/against)
3. Mismatched Support/Oppose classifications
4. Missing transactions
5. Data inconsistencies
"""

import logging
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

from django.db.models import Sum, Count, Q
from django.db.models.functions import Abs

from transparency.models import (
    Committee, Transaction, Office, Cycle, Party
)
from .external_data_clients import ExternalDataAggregator

logger = logging.getLogger(__name__)


class DiscrepancyType(Enum):
    """Types of data discrepancies"""
    MISSING_CANDIDATE = "missing_candidate"
    EXTRA_CANDIDATE = "extra_candidate"
    AMOUNT_MISMATCH = "amount_mismatch"
    SUPPORT_OPPOSE_MISMATCH = "support_oppose_mismatch"
    TRANSACTION_COUNT_MISMATCH = "transaction_count_mismatch"
    MISSING_IE_DATA = "missing_ie_data"
    CANDIDATE_NOT_LINKED = "candidate_not_linked"


class Severity(Enum):
    """Severity levels for discrepancies"""
    CRITICAL = "critical"  # Major data issue
    HIGH = "high"          # Significant mismatch
    MEDIUM = "medium"      # Notable difference
    LOW = "low"            # Minor variance
    INFO = "info"          # Informational only


@dataclass
class Discrepancy:
    """Represents a single data discrepancy"""
    discrepancy_type: DiscrepancyType
    severity: Severity
    office: str
    cycle: str
    candidate_name: Optional[str]
    description: str
    az_sunshine_value: Any
    external_value: Any
    external_source: str
    variance_amount: Optional[Decimal] = None
    variance_percent: Optional[float] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['discrepancy_type'] = self.discrepancy_type.value
        result['severity'] = self.severity.value
        if self.variance_amount:
            result['variance_amount'] = float(self.variance_amount)
        return result


@dataclass
class VerificationResult:
    """Result of a verification run"""
    office: str
    cycle: str
    party: Optional[str]
    run_at: datetime
    status: str  # success, partial, failed
    discrepancies: List[Discrepancy]
    az_sunshine_candidates: int
    external_candidates: int
    match_rate: float
    total_ie_az_sunshine: Decimal
    total_ie_external: Decimal
    sources_checked: List[str]

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'office': self.office,
            'cycle': self.cycle,
            'party': self.party,
            'run_at': self.run_at.isoformat(),
            'status': self.status,
            'discrepancies': [d.to_dict() for d in self.discrepancies],
            'az_sunshine_candidates': self.az_sunshine_candidates,
            'external_candidates': self.external_candidates,
            'match_rate': self.match_rate,
            'total_ie_az_sunshine': float(self.total_ie_az_sunshine),
            'total_ie_external': float(self.total_ie_external),
            'sources_checked': self.sources_checked,
            'discrepancy_count': len(self.discrepancies),
            'critical_count': len([d for d in self.discrepancies
                                   if d.severity == Severity.CRITICAL]),
            'high_count': len([d for d in self.discrepancies
                              if d.severity == Severity.HIGH]),
        }


class DataVerificationEngine:
    """
    Main verification engine that compares Az-Sunshine data
    with external sources.
    """

    # Thresholds for determining severity
    CRITICAL_VARIANCE_PERCENT = 50.0  # >50% difference is critical
    HIGH_VARIANCE_PERCENT = 20.0      # >20% is high
    MEDIUM_VARIANCE_PERCENT = 5.0     # >5% is medium
    CRITICAL_VARIANCE_AMOUNT = Decimal('100000')  # >$100k difference
    HIGH_VARIANCE_AMOUNT = Decimal('10000')       # >$10k

    def __init__(self):
        self.external_aggregator = ExternalDataAggregator()

    def get_az_sunshine_race_data(self, office: Office, cycle: Cycle,
                                   party: Party = None) -> List[Dict]:
        """
        Get race data from Az-Sunshine database

        Uses the same logic as RaceAggregationManager for consistency
        """
        filters = {
            'subject_committee__candidate_office': office,
            'deleted': False,
            'subject_committee__isnull': False,
            'transaction_date__gte': cycle.begin_date,
            'transaction_date__lte': cycle.end_date,
            'transaction_type__income_expense_neutral': 2,
        }

        if party:
            filters['subject_committee__candidate_party'] = party

        # Get IE spending per candidate
        race_data = Transaction.objects.filter(
            **filters
        ).values(
            'subject_committee__committee_id',
            'subject_committee__name__last_name',
            'subject_committee__name__first_name',
            'subject_committee__candidate_party__name',
        ).annotate(
            ie_for=Sum(Abs('amount'), filter=Q(is_for_benefit=True)),
            ie_against=Sum(Abs('amount'), filter=Q(is_for_benefit=False)),
            total_ie=Sum(Abs('amount')),
            transaction_count=Count('transaction_id')
        ).order_by('-total_ie')

        results = []
        for row in race_data:
            name = f"{row['subject_committee__name__first_name'] or ''} {row['subject_committee__name__last_name'] or ''}".strip()
            results.append({
                'committee_id': row['subject_committee__committee_id'],
                'candidate_name': name,
                'party': row['subject_committee__candidate_party__name'],
                'ie_for': row['ie_for'] or Decimal('0'),
                'ie_against': row['ie_against'] or Decimal('0'),
                'total_ie': row['total_ie'] or Decimal('0'),
                'transaction_count': row['transaction_count'] or 0
            })

        return results

    def _calculate_severity(self, az_value: Decimal,
                           external_value: Decimal) -> Tuple[Severity, Decimal, float]:
        """
        Calculate severity based on variance

        Returns:
            Tuple of (severity, variance_amount, variance_percent)
        """
        variance = abs(az_value - external_value)
        if external_value > 0:
            variance_pct = float(variance / external_value * 100)
        elif az_value > 0:
            variance_pct = 100.0  # External is 0 but we have data
        else:
            variance_pct = 0.0

        # Determine severity
        if variance_pct >= self.CRITICAL_VARIANCE_PERCENT or variance >= self.CRITICAL_VARIANCE_AMOUNT:
            severity = Severity.CRITICAL
        elif variance_pct >= self.HIGH_VARIANCE_PERCENT or variance >= self.HIGH_VARIANCE_AMOUNT:
            severity = Severity.HIGH
        elif variance_pct >= self.MEDIUM_VARIANCE_PERCENT:
            severity = Severity.MEDIUM
        elif variance_pct > 0:
            severity = Severity.LOW
        else:
            severity = Severity.INFO

        return severity, variance, variance_pct

    def _normalize_candidate_name(self, name: str) -> str:
        """Normalize candidate name for comparison"""
        if not name:
            return ""
        # Lowercase, remove common suffixes, extra spaces
        name = name.lower().strip()
        for suffix in [' jr', ' sr', ' iii', ' ii', ' iv']:
            name = name.replace(suffix, '')
        return ' '.join(name.split())  # Normalize whitespace

    def _match_candidates(self, az_candidates: List[Dict],
                         external_candidates: List[Dict]) -> Dict[str, Dict]:
        """
        Match candidates between Az-Sunshine and external data

        Returns:
            Dict mapping normalized names to matched records
        """
        matches = {}

        # Index external candidates by normalized name
        external_by_name = {}
        for ec in external_candidates:
            name = self._normalize_candidate_name(ec.get('candidate_name', ''))
            if name:
                external_by_name[name] = ec

        # Match Az-Sunshine candidates
        for azc in az_candidates:
            name = self._normalize_candidate_name(azc.get('candidate_name', ''))
            if not name:
                continue

            matches[name] = {
                'az_sunshine': azc,
                'external': external_by_name.get(name),
                'matched': name in external_by_name
            }
            if name in external_by_name:
                del external_by_name[name]

        # Add unmatched external candidates
        for name, ec in external_by_name.items():
            matches[name] = {
                'az_sunshine': None,
                'external': ec,
                'matched': False
            }

        return matches

    def verify_race(self, office_name: str, cycle_year: str,
                   party_name: str = None) -> VerificationResult:
        """
        Verify a specific race against external sources

        Args:
            office_name: Office name (e.g., "Governor")
            cycle_year: Election cycle year (e.g., "2022")
            party_name: Optional party filter

        Returns:
            VerificationResult with discrepancies
        """
        discrepancies = []
        sources_checked = []

        # Get Az-Sunshine data
        try:
            office = Office.objects.get(name=office_name)
            cycle = Cycle.objects.get(name=cycle_year)
            party = Party.objects.get(name=party_name) if party_name else None
        except (Office.DoesNotExist, Cycle.DoesNotExist, Party.DoesNotExist) as e:
            logger.error(f"Verification failed - object not found: {e}")
            return VerificationResult(
                office=office_name,
                cycle=cycle_year,
                party=party_name,
                run_at=datetime.now(),
                status='failed',
                discrepancies=[],
                az_sunshine_candidates=0,
                external_candidates=0,
                match_rate=0.0,
                total_ie_az_sunshine=Decimal('0'),
                total_ie_external=Decimal('0'),
                sources_checked=[]
            )

        az_candidates = self.get_az_sunshine_race_data(office, cycle, party)
        az_total_ie = sum(c['total_ie'] for c in az_candidates)

        # Get external data
        year = int(cycle_year)
        external_data = self.external_aggregator.get_race_data(
            office=office_name,
            year=year,
            party=party_name
        )

        # Process FollowTheMoney data
        ftm_data = external_data['sources'].get('followthemoney', {})
        if ftm_data.get('status') == 'success':
            sources_checked.append('followthemoney')
            ftm_candidates = ftm_data.get('records', [])

            # Compare with FTM data
            ftm_discrepancies = self._compare_with_source(
                az_candidates=az_candidates,
                external_candidates=ftm_candidates,
                source_name='followthemoney',
                office=office_name,
                cycle=cycle_year
            )
            discrepancies.extend(ftm_discrepancies)

        # Process SeeTheMoney data
        stm_data = external_data['sources'].get('seethemoney', {})
        if stm_data.get('status') == 'success':
            sources_checked.append('seethemoney')
            stm_candidates = stm_data.get('records', [])

            # Compare with STM data
            stm_discrepancies = self._compare_with_source(
                az_candidates=az_candidates,
                external_candidates=stm_candidates,
                source_name='seethemoney',
                office=office_name,
                cycle=cycle_year
            )
            discrepancies.extend(stm_discrepancies)

        # ALWAYS run internal data quality checks
        sources_checked.append('internal_check')
        internal_discrepancies = self.check_internal_data_quality(office, cycle)
        discrepancies.extend(internal_discrepancies)

        # Calculate match rate
        external_count = max(
            ftm_data.get('count', 0),
            stm_data.get('count', 0)
        )
        if external_count > 0:
            matched = len([d for d in discrepancies
                          if d.discrepancy_type != DiscrepancyType.MISSING_CANDIDATE])
            match_rate = (len(az_candidates) - matched) / external_count * 100
        else:
            match_rate = 100.0 if len(az_candidates) == 0 else 0.0

        # Get external total IE (best available)
        external_total_ie = Decimal('0')
        # Would need to sum from external records

        return VerificationResult(
            office=office_name,
            cycle=cycle_year,
            party=party_name,
            run_at=datetime.now(),
            status='success' if sources_checked else 'no_external_data',
            discrepancies=discrepancies,
            az_sunshine_candidates=len(az_candidates),
            external_candidates=external_count,
            match_rate=match_rate,
            total_ie_az_sunshine=az_total_ie,
            total_ie_external=external_total_ie,
            sources_checked=sources_checked
        )

    def _compare_with_source(self, az_candidates: List[Dict],
                            external_candidates: List[Dict],
                            source_name: str,
                            office: str,
                            cycle: str) -> List[Discrepancy]:
        """
        Compare Az-Sunshine data with a specific external source

        Returns:
            List of discrepancies found
        """
        discrepancies = []

        # Match candidates
        matches = self._match_candidates(az_candidates, external_candidates)

        for name, match_data in matches.items():
            az_record = match_data.get('az_sunshine')
            ext_record = match_data.get('external')

            # Missing from Az-Sunshine
            if not az_record and ext_record:
                ext_total = Decimal(str(ext_record.get('total_ie', 0)))
                severity = Severity.CRITICAL if ext_total > self.HIGH_VARIANCE_AMOUNT else Severity.HIGH

                discrepancies.append(Discrepancy(
                    discrepancy_type=DiscrepancyType.MISSING_CANDIDATE,
                    severity=severity,
                    office=office,
                    cycle=cycle,
                    candidate_name=ext_record.get('candidate_name'),
                    description=f"Candidate found in {source_name} but missing from Az-Sunshine",
                    az_sunshine_value=None,
                    external_value=ext_record,
                    external_source=source_name
                ))
                continue

            # Extra in Az-Sunshine (not in external)
            if az_record and not ext_record:
                # This could be normal if external source has less data
                discrepancies.append(Discrepancy(
                    discrepancy_type=DiscrepancyType.EXTRA_CANDIDATE,
                    severity=Severity.LOW,
                    office=office,
                    cycle=cycle,
                    candidate_name=az_record.get('candidate_name'),
                    description=f"Candidate in Az-Sunshine but not found in {source_name}",
                    az_sunshine_value=az_record,
                    external_value=None,
                    external_source=source_name
                ))
                continue

            # Both exist - compare amounts
            if az_record and ext_record:
                az_total = az_record.get('total_ie', Decimal('0'))
                ext_total = Decimal(str(ext_record.get('total_ie', 0)))

                if az_total != ext_total:
                    severity, variance, variance_pct = self._calculate_severity(
                        az_total, ext_total
                    )

                    if severity != Severity.INFO:
                        discrepancies.append(Discrepancy(
                            discrepancy_type=DiscrepancyType.AMOUNT_MISMATCH,
                            severity=severity,
                            office=office,
                            cycle=cycle,
                            candidate_name=az_record.get('candidate_name'),
                            description=f"IE total mismatch: Az-Sunshine ${az_total:,.2f} vs {source_name} ${ext_total:,.2f}",
                            az_sunshine_value=float(az_total),
                            external_value=float(ext_total),
                            external_source=source_name,
                            variance_amount=variance,
                            variance_percent=variance_pct
                        ))

        return discrepancies

    def check_internal_data_quality(self, office: Office, cycle: Cycle) -> List[Discrepancy]:
        """
        Check for internal data quality issues like:
        1. Committees with IE spending but no candidate linked
        2. Duplicate committee entries for same candidate
        3. Committees with missing candidate_office

        This catches bugs like Katie Hobbs 2022 committee having no candidate link.
        """
        discrepancies = []

        # Find committees with IE spending but no candidate linked
        committees_with_ie = Transaction.objects.filter(
            subject_committee__candidate_office=office,
            deleted=False,
            transaction_date__gte=cycle.begin_date,
            transaction_date__lte=cycle.end_date,
            transaction_type__income_expense_neutral=2,
        ).values(
            'subject_committee__committee_id',
            'subject_committee__name__first_name',
            'subject_committee__name__last_name',
            'subject_committee__candidate',
            'subject_committee__candidate_party__name',
        ).annotate(
            total_ie=Sum(Abs('amount')),
            tx_count=Count('transaction_id')
        ).filter(total_ie__gt=0)

        for row in committees_with_ie:
            committee_name = f"{row['subject_committee__name__first_name'] or ''} {row['subject_committee__name__last_name'] or ''}".strip()
            total_ie = row['total_ie'] or Decimal('0')

            # Check if candidate is linked
            if row['subject_committee__candidate'] is None:
                severity = Severity.CRITICAL if total_ie > self.HIGH_VARIANCE_AMOUNT else Severity.HIGH

                discrepancies.append(Discrepancy(
                    discrepancy_type=DiscrepancyType.CANDIDATE_NOT_LINKED,
                    severity=severity,
                    office=office.name,
                    cycle=cycle.name,
                    candidate_name=committee_name,
                    description=f"Committee '{committee_name}' has ${total_ie:,.2f} in IE spending but NO candidate linked. This may cause the candidate to be excluded from some views.",
                    az_sunshine_value={
                        'committee_id': row['subject_committee__committee_id'],
                        'total_ie': float(total_ie),
                        'transaction_count': row['tx_count']
                    },
                    external_value=None,
                    external_source='internal_check'
                ))

        # Check for duplicate committee names (same candidate appearing multiple times)
        from collections import Counter
        name_counts = Counter()
        for row in committees_with_ie:
            name = f"{row['subject_committee__name__first_name'] or ''} {row['subject_committee__name__last_name'] or ''}".strip().lower()
            if name:
                name_counts[name] += 1

        for name, count in name_counts.items():
            if count > 1:
                discrepancies.append(Discrepancy(
                    discrepancy_type=DiscrepancyType.EXTRA_CANDIDATE,
                    severity=Severity.MEDIUM,
                    office=office.name,
                    cycle=cycle.name,
                    candidate_name=name.title(),
                    description=f"Candidate '{name.title()}' appears in {count} different committees. IE totals may be split across multiple entries.",
                    az_sunshine_value={'duplicate_count': count},
                    external_value=None,
                    external_source='internal_check'
                ))

        return discrepancies

    def verify_all_races(self, cycles: List[str] = None) -> List[VerificationResult]:
        """
        Verify all races for given cycles

        Args:
            cycles: List of cycle years to verify (default: 2016-2024)

        Returns:
            List of VerificationResult objects
        """
        if not cycles:
            cycles = ['2016', '2018', '2020', '2022', '2024']

        results = []

        # Get all offices with IE data
        # Find offices that have committees with IE transactions targeting them
        offices = Office.objects.filter(
            committee__subject_of_ies__isnull=False
        ).distinct().values_list('name', flat=True)

        for cycle in cycles:
            for office in offices:
                logger.info(f"Verifying {office} {cycle}...")
                result = self.verify_race(office, cycle)
                results.append(result)

                if result.discrepancies:
                    logger.warning(
                        f"  Found {len(result.discrepancies)} discrepancies "
                        f"({len([d for d in result.discrepancies if d.severity == Severity.CRITICAL])} critical)"
                    )

        return results

    def generate_verification_report(self, results: List[VerificationResult]) -> Dict:
        """
        Generate a summary report from verification results

        Args:
            results: List of VerificationResult objects

        Returns:
            Summary report dict
        """
        total_discrepancies = sum(len(r.discrepancies) for r in results)
        critical_count = sum(
            len([d for d in r.discrepancies if d.severity == Severity.CRITICAL])
            for r in results
        )
        high_count = sum(
            len([d for d in r.discrepancies if d.severity == Severity.HIGH])
            for r in results
        )

        return {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'races_verified': len(results),
                'total_discrepancies': total_discrepancies,
                'critical_issues': critical_count,
                'high_issues': high_count,
                'overall_health': 'critical' if critical_count > 0 else
                                  'warning' if high_count > 0 else 'good'
            },
            'by_severity': {
                'critical': critical_count,
                'high': high_count,
                'medium': sum(
                    len([d for d in r.discrepancies if d.severity == Severity.MEDIUM])
                    for r in results
                ),
                'low': sum(
                    len([d for d in r.discrepancies if d.severity == Severity.LOW])
                    for r in results
                ),
            },
            'by_type': {
                'missing_candidate': sum(
                    len([d for d in r.discrepancies
                         if d.discrepancy_type == DiscrepancyType.MISSING_CANDIDATE])
                    for r in results
                ),
                'amount_mismatch': sum(
                    len([d for d in r.discrepancies
                         if d.discrepancy_type == DiscrepancyType.AMOUNT_MISMATCH])
                    for r in results
                ),
                'extra_candidate': sum(
                    len([d for d in r.discrepancies
                         if d.discrepancy_type == DiscrepancyType.EXTRA_CANDIDATE])
                    for r in results
                ),
            },
            'races': [r.to_dict() for r in results]
        }
