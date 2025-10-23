from rest_framework import serializers
from .models import Race, Candidate, IECommittee, DonorEntity, Expenditure, Contribution, ContactLog


class RaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Race
        fields = "__all__"


class CandidateSerializer(serializers.ModelSerializer):
    race = RaceSerializer(read_only=True)
    race_id = serializers.PrimaryKeyRelatedField(
        queryset=Race.objects.all(), source="race", write_only=True, allow_null=True
    )

    class Meta:
        model = Candidate
        # include a few useful fields for admin/UI
        fields = [
            "id",
            "name",
            "race",
            "race_id",
            "email",
            "filing_date",
            "source",
            "contacted",
            "contacted_at",
            "external_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("created_at", "updated_at", "contacted_at")


class IECommitteeSerializer(serializers.ModelSerializer):
    class Meta:
        model = IECommittee
        fields = "__all__"


class DonorEntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DonorEntity
        fields = "__all__"


class ExpenditureSerializer(serializers.ModelSerializer):
    # Expose 'committee' in the API but map it to model field 'ie_committee'
    committee = IECommitteeSerializer(read_only=True)
    committee_id = serializers.PrimaryKeyRelatedField(
        queryset=IECommittee.objects.all(), source="ie_committee", write_only=True, allow_null=True
    )

    candidate = CandidateSerializer(read_only=True)
    candidate_id = serializers.PrimaryKeyRelatedField(
        queryset=Candidate.objects.all(), source="candidate", write_only=True, allow_null=True
    )

    race = RaceSerializer(read_only=True)
    race_id = serializers.PrimaryKeyRelatedField(
        queryset=Race.objects.all(), source="race", write_only=True, allow_null=True
    )

    class Meta:
        model = Expenditure
        fields = [
            "id",
            "committee",
            "committee_id",
            "candidate",
            "candidate_id",
            "race",
            "race_id",
            "amount",
            "date",
            "purpose",
            "support_oppose",
            "candidate_name",
            "raw",
            "created_at",
            "is_fake",
        ]
        read_only_fields = ("created_at",)
