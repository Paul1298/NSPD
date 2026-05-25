from pyproj import Transformer, CRS
from shapely import from_wkt
from pynspd import Nspd, NspdFeature
from shapely.ops import transform

contour = from_wkt(
    "Polygon ((37.62381 55.75345, 37.62577 55.75390, 37.62448 55.75278, 37.62381 55.75345))"
)

with Nspd() as nspd:
    feat = nspd.find("86:14:0101002:715")

init = feat.geometry.to_shape()
print("init", feat.geometry.to_shape())
center_point = init.centroid
print(center_point)

crs_4326_to_3857 = Transformer.from_crs(CRS("EPSG:4326"), CRS("EPSG:3857"), always_xy=True).transform
init_3857 = transform(crs_4326_to_3857, init)
print("1, ", init_3857.centroid)

circle_polygon = init_3857.centroid.buffer(distance=1000.0) # quad_segs?
print("2, ", circle_polygon.centroid)

crs_3857_to_4326 = Transformer.from_crs(CRS("EPSG:3857"), CRS("EPSG:4326"), always_xy=True).transform
circle_polygon = transform(crs_3857_to_4326, circle_polygon)
print(circle_polygon.centroid)

# print(circle_polygon)

with Nspd() as nspd:
    feats = nspd.search_in_contour(
        circle_polygon,
        NspdFeature.by_title("Земельные участки из ЕГРН"),
)
cns = [i.properties.options.cad_num for i in feats]
print(len(cns))
print(cns)
#> ["77:01:0001011:8", "77:01:0001011:14", "77:01:0001011:16"]