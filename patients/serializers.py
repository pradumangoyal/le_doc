from rest_framework import serializers

from patients.models import Patient

class PatientSerializer(serializers.ModelSerializer):

    doctor = serializers.ReadOnlyField(source='doctor.username')
    class Meta:
        model = Patient
        fields = ('id', 'username', 'created', 'name', 'age', 'gender', 'contact', 'blood_group', 'doctor')