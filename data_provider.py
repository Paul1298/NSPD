from functools import partial

import geopandas as gpd
from pynspd import NspdFeature, Nspd
from pyproj import Transformer, CRS
from shapely import Polygon
from shapely.ops import transform

from geo_processor import get_distance_direction


def process_target(target_feat: NspdFeature, coordinates):
    with Nspd() as nspd:
        target = {
            "feat": target_feat,
            "kad_id": target_feat.properties.options.cad_num,
            "short_id": ':'.join(target_feat.properties.options.cad_num.split(':')[2:]),
            "permission": nspd.tab_permission_type(target_feat),
            "address": target_feat.properties.options.readable_address,
            "4326": target_feat.geometry.to_shape(),
        }

    if coordinates:
        target["4326"] = Polygon(coordinates)

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
    """Возвращает круг поиска в UTM."""
    return target["utm"].buffer(distance=radius_meters)


def sort_neighbors_by_direction(neighbors_list: list[dict]) -> list[dict]:
    all_directions = [
        "с северной стороны", "с северо-восточной стороны", "с восточной стороны",
        "с юго-восточной стороны", "с южной стороны", "с юго-западной стороны",
        "с западной стороны", "с северо-западной стороны"
    ]
    direction_map = {direction: i for i, direction in enumerate(all_directions)}

    return sorted(
        neighbors_list,
        key=lambda neighbor: (
            direction_map.get(neighbor['direction'].split(', ')[0], len(all_directions)),
            len(neighbor['direction'].split(', ')),
            neighbor['distance']
        )
    )


def process_neighbors(
        target,
        search_circle_utm,
        nspd_func,
        crs_4326_to_utm,
        crs_utm_to_4326,
        area_limit=2,
        min_intersection_percent=5,
):
    neighbor_feats = nspd_func(
        crs_utm_to_4326(search_circle_utm),
        NspdFeature.by_title("Земельные участки из ЕГРН"),
    )

    if not neighbor_feats:
        return []

    processed_neighbors = []
    for neighbor_feat in neighbor_feats:
        if neighbor_feat.properties.options.cad_num == target["kad_id"]:
            continue

        if (
                neighbor_feat.properties.options.specified_area and
                neighbor_feat.properties.options.specified_area < area_limit
        ):
            continue

        neighbor = {
            "feat": neighbor_feat,
            'kad_id': neighbor_feat.properties.options.cad_num,
            "short_id": ':'.join(neighbor_feat.properties.options.cad_num.split(':')[2:]),
            # 'permission': nspd.tab_permission_type(neighbor_feat),
            "4326": neighbor_feat.geometry.to_shape(),
            "utm": crs_4326_to_utm(neighbor_feat.geometry.to_shape()),
        }

        distance, direction = get_distance_direction(
            target["utm"],
            neighbor["utm"],
            search_circle_utm,
            min_intersection_percent,
        )
        neighbor["distance"] = distance
        neighbor["direction"] = direction

        processed_neighbors.append(neighbor)

    return sort_neighbors_by_direction(processed_neighbors)
