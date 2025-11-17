# diagnostic_ie_data.py
# Save this file in your project root
# Run: python manage.py shell < diagnostic_ie_data.py

from transparency.models import Transaction, Committee
from django.db.models import Sum, Count, Q
from decimal import Decimal

print("\n" + "="*80)
print("ARIZONA SUNSHINE - IE DATA DIAGNOSTIC REPORT")
print("="*80 + "\n")

# 1. Check total IE transactions
print("1. INDEPENDENT EXPENDITURE TRANSACTIONS OVERVIEW")
print("-" * 80)

ie_transactions = Transaction.objects.filter(
    subject_committee__isnull=False,
    deleted=False
)

total_ie_count = ie_transactions.count()
print(f"Total IE transactions: {total_ie_count}")

if total_ie_count == 0:
    print("❌ ERROR: No IE transactions found!")
    print("   This means subject_committee is NULL on all transactions.\n")
else:
    print(f"✅ Found {total_ie_count} IE transactions\n")

# 2. Check is_for_benefit distribution
print("2. SUPPORT vs OPPOSE DISTRIBUTION")
print("-" * 80)

support_count = ie_transactions.filter(is_for_benefit=True).count()
oppose_count = ie_transactions.filter(is_for_benefit=False).count()
null_count = ie_transactions.filter(is_for_benefit__isnull=True).count()

if total_ie_count > 0:
    print(f"Support (is_for_benefit=True):  {support_count} transactions ({support_count/total_ie_count*100:.1f}%)")
    print(f"Oppose (is_for_benefit=False):  {oppose_count} transactions ({oppose_count/total_ie_count*100:.1f}%)")
    print(f"NULL (is_for_benefit=NULL):     {null_count} transactions")

if null_count > 0:
    print(f"\n⚠️  WARNING: {null_count} transactions have NULL is_for_benefit!")

if oppose_count > 0 and support_count == 0:
    print("\n⚠️  CRITICAL: ALL IE transactions marked as 'Oppose'")
    print("   This is likely a DATA IMPORT BUG")
elif support_count == 0 and oppose_count == 0:
    print("\n❌ ERROR: No Support/Oppose data available")
else:
    print(f"\n✅ Mix of Support and Oppose found")

# 3. Check amounts
print("\n3. IE SPENDING AMOUNTS ANALYSIS")
print("-" * 80)

positive_amounts = ie_transactions.filter(amount__gt=0)
negative_amounts = ie_transactions.filter(amount__lt=0)

pos_count = positive_amounts.count()
neg_count = negative_amounts.count()

pos_total = positive_amounts.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
neg_total = negative_amounts.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

print(f"Positive amounts: {pos_count} transactions, Total: ${pos_total:,.2f}")
print(f"Negative amounts: {neg_count} transactions, Total: ${neg_total:,.2f}")
print(f"\nNET TOTAL: ${(pos_total + neg_total):,.2f}")

if neg_count > 0:
    print(f"\n✅ Negative amounts present ({neg_count}) - likely amendments/corrections")

# 4. Support vs Oppose totals
print("\n4. SUPPORT vs OPPOSE SPENDING TOTALS")
print("-" * 80)

support_total = ie_transactions.filter(is_for_benefit=True).aggregate(
    total=Sum('amount')
)['total'] or Decimal('0.00')

oppose_total = ie_transactions.filter(is_for_benefit=False).aggregate(
    total=Sum('amount')
)['total'] or Decimal('0.00')

print(f"Total SUPPORT spending: ${support_total:,.2f}")
print(f"Total OPPOSE spending:  ${oppose_total:,.2f}")

# 5. Sample recent transactions
print("\n5. SAMPLE RECENT IE TRANSACTIONS (Last 10)")
print("-" * 80)

recent_ies = ie_transactions.select_related(
    'committee__name',
    'subject_committee__name',
    'transaction_type'
).order_by('-transaction_date')[:10]

for ie in recent_ies:
    support_oppose = "SUPPORT" if ie.is_for_benefit else "OPPOSE" if ie.is_for_benefit == False else "NULL"
    committee_name = ie.committee.name.full_name if ie.committee and ie.committee.name else "Unknown"
    candidate_name = ie.subject_committee.name.full_name if ie.subject_committee and ie.subject_committee.name else "Unknown"
    
    print(f"\nTransaction #{ie.transaction_id} | Date: {ie.transaction_date}")
    print(f"  Amount: ${ie.amount:,.2f}")
    print(f"  Type: {support_oppose}")
    print(f"  IE Committee: {committee_name}")
    print(f"  Target Candidate: {candidate_name}")

# 6. Dashboard calculation check
print("\n6. WHAT DASHBOARD SHOULD DISPLAY")
print("-" * 80)

dashboard_ie_total = ie_transactions.aggregate(
    total=Sum('amount')
)['total'] or Decimal('0.00')

print(f"Total IE Spending: ${dashboard_ie_total:,.2f}")
print(f"Support chart: ${support_total:,.2f}")
print(f"Oppose chart:  ${oppose_total:,.2f}")

if dashboard_ie_total < 0:
    print(f"\n❌ PROBLEM: Total IE Spending is NEGATIVE!")

# 7. Recommendations
print("\n" + "="*80)
print("DIAGNOSIS")
print("="*80 + "\n")

if oppose_count > 0 and support_count == 0:
    print("❌ ISSUE FOUND: All IEs marked as 'Oppose'")
    print("\nFIX NEEDED: Check your data import for is_for_benefit field")
elif support_count > 0 and oppose_count > 0:
    print("✅ Data looks correct!")
    print("\nIssue is likely in frontend display, not data")

print("\n" + "="*80)