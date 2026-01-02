#!/usr/bin/env python3
"""
Automated Data Verification Script
Compares Az-Sunshine database data with seethemoney.az.gov CSV files
Uses Claude Opus 4.5 API for intelligent comparison and analysis

Usage:
    export ANTHROPIC_API_KEY="your-api-key"
    python automated_verification.py
"""

import os
import sys
import django
import pandas as pd
import json
from decimal import Decimal
from anthropic import Anthropic
from pathlib import Path


# Setup Django - Update this path for your environment
BACKEND_PATH = os.getenv('AZ_SUNSHINE_BACKEND', '/opt/az_sunshine/backend')
sys.path.insert(0, BACKEND_PATH)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()


from transparency.models import Committee, Entity, Transaction, TransactionType, Cycle
from django.db.models import Sum


# Configuration - Use environment variables for sensitive data
CLAUDE_API_KEY = os.getenv('ANTHROPIC_API_KEY')
if not CLAUDE_API_KEY:
    print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
    print("   Run: export ANTHROPIC_API_KEY='your-api-key'")
    sys.exit(1)

SEETHEMONEY_DIR = Path(os.getenv(
    'SEETHEMONEY_DIR',
    os.path.join(BACKEND_PATH, 'data/seethemoney_downloads')
))
OUTPUT_FILE = Path(os.getenv(
    'VERIFICATION_OUTPUT',
    './VERIFICATION_REPORT.md'
))


# Initialize Claude
client = Anthropic(api_key=CLAUDE_API_KEY)


def load_seethemoney_data(year=2024):
    """Load seethemoney CSV data for specified year"""
    print(f"\n📂 Loading seethemoney data for {year}...")

    # Find the transformed CSV file for the year
    csv_files = list(SEETHEMONEY_DIR.glob(f"seethemoney_candidate_{year}_*_transformed.csv"))

    if not csv_files:
        # Try non-transformed version
        csv_files = list(SEETHEMONEY_DIR.glob(f"seethemoney_candidate_{year}_*.csv"))

    if not csv_files:
        # Try "all" files that might contain candidate data
        csv_files = list(SEETHEMONEY_DIR.glob(f"seethemoney_all_{year}_*.csv"))

    if not csv_files:
        print(f"❌ No seethemoney data found for {year}")
        return None

    csv_file = csv_files[0]
    print(f"   Using: {csv_file.name}")

    # Load CSV - try multiple encodings
    for encoding in ['utf-16', 'utf-16-le', 'utf-8', 'latin-1']:
        try:
            df = pd.read_csv(csv_file, encoding=encoding)
            print(f"   ✓ Loaded {len(df)} rows (encoding: {encoding})")
            print(f"   ✓ Columns: {list(df.columns)[:5]}...")
            return df
        except Exception:
            continue

    print("   ❌ Error loading CSV with any encoding")
    return None


def get_our_database_data(year=2024, office=None):
    """Extract data from our database for comparison"""
    print(f"\n📊 Extracting our database data for {year}...")

    try:
        # Get IE transaction types
        ie_types = TransactionType.objects.filter(
            name__icontains='Independent Expenditure'
        )

        print(f"   Found {ie_types.count()} IE transaction types:")
        for ie_type in ie_types:
            print(f"      - {ie_type.name}")

        # Get all IE transactions for this cycle
        ie_transactions = Transaction.objects.filter(
            transaction_type__in=ie_types,
            transaction_date__year=year
        ).select_related(
            'committee',
            'subject_committee',
            'entity',
            'transaction_type'
        )

        print(f"   ✓ Found {ie_transactions.count()} IE transactions for {year}")

        # Aggregate by subject committee (candidate)
        data = []
        subject_committees = ie_transactions.values_list('subject_committee', flat=True).distinct()

        print(f"   Processing {len([sc for sc in subject_committees if sc is not None])} candidates...")

        for subject_comm_id in subject_committees:
            if not subject_comm_id:
                continue

            try:
                subject_comm = Committee.objects.get(committee_id=subject_comm_id)
            except Committee.DoesNotExist:
                print(f"   ⚠️  Warning: Committee {subject_comm_id} not found")
                continue

            # Get IE FOR and AGAINST
            ie_for = ie_transactions.filter(
                subject_committee_id=subject_comm_id,
                is_for_benefit=True
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

            ie_against = ie_transactions.filter(
                subject_committee_id=subject_comm_id,
                is_for_benefit=False
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

            candidate_name = subject_comm.name.last_name if subject_comm.name else subject_comm.name_text or 'Unknown'

            data.append({
                'committee_name': candidate_name,
                'committee_id': subject_comm.committee_id,
                'ie_for': abs(float(ie_for)),
                'ie_against': abs(float(ie_against)),
                'total_ie': abs(float(ie_for)) + abs(float(ie_against))
            })

        df = pd.DataFrame(data)
        print(f"   ✓ Created dataset with {len(df)} candidates")
        return df

    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def compare_with_claude(our_data, seethemoney_data, year):
    """Use Claude Opus 4.5 to intelligently compare the datasets"""
    print(f"\n🤖 Using Claude Opus 4.5 for comparison analysis...")

    # Prepare data for Claude
    our_summary = our_data.to_json(orient='records', indent=2) if our_data is not None else "No data"

    # Show seethemoney structure
    seethemoney_info = "No data"
    if seethemoney_data is not None:
        seethemoney_info = f"""
Column names: {list(seethemoney_data.columns)}
Sample records (first 20):
{seethemoney_data.head(20).to_json(orient='records', indent=2)}
Total records: {len(seethemoney_data)}
"""

    prompt = f"""You are analyzing campaign finance data for Arizona {year} elections.

I have two datasets to compare:

1. OUR DATABASE DATA (Az-Sunshine):
{our_summary}

2. SEETHEMONEY.AZ.GOV PUBLIC DATA:
{seethemoney_info}

Your task:
1. First, analyze the seethemoney data structure to understand what columns represent candidates and IE amounts
2. Identify matching candidates/committees between both datasets (use fuzzy matching for names)
3. Compare Independent Expenditure (IE) amounts
4. Calculate discrepancies (dollar amounts and percentages)
5. Flag any significant differences (>5% or >$10,000)
6. Identify potential data quality issues
7. Suggest specific records to investigate

Important notes:
- Names may not match exactly (e.g., "Smith, John" vs "John Smith")
- Look for columns like "Committee Name", "Candidate", "IE Support", "IE Opposition", etc.
- IE amounts might be in separate columns (FOR vs AGAINST)

Provide a detailed analysis in markdown format with:
- Executive Summary
- Match Rate (% of records that match)
- Detailed Comparison Table (with specific examples)
- Flagged Discrepancies (with candidate names and amounts)
- Root Cause Analysis
- Recommendations

Be critical and thorough. Look for patterns in the discrepancies."""

    try:
        response = client.messages.create(
            model="claude-opus-4-20250514",
            max_tokens=8000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        analysis = response.content[0].text
        print("   ✓ Analysis complete")
        return analysis

    except Exception as e:
        print(f"   ❌ Claude API error: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_report(analysis, our_data, seethemoney_data, year):
    """Generate comprehensive verification report"""
    print(f"\n📝 Generating verification report...")

    # Get database name from environment
    db_name = os.getenv('DB_NAME', 'NOT SET')

    report = f"""# Az-Sunshine Data Verification Report
## {year} Election Data Comparison

**Generated**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
**Verification Method**: Automated comparison using Claude Opus 4.5
**Reference Source**: seethemoney.az.gov

---

## Dataset Summary

### Our Database (Az-Sunshine)
- Records: {len(our_data) if our_data is not None else 0}
- Database: {db_name}
- Total IE Spending: ${our_data['total_ie'].sum():,.2f if our_data is not None else 0}

### Reference Data (seethemoney.az.gov)
- Records: {len(seethemoney_data) if seethemoney_data is not None else 0}
- Source: CSV export from seethemoney.az.gov

---

## Claude Opus 4.5 Analysis

{analysis if analysis else 'Analysis failed - see errors above'}

---

## Top 10 Candidates by IE Spending (Our Database)

"""

    if our_data is not None and len(our_data) > 0:
        top_10 = our_data.nlargest(10, 'total_ie')
        report += "| Rank | Candidate | IE Support | IE Opposition | Total IE |\n"
        report += "|------|-----------|------------|---------------|----------|\n"
        for idx, row in enumerate(top_10.itertuples(), 1):
            report += f"| {idx} | {row.committee_name} | ${row.ie_for:,.2f} | ${row.ie_against:,.2f} | ${row.total_ie:,.2f} |\n"
    else:
        report += "No data available\n"

    report += """

---

## Manual Verification Checklist

Based on this analysis, manually verify these specific items:

1. [ ] Open both websites side-by-side
2. [ ] Pick the top 3 candidates with highest IE spending
3. [ ] Verify each IE amount matches exactly
4. [ ] Check the direction (FOR vs AGAINST)
5. [ ] Document any discrepancies with screenshots

---

## Next Steps

1. **If Match Rate > 95%**: ✅ Data is accurate, ready for demo
2. **If Match Rate 80-95%**: ⚠️ Investigate flagged discrepancies
3. **If Match Rate < 80%**: ❌ Significant data quality issues, delay demo

---

## URLs for Manual Verification

**Our Site**: http://localhost:5173/races?office=[OFFICE]&cycle={year}
**Public Site**: https://seethemoney.az.gov/

Replace [OFFICE] with: Governor, Attorney General, Corporation Commission, etc.

---

## Technical Notes

**Environment Variables Required**:
- `ANTHROPIC_API_KEY`: Claude API key
- `AZ_SUNSHINE_BACKEND`: Path to backend directory (default: /opt/az_sunshine/backend)
- `SEETHEMONEY_DIR`: Path to CSV downloads directory
- `VERIFICATION_OUTPUT`: Output report path (default: ./VERIFICATION_REPORT.md)
- `DB_NAME`: Database name for documentation

---

"""

    if our_data is not None and len(our_data) > 0:
        report += f"""## Raw Data for Reference

### Our Top 10 Candidates (JSON)
```json
{our_data.nlargest(10, 'total_ie').to_json(orient='records', indent=2)}
```
"""

    # Write report
    OUTPUT_FILE.write_text(report)
    print(f"   ✓ Report saved to: {OUTPUT_FILE}")

    return report


def main():
    """Main execution"""
    print("=" * 80)
    print("🔍 Az-Sunshine Data Verification Tool")
    print("=" * 80)

    # Configuration
    YEAR = int(os.getenv('VERIFICATION_YEAR', '2016'))

    print(f"\nTarget Year: {YEAR}")
    print(f"Database: {os.getenv('DB_NAME', 'NOT SET')}")
    print(f"Seethemoney CSV Directory: {SEETHEMONEY_DIR}")

    # Check what CSV files exist
    if SEETHEMONEY_DIR.exists():
        csv_files = list(SEETHEMONEY_DIR.glob("*.csv"))
        print(f"\nAvailable CSV files: {len(csv_files)}")
        for csv_file in csv_files[:10]:  # Show first 10
            print(f"   - {csv_file.name}")
    else:
        print(f"\n⚠️  Seethemoney directory not found: {SEETHEMONEY_DIR}")

    # Step 1: Load seethemoney data
    seethemoney_data = load_seethemoney_data(YEAR)
    if seethemoney_data is None:
        print("\n❌ Cannot proceed without seethemoney reference data")
        print("\nRECOMMENDATION:")
        print("1. Download data from https://seethemoney.az.gov/")
        print(f"2. Save to: {SEETHEMONEY_DIR}/")
        print("3. Re-run this script")
        return 1

    # Step 2: Load our database data
    our_data = get_our_database_data(YEAR)
    if our_data is None or len(our_data) == 0:
        print(f"\n❌ No data in our database for {YEAR}")
        print("\nRECOMMENDATION:")
        print("1. Check TransactionType table for IE types")
        print("2. Verify transactions have correct transaction_type foreign keys")
        print("3. Check if subject_committee field is populated")
        return 1

    # Step 3: Compare using Claude Opus 4.5
    analysis = compare_with_claude(our_data, seethemoney_data, YEAR)

    # Step 4: Generate report
    report = generate_report(analysis, our_data, seethemoney_data, YEAR)

    print("\n" + "=" * 80)
    print("✅ VERIFICATION COMPLETE!")
    print("=" * 80)
    print(f"\n📄 Report available at: {OUTPUT_FILE}")
    print("\nNext: Review the report and follow the manual verification checklist")

    # Print summary
    if our_data is not None and len(our_data) > 0:
        print(f"\n📊 QUICK SUMMARY:")
        print(f"   Candidates in our DB: {len(our_data)}")
        print(f"   Total IE Spending: ${our_data['total_ie'].sum():,.2f}")
        print(f"   Top candidate: {our_data.nlargest(1, 'total_ie').iloc[0]['committee_name']}")
        print(f"   Top IE amount: ${our_data.nlargest(1, 'total_ie').iloc[0]['total_ie']:,.2f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
