from django.urls import path

from .views import IndexView, ReportDownloadView

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('reports/<str:filename>/', ReportDownloadView.as_view(), name='report_download'),
]
