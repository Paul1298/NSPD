import math

from pynspd import Nspd
from shapely.ops import transform, nearest_points
from pyproj import CRS, Transformer, Geod
import matplotlib.pyplot as plt
import shapely.plotting
import geopandas as gpd


def get_utm_crs(gdf):
    """
    Автоматически определяет подходящую UTM CRS для GeoDataFrame.
    """
    # Убедимся, что исходная CRS - географическая
    if gdf.crs.is_geographic:
        # Находим центральную точку всех геометрий в датафрейме
        unified_geometry = gdf.union_all()  # Вызываем метод со скобками
        central_point = unified_geometry.centroid
        central_lon = central_point.x
        central_lat = central_point.y

        # Вычисляем номер UTM-зоны
        utm_zone = math.floor((central_lon + 180) / 6) + 1

        # Определяем полушарие и формируем EPSG-код
        if central_lat >= 0:
            # Северное полушарие
            epsg_code = 32600 + utm_zone
        else:
            # Южное полушарие
            epsg_code = 32700 + utm_zone

        return f'EPSG:{epsg_code}'
    else:
        # Если данные уже в проекционной CRS, возвращаем ее же
        print("Данные уже в проекционной CRS.")
        return gdf.crs


with Nspd() as nspd:
    g1_4326 = nspd.find('47:01:1014001:14').geometry.to_shape()
    g2_4326 = nspd.find('47:01:1014001:4873').geometry.to_shape()

    # print(nspd.tab_permission_type(nspd.find('86:14:0000000:1860')))
    # g2_4326 = nspd.find('86:14:0101003:223').geometry.to_shape()

# print(g1_4326)
gdf = gpd.GeoDataFrame(
    {'id': [1, 2], 'geometry': [g1_4326, g2_4326]},
    crs='EPSG:4326'
)

# print(g2_4326)
# plt.plot(*g1_4326.exterior.xy)
# plt.plot(*g2_4326.exterior.xy)

shapely.plotting.plot_polygon(g1_4326)
shapely.plotting.plot_polygon(g2_4326)
plt.show()


# dist = g1_4326.distance(g2_4326)
# print(dist*1000)
# переводим в подходящую для измерений систему координат
crs_4326_to_3857 = Transformer.from_crs(CRS("EPSG:4326"), gdf.estimate_utm_crs(), always_xy=True).transform
g1_3857 = transform(crs_4326_to_3857, g1_4326)
g2_3857 = transform(crs_4326_to_3857, g2_4326)
# print(g1_3857)
# print(g2_3857)
# shapely.plotting.plot_polygon(g1_3857)
# shapely.plotting.plot_polygon(g2_3857)
# plt.show()

dist = shapely.distance(g1_3857,g2_3857)
print(shapely.distance(g1_4326,g2_4326))
print(dist)


p1, p2 = nearest_points(g1_4326, g2_4326)

print(f"Ближайшая точка на полигоне 1: {p1.wkt}")
print(f"Ближайшая точка на полигоне 2: {p2.wkt}")

# 2. Готовим объект для геодезических расчетов на эллипсоиде WGS84
geod = Geod(ellps='WGS84')

# 3. Рассчитываем расстояние между двумя точками
# geod.inv возвращает азимут, обратный азимут и расстояние в метрах
azimuth1, azimuth2, distance_meters = geod.inv(
    lons1=p1.x, lats1=p1.y,
    lons2=p2.x, lats2=p2.y
)

print(f"\nРасстояние между полигонами: {distance_meters:.2f} метров")




# --- Важная часть: перепроецирование ---

# 3. Найдем подходящую UTM-зону для наших данных.
# Для Москвы (долгота ~37.6) это зона 37N.
# EPSG-код для UTM Zone 37N - это 'EPSG:32637'.
# Если вы не знаете зону, можно найти ее по долготе или использовать готовые функции.
# Пример автоматического поиска:
# centroid_lon = gdf.unary_union.centroid.x
# utm_zone = int(1 + (centroid_lon + 180) / 6)
# utm_crs = f'EPSG:{32600 + utm_zone}' # Для северного полушария
# print(f"Автоматически определенная UTM CRS: {utm_crs}")

# Используем заранее известную CRS для Москвы
# utm_crs = 'EPSG:32637'
utm_crs = get_utm_crs(gdf)
# print("utm_crs", utm_crs)

# 4. Перепроецируем наш GeoDataFrame в UTM
gdf_projected = gdf.to_crs(utm_crs)

# 5. Теперь полигоны находятся в системе координат, где единицы - метры.
# Можно безопасно считать расстояние.
poly1_proj = gdf_projected.geometry[0]
poly2_proj = gdf_projected.geometry[1]

nearest_pts = nearest_points(poly1_proj, poly2_proj)

# Вычисляем расстояние между ближайшими точками
distance = nearest_pts[0].distance(nearest_pts[1])


distance_meters = poly1_proj.distance(poly2_proj)

# print(f"Полигоны:\n{gdf.geometry.to_wkt()}\n")
print(gdf.estimate_utm_crs())
print(f"Система координат UTM для этого региона: {utm_crs}")
print(f"1способ.Расстояние между полигонами: {distance_meters:.2f} метров")
