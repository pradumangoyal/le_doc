import os
from PIL import Image
from django.core.files import File
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from doc_doc.settings import MEDIA_ROOT, BASE_DIR
from patients.models import Patient
from skin_cancer.serializers import SkinCancerSerializer
from skin_cancer.models import SkinCancer
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import datasets, transforms, models

import numpy as np
import cv2
# Create your views here.
def min_index(array):
    min=0
    for i in range(1,len(array)):
        if array[i]<array[min]:
            min=i
    return min 

class SkinCancerList(generics.ListCreateAPIView):
    queryset = SkinCancer.objects.all()
    serializer_class = SkinCancerSerializer

    def get_queryset(self):
        patient = self.request.GET['username']
        patient = get_object_or_404(Patient, username=patient)
        return SkinCancer.objects.filter(patient=patient)

    def list(self, request):
        if not 'username' in self.request.GET:
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            if (get_object_or_404(Patient, username=request.GET['username'])).doctor == request.user:
                queryset = self.get_queryset()
                serializer = SkinCancerSerializer(queryset, many=True)
                return Response(serializer.data)
            else:
                return Response(status=status.HTTP_403_FORBIDDEN)

    def post(self, request, format=None):
        if get_object_or_404(Patient, id=request.data['patient']).doctor == request.user:
            serializer = SkinCancerSerializer(data=request.data)
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
        obj = get_object_or_404(SkinCancer, id=request.GET['id'])
        if request.user == obj.patient.doctor:
            if not obj.clustered:
                #It will give you an image opened in PIL
                img=Image.open(obj.uploaded.file.name)
                intermediate_path = MEDIA_ROOT+'/skin_cancer/'+obj.patient.username+'/orignal/intermediate_'+os.path.basename(obj.uploaded.file.name)
                #It will give you an image opened in PIL

                img = img.resize((224, 224))
                img.save(intermediate_path)
                
                model_image = Image.open(intermediate_path)

                file = open(intermediate_path, 'rb')
                obj.uploaded.save(os.path.basename(obj.uploaded.file.name), File(file))
                img = img.convert('L')
                img.save(intermediate_path)
                image = cv2.imread(intermediate_path)
                image = image[:, :, 1]
                image_new = image.reshape([1,-1])

                centroid = [40, 140]
                for k in range(5):
                    dist = np.zeros([image_new.shape[1], 2])
                    for i in range(0,image_new.shape[1]):
                        for j in range(0,2):
                            dist[i,j] = abs(image_new[0,i] - centroid[j])
                    col = np.zeros([image_new.shape[1],1])
                    for i in range(0, image_new.shape[1]):
                        col[i] = min_index(dist[i,:])  
                    cent0 = np.array([image_new[0,j] for j in range(image_new.shape[1]) if col[j]==0])
                    cent1 = np.array([image_new[0,j] for j in range(image_new.shape[1]) if col[j]==1])
                    centroid[0] = cent0.mean()
                    centroid[1] = cent1.mean()

                image = image_new.reshape([224,-1])
                column = col.reshape([224, -1])
                color_matrix = np.zeros([column.shape[0], column.shape[1], 3])

                for i in range(column.shape[0]):
                    for j in range(column.shape[1]):
                        if column[i, j] == 0:
                            color_matrix[i, j, 0] = 255
                            color_matrix[i, j, 1] = 255
                            color_matrix[i,j,2]= 255   
                        elif column[i, j] == 1:
                            color_matrix[i, j, 0] = 0
                            color_matrix[i, j, 1] = 0
                            color_matrix[i,j,2]= 0

                cv2.imwrite(intermediate_path, color_matrix)

                #Predicting the classification os disease types
                model = models.vgg16_bn(pretrained=True)
                for param in model.parameters():
                    param.requires_grad = False

                from collections import OrderedDict
                classifier = nn.Sequential(nn.Linear(25088, 4096),
                                        nn.ReLU(),
                                        nn.Dropout(0.4),
                                        nn.Linear(4096, 1000),
                                        nn.ReLU(),
                                        nn.Dropout(0.4),
                                        nn.Linear(1000, 256),
                                        nn.ReLU(),
                                        nn.Dropout(0.4),
                                        nn.Linear(256, 7),
                                        nn.LogSoftmax(dim=1))
                    
                model.classifier = classifier
                print(BASE_DIR)
                state_dict = torch.load(BASE_DIR + '/skin_cancer/checkpoint.pth', map_location='cpu')
                model.load_state_dict(state_dict)
                train_transforms = transforms.Compose([transforms.ToTensor(),
                                                       transforms.Normalize([0.485, 0.456, 0.406],
                                                                            [0.229, 0.224, 0.225])])
                model_image_new = train_transforms(model_image)
                model_image_new = model_image_new.view(1, 3, 224, 224)
                logps = model.forward(model_image_new)
                probailities = torch.exp(logps)

                #Equivalent to ML part converting in B&W
                #bw = img.point(lambda x: 0 if x<128 else 255, '1')
                obj.bowen = str(round(probailities[0][0].item()*100, 2))
                obj.carcinoma = str(round(probailities[0][1].item()*100, 2))
                obj.keratoses = str(round(probailities[0][2].item()*100, 2))
                obj.dermatofibroma = str(round(probailities[0][3].item()*100, 2))
                obj.melanoma = str(round(probailities[0][4].item()*100, 2))
                obj.nevus = str(round(probailities[0][5].item()*100, 2))
                obj.vascular = str(round(probailities[0][6].item()*100, 2))
                #Equivalent to ML part converting in B&W

                #Save the image as clustered
                file = open(intermediate_path, 'rb')
                obj.clustered.save(os.path.basename(obj.uploaded.file.name), File(file))
                os.remove(intermediate_path)
                #Save the image as clustered

            return Response(data=SkinCancerSerializer(obj).data)

        return Response(status=status.HTTP_403_FORBIDDEN)
