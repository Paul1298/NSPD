import math

import geopandas as gpd
import matplotlib.pyplot as plt
from pyproj import Transformer, CRS
from shapely import Polygon
from shapely.geometry import Point
from shapely.ops import transform

from geo_processor import get_distance_direction


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


def plot_features(target_feat, neighbor_feats, search_circle, radius_meters):
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

    gdf = gpd.GeoDataFrame(
        {'id': [1], 'geometry': [target_feat.geometry.to_shape()]},
        crs='EPSG:4326'
    )
    UTM_CRS = gdf.estimate_utm_crs()

    crs_4326_to_utm = Transformer.from_crs(CRS("EPSG:4326"), UTM_CRS, always_xy=True).transform

    # Отрисовка области поиска
    search_circle_utm = transform(crs_4326_to_utm, search_circle)
    plt.fill(*search_circle_utm.exterior.xy, color='gray', alpha=0.1, label='Область поиска')
    plt.plot(*search_circle_utm.exterior.xy, color='gray', linestyle='--', linewidth=1)

    # Отрисовка секторов
    search_circle_center = search_circle_utm.centroid
    plot_sectors(
        plt.gca(),
        search_circle_center,
        search_circle_utm.exterior.distance(search_circle_center),
        color_map
    )

    # Отрисовка целевого участка
    target_feat_utm = transform(crs_4326_to_utm, target_feat.geometry.to_shape())

    plt.fill(*target_feat_utm.exterior.xy, color='red', alpha=0.5, label='Целевой участок')
    # plt.plot(*target_feat_utm.exterior.xy, color='red', marker='o', markersize=2, linestyle='-')

    # Отрисовка соседних участков
    for neighbor_feat in neighbor_feats:
        if neighbor_feat.properties.options.cad_num == target_feat.properties.options.cad_num:
            continue

        dist, direction = get_distance_direction(target_feat, neighbor_feat, search_circle_utm)

        neighbor_feat_utm = transform(crs_4326_to_utm, neighbor_feat.geometry.to_shape())

        color = color_map.get(direction.split(',')[0], 'gray')

        if len(direction.split(',')) > 1:
            directions_str = '\n' + direction.replace(',', ',\n')
        else:
            directions_str = direction

        try:
            plt.fill(*neighbor_feat_utm.exterior.xy, color=color, alpha=0.5,
                     label=f'{neighbor_feat.properties.options.cad_num[6:]} ({directions_str})')
        except:
            pass
        # plt.plot(*neighbor_feat_utm.exterior.xy, color=color, marker='o', markersize=2, linestyle='-')

        # Добавляем подпись кадастрового номера для соседних участков
        plt.text(neighbor_feat_utm.centroid.x, neighbor_feat_utm.centroid.y,
                 neighbor_feat.properties.options.cad_num[6:],
                 fontsize=8, ha='center', va='center')

    target_center = target_feat_utm.centroid
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

    plt.tight_layout()
    # plt.axis('equal')  # Сохраняем пропорции
    plt.show()
