from dataclasses import dataclass
from typing import List, Optional, Tuple, Callable

from pynspd import Nspd

from data_provider import process_neighbors, process_target, search_area
from report_generator import generate_report


@dataclass
class ParcelResult:
    kad_id: str
    success: bool
    message: str
    neighbors_count: int = 0
    report_filename: Optional[str] = None
    report_text: Optional[str] = None
    plot_filename: Optional[str] = None


def run_batch_with_callback(
        kad_ids: List[str],
        radius_meters: int,
        area_limit: int,
        min_intersection_percent: int,
        draw_plots: bool = False,
        draw_kad: bool = False,
        log_callback: Optional[Callable[[str, str], None]] = None,
        polygon_coordinates: Optional[List[List[float]]] = None,  # <-- НОВЫЙ АРГУМЕНТ
) -> Tuple[List[ParcelResult], List[str]]:
    results = []
    logs = []
    figsize = (12, 8)

    def log(message: str, log_type: str = 'info'):
        logs.append(message)
        if log_callback:
            log_callback(message, log_type)

    # Если передан полигон, обрабатываем только его
    if polygon_coordinates:
        log(f'🚀 Запуск анализа пользовательского полигона...', 'info')

        target, crs_4326_to_utm, crs_utm_to_4326 = process_target(None, polygon_coordinates)
        search_circle_utm = search_area(target, radius_meters)

        result = _analyze_one(
            target, search_circle_utm, crs_4326_to_utm, crs_utm_to_4326,
            radius_meters, area_limit, min_intersection_percent,
            log, draw_plots, draw_kad, figsize
        )
        results.append(result)

        if result.success:
            log(f'✅ Анализ полигона завершён успешно. Найдено соседей: {result.neighbors_count}', 'success')
        else:
            log(f'❌ Анализ полигона не удался: {result.message}', 'error')

    else:
        # Стандартная логика для кадастровых номеров
        with Nspd() as nspd:
            total = len(kad_ids)
            log(f'🚀 Запуск анализа {total} участок(ов)...', 'info')

            for index, kad_id in enumerate(kad_ids, start=1):
                log(f'{"=" * 60}', 'info')
                log(f'▶️ [{index}/{total}] Начало обработки участка {kad_id}', 'progress')

                target_feat = nspd.find(kad_id)
                if not target_feat:
                    log(f'  ⚠️ Участок {kad_id} не найден в НСПД.', 'error')
                    results.append(ParcelResult(kad_id=kad_id, success=False, message='Не найден'))
                    continue

                target, crs_4326_to_utm, crs_utm_to_4326 = process_target(target_feat, None)
                search_circle_utm = search_area(target, radius_meters)

                result = _analyze_one(
                    nspd,
                    kad_id,
                    radius_meters,
                    area_limit,
                    min_intersection_percent,
                    log,
                    draw_plots,
                    draw_kad,
                    figsize,
                )
                results.append(result)

                if result.success:
                    log(f'✅ [{index}/{total}] Участок {kad_id} завершён успешно. Найдено соседей: {result.neighbors_count}',
                        'success')
                else:
                    log(f'❌ [{index}/{total}] Участок {kad_id} не обработан: {result.message}', 'error')

    success_count = sum(1 for r in results if r.success)
    log(f'{"=" * 60}', 'info')
    log(f'🎉 Анализ завершён: {success_count} из {len(results)} успешно.', 'success')

    return results, logs


def _analyze_one(
        nspd: Nspd,
        kad_id: str,
        radius_meters: int,
        area_limit: int,
        min_intersection_percent: int,
        log: Callable[[str, str], None],
        draw_plots: bool = False,
        draw_kad: bool = False,
        figsize: tuple = (12, 8),
) -> ParcelResult:
    log(f'  🔍 Поиск участка {kad_id} в НСПД...', 'progress')

    target_feat = nspd.find(kad_id)
    if not target_feat:
        message = f'Участок {kad_id} не найден в НСПД.'
        log(f'  ⚠️ {message}', 'error')
        return ParcelResult(kad_id=kad_id, success=False, message=message)

    log(f'  ✓ Участок найден, обработка геометрии...', 'info')
    target, crs_4326_to_utm, crs_utm_to_4326 = process_target(target_feat, [])
    search_circle_utm = search_area(target, radius_meters)

    def progress_callback(current: int, total: int, message: str):
        """Callback для обновления прогресса поиска соседей"""
        if total > 0:
            percent = int((current / total) * 100)
            if percent % 5 == 0:
                log(f'  📊 [{percent}%] {message}', 'progress')
        else:
            log(f'  📊 {message}', 'progress')

    log(f'  📡 Поиск соседей в радиусе {radius_meters}м...', 'progress')
    processed_neighbors = process_neighbors(
        target,
        search_circle_utm,
        nspd.search_in_contour,
        crs_4326_to_utm,
        crs_utm_to_4326,
        area_limit,
        min_intersection_percent,
        progress_callback=progress_callback,
    )
    log(f'  ✓ Найдено соседей: {len(processed_neighbors)}', 'info')

    log(f'  📄 Генерация текстового отчёта...', 'progress')
    report_path, report_text = generate_report(target, processed_neighbors)
    report_filename = report_path.split('/')[-1].split('\\')[-1]
    log(f'  ✓ Отчёт сохранён: {report_filename}', 'success')

    plot_filename = None
    if draw_plots:
        from plotting import plot_features_to_file
        log(f'  🎨 Построение графика...', 'progress')
        plot_filename = plot_features_to_file(
            target, processed_neighbors, search_circle_utm, radius_meters, draw_kad, kad_id, figsize
        )
        if plot_filename:
            log(f'  ✓ График сохранён: {plot_filename}', 'success')
        else:
            log(f'  ⚠️ Не удалось сохранить график', 'error')

    return ParcelResult(
        kad_id=kad_id,
        success=True,
        message='Успешно',
        neighbors_count=len(processed_neighbors),
        report_filename=report_filename,
        report_text=report_text,
        plot_filename=plot_filename,
    )
