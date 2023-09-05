#!/usr/bin/env python3

# Utility functions for geojson files.
# All geojsons must be in the EPSG:4326 (WGS 84) projection

import geojson
import shapely
import utm

def geojson_poly_to_shapely(geojson_polygon):
    outer_boundary = []
    holes = []
    for lon,lat in geojson_polygon[0]:
        outer_boundary.append((lat, lon))
    for geojson_hole in geojson_polygon[1:]:
        hole = []
        for lon,lat in geojson_hole:
            hole.append((lat, lon))
        holes.append(hole)

    return shapely.Polygon(outer_boundary, holes)

def geojson_multipoly_to_shapely(geojson_multipoly):
    polys = []
    for geojson_poly in geojson_multipoly:
        polys.append(geojson_poly_to_shapely(geojson_poly))

    return polys

def shapely_polygon_to_geojson(shapely_poly):
    return geojson.Polygon([list(shapely_poly.exterior.coords)] + [list(hole.coords) for hole in shapely_poly.interiors])

def shapely_multipolygon_to_geojson(shapely_multipoly):
    return geojson.MultiPolygon([shapely_polygon_to_geojson(shapely_poly) for shapely_poly in shapely_multipoly.geoms])
