from django.urls import path

from brain_stroke import views

urlpatterns = [
    path('list/', views.BrainStrokeList.as_view()),
    path('operate/', views.operate)
]