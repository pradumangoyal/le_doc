from rest_framework import permissions

class IsPatientDoctor(permissions.BasePermission):


    def has_object_permission(self, request, view, obj):
        return obj.doctor == request.user