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
from general_utils import *
from geojson_utils import *
from latlon_to_utm import *
from svg_utils import *
from tile_id import *

def main():
    parser = argparse.ArgumentParser(description="Create tile texture SVGs and JPGs for tiles.")
    parser.add_argument("-d", "--data_directory", required=True, help="Name of output directory")
    parser.add_argument("-c", "--city_name", required=True, help="Name of city (sub-directory of output directory that will be created)")
    parser.add_argument("--sw", required=True, help='SW corner formatted as "lat,lon" or "lat, lon"')
    parser.add_argument("--ne", required=True, help='NE corner formatted as "lat,lon" or "lat, lon"')

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

    ROAD_FILENAME = "road_polygons.geojson"
    SIDEWALK_FILENAME = "sidewalk_polygons.geojson"
    WATER_FILENAME = "water_polygons.geojson"
    SVG_FILENAME = "tile_texture.svg"
    JPG_FILENAME = "tile_texture.jpg"
    city_directory = os.path.join(args.data_directory, args.city_name)
    ROAD_COLOR = "rgb(60,60,60)"
    GRASS_COLOR = "rgb(0,180,20)"
    SIDEWALK_COLOR = "rgb(128,128,128)"
    WATER_COLOR = "rgb(0,140,190)"
    JPG_SIZE = 4096

    # Iterate over every tile, creating an SVG manually and using ImageMagick to convert to JPG
    start_time = time.time()
    num_complete = 0
    for i in range(min_i, max_i + 1):
        for j in range(min_j, max_j + 1):
            current_tile = TileID.tile_indices_to_object(i, j, tile_min.zone)
            sw_x, sw_y = current_tile.sw_corner()
            full_path = os.path.join(city_directory, "%d_%d_%d" % (i, j, tile_min.zone))
            
            # Read the contents of the road geojson file
            f = open(os.path.join(full_path, ROAD_FILENAME))
            road_geojson_contents = geojson.loads(f.read())
            f.close()

            # Convert roads to shapely polygons
            shapely_road_polygons = []
            for geojson_multipolygon in road_geojson_contents['features']:
                shapely_road_polygons += geojson_multipoly_to_shapely(geojson_multipolygon['geometry']['coordinates'])

            # Read the contents of the sidewalk geojson file
            f = open(os.path.join(full_path, SIDEWALK_FILENAME))
            sidewalk_geojson_contents = geojson.loads(f.read())
            f.close()

            # Convert sidewalks to shapely polygons
            shapely_sidewalk_polygons = []
            for geojson_multipolygon in sidewalk_geojson_contents['features']:
                shapely_sidewalk_polygons += geojson_multipoly_to_shapely(geojson_multipolygon['geometry']['coordinates'])

            # Read the contents of the water geojson file
            f = open(os.path.join(full_path, WATER_FILENAME))
            water_geojson_contents = geojson.loads(f.read())
            f.close()

            # Convert water to shapely polygons
            shapely_water_polygons = []
            for geojson_multipolygon in water_geojson_contents['features']:
                shapely_water_polygons += geojson_multipoly_to_shapely(geojson_multipolygon['geometry']['coordinates'])

            # Write a SVG to the tile
            color_polygons_pairs = [(GRASS_COLOR, [current_tile.polygon_xy_flipped()]),\
                    (WATER_COLOR, shapely_water_polygons),\
                    (ROAD_COLOR, shapely_road_polygons),\
                    (SIDEWALK_COLOR, shapely_sidewalk_polygons)]
            svg_path = os.path.join(full_path, SVG_FILENAME)
            create_tile_svg(current_tile, color_polygons_pairs, svg_path)

            # Convert the SVG to JPG using ImageMagick
            PATH_TO_IMAGE_MAGICK = "C:/Program Files/ImageMagick-7.1.1-Q16-HDRI/magick.exe"
            jpg_path = os.path.join(full_path, JPG_FILENAME)
            subprocess.run([PATH_TO_IMAGE_MAGICK, "convert", "-size", "%dx%d" % (JPG_SIZE, JPG_SIZE), svg_path, jpg_path])

            # Log the status
            time_elapsed = time.time() - start_time
            num_complete += 1
            print(get_time_estimate_string(time_elapsed, num_complete, num_tiles))


if __name__ == "__main__":
    main()
