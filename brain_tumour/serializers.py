from rest_framework import serializers

from brain_tumour.models import BrainTumour

class BrainTumourSerializer(serializers.ModelSerializer):

    # patient = serializers.ReadOnlyField(source='patient.username')
    class Meta:
        model = BrainTumour
        fields = ('id','timestamp', 'uploaded', 'clustered', 'stage', 'patient')