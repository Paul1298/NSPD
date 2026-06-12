from django.conf import settings
from django.http import FileResponse, Http404, StreamingHttpResponse, JsonResponse
from django.shortcuts import render
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import asyncio
import json
import time
from typing import Dict, List

from .forms import AnalysisForm
from .services import run_batch_with_callback

# Глобальное хранилище сессий
log_sessions: Dict[str, List[Dict]] = {}


@csrf_exempt
async def logs_stream(request, session_id: str):
    """
    Async SSE endpoint для стриминга логов.
    Работает через Daphne (ASGI) без блокировки воркеров.
    """

    async def event_generator():
        last_id = 0
        while True:
            if session_id in log_sessions:
                logs = log_sessions[session_id]
                while last_id < len(logs):
                    log_entry = logs[last_id]
                    yield f"data: {json.dumps(log_entry)}\n\n"
                    last_id += 1
            await asyncio.sleep(0.1)

    response = StreamingHttpResponse(
        event_generator(),
        content_type='text/event-stream',
    )
    # Не добавляем 'Connection' заголовок - ASGI сам обрабатывает
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@method_decorator(csrf_exempt, name='dispatch')
class IndexView(View):
    def get(self, request):
        form = AnalysisForm()
        return render(request, 'analyzer/index.html', {'form': form})

    def post(self, request):
        form = AnalysisForm(request.POST)

        if not form.is_valid():
            return JsonResponse({'success': False, 'error': str(form.errors)})

        # 🔥 ИСПРАВЛЕНИЕ: Берем session_id из данных формы, а не генерируем новый
        session_id = request.POST.get('session_id')
        if not session_id:
            # Фоллбэк, если фронтенд вдруг не прислал ID
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

        # Для AJAX возвращаем HTML результатов
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from django.template.loader import render_to_string
            html = render_to_string('analyzer/_results_partial.html', {
                'results': results,
                'logs': logs,
                'success_count': sum(1 for r in results if r.success),
                'total_count': len(results),
            })
            return JsonResponse({'success': True, 'html': html})

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