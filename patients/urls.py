from django.urls import path

from patients import views

urlpatterns = [
    path('username_available/', views.username_available),
    path('have_patient_permissions/', views.have_patient_access),
    path('patient_list/', views.PatientList.as_view()),
    path('patient_list/<slug:username>', views.PatientDetail.as_view())
]