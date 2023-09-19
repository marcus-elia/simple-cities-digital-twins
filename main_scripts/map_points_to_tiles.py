#!/usr/bin/env python3

# Map point/multi-point geojson files (containing things like trees)
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

def main():
    parser = argparse.ArgumentParser(description="Map geojson points into tiles.")
    parser.add_argument("-i", "--input-filepath", required=True, help="Path to input geojson file")  
    parser.add_argument("-t", "--tile-directory", required=True, help="Name of tile directory")
    parser.add_argument("--city-name", required=True, help="Name of city (sub-directory of output directory that will be created)")
    parser.add_argument("--sw", required=True, help='SW corner formatted as "lat,lon" or "lat, lon"')
    parser.add_argument("--ne", required=True, help='NE corner formatted as "lat,lon" or "lat, lon"')
    parser.add_argument("--offset-x", required=False, type=float, default=0., help='Offset x coord of each point')
    parser.add_argument("--offset-y", required=False, type=float, default=0., help='Offset y coord of each point')

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

    # Start by mapping every tile to an empty polygon
    tile_to_points_map = {}
    for i in range(min_i, max_i + 1):
        for j in range(min_j, max_j + 1):
            tile_to_points_map[(i, j)] = []

    # Collect info for logging
    start_time = time.time()
    num_points = num_features_in_geojson_file(geojson_contents)
    num_completed = 0

    # Now iterate over every polygon in the geojson, intersecting only with relevant tiles
    for geojson_feature in geojson_contents['features']:
        shapely_points = geojson_feature_to_shapely(geojson_feature)
        for shapely_point_lonlat in shapely_points:
            shapely_point_utm = point_lonlat_to_utm(shapely_point_lonlat, offset=(args.offset_x, args.offset_y))

            containing_tile = TileID(shapely_point_utm.x, shapely_point_utm.y, tile_min.zone)
            i = containing_tile.i
            j = containing_tile.j
            if (i, j) in tile_to_points_map:
                tile_to_points_map[(i, j)].append(shapely_point_utm)
            else:
                pass

            # Log the status
            num_completed += 1
            time_elapsed = int(time.time() - start_time)
            print(get_time_estimate_string(time_elapsed, num_completed, num_points))

    # The tile to points map is complete. Write each tile's geojson file.
    print("Storing files in tiles.")
    for i in range(min_i, max_i + 1):
        for j in range(min_j, max_j + 1):
            shapely_points = tile_to_points_map[(i, j)]
            geojson_multipoint = shapely_points_to_geojson(shapely_points)
            features = [geojson.Feature(geometry=geojson_multipoint)]

            # Create the tile's directory, in case it doesn't exist yet
            full_path = os.path.join(city_directory, "%d_%d_%d" % (i, j, tile_min.zone))
            p = subprocess.Popen(['mkdir', full_path], shell=True)
            p.communicate()

            # Dump the geojson object into a string
            dump = geojson.dumps(geojson.FeatureCollection(features=features, crs=geojson_crs))

            # Finally, write to the file
            full_path = os.path.join(full_path, "trees.geojson")
            f = open(full_path, 'w')
            f.write(dump)
            f.close()
    print("Stored %d %s files in %s." % (num_tiles, "trees.geojson", args.tile_directory))

if __name__ == "__main__":
    main()
