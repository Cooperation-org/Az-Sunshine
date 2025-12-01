# serializers.py for Arizona Sunshine Transparency Project - PHASE 1
# DRF serializers for API responses

from rest_framework import serializers
from .models import *


# ==================== LOOKUP/REFERENCE SERIALIZERS ====================

class CountySerializer(serializers.ModelSerializer):
    class Meta:
        model = County
        fields = ['county_id', 'name']


class PartySerializer(serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = ['party_id', 'name', 'abbreviation']


class OfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Office
        fields = ['office_id', 'name', 'office_type']


class CycleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cycle
        fields = ['cycle_id', 'name', 'begin_date', 'end_date']


class EntityTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntityType
        fields = ['entity_type_id', 'name']


class TransactionTypeSerializer(serializers.ModelSerializer):
    is_contribution = serializers.BooleanField(read_only=True)
    is_expense = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = TransactionType
        fields = ['transaction_type_id', 'name', 'income_expense_neutral', 
                  'is_contribution', 'is_expense']


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = ['category_id', 'name']


class BallotMeasureSerializer(serializers.ModelSerializer):
    election_year = serializers.IntegerField(read_only=True)
    measure_type = serializers.CharField(read_only=True)
    
    class Meta:
        model = BallotMeasure
        fields = ['ballot_measure_id', 'sos_identifier', 'measure_number',
                  'short_title', 'official_title', 'election_year', 'measure_type']


# ==================== ENTITY SERIALIZERS ====================

class EntitySerializer(serializers.ModelSerializer):
    """Basic entity serializer for list views"""
    entity_type = EntityTypeSerializer(read_only=True)
    county = CountySerializer(read_only=True)
    full_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = Entity
        fields = [
            'name_id', 'name_group_id', 'entity_type', 'full_name',
            'last_name', 'first_name', 'middle_name', 'suffix',
            'address1', 'address2', 'city', 'state', 'zip_code', 'county',
            'occupation', 'employer'
        ]


class EntityDetailSerializer(EntitySerializer):
    """Detailed entity serializer with contribution summary"""
    contribution_summary = serializers.SerializerMethodField()
    
    class Meta(EntitySerializer.Meta):
        fields = EntitySerializer.Meta.fields + ['contribution_summary']
    
    def get_contribution_summary(self, obj):
        return obj.get_contribution_summary()


# ==================== COMMITTEE SERIALIZERS ====================

class CommitteeSerializer(serializers.ModelSerializer):
    """Basic committee serializer for list views"""
    name = EntitySerializer(read_only=True)
    candidate = EntitySerializer(read_only=True)
    candidate_party = PartySerializer(read_only=True)
    candidate_office = OfficeSerializer(read_only=True)
    candidate_county = CountySerializer(read_only=True)
    election_cycle = CycleSerializer(read_only=True)
    sponsor = EntitySerializer(read_only=True)
    ballot_measure = BallotMeasureSerializer(read_only=True)
    
    is_candidate_committee = serializers.BooleanField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Committee
        fields = [
            'committee_id', 'name', 
            'candidate', 'candidate_party', 'candidate_office', 'candidate_county',
            'is_incumbent', 'election_cycle',
            'sponsor', 'sponsor_type', 'sponsor_relationship',
            'ballot_measure', 'benefits_ballot_measure',
            'organization_date', 'termination_date',
            'physical_city', 'physical_state',
            'is_candidate_committee', 'is_active'
        ]


class CommitteeDetailSerializer(CommitteeSerializer):
    """Detailed committee serializer with financial data"""
    chairperson = EntitySerializer(read_only=True)
    treasurer = EntitySerializer(read_only=True)
    
    total_income = serializers.SerializerMethodField()
    total_expenses = serializers.SerializerMethodField()
    cash_balance = serializers.SerializerMethodField()
    ie_for = serializers.SerializerMethodField()
    ie_against = serializers.SerializerMethodField()
    
    class Meta(CommitteeSerializer.Meta):
        fields = CommitteeSerializer.Meta.fields + [
            'chairperson', 'treasurer',
            'physical_address1', 'physical_address2', 'physical_zip_code',
            'financial_institution1', 'financial_institution2', 'financial_institution3',
            'total_income', 'total_expenses', 'cash_balance',
            'ie_for', 'ie_against'
        ]
    
    def get_total_income(self, obj):
        return str(obj.get_total_income())
    
    def get_total_expenses(self, obj):
        return str(obj.get_total_expenses())
    
    def get_cash_balance(self, obj):
        return str(obj.get_cash_balance())
    
    def get_ie_for(self, obj):
        return str(obj.get_ie_for())
    
    def get_ie_against(self, obj):
        return str(obj.get_ie_against())


# ==================== TRANSACTION SERIALIZERS ====================

class TransactionSerializer(serializers.ModelSerializer):
    """Transaction serializer with related entity data"""
    committee = serializers.SerializerMethodField()
    entity = EntitySerializer(read_only=True)
    transaction_type = TransactionTypeSerializer(read_only=True)
    category = ExpenseCategorySerializer(read_only=True)
    subject_committee = serializers.SerializerMethodField()
    
    is_contribution = serializers.BooleanField(read_only=True)
    is_expense = serializers.BooleanField(read_only=True)
    is_ie_spending = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'transaction_id', 'committee', 'transaction_type',
            'transaction_date', 'amount', 'entity',
            'subject_committee', 'is_for_benefit',
            'category', 'memo', 'account_type',
            'is_contribution', 'is_expense', 'is_ie_spending',
            'deleted'
        ]
    
    def get_committee(self, obj):
        """Return basic committee info"""
        return {
            'committee_id': obj.committee.committee_id,
            'name': obj.committee.name.full_name,
            'is_candidate': obj.committee.is_candidate_committee,
        }
    
    def get_subject_committee(self, obj):
        """Return subject committee for IE transactions"""
        if obj.subject_committee:
            return {
                'committee_id': obj.subject_committee.committee_id,
                'name': obj.subject_committee.name.full_name,
                'candidate_name': obj.subject_committee.candidate.full_name if obj.subject_committee.candidate else None,
                'office': obj.subject_committee.candidate_office.name if obj.subject_committee.candidate_office else None,
                'party': obj.subject_committee.candidate_party.name if obj.subject_committee.candidate_party else None,
            }
        return None


# ==================== REPORT SERIALIZERS ====================

class ReportTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportType
        fields = ['report_type_id', 'name', 'is_active']


class ReportNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportName
        fields = ['report_name_id', 'name']


class ReportSerializer(serializers.ModelSerializer):
    """Campaign finance report serializer"""
    committee = serializers.SerializerMethodField()
    cycle = CycleSerializer(read_only=True)
    report_type = ReportTypeSerializer(read_only=True)
    report_name = ReportNameSerializer(read_only=True)
    
    is_amendment = serializers.BooleanField(read_only=True)
    is_late = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Report
        fields = [
            'report_id', 'committee', 'cycle', 'report_type', 'report_name',
            'report_period_begin', 'report_period_end',
            'filing_period_begin', 'filing_period_end', 'filing_datetime',
            'is_amendment', 'is_late'
        ]
    
    def get_committee(self, obj):
        return {
            'committee_id': obj.committee.committee_id,
            'name': obj.committee.name.full_name,
        }


# ==================== PHASE 1: CANDIDATE SOI SERIALIZER ====================

class CandidateSOISerializer(serializers.ModelSerializer):
    """
    Phase 1 Requirement 1: Candidate Statement of Interest tracking
    """
    office = OfficeSerializer(read_only=True)
    entity = EntitySerializer(read_only=True)
    
    # Write fields for creating/updating
    office_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = CandidateStatementOfInterest
        fields = [
            'id', 'candidate_name', 'office', 'office_id', 'email',
            'filing_date', 'contact_status', 'contact_date', 'contacted_by',
            'pledge_received', 'pledge_date', 'notes', 'entity',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_email(self, value):
        """Validate email format if provided"""
        if value and '@' not in value:
            raise serializers.ValidationError("Invalid email format")
        return value
    
    def validate_contact_status(self, value):
        """Validate contact status transitions"""
        if self.instance:
            # Can't go backwards from acknowledged to uncontacted
            if self.instance.contact_status == 'acknowledged' and value == 'uncontacted':
                raise serializers.ValidationError(
                    "Cannot change status from acknowledged to uncontacted"
                )
        return value


# ==================== PHASE 1: AGGREGATION SERIALIZERS ====================

class RaceAggregationSerializer(serializers.Serializer):
    """
    Phase 1: Race-level IE spending aggregation
    Ben's requirement: "Aggregate by entity, race, and candidate"
    """
    office = OfficeSerializer()
    cycle = CycleSerializer()
    party = PartySerializer(required=False, allow_null=True)
    candidates = serializers.ListField(
        child=serializers.DictField()
    )


class IESpendingSummarySerializer(serializers.Serializer):
    """
    Phase 1: IE spending for/against summary
    Ben's requirements 2a-2e
    """
    committee_id = serializers.IntegerField()
    candidate_name = serializers.CharField(allow_null=True)
    office = serializers.CharField(allow_null=True)
    party = serializers.CharField(allow_null=True)
    ie_spending = serializers.DictField()


class IEDonorSerializer(serializers.Serializer):
    """
    Phase 1: IE donor information
    Ben's requirement: "Aggregate IE donors by race and candidate"
    """
    entity_id = serializers.IntegerField()
    entity_name = serializers.CharField()
    entity_type = serializers.CharField()
    occupation = serializers.CharField(allow_blank=True, allow_null=True)
    employer = serializers.CharField(allow_blank=True, allow_null=True)
    total_contributed = serializers.DecimalField(max_digits=12, decimal_places=2)
    num_contributions = serializers.IntegerField()


class GrassrootsThresholdSerializer(serializers.Serializer):
    """
    Phase 1: Grassroots threshold comparison
    Ben's requirements 2d-2e
    """
    committee_id = serializers.IntegerField()
    candidate_name = serializers.CharField(allow_null=True)
    comparison = serializers.DictField()


class DonorImpactSerializer(serializers.Serializer):
    """
    Phase 1: Donor impact across candidates
    Ben's requirement: "Compare total IE spending funded indirectly by a given donor"
    """
    entity_id = serializers.IntegerField()
    entity_name = serializers.CharField()
    ie_impact_by_candidate = serializers.ListField(
        child=serializers.DictField()
    )


# ==================== DASHBOARD SERIALIZERS ====================

class DashboardSummarySerializer(serializers.Serializer):
    """Phase 1 dashboard summary statistics"""
    current_cycle = serializers.CharField(allow_null=True)
    candidate_committees = serializers.IntegerField()
    total_ie_spending = serializers.DecimalField(max_digits=12, decimal_places=2)
    candidates_over_grassroots_threshold = serializers.IntegerField()
    grassroots_threshold = serializers.DecimalField(max_digits=12, decimal_places=2)
    soi_tracking = serializers.DictField()
    last_updated = serializers.DateTimeField()


class DataValidationSerializer(serializers.Serializer):
    """Phase 1 data validation results"""
    ie_tracking = serializers.DictField()
    candidate_tracking = serializers.DictField()
    donor_tracking = serializers.DictField()
    integrity_issues = serializers.ListField(child=serializers.CharField())
    validation_timestamp = serializers.DateTimeField()
    



# ==================== EMAIL SERIALIZERS ====================

class EmailTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer for email templates
    Phase 1 Requirement 1b: Email template management
    """
    class Meta:
        model = EmailTemplate
        fields = [
            'id', 'name', 'category', 'subject', 'body',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EmailCampaignSerializer(serializers.ModelSerializer):
    """
    Serializer for email campaigns
    Phase 1: Bulk email campaign tracking
    """
    template_name = serializers.CharField(source='template.name', read_only=True)
    total_sent = serializers.SerializerMethodField()
    total_opened = serializers.SerializerMethodField()
    total_clicked = serializers.SerializerMethodField()
    
    class Meta:
        model = EmailCampaign
        fields = [
            'id', 'name', 'template', 'template_name',
            'scheduled_for', 'sent_at', 'status',
            'total_sent', 'total_opened', 'total_clicked',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'total_sent', 'total_opened', 'total_clicked']
    
    def get_total_sent(self, obj):
        return EmailLog.objects.filter(campaign=obj, status='sent').count()
    
    def get_total_opened(self, obj):
        return EmailLog.objects.filter(campaign=obj, opened_at__isnull=False).count()
    
    def get_total_clicked(self, obj):
        return EmailLog.objects.filter(campaign=obj, clicked_at__isnull=False).count()


class EmailLogSerializer(serializers.ModelSerializer):
    """
    Serializer for email logs
    Phase 1: Email tracking and history
    """
    candidate_name = serializers.CharField(source='candidate.candidate_name', read_only=True)
    candidate_email = serializers.CharField(source='candidate.email', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    campaign_name = serializers.CharField(source='campaign.name', read_only=True, allow_null=True)
    
    class Meta:
        model = EmailLog
        fields = [
            'id', 'campaign', 'campaign_name',
            'candidate', 'candidate_name', 'candidate_email',
            'template', 'template_name',
            'subject', 'body', 'tracking_id',
            'sent_at', 'status', 'error_message',
            'opened_at', 'clicked_at'
        ]
        read_only_fields = [
            'id', 'sent_at', 'tracking_id',
            'opened_at', 'clicked_at'
        ]


class EmailLogListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for email log lists (without body)
    """
    candidate_name = serializers.CharField(source='candidate.candidate_name', read_only=True)
    candidate_email = serializers.CharField(source='candidate.email', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    campaign_name = serializers.CharField(source='campaign.name', read_only=True, allow_null=True)
    
    class Meta:
        model = EmailLog
        fields = [
            'id', 'campaign_name',
            'candidate_name', 'candidate_email',
            'template_name', 'subject',
            'sent_at', 'status',
            'opened_at', 'clicked_at'
        ]




