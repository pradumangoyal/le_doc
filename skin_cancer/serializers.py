from rest_framework import serializers

from skin_cancer.models import SkinCancer

class SkinCancerSerializer(serializers.ModelSerializer):

    # patient = serializers.ReadOnlyField(source='patient.username')
    class Meta:
        model = SkinCancer
        fields = ('id','timestamp', 'uploaded', 'clustered', 
                'melanoma', 'vascular', 'nevus', 'dermatofibroma', 
                'bowen', 'keratoses', 'carcinoma', 'patient')