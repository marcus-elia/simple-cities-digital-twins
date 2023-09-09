#!/usr/bin/env python3

# Create tile meshes in the OBJ format.

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
    parser = argparse.ArgumentParser(description="Create tile mesh OBJ files.")
    parser.add_argument("-d", "--data_directory", required=True, help="Name of output directory")
    parser.add_argument("-c", "--city_name", required=True, help="Name of city (sub-directory of output directory)")
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

    TILE_TEXTURE_FILENAME = "tile_texture.jpg"
    city_directory = os.path.join(args.data_directory, args.city_name)
    MTL_FILENAME = "tile.mtl"
    OBJ_FILENAME = "tile.obj"
 
    # Iterate over every tile, creating an OBJ manually.
    start_time = time.time()
    num_complete = 0
    for i in range(min_i, max_i + 1):
        for j in range(min_j, max_j + 1):
            current_tile = TileID.tile_indices_to_object(i, j, tile_min.zone)
            full_path = os.path.join(city_directory, "%d_%d_%d" % (i, j, tile_min.zone))
            
            # Create the MTL file (the easy part)
            mtl_path = os.path.join(full_path, MTL_FILENAME)
            material_name = "%d_%d_%d" % (i, j, tile_min.zone)
            f = open(mtl_path, 'w')
            f.write("newmtl %s\n" % (material_name))
            f.write("Ka 1.0000 1.0000 1.0000\n")
            f.write("Kd 1.0000 1.0000 1.0000\n")
            f.write("illum 1\n")
            f.write("map_Kd %s" % TILE_TEXTURE_FILENAME)
            f.close()

            # Start the OBJ file
            obj_path = os.path.join(full_path, OBJ_FILENAME)
            f = open(obj_path, 'w')
            
            # Add the terrain. For, it is flat with only 4 vertices.
            f.write("mtllib %s\n" % (MTL_FILENAME))
            f.write("v    0.000000    0.000000    0.000000\n")
            f.write("v    0.000000    0.000000    %f\n" % (TileID.TILE_SIZE))
            f.write("v    %f    0.000000    %f\n" % (TileID.TILE_SIZE, TileID.TILE_SIZE))
            f.write("v    %f    0.000000    0.000000\n" % (TileID.TILE_SIZE))
            # These are UV coordinates
            f.write("vt   0.000000    0.000000\n")
            f.write("vt   0.000000    1.000000\n")
            f.write("vt   1.000000    1.000000\n")
            f.write("vt   1.000000    0.000000\n")
            f.write("g terrain\n")
            f.write("usemtl %s\n" % (material_name))
            f.write("f 1/1 2/2 3/3\n")
            f.write("f 1/1 3/3 4/4")
            f.close()

            # Log the status
            time_elapsed = time.time() - start_time
            num_complete += 1
            print(get_time_estimate_string(time_elapsed, num_complete, num_tiles))


if __name__ == "__main__":
    main()
