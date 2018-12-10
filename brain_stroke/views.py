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

import zipfile
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import datasets, transforms, models
import numpy as np
import cv2
# Create your views here.

#For power transform in images
def adjust_gamma(image, gamma=1.0):
	invGamma = 1.0 / gamma
	table = np.array([((i / 255.0) ** invGamma) * 255
		for i in np.arange(0, 256)]).astype("uint8")
 
	return cv2.LUT(image, table)

#For finding the min value of passed array
def min_index(array):
    min=0
    for i in range(1,len(array)):
        if array[i]<array[min]:
            min=i
    return min 

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
                # img=Image.open(obj.uploaded.file.name).convert('L') 
                intermediate_path = MEDIA_ROOT+'/brain_stroke/'+obj.patient.username+'/orignal/intermediate_'+os.path.basename(obj.uploaded.file.name)

                #It will give you an image opened in PIL
                with zipfile.ZipFile(obj.uploaded.file.name, 'r') as zip_ref:
                    zip_ref.extractall(intermediate_path)

                item = []
                files = os.listdir(intermediate_path)
                print(files)
                intermediate_root_dir = intermediate_path+'/'+files[0]
                print(files[0])
                print(intermediate_root_dir)
                item = os.listdir(intermediate_root_dir)
                item=[intermediate_root_dir + s for s in item]
                print(item)

                #Equivalent to ML part converting in B&W
                # bw = img.point(lambda x: 0 if x<128 else 255, '1')
                # obj.stage = "3" #storing predicted value
                # bw.save(intermediate_path)    
                #Equivalent to ML part converting in B&W

                #Save the image as clustered
                # file = open(intermediate_path, 'rb')
                # obj.clustered.save(os.path.basename(obj.uploaded.file.name), File(file))
                # os.remove(intermediate_path)
                #Save the image as clustered

            return Response(data=BrainStrokeSerializer(obj).data)

        return Response(status=status.HTTP_403_FORBIDDEN)
