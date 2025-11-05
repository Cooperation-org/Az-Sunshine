import django
from decimal import Decimal
from django.db.models import Count, Sum
from transparency.models import Committee, Entity, Transaction

print("=" * 80)
print("ARIZONA SUNSHINE MDB IMPORT SANITY CHECK")
print("=" * 80)

# --------------------------------------------------------------------------------------
# 1. Committee ↔ Entity linkage
# --------------------------------------------------------------------------------------
print("\n[1] Checking Committee ↔ Entity linkage...")

total_committees = Committee.objects.count()
total_entities = Entity.objects.count()
missing_entity_link = Committee.objects.filter(name__isnull=True).count()

print(f"✓ Total Committees: {total_committees:,}")
print(f"✓ Total Entities: {total_entities:,}")
if missing_entity_link == 0:
    print("✓ All Committees have valid linked Entities.")
else:
    print(f"⚠️ Committees missing Entity link: {missing_entity_link:,}")

# --------------------------------------------------------------------------------------
# 2. Transactions ↔ Committees
# --------------------------------------------------------------------------------------
print("\n[2] Checking Transactions ↔ Committees...")

txn_total = Transaction.objects.count()
txn_missing_committee = Transaction.objects.filter(committee__isnull=True).count()
txn_missing_entity = Transaction.objects.filter(entity__isnull=True).count()

print(f"✓ Total Transactions: {txn_total:,}")
print(f"⚠️ Transactions missing Committee link: {txn_missing_committee:,}")
print(f"⚠️ Transactions missing Entity link: {txn_missing_entity:,}")

if txn_total > 0:
    committee_ids_in_txn = (
        Transaction.objects.values_list("committee__committee_id", flat=True)
        .distinct()
        .count()
    )
    print(f"✓ Unique Committees referenced in Transactions: {committee_ids_in_txn:,}")

# --------------------------------------------------------------------------------------
# 3. Detect orphaned transactions (with non-existent committees)
# --------------------------------------------------------------------------------------
print("\n[3] Checking for orphaned Transactions (Committee link mismatch)...")

committee_ids = set(Committee.objects.values_list("committee_id", flat=True))
txn_committee_ids = set(
    Transaction.objects.values_list("committee__committee_id", flat=True)
)

orphaned_committee_refs = txn_committee_ids - committee_ids
if orphaned_committee_refs:
    print(f"⚠️ Found {len(orphaned_committee_refs):,} orphaned committee references in Transactions!")
else:
    print("✓ No orphaned Transaction → Committee links found.")

# --------------------------------------------------------------------------------------
# 4. Basic totals sanity (income vs expense)
# --------------------------------------------------------------------------------------
print("\n[4] Computing overall financial totals...")

income_total = (
    Transaction.objects.filter(transaction_type__income_expense_neutral=1)
    .aggregate(total=Sum("amount"))["total"]
    or Decimal("0.00")
)
expense_total = (
    Transaction.objects.filter(transaction_type__income_expense_neutral=2)
    .aggregate(total=Sum("amount"))["total"]
    or Decimal("0.00")
)

print(f"💰 Total Income (Contributions): ${income_total:,.2f}")
print(f"💸 Total Expenses (Expenditures): ${expense_total:,.2f}")
print(f"📊 Net = ${income_total - expense_total:,.2f}")

# --------------------------------------------------------------------------------------
# 5. Committees without Transactions
# --------------------------------------------------------------------------------------
print("\n[5] Checking Committees with no Transactions...")

committees_with_txns = (
    Transaction.objects.values_list("committee__committee_id", flat=True)
    .distinct()
)
committees_no_txns = Committee.objects.exclude(
    committee_id__in=committees_with_txns
).count()

print(f"⚠️ Committees with no transactions: {committees_no_txns:,}")

# --------------------------------------------------------------------------------------
# 6. Entity sanity check
# --------------------------------------------------------------------------------------
print("\n[6] Checking for Entities missing key data...")

missing_names = Entity.objects.filter(last_name="").count()
missing_entity_type = Entity.objects.filter(entity_type__isnull=True).count()

print(f"⚠️ Entities missing last name or org name: {missing_names:,}")
print(f"⚠️ Entities missing entity type: {missing_entity_type:,}")

# --------------------------------------------------------------------------------------
# Summary
# --------------------------------------------------------------------------------------
print("\n" + "=" * 80)
print("✅ SANITY CHECK COMPLETE")
print("=" * 80)
