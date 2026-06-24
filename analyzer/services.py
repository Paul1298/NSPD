from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Callable, Any

import shapely
from pynspd import Nspd

from data_provider import process_neighbors, process_target, search_area
from report_generator import generate_report


@dataclass
class ParcelResult:
    kad_id: str
    success: bool
    message: str
    neighbors_count: int = 0

    # Результаты анализа (текст/файлы)
    report_filename: Optional[str] = None
    report_text: Optional[str] = None

    # Данные для ОТЛОЖЕННОЙ отрисовки (храним как WKT строки)
    target_geom_wkt: Optional[str] = None
    search_circle_wkt: Optional[str] = None
    neighbors_data: List[dict] = field(default_factory=list)
    # neighbors_data содержит: {'kad_id': ..., 'short_id': ..., 'geom_wkt': ..., 'dir_dist': ...}


def run_batch_with_callback(
        kad_ids: List[str],
        radius_meters: int,
        area_limit: int,
        min_intersection_percent: int,
        log_callback: Optional[Callable[[str, str], None]] = None,
        polygon_coordinates: Optional[List[List[float]]] = None,
        merge_directions: bool = True,
) -> Tuple[List[ParcelResult], List[str]]:
    results = []
    logs = []

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
            nspd=None,
            kad_id="custom_polygon",
            radius_meters=radius_meters,
            area_limit=area_limit,
            min_intersection_percent=min_intersection_percent,
            log=log,
            merge_directions=merge_directions,
            target_override=target,
            crs_override=(crs_4326_to_utm, crs_utm_to_4326),
            search_circle_override=search_circle_utm,
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
                    merge_directions=merge_directions,
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
        nspd: Optional[Nspd],
        kad_id: str,
        radius_meters: int,
        area_limit: int,
        min_intersection_percent: int,
        log: Callable[[str, str], None],
        merge_directions: bool = True,
        target_override: Optional[dict] = None,
        crs_override: Optional[tuple] = None,
        search_circle_override: Optional[Any] = None,
) -> ParcelResult:
    log(f'  🔍 Поиск участка {kad_id} в НСПД...', 'progress')

    # Используем переданные параметры или получаем из НСПД
    if target_override and crs_override and search_circle_override:
        target = target_override
        crs_4326_to_utm, crs_utm_to_4326 = crs_override
        search_circle_utm = search_circle_override
    else:
        target_feat = nspd.find(kad_id)
        if not target_feat:
            message = f'Участок {kad_id} не найден в НСПД.'
            log(f'  ⚠️ {message}', 'error')
            return ParcelResult(kad_id=kad_id, success=False, message=message)

        log(f'  ✓ Участок найден, обработка геометрии...', 'info')
        target, crs_4326_to_utm, crs_utm_to_4326 = process_target(target_feat, [])
        search_circle_utm = search_area(target, radius_meters)

    def progress_callback(current: int, total: int, message: str, important: bool = False):
        """Callback для обновления прогресса поиска соседей

        Args:
            current: текущий прогресс
            total: всего элементов
            message: сообщение
            important: если True, сообщение логируется всегда, иначе только кратно 5%
        """
        if total > 0:
            percent = int((current / total) * 100)
            if important or percent % 5 == 0:
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
        merge_directions=merge_directions,
    )
    log(f'  ✓ Найдено соседей: {len(processed_neighbors)}', 'info')

    log(f'  📄 Генерация текстового отчёта...', 'progress')
    report_path, report_text = generate_report(
        target,
        processed_neighbors,
        merge_directions=merge_directions,
    )
    report_filename = report_path.split('/')[-1].split('\\')[-1]
    log(f'  ✓ Отчёт сохранён: {report_filename}', 'success')

    plot_data = {
        'target_geom_wkt': shapely.wkt.dumps(target['utm']),
        'search_circle_wkt': shapely.wkt.dumps(search_circle_utm),
        'neighbors_data': []
    }

    for n in processed_neighbors:
        plot_data['neighbors_data'].append({
            'kad_id': n['kad_id'],
            'short_id': n['short_id'],
            'geom_wkt': shapely.wkt.dumps(n['utm']),
            'dir_dist': n['dir_dist']
        })

    # 🔥 УБИРАЕМ ВЫЗОВ plot_features_to_file ОТСЮДА

    return ParcelResult(
        kad_id=kad_id,
        success=True,
        message='Успешно',
        neighbors_count=len(processed_neighbors),
        report_filename=report_path.split('/')[-1],
        report_text=report_text,
        # Сохраняем данные для будущей отрисовки
        target_geom_wkt=plot_data['target_geom_wkt'],
        search_circle_wkt=plot_data['search_circle_wkt'],
        neighbors_data=plot_data['neighbors_data'],
    )
