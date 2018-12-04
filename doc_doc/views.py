from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def who_am_i(request):
        return Response(data = {
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "username": request.user.username,
            "email": request.user.email,
        }, status=status.HTTP_200_OK)

@api_view(['GET'])
@ensure_csrf_cookie
def ensure_csrf(request):
    return Response(status=status.HTTP_200_OK)

