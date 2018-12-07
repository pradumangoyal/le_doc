from django.shortcuts import get_object_or_404
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from patients.models import Patient
from patients.serializers import PatientSerializer
from patients.permissions import IsPatientDoctor
# Create your views here.
@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def username_available(request):
    if not 'username' in request.GET:
        return Response(data = {'available': False}, status=status.HTTP_200_OK)
    else:
        if not Patient.objects.filter(username=request.GET['username']):
            return Response(data = {'available': True}, status=status.HTTP_200_OK)
        else:
            return Response(data = {'available': False}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def have_patient_access(request):
    if not 'username' in request.GET:
        return Response(status=status.HTTP_404_NOT_FOUND)
    else:
        if request.user == get_object_or_404(Patient, username=request.GET['username']).doctor:
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_403_FORBIDDEN)

class PatientList(generics.ListCreateAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return user.patients.all()

    def list(self, request):
        queryset = self.get_queryset()
        serializer = PatientSerializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(doctor=self.request.user)

class PatientDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    lookup_field = 'username'
    permission_classes = (IsAuthenticated, IsPatientDoctor, )