import os
from PIL import Image
from django.core.files import File
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from doc_doc.settings import MEDIA_ROOT
from patients.models import Patient
from brain_stroke.serializers import BrainStrokeSerializer
from brain_stroke.models import BrainStroke
# Create your views here.

class BrainStrokeList(generics.ListCreateAPIView):
    queryset = BrainStroke.objects.all()
    serializer_class = BrainStrokeSerializer

    def get_queryset(self):
        patient = self.request.GET['username']
        patient = get_object_or_404(Patient, username=patient)
        return BrainStroke.objects.filter(patient=patient)

    def list(self, request):
        if not 'username' in self.request.GET:
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            if (get_object_or_404(Patient, username=request.GET['username'])).doctor == request.user:
                queryset = self.get_queryset()
                serializer = BrainStrokeSerializer(queryset, many=True)
                return Response(serializer.data)
            else:
                return Response(status=status.HTTP_403_FORBIDDEN)

    def post(self, request, format=None):
        if get_object_or_404(Patient, id=request.data['patient']).doctor == request.user:
            serializer = BrainStrokeSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)

@api_view(['GET'])
def operate(request):
    if  not 'id' in request.GET:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    else:
        obj = get_object_or_404(BrainStroke, id=request.GET['id'])
        if request.user == obj.patient.doctor:
            if not obj.clustered:
                #It will give you an image opened in PIL
                img=Image.open(obj.uploaded.file.name).convert('L') 
                intermediate_path = MEDIA_ROOT+'/brain_stroke/'+obj.patient.username+'/orignal/intermediate_'+os.path.basename(obj.uploaded.file.name)
                #It will give you an image opened in PIL
                
                #Equivalent to ML part converting in B&W
                bw = img.point(lambda x: 0 if x<128 else 255, '1')
                obj.stage = "3" #storing predicted value
                bw.save(intermediate_path)    
                #Equivalent to ML part converting in B&W

                #Save the image as clustered
                file = open(intermediate_path, 'rb')
                obj.clustered.save(os.path.basename(obj.uploaded.file.name), File(file))
                os.remove(intermediate_path)
                #Save the image as clustered

            return Response(data=BrainStrokeSerializer(obj).data)

        return Response(status=status.HTTP_403_FORBIDDEN)
