# transparency/serializers.py

from rest_framework import serializers
from .models import (
    Race,
    Candidate,
    Party,
    IECommittee,
    DonorEntity,
    Expenditure,
    Contribution,
    ContactLog,
)


# -------------------------
# RACE + PARTY SERIALIZERS
# -------------------------
class RaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Race
        fields = "__all__"


class PartySerializer(serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = ["id", "name"]


# -------------------------
# CANDIDATE SERIALIZER
# -------------------------
class CandidateSerializer(serializers.ModelSerializer):
    race_name = serializers.CharField(source="race.name", read_only=True, default=None)
    party_name = serializers.CharField(source="party.name", read_only=True, default=None)

    race_id = serializers.PrimaryKeyRelatedField(
        queryset=Race.objects.all(),
        source="race",
        write_only=True,
        allow_null=True,
        required=False,
    )
    party_id = serializers.PrimaryKeyRelatedField(
        queryset=Party.objects.all(),
        source="party",
        write_only=True,
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Candidate
        fields = [
            "id",
            "name",
            "race_name",
            "race_id",
            "party_name",
            "party_id",
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


# -------------------------
# COMMITTEE + DONOR SERIALIZERS
# -------------------------
class IECommitteeSerializer(serializers.ModelSerializer):
    class Meta:
        model = IECommittee
        fields = "__all__"


class DonorEntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DonorEntity
        fields = "__all__"


# -------------------------
# EXPENDITURE SERIALIZER
# -------------------------
class ExpenditureSerializer(serializers.ModelSerializer):
    committee_name = serializers.CharField(source="ie_committee.name", read_only=True, default=None)
    candidate_name = serializers.CharField(source="candidate.name", read_only=True, default=None)
    race_name = serializers.CharField(source="race.name", read_only=True, default=None)

    committee_id = serializers.PrimaryKeyRelatedField(
        queryset=IECommittee.objects.all(),
        source="ie_committee",
        write_only=True,
        allow_null=True,
        required=False,
    )
    candidate_id = serializers.PrimaryKeyRelatedField(
        queryset=Candidate.objects.all(),
        source="candidate",
        write_only=True,
        allow_null=True,
        required=False,
    )
    race_id = serializers.PrimaryKeyRelatedField(
        queryset=Race.objects.all(),
        source="race",
        write_only=True,
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Expenditure
        fields = [
            "id",
            "committee_name",
            "committee_id",
            "candidate_name",
            "candidate_id",
            "race_name",
            "race_id",
            "amount",
            "date",
            "purpose",
            "support_oppose",
            "raw",
            "created_at",
            "is_fake",
        ]
        read_only_fields = ("created_at",)


# -------------------------
# CONTRIBUTIONS + CONTACT LOGS
# -------------------------
class ContributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contribution
        fields = "__all__"


class ContactLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactLog
        fields = "__all__"
from rest_framework import serializers
from .models import (
    Race,
    Candidate,
    Party,
    IECommittee,
    DonorEntity,
    Expenditure,
    Contribution,
    ContactLog,
)

class RaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Race
        fields = "__all__"


class PartySerializer(serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = "__all__"


class CandidateSerializer(serializers.ModelSerializer):
    race = RaceSerializer(read_only=True)
    party = PartySerializer(read_only=True)

    class Meta:
        model = Candidate
        fields = "__all__"


class IECommitteeSerializer(serializers.ModelSerializer):
    class Meta:
        model = IECommittee
        fields = "__all__"


class DonorEntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DonorEntity
        fields = "__all__"


class ExpenditureSerializer(serializers.ModelSerializer):
    candidate = CandidateSerializer(read_only=True)
    race = RaceSerializer(read_only=True)
    ie_committee = IECommitteeSerializer(read_only=True)

    class Meta:
        model = Expenditure
        fields = "__all__"


class ContributionSerializer(serializers.ModelSerializer):
    donor = DonorEntitySerializer(read_only=True)
    committee = IECommitteeSerializer(read_only=True)

    class Meta:
        model = Contribution
        fields = "__all__"


class ContactLogSerializer(serializers.ModelSerializer):
    candidate = CandidateSerializer(read_only=True)

    class Meta:
        model = ContactLog
        fields = "__all__"
