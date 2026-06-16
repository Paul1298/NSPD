import sys

from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    path('', include('analyzer.urls')),
]

# Настройка обслуживания статических файлов графиков
if settings.DEBUG:
    urlpatterns += static('plots/', document_root=settings.BASE_DIR / 'plots')

if settings.DEBUG or getattr(sys, 'frozen', False):
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT or settings.BASE_DIR)

