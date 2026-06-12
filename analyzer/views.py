from django.conf import settings
from django.http import FileResponse, Http404, StreamingHttpResponse
from django.shortcuts import render
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
import time
import threading
from typing import Dict, List

from .forms import AnalysisForm
from .services import run_batch_with_callback

# Хранилище сессий логов (в памяти для простоты)
log_sessions: Dict[str, List[str]] = {}


@csrf_exempt
def logs_stream(request, session_id: str):
    """Server-Sent Events endpoint для стриминга логов"""

    def event_stream():
        last_id = 0
        while True:
            if session_id in log_sessions:
                logs = log_sessions[session_id]
                while last_id < len(logs):
                    log_entry = logs[last_id]
                    yield f"data: {json.dumps(log_entry)}\n\n"
                    last_id += 1
            time.sleep(0.1)

    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream',
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


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

        # Если нажата кнопка "Новый анализ" - просто показываем чистую форму
        if 'reset' in request.POST:
            return render(request, 'analyzer/index.html', {
                'form': AnalysisForm(),
                'results': None,
                'logs': [],
                'success_count': 0,
                'total_count': 0,
            })

        if not form.is_valid():
            return render(request, 'analyzer/index.html', {
                'form': form,
                'results': None,
                'logs': [],
                'success_count': 0,
                'total_count': 0,
            })

        # Создаём сессию для логов
        session_id = str(int(time.time() * 1000))
        log_sessions[session_id] = []

        def log_callback(message: str, log_type: str = 'info'):
            """Callback для добавления логов в сессию"""
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

        # Очищаем сессию после завершения
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

        return FileResponse(
            open(filepath, 'rb'),
            as_attachment=True,
            filename=filename,
        )


