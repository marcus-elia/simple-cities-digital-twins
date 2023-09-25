#!/usr/bin/env python3

# Create tile textures and write them to SVGs/JPGs.

import argparse
import geojson
import os
import shapely
import subprocess
import sys
import time

sys.path.insert(1, 'C:/Users/mse93/Documents/simple-cities-digital-twins/utility_scripts')
from configuration import *
from general_utils import *
from geojson_utils import *
from latlon_to_utm import *
from svg_utils import *
from tile_id import *

def main():
    parser = argparse.ArgumentParser(description="Create tile texture SVGs and JPGs for tiles.")
    parser.add_argument("--config-file", required=True, help="Path to the configuration file")
    parser.add_argument("-t", "--tile-directory", required=True, help="Name of tile directory")
    parser.add_argument("--city-name", required=True, help="Name of city (sub-directory of output directory that will be created)")
    parser.add_argument("--sw", required=True, help='SW corner formatted as "lat,lon" or "lat, lon"')
    parser.add_argument("--ne", required=True, help='NE corner formatted as "lat,lon" or "lat, lon"')

    args = parser.parse_args()

    config = Configuration(args.config_file)

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

    city_directory = os.path.join(args.tile_directory, args.city_name)

    # Iterate over every tile, creating an SVG manually and using ImageMagick to convert to JPG
    start_time = time.time()
    num_complete = 0
    for i in range(min_i, max_i + 1):
        for j in range(min_j, max_j + 1):
            current_tile = TileID.tile_indices_to_object(i, j, tile_min.zone)
            sw_x, sw_y = current_tile.sw_corner()
            full_path = os.path.join(city_directory, "%d_%d_%d" % (i, j, tile_min.zone))

            # Read the contents of the road geojson file
            shapely_road_polygons = read_geojson_file_to_shapely_list(full_path, ROAD_FILENAME)

            # Read the contents of the sidewalk geojson file
            shapely_sidewalk_polygons = read_geojson_file_to_shapely_list(full_path, SIDEWALK_FILENAME)

            # Read the contents of the parking lot geojson file
            shapely_parking_polygons = read_geojson_file_to_shapely_list(full_path, PARKING_FILENAME)

            # Read the contents of the water geojson file
            shapely_water_polygons = read_geojson_file_to_shapely_list(full_path, WATER_FILENAME)

            # Read the contents of the downtown geojson file
            shapely_downtown_polygons = read_geojson_file_to_shapely_list(full_path, DOWNTOWN_FILENAME)

            # Read the contents of the park geojson file
            shapely_park_polygons = read_geojson_file_to_shapely_list(full_path, PARK_FILENAME)

            # Read the contents of the beach geojson file
            shapely_beach_polygons = read_geojson_file_to_shapely_list(full_path, BEACH_FILENAME)

            # Read the contents of the baseball field geojson file
            shapely_baseball_polygons = read_geojson_file_to_shapely_list(full_path, BASEBALL_FILENAME)

            # Read the contents of the track geojson file
            shapely_track_polygons = read_geojson_file_to_shapely_list(full_path, TRACK_FILENAME)

            # Read the contents of the swimming pool geojson file
            shapely_pool_polygons = read_geojson_file_to_shapely_list(full_path, POOL_FILENAME)

            # Read the contents of the runway geojson file
            shapely_runway_polygons = read_geojson_file_to_shapely_list(full_path, RUNWAY_FILENAME)

            # Write a SVG to the tile
            color_polygons_pairs = [(config.at["GRASS_COLOR"], [current_tile.polygon()]),\
                    (config.at["DOWNTOWN_COLOR"], shapely_downtown_polygons),\
                    (config.at["GRASS_COLOR"], shapely_park_polygons),\
                    (config.at["BEACH_COLOR"], shapely_beach_polygons),\
                    (config.at["WATER_COLOR"], shapely_water_polygons),\
                    (config.at["ROAD_COLOR"], shapely_road_polygons),\
                    (config.at["ROAD_COLOR"], shapely_runway_polygons),\
                    (config.at["PARKING_COLOR"], shapely_parking_polygons),\
                    (config.at["SIDEWALK_COLOR"], shapely_sidewalk_polygons),\
                    (config.at["TRACK_COLOR"], shapely_track_polygons),\
                    (config.at["POOL_COLOR"], shapely_pool_polygons),\
                    (config.at["BASEBALL_COLOR"], shapely_baseball_polygons)]
            svg_path = os.path.join(full_path, SVG_FILENAME)
            create_tile_svg(current_tile, color_polygons_pairs, svg_path)

            # Convert the SVG to JPG using ImageMagick
            PATH_TO_IMAGE_MAGICK = "C:/Program Files/ImageMagick-7.1.1-Q16-HDRI/magick.exe"
            jpg_path = os.path.join(full_path, JPG_FILENAME)
            subprocess.run([PATH_TO_IMAGE_MAGICK, "convert", "-size", "%dx%d" % (config.at["JPG_SIZE"], config.at["JPG_SIZE"]), svg_path, jpg_path])

            # Log the status
            time_elapsed = time.time() - start_time
            num_complete += 1
            print(get_time_estimate_string(time_elapsed, num_complete, num_tiles))

if __name__ == "__main__":
    main()
