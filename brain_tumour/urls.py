from django.urls import path

from brain_tumour import views

urlpatterns = [
    path('list/', views.BrainTumourList.as_view()),
    path('operate/', views.operate)
]