#!/usr/bin/env python
"""
Arizona Sunshine Transparency Project - Phase 1 Validation Script

Run this script to validate that all Phase 1 requirements are met:
- IE spending tracking
- Candidate aggregations
- Donor impact analysis
- Race-level aggregations
- Data integrity checks

Usage:
    python phase1_validation.py

Requirements:
    - Django project must be configured
    - Database must be populated with data
"""

import os
import sys
import django
from datetime import datetime
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from transparency.models import (
    Committee, Entity, Office, Cycle, Transaction,
    RaceAggregationManager, Phase1DataValidator
)


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")


def print_section(text):
    """Print a formatted section"""
    print(f"\n{Colors.OKBLUE}{Colors.BOLD}>>> {text}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{'-'*80}{Colors.ENDC}")


def print_success(text):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_warning(text):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_info(key, value):
    """Print info key-value pair"""
    print(f"{Colors.OKCYAN}  {key}:{Colors.ENDC} {value}")


def validate_data_integrity():
    """Run all data integrity checks"""
    print_header("PHASE 1 DATA INTEGRITY VALIDATION")
    
    print_section("1. IE Tracking Validation")
    ie_validation = Phase1DataValidator.validate_ie_tracking()
    
    print_info("Total IE Transactions", f"{ie_validation['total_ie_transactions']:,}")
    print_info("IE Committees Count", f"{ie_validation['ie_committees_count']:,}")
    print_info("Candidates with IE Spending", f"{ie_validation['candidates_with_ie_spending']:,}")
    print_info("IE FOR Count", f"{ie_validation['ie_for_count']:,}")
    print_info("IE AGAINST Count", f"{ie_validation['ie_against_count']:,}")
    
    if ie_validation['total_ie_transactions'] > 0:
        print_success("IE tracking appears to be working correctly")
    else:
        print_warning("No IE transactions found - check if data is loaded")
    
    print_section("2. Candidate Committee Validation")
    candidate_validation = Phase1DataValidator.validate_candidate_tracking()
    
    print_info("Total Committees", f"{candidate_validation['total_committees']:,}")
    print_info("Candidate Committees", f"{candidate_validation['candidate_committees']:,}")
    print_info("Candidates with Office", f"{candidate_validation['candidates_with_office']:,}")
    print_info("Candidates with Party", f"{candidate_validation['candidates_with_party']:,}")
    print_info("Candidates with Cycle", f"{candidate_validation['candidates_with_cycle']:,}")
    
    if candidate_validation['candidate_committees'] > 0:
        print_success("Candidate tracking appears to be working correctly")
        
        # Calculate data quality percentage
        if candidate_validation['candidate_committees'] > 0:
            office_pct = (candidate_validation['candidates_with_office'] / 
                         candidate_validation['candidate_committees'] * 100)
            party_pct = (candidate_validation['candidates_with_party'] / 
                        candidate_validation['candidate_committees'] * 100)
            cycle_pct = (candidate_validation['candidates_with_cycle'] / 
                        candidate_validation['candidate_committees'] * 100)
            
            print_info("Data Quality - Office", f"{office_pct:.1f}%")
            print_info("Data Quality - Party", f"{party_pct:.1f}%")
            print_info("Data Quality - Cycle", f"{cycle_pct:.1f}%")
    else:
        print_warning("No candidate committees found - check if data is loaded")
    
    print_section("3. Donor Tracking Validation")
    donor_validation = Phase1DataValidator.validate_donor_tracking()
    
    print_info("Total Entities", f"{donor_validation['total_entities']:,}")
    print_info("Entities with Contributions", f"{donor_validation['entities_with_contributions']:,}")
    print_info("Total Contribution Transactions", f"{donor_validation['total_contribution_transactions']:,}")
    print_info("Unique Donors", f"{donor_validation['unique_donors']:,}")
    
    if donor_validation['unique_donors'] > 0:
        print_success("Donor tracking appears to be working correctly")
    else:
        print_warning("No donors found - check if data is loaded")
    
    print_section("4. Data Integrity Issues")
    issues = Phase1DataValidator.check_data_integrity()
    
    if len(issues) == 1 and "No data integrity issues" in issues[0]:
        print_success(issues[0])
    else:
        for issue in issues:
            print_error(issue)
    
    return ie_validation, candidate_validation, donor_validation, issues


def test_ie_spending_for_candidate():
    """Test IE spending aggregation for a specific candidate"""
    print_section("5. Testing IE Spending Aggregation (Sample Candidate)")
    
    # Find a candidate with IE spending
    candidates_with_ie = Committee.objects.filter(
        subject_of_ies__deleted=False,
        candidate__isnull=False
    ).distinct()[:5]
    
    if not candidates_with_ie.exists():
        print_warning("No candidates with IE spending found to test")
        return None
    
    for candidate in candidates_with_ie:
        print(f"\n{Colors.BOLD}Candidate: {candidate.name.full_name}{Colors.ENDC}")
        print_info("Committee ID", candidate.committee_id)
        if candidate.candidate_office:
            print_info("Office", candidate.candidate_office.name)
        if candidate.candidate_party:
            print_info("Party", candidate.candidate_party.name)
        
        # Get IE spending summary
        ie_summary = candidate.get_ie_spending_summary()
        print_info("IE FOR", f"${ie_summary['for']['total']:,.2f} ({ie_summary['for']['count']} transactions)")
        print_info("IE AGAINST", f"${ie_summary['against']['total']:,.2f} ({ie_summary['against']['count']} transactions)")
        print_info("NET IE", f"${ie_summary['net']:,.2f}")
        
        # Compare to grassroots threshold
        threshold_comparison = candidate.compare_to_grassroots_threshold(5000)
        print_info("Grassroots Threshold", f"${threshold_comparison['threshold']:,.2f}")
        
        if threshold_comparison['exceeds_threshold_for']:
            print_warning(f"IE FOR exceeds threshold by {threshold_comparison['times_threshold_for']:.2f}x")
        
        if threshold_comparison['exceeds_threshold_against']:
            print_warning(f"IE AGAINST exceeds threshold by {threshold_comparison['times_threshold_against']:.2f}x")
        
        # Get IE donors
        ie_donors = candidate.get_ie_donors()[:5]
        if ie_donors:
            print(f"\n{Colors.OKCYAN}  Top 5 IE Donors (contributing to IE committees):{Colors.ENDC}")
            for i, donor in enumerate(ie_donors, 1):
                donor_name = f"{donor.get('entity__first_name', '')} {donor['entity__last_name']}".strip()
                print(f"    {i}. {donor_name}: ${donor['total_contributed']:,.2f}")
    
    return candidates_with_ie


def test_race_aggregation():
    """Test race-level IE aggregations"""
    print_section("6. Testing Race-Level IE Aggregation")
    
    # Find offices with IE spending
    # FIX: Changed 'committees' to 'committee' (singular relationship name)
    offices_with_ie = Office.objects.filter(
        committee__subject_of_ies__deleted=False
    ).distinct()[:3]
    
    if not offices_with_ie.exists():
        print_warning("No offices with IE spending found to test")
        return
    
    for office in offices_with_ie:
        # Find most recent cycle for this office
        # FIX: Changed 'committees' to 'committee' here as well
        cycles = Cycle.objects.filter(
            committee__candidate_office=office,
            committee__subject_of_ies__deleted=False
        ).distinct().order_by('-begin_date')[:1]
        
        if not cycles.exists():
            continue
        
        cycle = cycles.first()
        
        print(f"\n{Colors.BOLD}Race: {office.name} - {cycle.name}{Colors.ENDC}")
        
        # Get race IE spending
        race_spending = RaceAggregationManager.get_race_ie_spending(office, cycle)
        
        if race_spending:
            print(f"\n{Colors.OKCYAN}  IE Spending by Candidate:{Colors.ENDC}")
            for item in race_spending[:5]:
                candidate_name = f"{item.get('subject_committee__name__first_name', '')} {item['subject_committee__name__last_name']}".strip()
                party = item.get('subject_committee__candidate_party__name', 'N/A')
                benefit = "FOR" if item.get('is_for_benefit') else "AGAINST"
                print(f"    • {candidate_name} ({party}) - {benefit}: ${item['total_ie']:,.2f}")
        
        # Get top IE donors for this race
        top_race_donors = RaceAggregationManager.get_top_ie_donors_by_race(office, cycle, limit=5)
        
        if top_race_donors:
            print(f"\n{Colors.OKCYAN}  Top 5 Donors Impacting This Race:{Colors.ENDC}")
            for i, donor in enumerate(top_race_donors, 1):
                donor_name = f"{donor.get('entity__first_name', '')} {donor['entity__last_name']}".strip()
                occupation = donor.get('entity__occupation', 'N/A')
                print(f"    {i}. {donor_name} ({occupation}): ${donor['total_contributed']:,.2f}")


def test_donor_impact():
    """Test donor IE impact tracking"""
    print_section("7. Testing Donor IE Impact Analysis")
    
    # Find donors with significant contributions to IE committees
    ie_committees = Committee.objects.filter(
        transactions__subject_committee__isnull=False,
        transactions__deleted=False
    ).distinct()
    
    from django.db.models import Sum
    
    top_donors = Transaction.objects.filter(
        committee__in=ie_committees,
        transaction_type__income_expense_neutral=1,
        deleted=False
    ).values('entity').annotate(
        total=Sum('amount')
    ).order_by('-total')[:3]
    
    if not top_donors:
        print_warning("No donors to IE committees found")
        return
    
    for donor_data in top_donors:
        try:
            donor = Entity.objects.get(name_id=donor_data['entity'])
            
            print(f"\n{Colors.BOLD}Donor: {donor.full_name}{Colors.ENDC}")
            print_info("Total Contributions to IE Committees", f"${donor_data['total']:,.2f}")
            
            # Get contribution summary
            contrib_summary = donor.get_contribution_summary()
            if contrib_summary['total']:
                print_info("Total All Contributions", f"${contrib_summary['total']:,.2f}")
                print_info("Number of Contributions", f"{contrib_summary['count']:,}")
            
            # Get IE impact by candidate
            donor_impact = donor.get_total_ie_impact_by_candidate()
            
            if donor_impact:
                print(f"\n{Colors.OKCYAN}  Candidates Impacted (via IE spending):{Colors.ENDC}")
                for impact in donor_impact[:5]:
                    candidate_name = f"{impact.get('subject_committee__name__first_name', '')} {impact['subject_committee__name__last_name']}".strip()
                    office = impact.get('subject_committee__candidate_office__name', 'N/A')
                    benefit = "FOR" if impact.get('is_for_benefit') else "AGAINST"
                    print(f"    • {candidate_name} ({office}) - {benefit}: ${impact['ie_total']:,.2f}")
        except Entity.DoesNotExist:
            continue


def generate_summary_report(ie_val, candidate_val, donor_val, issues):
    """Generate a summary report of the validation"""
    print_header("VALIDATION SUMMARY REPORT")
    
    print(f"{Colors.BOLD}Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}\n")
    
    # Overall status
    has_ie_data = ie_val['total_ie_transactions'] > 0
    has_candidates = candidate_val['candidate_committees'] > 0
    has_donors = donor_val['unique_donors'] > 0
    has_no_issues = len(issues) == 1 and "No data integrity issues" in issues[0]
    
    print_section("Overall Status")
    
    if has_ie_data:
        print_success("IE Tracking: OPERATIONAL")
    else:
        print_error("IE Tracking: NO DATA")
    
    if has_candidates:
        print_success("Candidate Tracking: OPERATIONAL")
    else:
        print_error("Candidate Tracking: NO DATA")
    
    if has_donors:
        print_success("Donor Tracking: OPERATIONAL")
    else:
        print_error("Donor Tracking: NO DATA")
    
    if has_no_issues:
        print_success("Data Integrity: PASSED")
    else:
        print_error(f"Data Integrity: {len(issues)} ISSUES FOUND")
    
    # Recommendations
    print_section("Recommendations")
    
    if not has_ie_data:
        print("  • Load IE transaction data into the database")
        print("  • Verify subject_committee field is populated for IE transactions")
    
    if not has_candidates:
        print("  • Load candidate committee data")
        print("  • Ensure candidate field is populated for candidate committees")
    
    if not has_donors:
        print("  • Load contribution transaction data")
        print("  • Verify entity relationships are properly established")
    
    if not has_no_issues:
        print("  • Review and fix the data integrity issues listed above")
    
    if has_ie_data and has_candidates and has_donors and has_no_issues:
        print_success("All systems operational! Ready for Phase 1 analysis.")
        print("\n  Next steps:")
        print("  • Review the sample outputs above to verify data accuracy")
        print("  • Begin building the Phase 1 dashboard")
        print("  • Set up automated reporting for IE spending alerts")


def main():
    """Main execution function"""
    try:
        print_header("ARIZONA SUNSHINE TRANSPARENCY PROJECT")
        print(f"{Colors.OKCYAN}Phase 1 Validation Script{Colors.ENDC}")
        print(f"Testing all Ben's requirements for IE tracking and aggregation\n")
        
        # Run validation tests
        ie_val, candidate_val, donor_val, issues = validate_data_integrity()
        
        # Run functional tests if data exists
        if ie_val['total_ie_transactions'] > 0:
            test_ie_spending_for_candidate()
            test_race_aggregation()
            test_donor_impact()
        else:
            print_warning("\nSkipping functional tests - no IE data found")
        
        # Generate summary
        generate_summary_report(ie_val, candidate_val, donor_val, issues)
        
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}Validation complete!{Colors.ENDC}\n")
        
    except Exception as e:
        print_error(f"\nValidation failed with error: {str(e)}")
        import traceback
        print(f"\n{Colors.FAIL}{traceback.format_exc()}{Colors.ENDC}")
        sys.exit(1)


if __name__ == "__main__":
    main()