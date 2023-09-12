#!/usr/bin/env python3

# Utility functions for geojson files.
# All geojsons must be in the EPSG:4326 (WGS 84) projection

import geojson
import shapely
import utm

def geojson_poly_to_shapely(geojson_polygon):
    # Special case for empty polygon
    if len(geojson_polygon) == 0:
        return shapely.Polygon()

    # Single polygon with no holes
    if type(geojson_polygon[0][0]) != list:
        outer_boundary = []
        for x,y in geojson_polygon:
            outer_boundary.append((x, y))
        return shapely.Polygon(outer_boundary)
    
    # A polygon that does have holes
    outer_boundary = []
    holes = []
    for x,y in geojson_polygon[0]:
        outer_boundary.append((x, y))
    for geojson_hole in geojson_polygon[1:]:
        hole = []
        for x,y in geojson_hole:
            hole.append((x, y))
        holes.append(hole)

    return shapely.Polygon(outer_boundary, holes)

def geojson_multipoly_to_shapely(geojson_multipoly):
    polys = []
    for geojson_poly in geojson_multipoly:
        polys.append(geojson_poly_to_shapely(geojson_poly))

    return polys

def num_polygons_in_geojson_file(geojson_contents):
    return len(geojson_contents['features'])

def shapely_polygon_to_geojson(shapely_poly):
    return geojson.Polygon([list(shapely_poly.exterior.coords)] + [list(hole.coords) for hole in shapely_poly.interiors])

def shapely_multipolygon_to_geojson(shapely_multipoly):
    return geojson.MultiPolygon([shapely_polygon_to_geojson(shapely_poly) for shapely_poly in shapely_multipoly.geoms])
