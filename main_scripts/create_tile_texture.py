#!/usr/bin/env python3

# Create tile textures and write them to PNGs.

import argparse
import geojson
import os
import png
import shapely
import sys
import time

sys.path.insert(1, 'C:/Users/mse93/Documents/simple-cities-digital-twins/utility_scripts')
from general_utils import *
from geojson_utils import *
from latlon_to_utm import *
from tile_id import *

def main():
    parser = argparse.ArgumentParser(description="Create tile texture PNGs for tiles.")
    parser.add_argument("-o", "--output_filename", required=True, help="Name of output file to write in tiles")
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
    city_directory = os.path.join(args.data_directory, args.city_name)
    ROAD_COLOR = (0, 0, 20)
    GRASS_COLOR = (0, 180, 20)
    SIDEWALK_COLOR = (80, 80, 80)
    PNG_SIZE = 1024
    RESOLUTION = TileID.TILE_SIZE / PNG_SIZE

    for i in range(min_i, max_i + 1):
        for j in range(min_j, max_j + 1):
            current_tile = TileID.tile_indices_to_object(i, j, tile_min.zone)
            sw_x, sw_y = current_tile.sw_corner()
            full_path = os.path.join(city_directory, "%d_%d_%d" % (i, j, tile_min.zone))
            
            # Read the contents of the road geojson file
            f = open(os.path.join(full_path, ROAD_FILENAME))
            road_geojson_contents = geojson.loads(f.read())
            f.close()

            # Convert to roads shapely polygons
            shapely_road_polygons = []
            for geojson_multipolygon in road_geojson_contents['features']:
                shapely_road_polygons += geojson_multipoly_to_shapely(geojson_multipolygon['geometry']['coordinates'])

            # Read the contents of the sidewalk geojson file
            f = open(os.path.join(full_path, SIDEWALK_FILENAME))
            sidewalk_geojson_contents = geojson.loads(f.read())
            f.close()

            # Convert to roads shapely polygons
            shapely_sidewalk_polygons = []
            for geojson_multipolygon in sidewalk_geojson_contents['features']:
                shapely_sidewalk_polygons += geojson_multipoly_to_shapely(geojson_multipolygon['geometry']['coordinates'])

            # Initialize the image's array
            pixel_rgb_array = [[0 for _ in range(3 * PNG_SIZE)] for _ in range(PNG_SIZE)]

            # Iterate over every index of the array and set the color of the pixel
            num_complete = 0
            num_pixels = PNG_SIZE * PNG_SIZE
            start_time = time.time()
            print("Iterating over pixels")
            for row in range(PNG_SIZE):
                for col in range(0, 3 * PNG_SIZE, 3):
                    # Determine the UTM coordinate of the pixel
                    x = sw_x + RESOLUTION / 2 + col / 3 * TileID.TILE_SIZE / PNG_SIZE
                    y = sw_y + RESOLUTION / 2 + row * TileID.TILE_SIZE / PNG_SIZE
                    pixel_point_utm = shapely.Point(y, x)

                    # Check for containments
                    in_road = False
                    in_sidewalk = False
                    for polygon in shapely_road_polygons:
                        if polygon.contains(pixel_point_utm):
                            in_road = True
                            break
                    for polygon in shapely_sidewalk_polygons:
                        if polygon.contains(pixel_point_utm):
                            in_sidewalk = True
                            break

                    # Set pixel's color
                    if in_road:
                        color = ROAD_COLOR
                    elif in_sidewalk:
                        color = SIDEWALK_COLOR
                    else:
                        color = GRASS_COLOR
                    png_row = PNG_SIZE - row - 1 # PNG has y inverted
                    pixel_rgb_array[png_row][col] = color[0]
                    pixel_rgb_array[png_row][col + 1] = color[1]
                    pixel_rgb_array[png_row][col + 2] = color[2]

                    num_complete += 1
                    time_elapsed = time.time() - start_time
                    status_string = get_time_estimate_string(time_elapsed, num_complete, num_pixels)
                    sys.stdout.write("\r%s" % (status_string))
                    sys.stdout.flush()

            # Write the PNG to the tile
            f = open(os.path.join(full_path, args.output_filename), 'wb')
            w = png.Writer(PNG_SIZE, PNG_SIZE, greyscale=False)
            w.write(f, pixel_rgb_array)
            f.close()
            print("Wrote %d x %d PNG to %s" % (PNG_SIZE, PNG_SIZE, os.path.join(full_path, args.output_filename)))

if __name__ == "__main__":
    main()
