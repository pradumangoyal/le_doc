from django.urls import path

from skin_cancer import views

urlpatterns = [
    path('list/', views.SkinCancerList.as_view()),
    path('operate/', views.operate)
]