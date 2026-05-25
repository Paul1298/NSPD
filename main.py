# Библиотеки
import math
from pprint import pprint

import geopandas as gpd
import shapely
from pynspd import Nspd, NspdFeature
from shapely import Polygon
from shapely.wkt import loads
from shapely.geometry import Point
import pynspd  # Библиотека для работы с кадастром
from pyproj import Transformer, CRS
from shapely.ops import transform, nearest_points
import shapely.plotting
import matplotlib.pyplot as plt
import numpy as np


def search_area(target_feat: NspdFeature, radius_meters=100) -> Polygon:
    target_feat_4326 = target_feat.geometry.to_shape()

    gdf = gpd.GeoDataFrame(
        {'id': [1], 'geometry': [target_feat_4326]},
        crs='EPSG:4326'
    )
    UTM_CRS = gdf.estimate_utm_crs()


    # target_center = target_feat_4326.centroid
    crs_4326_to_utm = Transformer.from_crs(CRS("EPSG:4326"), UTM_CRS, always_xy=True).transform
    # переводим в метры
    target_feat_utm = transform(crs_4326_to_utm, target_feat_4326)

    circle_polygon = target_feat_utm.centroid.buffer(distance=radius_meters)  #todo quad_segs для увеличения точности?
    #todo добавить отрисовку полигона

    crs_utm_to_4326 = Transformer.from_crs(UTM_CRS, CRS("EPSG:4326"), always_xy=True).transform
    circle_polygon = transform(crs_utm_to_4326, circle_polygon)
    return circle_polygon


def get_direction(point1, point2):
    """
    Определяет направление от point1 к point2

    Args:
        point1 (Point): Начальная точка
        point2 (Point): Конечная точка

    Returns:
        str: Направление света
    """
    # Вычисляем угол между точками
    dx = point2.x - point1.x
    dy = point2.y - point1.y

    # Вычисляем угол в градусах
    angle = math.degrees(math.atan2(dy, dx))

    # Нормализуем угол от 0 до 360
    if angle < 0:
        angle += 360

    # Определяем направление
    directions = [
        ("с северной стороны", 337.5, 22.5),
        ("с северо-восточной стороны", 22.5, 67.5),
        ("с восточной стороны", 67.5, 112.5),
        ("с юго-восточной стороны", 112.5, 157.5),
        ("с южной стороны", 157.5, 202.5),
        ("с юго-западной стороны", 202.5, 247.5),
        ("с западной стороны", 247.5, 292.5),
        ("с северо-западной стороны", 292.5, 337.5)
    ]

    for direction, start, end in directions:
        if start <= angle < end:
            return direction

    return "с северной стороны"  # На случай if angle == 360

def get_distance_direction(target_feat: NspdFeature, neighbor_feat: NspdFeature):
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
    distance = int(nearest_pts[0].distance(nearest_pts[1])) #todo rounding to int - maybe replace with ceil

    direction = get_direction(nearest_pts[0], nearest_pts[1]) #todo replace with sectors


    return distance, direction


def get_sector(point1, point2):
    """
    Определяет сектор между двумя точками

    Args:
        point1 (Point): Начальная точка
        point2 (Point): Конечная точка

    Returns:
        str: Сектор со стороной света
    """
    # Вычисляем угол между точками
    dx = point2.x - point1.x
    dy = point2.y - point1.y

    # Вычисляем угол в градусах
    angle = math.degrees(math.atan2(dy, dx))

    # Нормализуем угол от 0 до 360
    if angle < 0:
        angle += 360

    # Определяем сектор
    sectors = [
        (0, 45, "СВ"),
        (45, 90, "В"),
        (90, 135, "ЮВ"),
        (135, 180, "Ю"),
        (180, 225, "ЮЗ"),
        (225, 270, "З"),
        (270, 315, "СЗ"),
        (315, 360, "С")
    ]

    for start, end, sector in sectors:
        if start <= angle < end:
            return sector

    return "С"  # На случай если угол == 360


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
        ("с северной стороны", 337.5, 22.5),
        ("с северо-восточной стороны", 22.5, 67.5),
        ("с восточной стороны", 67.5, 112.5),
        ("с юго-восточной стороны", 112.5, 157.5),
        ("с южной стороны", 157.5, 202.5),
        ("с юго-западной стороны", 202.5, 247.5),
        ("с западной стороны", 247.5, 292.5),
        ("с северо-западной стороны", 292.5, 337.5)
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
        ax.fill(x, y, color=color, alpha=0.2)


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

        dist, direction = get_distance_direction(target_feat, neighbor_feat)

        neighbor_feat_utm = transform(crs_4326_to_utm, neighbor_feat.geometry.to_shape())

        color = color_map.get(direction, 'gray')

        plt.fill(*neighbor_feat_utm.exterior.xy, color=color, alpha=0.5,
                 label=f'{neighbor_feat.properties.options.cad_num} ({direction})')
        # plt.plot(*neighbor_feat_utm.exterior.xy, color=color, marker='o', markersize=2, linestyle='-')

    plt.axis('equal')  # Сохраняем пропорции
    target_center = target_feat_utm.centroid
    # Устанавливаем границы области отображения
    coef = 1.5
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
    plt.tight_layout()
    plt.show()

def main(kad_id, radius_meters=100):
    # 1. Подключение к NSPD
    with Nspd() as nspd:  # Инициализация клиента

        # 2. Получение данных о целевом участке
        target_feat = nspd.find(kad_id)
        # target_geometry = loads(target_feat.get_geometry())
        target_permission = nspd.tab_permission_type(target_feat)
        print(target_permission)

        # 3. Создание области поиска
        search_circle = search_area(target_feat, radius_meters)

        # 4. Поиск соседних участков
        neighbor_feats = nspd.search_in_contour(
            search_circle,
            NspdFeature.by_title("Земельные участки из ЕГРН"),
        )
        cns = [i.properties.options.cad_num for i in neighbor_feats]

        print(f"Соседи в радиусе {radius_meters}м. : {len(cns)}\n",  '\n'.join(cns))
        # print(cns)

        # neighbor_feats = [
        #     feat for feat in neighbor_feats
        #     if feat.properties.options.cad_num != '50:58:0000000:12'
        # ]

        # Добавляем визуализацию
        plot_features(target_feat, neighbor_feats, search_circle, radius_meters)
        return

        # 5. Обработка найденных участков
        processed_neighbors = []
        for neighbor_feat in neighbor_feats:
            if neighbor_feat.properties.options.cad_num == kad_id:
                continue  # Пропускаем сам целевой участок

            # Получаем полную информацию о соседе
            # neighbor_details = nspd.find(neighbor_feat.kad_num)
            dist, direction = get_distance_direction(target_feat, neighbor_feat)

            # Здесь будет логика определения направления и расстояния
            # Пока что заглушка
            processed_neighbors.append({
                'kad_id': neighbor_feat.properties.options.cad_num,
                'permission': nspd.tab_permission_type(neighbor_feat),
                'direction': direction,
                'distance': dist
            })


        pprint(processed_neighbors)

        return

        # 6. Генерация отчета
        # generate_report(target_feat, processed_neighbors)


def generate_report(target_feat, neighbors):
    # Формирование текстового отчета
    report = f"Отчет для участка {target_feat.kad_num}\n"
    report += f"Разрешенное использование: {target_feat.tab_permission_type()}\n\n"

    # Группировка и сортировка соседей по направлениям
    neighbors_by_direction = {}
    for neighbor in neighbors:
        if neighbor['direction'] not in neighbors_by_direction:
            neighbors_by_direction[neighbor['direction']] = []
        neighbors_by_direction[neighbor['direction']].append(neighbor)

    # Вывод для каждого направления
    for direction, direction_neighbors in neighbors_by_direction.items():
        report += f"{direction}:\n"
        for neighbor in direction_neighbors:
            report += (
                f"- на расстоянии {neighbor['distance']} м "
                f"расположен ЗУ с КН {neighbor['kad_id']}, "
                f"разрешенное использование – {neighbor['permission']}\n"
            )

    # Сохранение в файл
    with open('report.txt', 'w', encoding='utf-8') as f:
        f.write(report)

    print("Отчет сохранен в report.txt")


if __name__ == "__main__":
    # Пример использования
    main('50:58:0020204:50', radius_meters=175)