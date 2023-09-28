#!/usr/bin/env python3

# Map polygon/multi-polygon geojson files (containing roads, sidewalks, etc.)
# into tiles in a specified tile area.

import argparse
import geojson
import os
import shapely
import subprocess
import sys
import time
import utm

sys.path.insert(1, 'C:/Users/mse93/Documents/simple-cities-digital-twins/utility_scripts')
from configuration import *
from general_utils import *
from geojson_utils import *
from latlon_to_utm import *
from polygon_utils import *
from tile_id import *

def map_shapely_polygon_into_tile(tile, shapely_polygon_latlon, manual_offset=(0.,0.)):
    shapely_polygon_utm = poly_latlon_to_utm(shapely_polygon_latlon, offset=manual_offset)
    clipped_poly = tile.polygon().intersection(shapely_polygon_utm)
    if clipped_poly.is_simple:
        return clipped_poly
    else:
        return shapely.Polygon()

def get_overlapping_tiles(shapely_polygon_utm, zone):
    x_min, y_min, x_max, y_max = shapely_polygon_utm.bounds
    min_tile = TileID(x_min, y_min, zone)
    max_tile = TileID(x_max, y_max, zone)
    return (min_tile.i, min_tile.j, max_tile.i, max_tile.j)

def main():
    parser = argparse.ArgumentParser(description="Map geojson polygons into tiles.")
    parser.add_argument("-i", "--input-filepath", required=True, help="Path to input geojson file")  
    parser.add_argument("-t", "--tile-directory", required=True, help="Name of tile directory")
    parser.add_argument("--city-name", required=True, help="Name of city (sub-directory of output directory that will be created)")
    parser.add_argument("--sw", required=True, help='SW corner formatted as "lat,lon" or "lat, lon"')
    parser.add_argument("--ne", required=True, help='NE corner formatted as "lat,lon" or "lat, lon"')
    parser.add_argument("--offset-x", required=False, type=float, default=0., help='Offset x coord of each point')
    parser.add_argument("--offset-y", required=False, type=float, default=0., help='Offset y coord of each point')
    optimization_group = parser.add_mutually_exclusive_group(required=True)
    optimization_group.add_argument("--time", action='store_true', help='Optimize for time')
    optimization_group.add_argument("--memory", action='store_true', help='Optimize for memory usage')
    polygon_category_group = parser.add_mutually_exclusive_group(required=True)
    polygon_category_group.add_argument("--road", action='store_true', help='The geojson polygons are roads')
    polygon_category_group.add_argument("--sidewalk", action='store_true', help='The geojson polygons are sidewalks')
    polygon_category_group.add_argument("--parking", action='store_true', help='The geojson polygons are parking lots')
    polygon_category_group.add_argument("--water", action='store_true', help='The geojson polygons are water')
    polygon_category_group.add_argument("--beach", action='store_true', help='The geojson polygons are beaches')
    polygon_category_group.add_argument("--downtown", action='store_true', help='The geojson polygons are where downtown is')
    polygon_category_group.add_argument("--park", action='store_true', help='The geojson polygons are parks')
    polygon_category_group.add_argument("--baseball", action='store_true', help='The geojson polygons are baseball fields')
    polygon_category_group.add_argument("--track", action='store_true', help='The geojson polygons are tracks')
    polygon_category_group.add_argument("--pool", action='store_true', help='The geojson polygons are swimming pools')
    polygon_category_group.add_argument("--forest", action='store_true', help='The geojson polygons are forests (natural=wood in osm)')
    polygon_category_group.add_argument("--runway", action='store_true', help='The geojson polygons are airport runways')

    args = parser.parse_args()

    # Get the min/max tile IDs from the lat/lon
    lat1, lon1 = parse_latlon_string(args.sw)
    lat2, lon2 = parse_latlon_string(args.ne)
    tile_min = TileID(lat1, lon1)
    tile_max = TileID(lat2, lon2)
    if tile_min.zone != tile_max.zone:
        print("Crossing from UTM zone %d to %d. Quitting." % (tile_min.zone, tile_max.zone))
        return
    min_i = tile_min.i
    min_j = tile_min.j
    max_i = tile_max.i
    max_j = tile_max.j
    num_tiles = (max_i - min_i + 1) * (max_j - min_j + 1)
    print("You have specified %d tile%s." % (num_tiles,  "s" if num_tiles > 1 else ""))

    # Set things based on the category of polygons specified
    # TODO somehow this should be done automatically
    if args.road:
        output_filename = ROAD_FILENAME
    elif args.sidewalk:
        output_filename = SIDEWALK_FILENAME
    elif args.parking:
        output_filename = PARKING_FILENAME
    elif args.water:
        output_filename = WATER_FILENAME
    elif args.beach:
        output_filename = BEACH_FILENAME
    elif args.downtown:
        output_filename = DOWNTOWN_FILENAME
    elif args.park:
        output_filename = PARK_FILENAME
    elif args.baseball:
        output_filename = BASEBALL_FILENAME
    elif args.track:
        output_filename = TRACK_FILENAME
    elif args.pool:
        output_filename = POOL_FILENAME
    elif args.forest:
        output_filename = FOREST_FILENAME
    elif args.runway:
        output_filename = RUNWAY_FILENAME

    # Set the variables that will be used in every tile
    geojson_crs = { "type": "name", "properties": { "name": "urn:ogc:def:crs:EPSG::322%d" % (tile_min.zone)}}
    city_directory = os.path.join(args.tile_directory, args.city_name)

    # Try to create the directory, in case it doesn't exist
    p = subprocess.Popen(['mkdir', args.tile_directory], shell=True)
    p.communicate()
    p = subprocess.Popen(['mkdir', city_directory], shell=True)
    p.communicate()

    geojson.geometry.DEFAULT_PRECISION = 10

    # Read the contents of the geojson file
    f = open(args.input_filepath)
    geojson_contents = geojson.loads(f.read())
    f.close()

    # When you are concerned about running out of RAM, we do the slow naive thing. For each tile, intersect
    # every polygon with it and then immediately write to that file. Nothing gets stored.
    if args.memory:
        # Intersect every geometry from the geojson with every tile
        num_completed = 0
        start_time = time.time()
        for i in range(min_i, max_i + 1):
            for j in range(min_j, max_j + 1):
                current_tile = TileID.tile_indices_to_object(i, j, tile_min.zone)
                tile_union = shapely.Polygon()
                for geojson_multipolygon in geojson_contents['features']:
                    shapely_polygons = geojson_multipoly_to_shapely(geojson_multipolygon.geometry.coordinates)
                    for shapely_polygon_latlon in shapely_polygons:
                        clipped_polygon = map_shapely_polygon_into_tile(current_tile, shapely_polygon_latlon, manual_offset=(args.offset_x, args.offset_y))
                        tile_union = tile_union.union(clipped_polygon)
                # Once every polygon has been intersected with the tile, overwrite the tile's geojson file

                # Convert the multipolygon from shapely to geojson
                if type(tile_union) == shapely.geometry.multipolygon.MultiPolygon:
                    geojson_tile_union = shapely_multipolygon_to_geojson(tile_union)
                elif type(tile_union) == shapely.geometry.polygon.Polygon:
                    geojson_tile_union = shapely_polygon_to_geojson(tile_union)
                features = [geojson.Feature(geometry=geojson_tile_union)]

                # Create the tile's directory, in case it doesn't exist yet
                full_path = os.path.join(city_directory, "%d_%d_%d" % (i, j, tile_min.zone))
                p = subprocess.Popen(['mkdir', full_path], shell=True)
                p.communicate()

                # Dump the geojson object into a string
                dump = geojson.dumps(geojson.FeatureCollection(features=features, crs=geojson_crs))

                # Finally, write to the file
                full_path = os.path.join(full_path, args.output_filename)
                f = open(full_path, 'w')
                f.write(dump)
                f.close()

                # Log the status
                num_completed += 1
                percent_complete = float(num_completed) / float(num_tiles) * 100
                time_elapsed = int(time.time() - start_time)
                time_remaining = int(time_elapsed * (100 - percent_complete) / percent_complete)
                if time_elapsed < 120:
                    time_string = "%d seconds, %d seconds remaining" % (time_elapsed, time_remaining)
                else:
                    time_elapsed = int(time_elapsed / 60)
                    time_remaining = int(time_remaining / 60)
                    if time_elapsed < 120:
                        time_string = "%d minutes, %d minutes remaining" % (time_elapsed, time_remaining)
                    else:
                        time_elapsed = int(time_elapsed / 60)
                        time_remaining = int(time_remaining / 60)
                        time_string = "%d hours, %d hours remaining" % (time_elapsed, time_remaining)
                print("Completed %d/%d tiles (%.1f percent) in %s" % (num_completed, num_tiles, percent_complete, time_string))
        print("Stored %d %s files in %s." % (num_tiles, args.output_filename, full_path))

    # If we have plenty of RAM and want things to run faster, we only intersect each polygon with the
    # tiles that actually overlap with it. This requires storing a map from each tile to its polygon.
    elif args.time:
        # Start by mapping every tile to an empty polygon
        tile_to_polygon_map = {}
        print("Initializing an empty polygon for all %d tiles." % (num_tiles))
        for i in range(min_i, max_i + 1):
            for j in range(min_j, max_j + 1):
                tile_to_polygon_map[(i, j)] = shapely.Polygon()

        # Collect info for logging
        start_time = time.time()
        num_polygons = num_features_in_geojson_file(geojson_contents)
        num_completed = 0

        # Now iterate over every polygon in the geojson, intersecting only with relevant tiles
        for geojson_feature in geojson_contents['features']:
            shapely_polygons = geojson_feature_to_shapely(geojson_feature)
            for shapely_polygon_lonlat in shapely_polygons:
                shapely_polygon_utm = poly_lonlat_to_utm(shapely_polygon_lonlat, offset=(args.offset_x, args.offset_y))

                # With the polygon in UTM, determine which tiles overlap with its bbox.
                # Also, make sure it doesn't go beyond the user-specified tile area.
                bbox_i_min, bbox_j_min, bbox_i_max, bbox_j_max = get_overlapping_tiles(shapely_polygon_utm, tile_min.zone)
                bbox_i_min = max(bbox_i_min, min_i)
                bbox_j_min = max(bbox_j_min, min_j)
                bbox_i_max = min(bbox_i_max, max_i)
                bbox_j_max = min(bbox_j_max, max_j)

                # Intersect it with each of those tiles
                for i in range(bbox_i_min, bbox_i_max + 1):
                    for j in range(bbox_j_min, bbox_j_max + 1):
                        current_tile = TileID.tile_indices_to_object(i, j, tile_min.zone)
                        try:
                            clipped_poly = current_tile.polygon().intersection(shapely_polygon_utm)
                        except shapely.errors.GEOSException:
                            print("Error intersecting polygon with tile. Skipping")
                            continue

                        tile_to_polygon_map[(i, j)] = tile_to_polygon_map[(i, j)].union(clipped_poly)

                # Log the status
                num_completed += 1
                time_elapsed = int(time.time() - start_time)
                print(get_time_estimate_string(time_elapsed, num_completed, num_polygons))

        # The tile to polygon map is complete. Write each tile's geojson file.
        print("Storing files in tiles.")
        for i in range(min_i, max_i + 1):
            for j in range(min_j, max_j + 1):
                tile_union = tile_to_polygon_map[(i, j)]
                # If the tile union is somehow a "geometry collection", make it not that
                if type(tile_union) == shapely.geometry.collection.GeometryCollection:
                    polygon_union = shapely.Polygon()
                    for geom in tile_union.geoms:
                        if type(geom) == shapely.geometry.polygon.Polygon:
                            polygon_union = polygon_union.union(geom)
                        else:
                            pass
                    # Now it should be either a Polygon or MultiPolygon
                    tile_union = polygon_union

                # Convert the multipolygon from shapely to geojson
                if type(tile_union) == shapely.geometry.multipolygon.MultiPolygon:
                    geojson_tile_union = shapely_multipolygon_to_geojson(tile_union)
                elif type(tile_union) == shapely.geometry.polygon.Polygon:
                    geojson_tile_union = shapely_polygon_to_geojson(tile_union)
                else:
                    print("Unknown shapely type %s" % (type(tile_union)))
                features = [geojson.Feature(geometry=geojson_tile_union)]

                # Create the tile's directory, in case it doesn't exist yet
                full_path = os.path.join(city_directory, "%d_%d_%d" % (i, j, tile_min.zone))
                p = subprocess.Popen(['mkdir', full_path], shell=True)
                p.communicate()

                # Dump the geojson object into a string
                dump = geojson.dumps(geojson.FeatureCollection(features=features, crs=geojson_crs))

                # Finally, write to the file
                full_path = os.path.join(full_path, output_filename)
                f = open(full_path, 'w')
                f.write(dump)
                f.close()
        print("Stored %d %s files in %s." % (num_tiles, output_filename, args.tile_directory))

if __name__ == "__main__":
    main()
