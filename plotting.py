import math

import matplotlib

matplotlib.use('Agg')  # Явное указание бэкенда
import matplotlib.pyplot as plt
import shapely
import shapely.plotting
from shapely import Polygon
from shapely.geometry import Point

from geo_processor import get_sectors
from django.conf import settings


def plot_sectors(ax, center, radius, color_map=None):
    """
    Рисует секторы вокруг центральной точки с заданными градусами и цветами

    Args:
        ax (matplotlib.axes.Axes): Осевой объект для рисования
        center (Point): Центральная точка
        radius (float): Радиус секторов
        color_map (dict, optional): Словарь цветов для секторов
    """
    sectors = [
        ("с северной стороны", 67.5, 112.5),  # Сектор вокруг 90 градусов
        ("с северо-восточной стороны", 22.5, 67.5),  # Сектор вокруг 45 градусов
        ("с восточной стороны", 337.5, 22.5),  # Сектор вокруг 0/360 градусов
        ("с юго-восточной стороны", 292.5, 337.5),  # Сектор вокруг 315 градусов
        ("с южной стороны", 247.5, 292.5),  # Сектор вокруг 270 градусов
        ("с юго-западной стороны", 202.5, 247.5),  # Сектор вокруг 225 градусов
        ("с западной стороны", 157.5, 202.5),  # Сектор вокруг 180 градусов
        ("с северо-западной стороны", 112.5, 157.5),  # Сектор вокруг 135 градусов
    ]

    # Если цветовая карта не передана, используем дефолтную
    if color_map is None:
        color_map = {direction: plt.cm.tab10(i) for i, (direction, _, _) in enumerate(sectors)}

    for direction, start, end in sectors:
        # Преобразуем углы в радианы
        start_rad, end_rad = math.radians(start), math.radians(end)

        # Вычисляем точки сектора
        x1 = center.x + radius * math.cos(start_rad)
        y1 = center.y + radius * math.sin(start_rad)
        x2 = center.x + radius * math.cos(end_rad)
        y2 = center.y + radius * math.sin(end_rad)

        # Создаем сектор как многоугольник
        sector_poly = Polygon([
            (center.x, center.y),
            (x1, y1),
            (x2, y2)
        ])

        # Выбираем цвет для сектора
        color = color_map.get(direction, 'lightgray')

        # Рисуем сектор
        x, y = sector_poly.exterior.xy
        ax.fill(x, y, color=color, alpha=0.1)


def plot_features(target, neighbors, search_circle_utm, radius_meters, should_draw_kad, figsize=(12, 8)):
    """
    Оригинальная функция для интерактивного отображения графика
    """
    fig = plot_features_common(target, neighbors, search_circle_utm, radius_meters, should_draw_kad, figsize)
    plt.show()


def plot_features_to_file(target, neighbors, search_circle_utm, radius_meters, should_draw_kad, kad_id,
                          figsize=(12, 8)):
    """
    Сохраняет график в файл вместо отображения

    Args:
        target: целевой участок
        neighbors: список соседних участков
        search_circle_utm: круг поиска
        radius_meters: радиус поиска в метрах
        should_draw_kad: флаг отображения кадастровых номеров
        kad_id: кадастровый номер для имени файла
        figsize: кортеж (ширина, высота) в дюймах

    Returns:
        str: относительный путь к сохранённому файлу или None при ошибке
    """
    try:
        # Создаём директорию для графиков
        PLOTS_DIR = settings.BASE_DIR / 'plots'
        PLOTS_DIR.mkdir(exist_ok=True)

        # Генерируем имя файла
        safe_kad_id = kad_id.replace(':', '_')
        filename = f'plot_{safe_kad_id}.png'
        filepath = PLOTS_DIR / filename

        fig = plot_features_common(target, neighbors, search_circle_utm, radius_meters, should_draw_kad, figsize)

        # Сохраняем график
        fig.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)

        # Возвращаем относительный путь от BASE_DIR
        return str(filepath.relative_to(settings.BASE_DIR))

    except Exception as e:
        print(f"Ошибка при сохранении графика: {e}")
        return None


def plot_features_common(target, neighbors, search_circle_utm, radius_meters, should_draw_kad, figsize=(12, 8)):
    """
    Общая логика построения графика, возвращает фигуру без отображения
    """
    fig = plt.figure(figsize=figsize)
    ax = fig.gca()

    directions = [
        "с северной стороны",
        "с северо-восточной стороны",
        "с восточной стороны",
        "с юго-восточной стороны",
        "с южной стороны",
        "с юго-западной стороны",
        "с западной стороны",
        "с северо-западной стороны"
    ]
    color_map = {direction: plt.cm.tab10(i) for i, direction in enumerate(directions)}

    # Отрисовка секторов
    plt.plot(*search_circle_utm.exterior.xy, color='blue', linewidth=0.5, linestyle='--')

    sectors = get_sectors(search_circle_utm)

    # 2. Отрисовка секторов (заменяет старую функцию plot_sectors)
    for direction_name, sector_poly in sectors.items():
        color = color_map.get(direction_name, 'lightgray')
        x, y = sector_poly.exterior.xy
        plt.fill(x, y, color=color, alpha=0.3)

    # Отрисовка целевого участка
    plt.fill(*target["utm"].exterior.xy, color='blue', alpha=0.4, label=f'{target["short_id"]} Целевой участок')
    plt.text(target["utm"].centroid.x, target["utm"].centroid.y,
             target["short_id"],
             fontsize=8, ha='center', va='center')
    plt.plot(*target["utm"].exterior.xy, color='blue', linestyle='-')

    # Группируем соседей по направлениям для компактной легенды
    # neighbor_by_direction = {}
    # for neighbor in neighbors:
    #     direction = neighbor["direction"].split(',')[0].strip()
    #     if direction not in neighbor_by_direction:
    #         neighbor_by_direction[direction] = []
    #     neighbor_by_direction[direction].append(neighbor)

    # Отрисовка соседних участков
    for neighbor in neighbors:
        shapely.plotting.plot_polygon(neighbor["utm"], add_points=False)

        direction = neighbor["dir_dist"][0][0]
        color = color_map.get(direction.split(',')[0], 'gray')

        if len(direction.split(',')) > 1:
            directions_str = '\n' + direction.replace(',', ',\n')
        else:
            directions_str = direction

        try:
            plt.fill(*neighbor["utm"].exterior.xy, color=color, alpha=0.5)
        except:
            pass

        if should_draw_kad:
            plt.text(neighbor["utm"].centroid.x, neighbor["utm"].centroid.y,
                     neighbor["short_id"],
                     fontsize=8, ha='center', va='center')

    target_poly: Polygon = target["utm"]
    minx, miny, maxx, maxy = target_poly.bounds
    coef = 2
    plt.xlim(
        minx - radius_meters * coef,
        maxx + radius_meters * coef
    )
    plt.ylim(
        miny - radius_meters * coef,
        maxy + radius_meters * coef
    )

    plt.title(f'Участки и их взаиморасположение ({target["kad_id"]})', fontsize=12)
    # plt.xlabel('Координата X', fontsize=10)
    # plt.ylabel('Координата Y', fontsize=10)

    # Создаём компактную легенду с группировкой по направлениям
    legend_elements = []

    # Целевой участок
    legend_elements.append(plt.Line2D([0], [0], marker='s', color='w', markerfacecolor='blue',
                                      markersize=8, label=f'{target["short_id"]} Целевой участок'))

    # # Группированные направления
    # for direction in directions:
    #     if direction in neighbor_by_direction:
    #         color = color_map.get(direction, 'gray')
    #         count = len(neighbor_by_direction[direction])
    #         label = f'{direction}: {count} ({", ".join([n["short_id"] for n in neighbor_by_direction[direction][:3]])}'
    #         if count > 3:
    #             label += f' +{count-3} др.)'
    #         else:
    #             label += ')'
    #         legend_elements.append(plt.Line2D([0], [0], marker='s', color='w', markerfacecolor=color,
    #                                            markersize=6, label=label))

    # Размещаем легенду внутри графика в верхнем правом углу
    # plt.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1, 1),
    #            fontsize=8, framealpha=0.9, borderpad=0.5)
    # plt.subplots_adjust(right=0.65)
    ax.set_xticks([])
    ax.set_yticks([])

    return fig


def get_polygons(geom):
    """
    Возвращает список Polygon из геометрии.
    Работает и с Polygon, и с MultiPolygon.
    """
    if geom.geom_type == 'Polygon':
        return [geom]
    elif geom.geom_type == 'MultiPolygon':
        return list(geom.geoms)
    else:
        return []


def plot_features_from_wkt(
        target_geom,
        search_circle,
        neighbors,
        radius_meters,
        should_draw_kad,
        kad_id,
        figsize=(8, 8),
):
    """
    Отрисовка на основе заранее подготовленных геометрий (WKT).
    Корректно работает с Polygon и MultiPolygon.
    """
    try:
        PLOTS_DIR = settings.BASE_DIR / 'plots'
        PLOTS_DIR.mkdir(exist_ok=True)

        safe_kad_id = kad_id.replace(':', '_')
        filename = f'plot_{safe_kad_id}.png'
        filepath = PLOTS_DIR / filename

        fig = plt.figure(figsize=figsize)
        ax = fig.gca()

        directions = [
            "с северной стороны", "с северо-восточной стороны", "с восточной стороны",
            "с юго-восточной стороны", "с южной стороны", "с юго-западной стороны",
            "с западной стороны", "с северо-западной стороны"
        ]
        color_map = {direction: plt.cm.tab10(i) for i, direction in enumerate(directions)}

        # Рисуем круг поиска
        plt.plot(*search_circle.exterior.xy, color='blue', linewidth=0.5, linestyle='--')

        # Рисуем секторы
        sectors = get_sectors(search_circle)
        for direction_name, sector_poly in sectors.items():
            color = color_map.get(direction_name, 'lightgray')
            x, y = sector_poly.exterior.xy
            plt.fill(x, y, color=color, alpha=0.15)

        # Рисуем целевой участок (может быть MultiPolygon)
        for poly in get_polygons(target_geom):
            plt.fill(*poly.exterior.xy, color='blue', alpha=0.4, label='Целевой участок')
            plt.plot(*poly.exterior.xy, color='blue', linestyle='-')

        # Подпись целевого участка (по центроиду всей геометрии)
        plt.text(target_geom.centroid.x, target_geom.centroid.y,
                 safe_kad_id, fontsize=6, ha='center', va='center')

        # Рисуем соседей (каждый может быть MultiPolygon)
        for neighbor in neighbors:
            geom = neighbor['utm']
            shapely.plotting.plot_polygon(geom, add_points=False)
            direction = neighbor['dir_dist'][0][0] if neighbor['dir_dist'] else ''
            color = color_map.get(direction.split(',')[0].strip(), 'gray')

            # Обрабатываем каждый полигон в геометрии соседа
            for poly in get_polygons(geom):
                plt.fill(*poly.exterior.xy, color=color, alpha=0.5)
                plt.plot(*poly.exterior.xy, color=color, linewidth=0.5)

            # if should_draw_kad:
            #     plt.text(geom.centroid.x, geom.centroid.y,
            #              neighbor['short_id'], fontsize=8, ha='center', va='center')

        # Настройка границ — используем search_circle.bounds
        minx, miny, maxx, maxy = search_circle.bounds

        # Добавляем небольшой запас (10-20%)
        padding = (maxx - minx) * 0.1  # 10% от ширины

        plt.xlim(minx - padding, maxx + padding)
        plt.ylim(miny - padding, maxy + padding)

        # plt.title(f'Участки и их взаиморасположение ({kad_id})', fontsize=12)
        ax.set_xticks([])
        ax.set_yticks([])

        fig.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)

        return str(filepath.relative_to(PLOTS_DIR))

    except Exception as e:
        print(f"Ошибка при сохранении графика: {e}")
        import traceback
        traceback.print_exc()
        return None
