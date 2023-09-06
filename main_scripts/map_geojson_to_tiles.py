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
from geojson_utils import *
from latlon_to_utm import *
from polygon_utils import *
from tile_id import *

def parse_latlon_string(latlon_string):
    lat,lon = latlon_string.split(',')
    return (float(lat.strip()), float(lon.strip()))

def map_shapely_polygon_into_tile(tile, shapely_polygon_latlon, manual_offset=(0,0)):
    shapely_polygon_utm = poly_latlon_to_utm(shapely_polygon_latlon, offset=manual_offset)
    clipped_poly = tile.polygon().intersection(shapely_polygon_utm)
    if clipped_poly.is_simple:
        return clipped_poly
    else:
        return shapely.Polygon()

def main():
    parser = argparse.ArgumentParser(description="Map geojson polygons into tiles.")
    parser.add_argument("-i", "--input", required=True, help="Path to input geojson file")  
    parser.add_argument("-o", "--output_filename", required=True, help="Name of output file to write in tiles")
    parser.add_argument("-d", "--data_directory", required=True, help="Name of output directory")
    parser.add_argument("-c", "--city_name", required=True, help="Name of city (sub-directory of output directory that will be created)")
    parser.add_argument("--sw", required=True, help='SW corner formatted as "lat,lon" or "lat, lon"')
    parser.add_argument("--ne", required=True, help='NE corner formatted as "lat,lon" or "lat, lon"')
    parser.add_argument("--offset_x", required=False, type=int, default=0, help='Offset x coord of each point')
    parser.add_argument("--offset_y", required=False, type=int, default=0, help='Offset y coord of each point')

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
    city_directory = os.path.join(args.data_directory, args.city_name)

    # Try to create the directory, in case it doesn't exist
    p = subprocess.Popen(['mkdir', args.data_directory], shell=True)
    p.communicate()
    p = subprocess.Popen(['mkdir', city_directory], shell=True)
    p.communicate()

    # Read the contents of the geojson file
    f = open('./shapefiles/lynchburgRoads.geojson')
    geojson_contents = geojson.loads(f.read())
    f.close()

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

if __name__ == "__main__":
    main()
