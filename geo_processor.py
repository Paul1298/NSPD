import math

import geopandas as gpd
import shapely
import shapely.plotting
from pynspd import NspdFeature
from pyproj import Transformer, CRS
from shapely import Polygon
from shapely.ops import transform, nearest_points


def get_direction(target_poly, neighbor_poly, search_circle_utm):
    """
    Определяет направления между полигонами с учетом секторов

    Args:
        target_poly (Polygon): Целевой полигон
        neighbor_poly (Polygon): Полигон соседа
        search_circle_utm (Polygon): Круг поиска в UTM

    Returns:
        str: Направления света
    """
    # Базовые направления
    directions = [
        ("с северной стороны", 67.5, 112.5),  # Сектор вокруг 90 градусов
        ("с северо-восточной стороны", 22.5, 67.5),  # Сектор вокруг 45 градусов
        ("с восточной стороны", 337.5, 22.5),  # Сектор вокруг 0/360 градусов
        ("с юго-восточной стороны", 292.5, 337.5),  # Сектор вокруг 315 градусов
        ("с южной стороны", 247.5, 292.5),  # Сектор вокруг 270 градусов
        ("с юго-западной стороны", 202.5, 247.5),  # Сектор вокруг 225 градусов
        ("с западной стороны", 157.5, 202.5),  # Сектор вокруг 180 градусов
        ("с северо-западной стороны", 112.5, 157.5),  # Сектор вокруг 135 градусов
    ]

    # Центр круга поиска
    search_center = search_circle_utm.centroid
    radius = search_circle_utm.exterior.distance(search_center)

    detected_directions = []

    for direction_name, start, end in directions:
        # Вычисляем точки сектора
        start_rad, end_rad = math.radians(start), math.radians(end)

        x1 = search_center.x + radius * math.cos(start_rad)
        y1 = search_center.y + radius * math.sin(start_rad)
        x2 = search_center.x + radius * math.cos(end_rad)
        y2 = search_center.y + radius * math.sin(end_rad)

        # Создаем полигон сектора
        sector_poly = Polygon([
            (search_center.x, search_center.y),
            (x1, y1),
            (x2, y2)
        ])

        # Проверяем пересечение центроидов
        if sector_poly.intersects(neighbor_poly):
            detected_directions.append(direction_name)

    # Возвращаем список направлений или дефолтное
    return ', '.join(detected_directions) if detected_directions else "не опознан"


def get_distance_direction(target_feat: NspdFeature, neighbor_feat: NspdFeature, search_circle_utm: Polygon):
    target_feat_4326 = target_feat.geometry.to_shape()

    gdf = gpd.GeoDataFrame(
        {'id': [1], 'geometry': [target_feat_4326]},
        crs='EPSG:4326'
    )
    UTM_CRS = gdf.estimate_utm_crs()

    crs_4326_to_utm = Transformer.from_crs(CRS("EPSG:4326"), UTM_CRS, always_xy=True).transform
    # переводим в метры
    target_feat_utm = transform(crs_4326_to_utm, target_feat_4326)

    neighbor_feat_4326 = neighbor_feat.geometry.to_shape()
    neighbor_feat_utm = transform(crs_4326_to_utm, neighbor_feat_4326)
    shapely.plotting.plot_polygon(neighbor_feat_utm, add_points=False)

    # Находим ближайшие точки
    nearest_pts = nearest_points(target_feat_utm, neighbor_feat_utm)
    # Вычисляем расстояние между ближайшими точками
    distance = int(nearest_pts[0].distance(nearest_pts[1]))  # todo rounding to int - maybe replace with ceil

    direction = get_direction(target_feat_utm, neighbor_feat_utm, search_circle_utm)  # todo replace with sectors

    return distance, direction
