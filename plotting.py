import math

import matplotlib.pyplot as plt
import shapely
import shapely.plotting
from shapely import Polygon
from shapely.geometry import Point

from geo_processor import get_sectors


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


def plot_features(target, neighbors, search_circle_utm, radius_meters):
    plt.figure(figsize=(15, 10))

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
    sectors = get_sectors(search_circle_utm)

    # 2. Отрисовка секторов (заменяет старую функцию plot_sectors)
    for direction_name, sector_poly in sectors.items():
        color = color_map.get(direction_name, 'lightgray')
        x, y = sector_poly.exterior.xy
        plt.fill(x, y, color=color, alpha=0.15)

    # Отрисовка целевого участка

    plt.fill(*target["utm"].exterior.xy, color='red', alpha=0.5, label=f'{target["short_id"]} Целевой участок')
    # Добавляем подпись кадастрового номера для соседних участков
    plt.text(target["utm"].centroid.x, target["utm"].centroid.y,
             target["short_id"],
             fontsize=8, ha='center', va='center')
    # plt.plot(*target_feat_utm.exterior.xy, color='red', marker='o', markersize=2, linestyle='-')

    # Отрисовка соседних участков
    for neighbor in neighbors:
        shapely.plotting.plot_polygon(neighbor["utm"], add_points=False)

        direction = neighbor["direction"]
        color = color_map.get(direction.split(',')[0], 'gray')

        if len(direction.split(',')) > 1:
            directions_str = '\n' + direction.replace(',', ',\n')
        else:
            directions_str = direction

        try:
            plt.fill(*neighbor["utm"].exterior.xy, color=color, alpha=0.5,
                     label=f'{neighbor["short_id"]} ({directions_str})')
        except:
            pass
        # plt.plot(*neighbor_feat_utm.exterior.xy, color=color, marker='o', markersize=2, linestyle='-')

        # Добавляем подпись кадастрового номера для соседних участков
        plt.text(neighbor["utm"].centroid.x, neighbor["utm"].centroid.y,
                 neighbor["short_id"],
                 fontsize=8, ha='center', va='center')

    target_center = target["utm"].centroid
    # plt.tight_layout()
    # Устанавливаем границы области отображения
    coef = 1
    plt.xlim(
        target_center.x - radius_meters * coef,
        target_center.x + radius_meters * coef
    )
    plt.ylim(
        target_center.y - radius_meters * coef,
        target_center.y + radius_meters * coef
    )

    plt.title('Участки и их взаиморасположение')
    plt.xlabel('Координата X')
    plt.ylabel('Координата Y')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.subplots_adjust(right=0.75)

    # plt.tight_layout()
    # plt.axis('equal')  # Сохраняем пропорции
    plt.show()
