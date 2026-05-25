import geopandas as gpd
from pynspd import NspdFeature
from pyproj import Transformer, CRS
from shapely import Polygon
from shapely.ops import transform


def search_area(target_feat: NspdFeature, radius_meters=100) -> Polygon:
    """
    Возвращает в 4326
    :param target_feat:
    :param radius_meters:
    :return:
    """
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

    circle_polygon = target_feat_utm.centroid.buffer(distance=radius_meters)  # todo quad_segs для увеличения точности?
    # todo добавить отрисовку полигона

    crs_utm_to_4326 = Transformer.from_crs(UTM_CRS, CRS("EPSG:4326"), always_xy=True).transform
    circle_polygon = transform(crs_utm_to_4326, circle_polygon)
    return circle_polygon
