from django.conf import settings
from django.http import FileResponse, Http404, StreamingHttpResponse, JsonResponse
from django.shortcuts import render
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
import asyncio
import json
import time
import threading
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
            # Проверяем отключение клиента (Django 4.1+)
            if hasattr(request, 'is_disconnected') and await request.is_disconnected():
                break

            if session_id in log_sessions:
                logs = log_sessions[session_id]
                while last_id < len(logs):
                    log_entry = logs[last_id]
                    yield f"data: {json.dumps(log_entry)}\n\n"
                    last_id += 1

                    # Если получили сигнал завершения — выходим
                    if log_entry.get('type') == 'done':
                        await asyncio.sleep(0.2)
                        return

            await asyncio.sleep(0.2)

    response = StreamingHttpResponse(
        event_generator(),
        content_type='text/event-stream',
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@csrf_exempt
def get_results(request, session_id: str):
    """
    Обычный GET-endpoint для получения результатов после завершения задачи.
    """
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    results_key = f"{session_id}_results"

    if results_key in log_sessions:
        results_data = log_sessions[results_key]

        html = render_to_string('analyzer/_results_partial.html', {
            'results': results_data['results'],
            'logs': results_data['logs'],
            'success_count': results_data['success_count'],
            'total_count': results_data['total_count'],
        })

        # Очищаем данные после отправки
        del log_sessions[results_key]
        if session_id in log_sessions:
            del log_sessions[session_id]

        return JsonResponse({'success': True, 'html': html})
    else:
        return JsonResponse({'success': False, 'error': 'Результаты ещё не готовы'}, status=404)


@method_decorator(csrf_exempt, name='dispatch')
class IndexView(View):
    def get(self, request):
        form = AnalysisForm()
        return render(request, 'analyzer/index.html', {'form': form})

    def post(self, request):
        form = AnalysisForm(request.POST)

        if not form.is_valid():
            return JsonResponse({'success': False, 'error': str(form.errors)}, status=400)

        # Берём session_id из формы (генерируется на фронтенде)
        session_id = request.POST.get('session_id')
        if not session_id:
            session_id = str(int(time.time() * 1000))

        log_sessions[session_id] = []

        def log_callback(message, log_type='info'):
            log_sessions[session_id].append({
                'message': message,
                'type': log_type,
                'timestamp': time.time(),
            })

        print("!!!", form.cleaned_data['kad_ids'])

        kad_ids_raw = form.cleaned_data.get('kad_ids', '')
        kad_ids = [k.strip() for k in kad_ids_raw.split('\n') if k.strip()] if kad_ids_raw else []

        # Функция, которая будет запущена в фоновом потоке
        def run_task():
            try:
                results, logs = run_batch_with_callback(
                    kad_ids=kad_ids,
                    radius_meters=form.cleaned_data['radius_meters'],
                    area_limit=form.cleaned_data['area_limit'],
                    min_intersection_percent=form.cleaned_data['min_intersection_percent'],
                    draw_plots=form.cleaned_data['draw_plots'],
                    draw_kad=form.cleaned_data['draw_kad'],
                    log_callback=log_callback,
                    polygon_coordinates=form.cleaned_data.get('parsed_polygon'),  # <-- Передаем полигон
                )

                # Сохраняем результаты для последующего GET-запроса
                log_sessions[f"{session_id}_results"] = {
                    'results': results,
                    'logs': logs,
                    'success_count': sum(1 for r in results if r.success),
                    'total_count': len(results),
                }

                # Сигнал завершения через SSE
                log_callback("✅ Анализ завершён!", "success")
                log_callback("DONE", "done")

            except Exception as e:
                log_callback(f"❌ Критическая ошибка: {str(e)}", "error")
                log_callback("DONE", "done")

        # Запускаем в отдельном потоке — НЕ блокируем ASGI-воркер
        thread = threading.Thread(target=run_task, daemon=True)
        thread.start()

        # Сразу возвращаем ответ клиенту
        return JsonResponse({
            'success': True,
            'message': 'Задача запущена',
            'session_id': session_id
        })


class ReportDownloadView(View):
    def get(self, request, filename):
        if not filename.startswith('report_') or not filename.endswith('.txt'):
            raise Http404
        filepath = settings.REPORTS_DIR / filename
        if not filepath.is_file():
            raise Http404
        return FileResponse(open(filepath, 'rb'), as_attachment=True, filename=filename)