from django.conf import settings
from django.http import FileResponse, Http404
from django.shortcuts import render
from django.views import View
import time

from .forms import AnalysisForm
from .services import run_batch_with_callback
from .streaming import log_sessions


class IndexView(View):
    def get(self, request):
        form = AnalysisForm()
        return render(request, 'analyzer/index.html', {
            'form': form,
            'results': None,
            'logs': [],
            'success_count': 0,
            'total_count': 0,
        })

    def post(self, request):
        form = AnalysisForm(request.POST)
        
        if not form.is_valid():
            return render(request, 'analyzer/index.html', {
                'form': form,
                'results': None,
                'logs': [],
                'success_count': 0,
                'total_count': 0,
            })

        session_id = str(int(time.time() * 1000))
        log_sessions[session_id] = []

        def log_callback(message, log_type='info'):
            log_sessions[session_id].append({
                'message': message,
                'type': log_type,
                'timestamp': time.time(),
            })

        results, logs = run_batch_with_callback(
            kad_ids=form.cleaned_data['kad_ids'],
            radius_meters=form.cleaned_data['radius_meters'],
            area_limit=form.cleaned_data['area_limit'],
            min_intersection_percent=form.cleaned_data['min_intersection_percent'],
            draw_plots=form.cleaned_data['draw_plots'],
            draw_kad=form.cleaned_data['draw_kad'],
            log_callback=log_callback,
        )

        if session_id in log_sessions:
            del log_sessions[session_id]

        return render(request, 'analyzer/index.html', {
            'form': form,
            'results': results,
            'logs': logs,
            'success_count': sum(1 for r in results if r.success),
            'total_count': len(results),
        })


class ReportDownloadView(View):
    def get(self, request, filename):
        if not filename.startswith('report_') or not filename.endswith('.txt'):
            raise Http404

        filepath = settings.REPORTS_DIR / filename
        if not filepath.is_file():
            raise Http404

        return FileResponse(open(filepath, 'rb'), as_attachment=True, filename=filename)
