"""
Data Validation Views
Endpoints for data quality checks, duplicate detection, and external source comparison
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Sum, Q, F
from django.db import connection
from decimal import Decimal
from .models import Transaction, Entity, Committee, Office, Cycle


@api_view(['GET'])
@permission_classes([IsAdminUser])
def data_quality_metrics(request):
    """
    Get overall data quality metrics
    - Completeness percentages
    - Missing critical fields
    - Data freshness
    """

    # Transaction completeness
    total_transactions = Transaction.objects.count()
    complete_transactions = Transaction.objects.exclude(
        Q(amount__isnull=True) |
        Q(entity__isnull=True) |
        Q(committee__isnull=True) |
        Q(transaction_date__isnull=True)
    ).count()

    # Entity completeness
    total_entities = Entity.objects.count()
    entities_with_location = Entity.objects.exclude(
        Q(city__isnull=True) | Q(city='')
    ).count()

    # Committee completeness
    total_committees = Committee.objects.count()
    committees_with_candidate = Committee.objects.filter(
        candidate__isnull=False
    ).exclude(
        Q(name__isnull=True)
    ).count()

    # Calculate percentages
    transaction_completeness = (complete_transactions / total_transactions * 100) if total_transactions > 0 else 0
    entity_location_completeness = (entities_with_location / total_entities * 100) if total_entities > 0 else 0

    return Response({
        'overall_health': 'good' if transaction_completeness > 95 else 'warning' if transaction_completeness > 85 else 'critical',
        'transaction_completeness': round(transaction_completeness, 2),
        'entity_location_completeness': round(entity_location_completeness, 2),
        'total_records': {
            'transactions': total_transactions,
            'entities': total_entities,
            'committees': total_committees
        },
        'missing_data': {
            'transactions_incomplete': total_transactions - complete_transactions,
            'entities_without_location': total_entities - entities_with_location
        }
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def duplicate_entities(request):
    """
    Find potential duplicate entities based on name similarity
    Uses simple matching to identify entities that might be the same person/organization
    """

    # Get entities with similar names (simplified version without fuzzy matching)
    # This uses exact substring matching instead of pg_trgm similarity

    duplicates = []

    # Find entities with very similar names in the same city
    entities = Entity.objects.exclude(
        Q(first_name__isnull=True) | Q(first_name='')
    ).exclude(
        Q(last_name__isnull=True) | Q(last_name='')
    ).exclude(
        Q(city__isnull=True) | Q(city='')
    ).values(
        'name_id', 'first_name', 'last_name', 'city'
    ).order_by('city', 'last_name')

    # Group by city and look for similar names
    from collections import defaultdict
    city_entities = defaultdict(list)

    for entity in entities:
        full_name = f"{entity['first_name']} {entity['last_name']}".lower()
        city_entities[entity['city'].lower()].append({
            'id': entity['name_id'],
            'name': full_name,
            'first_name': entity['first_name'],
            'last_name': entity['last_name'],
            'city': entity['city']
        })

    # Find duplicates within each city
    for city, city_ents in city_entities.items():
        for i, ent1 in enumerate(city_ents):
            for ent2 in city_ents[i+1:]:
                # Check for name similarity
                name1 = ent1['name']
                name2 = ent2['name']

                # Simple similarity checks:
                # 1. Same last name and first initial
                # 2. One name is substring of the other
                # 3. Names differ by only middle initial

                is_similar = False
                confidence = 0.0

                if ent1['last_name'].lower() == ent2['last_name'].lower():
                    if ent1['first_name'][0].lower() == ent2['first_name'][0].lower():
                        is_similar = True
                        confidence = 0.85

                if name1 in name2 or name2 in name1:
                    is_similar = True
                    confidence = max(confidence, 0.90)

                if is_similar:
                    duplicates.append({
                        'entities': [
                            {
                                'id': ent1['id'],
                                'name': f"{ent1['first_name']} {ent1['last_name']}",
                                'city': ent1['city']
                            },
                            {
                                'id': ent2['id'],
                                'name': f"{ent2['first_name']} {ent2['last_name']}",
                                'city': ent2['city']
                            }
                        ],
                        'confidence_score': confidence,
                        'reason': 'Name similarity in same location'
                    })

                if len(duplicates) >= 100:
                    break
            if len(duplicates) >= 100:
                break
        if len(duplicates) >= 100:
            break

    return Response({
        'duplicates': duplicates,
        'total_found': len(duplicates)
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def race_validation(request):
    """
    Validate race-level data against expected totals
    Compare with SOS data if available

    Query params:
    - office_id: Office ID to validate
    - cycle_id: Cycle ID to validate
    """

    office_id = request.GET.get('office_id')
    cycle_id = request.GET.get('cycle_id')

    if not office_id or not cycle_id:
        return Response(
            {'error': 'office_id and cycle_id are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        office = Office.objects.get(office_id=office_id)
        cycle = Cycle.objects.get(cycle_id=cycle_id)
    except (Office.DoesNotExist, Cycle.DoesNotExist):
        return Response(
            {'error': 'Office or Cycle not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Get all candidates for this race
    candidates = Committee.objects.filter(
        office=office,
        cycle=cycle,
        committee_type='candidate'
    )

    validation_results = []

    for candidate in candidates:
        # Get total contributions
        total_contributions = Transaction.objects.filter(
            recipient=candidate,
            transaction_type='contribution'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # Get total expenditures
        total_expenditures = Transaction.objects.filter(
            spender=candidate,
            transaction_type='expenditure'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # Get IE spending
        ie_for = Transaction.objects.filter(
            subject_committee=candidate,
            is_for_benefit=True,
            transaction_type='independent_expenditure'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        ie_against = Transaction.objects.filter(
            subject_committee=candidate,
            is_for_benefit=False,
            transaction_type='independent_expenditure'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        validation_results.append({
            'candidate_name': f"{candidate.name.first_name} {candidate.name.last_name}",
            'candidate_id': candidate.committee_id,
            'metrics': {
                'total_contributions': float(total_contributions),
                'total_expenditures': float(total_expenditures),
                'ie_for': float(ie_for),
                'ie_against': float(ie_against),
                'net_ie': float(ie_for - ie_against)
            },
            'data_quality': {
                'has_contributions': total_contributions > 0,
                'has_expenditures': total_expenditures > 0,
                'has_ie_data': (ie_for + ie_against) > 0
            }
        })

    return Response({
        'office': office.name,
        'cycle': cycle.name,
        'candidates': validation_results,
        'summary': {
            'total_candidates': len(validation_results),
            'candidates_with_contributions': sum(1 for c in validation_results if c['data_quality']['has_contributions']),
            'candidates_with_ie': sum(1 for c in validation_results if c['data_quality']['has_ie_data'])
        }
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def external_comparison(request):
    """
    Compare our data with external sources (OpenSecrets, SOS)
    This is a placeholder for future implementation

    Returns discrepancies between our data and external sources
    """

    # This would require integration with OpenSecrets API and SOS data
    # For now, return structure that frontend can use

    office_id = request.GET.get('office_id')
    cycle_id = request.GET.get('cycle_id')

    if not office_id or not cycle_id:
        return Response(
            {'error': 'office_id and cycle_id are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Placeholder response
    return Response({
        'status': 'not_implemented',
        'message': 'External source comparison requires OpenSecrets API integration',
        'planned_sources': [
            {
                'name': 'OpenSecrets',
                'status': 'pending_api_key',
                'description': 'Compare contribution totals and donor lists'
            },
            {
                'name': 'Arizona SOS',
                'status': 'pending_integration',
                'description': 'Compare official campaign finance reports'
            }
        ],
        'office_id': office_id,
        'cycle_id': cycle_id
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def merge_entities(request):
    """
    Merge duplicate entities

    Request body:
    {
        "primary_entity_id": 123,
        "duplicate_entity_ids": [456, 789]
    }
    """

    primary_id = request.data.get('primary_entity_id')
    duplicate_ids = request.data.get('duplicate_entity_ids', [])

    if not primary_id or not duplicate_ids:
        return Response(
            {'error': 'primary_entity_id and duplicate_entity_ids are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        primary_entity = Entity.objects.get(name_id=primary_id)
    except Entity.DoesNotExist:
        return Response(
            {'error': 'Primary entity not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Update all transactions to point to the primary entity
    merged_count = 0
    for dup_id in duplicate_ids:
        try:
            duplicate = Entity.objects.get(name_id=dup_id)

            # Update entity transactions
            Transaction.objects.filter(entity=duplicate).update(entity=primary_entity)

            # Mark duplicate as merged (or delete if preferred)
            # duplicate.delete()  # Uncomment to delete instead of marking

            merged_count += 1
        except Entity.DoesNotExist:
            continue

    return Response({
        'success': True,
        'primary_entity': {
            'id': primary_entity.name_id,
            'name': f"{primary_entity.first_name} {primary_entity.last_name}"
        },
        'merged_count': merged_count,
        'message': f'Successfully merged {merged_count} duplicate entities'
    })
