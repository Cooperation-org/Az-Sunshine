from rest_framework import serializers
from .models import Candidate, Race, IECommittee, DonorEntity, Expenditure, Contribution, ContactLog

class RaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Race
        fields = '__all__'

class CandidateSerializer(serializers.ModelSerializer):
    race = RaceSerializer(read_only=True)
    class Meta:
        model = Candidate
        fields = ['id','name','race','email','filing_date','source','contacted','contacted_at','notes','external_id','created_at']

class IECommitteeSerializer(serializers.ModelSerializer):
    class Meta:
        model = IECommittee
        fields = '__all__'

class DonorEntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DonorEntity
        fields = '__all__'

class ExpenditureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expenditure
        fields = '__all__'

class ContributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contribution
        fields = '__all__'

class ContactLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactLog
        fields = '__all__'
