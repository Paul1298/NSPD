import math

import shapely
from shapely.geometry import Polygon


def get_sectors(search_circle_utm: Polygon) -> dict[str, Polygon]:
    """
    Создает словарь с полигонами-секторами, вырезанными из круга поиска.

    Args:
        search_circle_utm (Polygon): Круг поиска в UTM (созданный через buffer).

    Returns:
        dict[str, Polygon]: Словарь, где ключ - название направления,
                            а значение - полигон соответствующего сектора.
    """
    # directions = [
    #     ("с восточной стороны", 337.5, 22.5),
    #     ("с северо-восточной стороны", 22.5, 67.5),
    #     ("с северной стороны", 67.5, 112.5),
    #     ("с северо-западной стороны", 112.5, 157.5),
    #     ("с западной стороны", 157.5, 202.5),
    #     ("с юго-западной стороны", 202.5, 247.5),
    #     ("с южной стороны", 247.5, 292.5),
    #     ("с юго-восточной стороны", 292.5, 337.5)
    # ]
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

    sectors = {}
    search_center = search_circle_utm.centroid
    # Создаем "нож", который заведомо больше круга
    large_radius = search_circle_utm.exterior.distance(search_center) * 2

    for direction_name, start_deg, end_deg in directions:
        start_rad = math.radians(start_deg)
        end_rad = math.radians(end_deg)

        # Конечные точки лучей "ножа"
        p1 = (search_center.x + large_radius * math.cos(start_rad),
              search_center.y + large_radius * math.sin(start_rad))
        p2 = (search_center.x + large_radius * math.cos(end_rad),
              search_center.y + large_radius * math.sin(end_rad))

        cutter_wedge = Polygon([(search_center.x, search_center.y), p1, p2])

        # Обработка сектора, пересекающего 0/360 градусов ("Восток")
        if start_deg > end_deg:
            p_360 = (search_center.x + large_radius, search_center.y)
            cutter1 = Polygon([(search_center.x, search_center.y), p1, p_360])
            cutter2 = Polygon([(search_center.x, search_center.y), p_360, p2])
            cutter_wedge = cutter1.union(cutter2)

        # Вырезаем сектор и сохраняем в словарь
        sector_poly = search_circle_utm.intersection(cutter_wedge)
        sectors[direction_name] = sector_poly

    return sectors


def get_direction(neighbor_poly: Polygon, sectors: dict[str, Polygon]) -> str:
    """
    Определяет, с какими из готовых секторов пересекается полигон соседа.

    Args:
        neighbor_poly (Polygon): Полигон соседа.
        sectors (dict[str, Polygon]): Словарь с полигонами секторов.

    Returns:
        str: Строка с перечислением направлений через запятую.
    """
    detected_directions = []
    for direction_name, sector_poly in sectors.items():
        if sector_poly.intersects(neighbor_poly):
            detected_directions.append(direction_name)

    return ', '.join(detected_directions) if detected_directions else "не опознан"


def get_distance_direction(target_feat_utm, neighbor_feat_utm, search_circle_utm: Polygon):
    distance = int(
        shapely.distance(target_feat_utm, neighbor_feat_utm))  # todo rounding to int - maybe replace with ceil
    direction = get_direction(neighbor_feat_utm, get_sectors(search_circle_utm))

    return distance, direction
