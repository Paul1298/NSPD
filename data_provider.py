from functools import partial

import geopandas as gpd
from pynspd import NspdFeature, Nspd
from pyproj import Transformer, CRS
from shapely import Polygon
from shapely.ops import transform

from geo_processor import get_distance_direction

# class DataProvider: todo

def process_target(target_feat: NspdFeature):
    with Nspd() as nspd:
        target = {
            "feat": target_feat,
            "kad_id": target_feat.properties.options.cad_num,
            "short_id": ':'.join(target_feat.properties.options.cad_num.split(':')[2:]),
            "permission": nspd.tab_permission_type(target_feat),
            "address": target_feat.properties.options.readable_address,
            "4326": target_feat.geometry.to_shape(),
        }


    gdf = gpd.GeoDataFrame(
        {'id': [1], 'geometry': [target["4326"]]},
        crs='EPSG:4326'
    )

    UTM_CRS = gdf.estimate_utm_crs()

    crs_4326_to_utm = Transformer.from_crs(CRS("EPSG:4326"), UTM_CRS, always_xy=True).transform
    crs_4326_to_utm = partial(transform, crs_4326_to_utm)
    crs_utm_to_4326 = Transformer.from_crs(UTM_CRS, CRS("EPSG:4326"), always_xy=True).transform
    crs_utm_to_4326 = partial(transform, crs_utm_to_4326)

    target["utm"] = crs_4326_to_utm(target["4326"])

    return target, crs_4326_to_utm, crs_utm_to_4326


def search_area(target: dict, radius_meters=100) -> Polygon:
    """
    Возвращает в utm
    :param target:
    :param radius_meters:
    :return:
    """

    circle_polygon_utm = target["utm"].centroid.buffer(
        distance=radius_meters,
        quad_segs=32,
    )

    return circle_polygon_utm

def process_neighbors(target, search_circle_utm, nspd_func, crs_4326_to_utm, crs_utm_to_4326):
    neighbor_feats = nspd_func(
        crs_utm_to_4326(search_circle_utm),
        NspdFeature.by_title("Земельные участки из ЕГРН"),
    )

    # cns = [i.properties.options.cad_num for i in neighbor_feats]

    # 5. Обработка найденных участков
    processed_neighbors = []
    for neighbor_feat in neighbor_feats:
        if neighbor_feat.properties.options.cad_num == target["kad_id"]:
            continue  # Пропускаем сам целевой участок

        with Nspd() as nspd:
            neighbor = {
                "feat": neighbor_feat,
                'kad_id': neighbor_feat.properties.options.cad_num,
                "short_id": ':'.join(neighbor_feat.properties.options.cad_num.split(':')[2:]),
                'permission': nspd.tab_permission_type(neighbor_feat),
                "4326": neighbor_feat.geometry.to_shape(),
                "utm": crs_4326_to_utm(neighbor_feat.geometry.to_shape()),
            }

        distance, direction = get_distance_direction(target["utm"], neighbor["utm"], search_circle_utm)
        neighbor["distance"] = distance
        neighbor["direction"] = direction

        processed_neighbors.append(neighbor)
    #
    # pprint(processed_neighbors)
    return processed_neighbors