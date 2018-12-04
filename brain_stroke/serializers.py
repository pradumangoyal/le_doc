from rest_framework import serializers

from brain_stroke.models import BrainStroke

class BrainStrokeSerializer(serializers.ModelSerializer):

    # patient = serializers.ReadOnlyField(source='patient.username')
    class Meta:
        model = BrainStroke
        fields = ('id','timestamp', 'uploaded', 'clustered', 'stage', 'patient')