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

import shutil
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
                uploaded_zip = obj.uploaded.file.name
                intermediate_picture = MEDIA_ROOT+'/brain_stroke/'+obj.patient.username+'/orignal/intermediate_state.jpg' 
                intermediate_path = MEDIA_ROOT+'/brain_stroke/'+obj.patient.username+'/orignal/intermediate_'+os.path.basename(obj.uploaded.file.name)

                #It will give you an image opened in PIL
                with zipfile.ZipFile(obj.uploaded.file.name, 'r') as zip_ref:
                    zip_ref.extractall(intermediate_path)

                item = []
                files = os.listdir(intermediate_path)
                intermediate_root_dir = intermediate_path+'/'+files[0]
                item = os.listdir(intermediate_root_dir)
                item=[intermediate_root_dir + '/' + s for s in item]
                #Equivalent to ML part converting in B&W
                # bw = img.point(lambda x: 0 if x<128 else 255, '1')
                # obj.stage = "3" #storing predicted value
                # bw.save(intermediate_path)    
                #Equivalent to ML part converting in B&W

                img_dwi = Image.open(item[0])
                img_dwi = img_dwi.resize((224, 224))
                img_dwi.save(item[0])
                img_flair = Image.open(item[1])
                img_flair = img_flair.resize((224, 224))
                img_flair.save(item[1])

                image_dwi = cv2.imread(item[0])
                image_flair = cv2.imread(item[1])

                #To get two images side by side
                out = np.concatenate((image_dwi, image_flair), axis=1)
                cv2.imwrite(intermediate_picture, out)
                file = open(intermediate_picture, 'rb')
                obj.uploaded.save(os.path.basename(obj.uploaded.file.name[:-3] + 'jpg'), File(file))
                os.remove(intermediate_picture)

                #Applying power transform and also smoothening
                kernel = np.ones((5,5),np.float32)/25
                image_dwi = cv2.filter2D(image_dwi,-1,kernel)
                image_dwi = adjust_gamma(image_dwi, 0.55)
                image_flair = cv2.filter2D(image_flair,-1,kernel)
                image_flair = adjust_gamma(image_flair, 0.55)

                image_dwi = image_dwi[:, :, 1]
                image_flair = image_flair[:, :, 1]
                image_new_dwi = image_dwi.reshape([1, -1])
                image_new_flair = image_flair.reshape([1, -1])


                #This is for optimizaing the centroid for the dwi image
                centroid_dwi = [10, 130, 220]
                for k in range(5):
                    dist = np.zeros([image_new_dwi.shape[1], 3])
                    for i in range(0,image_new_dwi.shape[1]):
                        for j in range(0,3):
                            dist[i,j] = abs(image_new_dwi[0,i] - centroid_dwi[j])
                    col_dwi = np.zeros([image_new_dwi.shape[1],1])
                    for i in range(0, image_new_dwi.shape[1]):
                        col_dwi[i] = min_index(dist[i,:])  
                    cent0 = np.array([image_new_dwi[0,j] for j in range(image_new_dwi.shape[1]) if col_dwi[j]==0])
                    cent1 = np.array([image_new_dwi[0,j] for j in range(image_new_dwi.shape[1]) if col_dwi[j]==1])
                    cent2 = np.array([image_new_dwi[0,j] for j in range(image_new_dwi.shape[1]) if col_dwi[j]==2])
                    
                    centroid_dwi[0] = cent0.mean()
                    centroid_dwi[1] = cent1.mean()
                    centroid_dwi[2] = cent2.mean()
                if(centroid_dwi[2] < 172):
                    centroid_dwi[2] = 172    
                #As the last iteration updation does not take place in the loop
                for i in range(0,image_new_dwi.shape[1]):
                        for j in range(0,3):
                            dist[i,j] = abs(image_new_dwi[0,i] - centroid_dwi[j])
                col_dwi = np.zeros([image_new_dwi.shape[1],1])
                for i in range(0, image_new_dwi.shape[1]):
                    col_dwi[i] = min_index(dist[i,:])


                #This is for optimizing the centroid for the flair image
                centroid_flair = [10, 130, 220]
                for k in range(5):
                    dist = np.zeros([image_new_flair.shape[1], 3])
                    for i in range(0,image_new_flair.shape[1]):
                        for j in range(0,3):
                            dist[i,j] = abs(image_new_flair[0,i] - centroid_flair[j])
                    col_flair = np.zeros([image_new_flair.shape[1],1])
                    for i in range(0, image_new_flair.shape[1]):
                        col_flair[i] = min_index(dist[i,:])  
                    cent0 = np.array([image_new_flair[0,j] for j in range(image_new_flair.shape[1]) if col_flair[j]==0])
                    cent1 = np.array([image_new_flair[0,j] for j in range(image_new_flair.shape[1]) if col_flair[j]==1])
                    cent2 = np.array([image_new_flair[0,j] for j in range(image_new_flair.shape[1]) if col_flair[j]==2])
                    
                    centroid_flair[0] = cent0.mean()
                    centroid_flair[1] = cent1.mean()
                    centroid_flair[2] = cent2.mean()
                if(centroid_flair[2] < 172):
                    centroid_flair[2] = 172    
                #As the last iteration updation does not take place in the loop
                for i in range(0,image_new_flair.shape[1]):
                    for j in range(0,3):
                        dist[i,j] = abs(image_new_flair[0,i] - centroid_flair[j])
                col_flair = np.zeros([image_new_flair.shape[1],1])
                for i in range(0, image_new_flair.shape[1]):
                    col_flair[i] = min_index(dist[i,:])

                #For basic resizing operations
                image_dwi = image_new_dwi.reshape([224,-1])
                column_dwi = col_dwi.reshape([224, -1])
                image_flair = image_new_flair.reshape([224,-1])
                column_flair = col_flair.reshape([224, -1])

                #This is for creation of the final output
                brain_image = cv2.imread(item[1])
                for i in range(brain_image.shape[0]):
                    for j in range(brain_image.shape[1]):
                        if column_dwi[i,j] == 2:
                            brain_image[i, j, 0] = 0
                            brain_image[i, j, 1] = 0
                            brain_image[i, j, 2] = 255
                        elif column_flair[i, j] == 2:
                            brain_image[i, j, 0] = 0
                            brain_image[i, j, 1] = 255
                            brain_image[i, j, 2] = 0
                
                cv2.imwrite(intermediate_picture, brain_image)
                file = open(intermediate_picture, 'rb')
                obj.clustered.save(os.path.basename(obj.uploaded.file.name[:-3] + 'jpg'), File(file))
                os.remove(intermediate_picture)
                os.remove(uploaded_zip)

                shutil.rmtree(intermediate_root_dir)

                #Save the image as clustered
                # file = open(intermediate_path, 'rb')
                # obj.clustered.save(os.path.basename(obj.uploaded.file.name), File(file))
                # os.remove(intermediate_path)
                #Save the image as clustered

            return Response(data=BrainStrokeSerializer(obj).data)

        return Response(status=status.HTTP_403_FORBIDDEN)
