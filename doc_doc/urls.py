from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from doc_doc import views

urlpatterns = [
    path('api-auth/', include('rest_framework.urls')),
    path('admin/', admin.site.urls),
    path('ensure_csrf/', views.ensure_csrf),
    path('who_am_i/',views.who_am_i),
    path('patients/', include('patients.urls')),
    path('brain_tumour/', include('brain_tumour.urls')),
    path('brain_stroke/', include('brain_stroke.urls')),
    path('skin_cancer/', include('skin_cancer.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)