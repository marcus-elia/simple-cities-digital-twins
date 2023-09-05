#!/usr/bin/env python3

# Map polygon/multi-polygon geojson files (containing roads, sidewalks, etc.)
# into tiles in a specified tile area.

import argparse
import sys
import utm

sys.path.insert(1, 'C:/Users/mse93/Documents/simple-cities-digital-twins/utility_scripts')
from tile_id import *

def parse_latlon_string(latlon_string):
    lat,lon = latlon_string.split(',')
    return (float(lat.strip()), float(lon.strip()))

def main():
    parser = argparse.ArgumentParser(description="Map geojson polygons into tiles.")
    parser.add_argument("-i", "--input", required=True, help="Path to input geojson file")  
    parser.add_argument("-o", "--output", required=True, help="Name of output file to write in tiles")
    parser.add_argument("-d", "--directory", required=True, help="Name of output directory")
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

if __name__ == "__main__":
    main()
