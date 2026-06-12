from django.urls import path
from .views import IndexView, ReportDownloadView, logs_stream, get_results

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('logs/<str:session_id>/', logs_stream, name='logs_stream'),
    path('reports/<str:filename>/', ReportDownloadView.as_view(), name='report_download'),
    path('results/<str:session_id>/', get_results, name='get_results'),
]
