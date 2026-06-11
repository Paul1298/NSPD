from dataclasses import dataclass
from typing import List, Optional, Tuple

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


def run_batch(
        kad_ids: List[str],
        radius_meters: int,
        area_limit: int,
        min_intersection_percent: int,
        draw_plots: bool = False,
        draw_kad: bool = False,
) -> Tuple[List[ParcelResult], List[str]]:
    results = []
    logs = []

    # Стандартный размер графика
    figsize = (12, 8)

    with Nspd() as nspd:
        for index, kad_id in enumerate(kad_ids, start=1):
            logs.append(f'--- [{index}/{len(kad_ids)}] {kad_id} ---')
            result = _analyze_one(
                nspd,
                kad_id,
                radius_meters,
                area_limit,
                min_intersection_percent,
                logs,
                draw_plots,
                draw_kad,
                figsize,
            )
            results.append(result)

    success_count = sum(1 for r in results if r.success)
    logs.append(f'Готово: {success_count} из {len(kad_ids)} участков.')
    return results, logs


def _analyze_one(
        nspd: Nspd,
        kad_id: str,
        radius_meters: int,
        area_limit: int,
        min_intersection_percent: int,
        logs: List[str],
        draw_plots: bool = False,
        draw_kad: bool = False,
        figsize: tuple = (12, 8),
) -> ParcelResult:
    logs.append(f'Поиск участка {kad_id}...')

    target_feat = nspd.find(kad_id)
    if not target_feat:
        message = f'Участок {kad_id} не найден в НСПД.'
        logs.append(message)
        return ParcelResult(kad_id=kad_id, success=False, message=message)

    target, crs_4326_to_utm, crs_utm_to_4326 = process_target(target_feat, [])
    search_circle_utm = search_area(target, radius_meters)

    processed_neighbors = process_neighbors(
        target,
        search_circle_utm,
        nspd.search_in_contour,
        crs_4326_to_utm,
        crs_utm_to_4326,
        area_limit,
        min_intersection_percent,
    )
    logs.append(f'Найдено соседей: {len(processed_neighbors)}')

    report_path, report_text = generate_report(target, processed_neighbors)
    report_filename = report_path.split('/')[-1].split('\\')[-1]
    logs.append(f'Отчёт сохранён: {report_path}')

    plot_filename = None
    if draw_plots:
        from plotting import plot_features_to_file
        plot_filename = plot_features_to_file(
            target, processed_neighbors, search_circle_utm, radius_meters, draw_kad, kad_id, figsize
        )
        if plot_filename:
            logs.append(f'График сохранён: {plot_filename}')

    return ParcelResult(
        kad_id=kad_id,
        success=True,
        message='Успешно',
        neighbors_count=len(processed_neighbors),
        report_filename=report_filename,
        report_text=report_text,
        plot_filename=plot_filename,
    )
