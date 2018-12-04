from rest_framework import generics, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from patients.models import Patient
from brain_tumour.serializers import BrainTumourSerializer
from brain_tumour.models import BrainTumour
# Create your views here.

class BrainTumourList(generics.ListCreateAPIView):
    queryset = BrainTumour.objects.all()
    serializer_class = BrainTumourSerializer

    def get_queryset(self):
        patient = self.request.GET['username']
        patient = get_object_or_404(Patient, username=patient)
        return BrainTumour.objects.filter(patient=patient)

    def list(self, request):
        if not 'username' in self.request.GET:
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            if get_object_or_404(Patient, username=request.GET['username']).doctor == request.user:
                queryset = self.get_queryset()
                serializer = BrainTumourSerializer(queryset, many=True)
                return Response(serializer.data)
            else:
                return Response(status=status.HTTP_403_FORBIDDEN) 

    def perform_create(self, serializer):
        serializer.save()