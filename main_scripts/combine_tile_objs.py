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
    parser = argparse.ArgumentParser(description="Combine OBJ files from tiles.")
    parser.add_argument("-t", "--tile-directory", required=True, help="Name of tile directory")
    parser.add_argument("-c", "--city-name", required=True, help="Name of city (sub-directory of tile directory)")
    parser.add_argument("--sw", required=True, help='SW corner formatted as "lat,lon" or "lat, lon"')
    parser.add_argument("--ne", required=True, help='NE corner formatted as "lat,lon" or "lat, lon"')
    parser.add_argument("--output-dir", required=True, help='Directory to write output OBJ, MTL, and JPGs')
    parser.add_argument("--output-filename", required=True, help='Name of combined OBJ and MTL files')

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

    city_directory = os.path.join(args.tile_directory, args.city_name)
    output_mtl_filepath = os.path.join(args.output_dir, args.output_filename + ".mtl")
    output_obj_filepath = os.path.join(args.output_dir, args.output_filename + ".obj")
    TILE_TEXTURE_FILENAME = "tile_texture.jpg"
    TILE_MTL_FILENAME = "tile.mtl"
    TILE_OBJ_FILENAME = "tile.obj"

    # Create the output directory
    p = subprocess.run(['mkdir', args.output_dir], shell=True)

    # Create both files
    mtl_file = open(output_mtl_filepath, 'w')
    obj_file = open(output_obj_filepath, 'w')

    # Keep track of which materials have already been added so we don't duplicate them
    material_names = set()
 
    # Iterate over every tile, read the tile's OBJ and MTL and add to the output files.
    # Also copy the tile textures to the output directory.
    start_time = time.time()
    num_complete = 0
    for i in range(min_i, max_i + 1):
        for j in range(min_j, max_j + 1):
            current_tile = TileID.tile_indices_to_object(i, j, tile_min.zone)
            tile_path = os.path.join(city_directory, "%d_%d_%d" % (i, j, tile_min.zone))
            
            # Add to the MTL file
            mtl_path = os.path.join(tile_path, TILE_MTL_FILENAME)
            f = open(mtl_path, 'r')
            lines = f.readlines()
            line_index = 0
            # TODO this MTL parsing is fragile
            while line_index < len(lines):
                line = lines[line_index]
                if line.startswith("newmtl"):
                    material_name = line.split()[-1].strip()
                    if not material_name in material_names:
                        material_names.add(material_name)
                        mtl_file.write(line)
                        line_index += 1
                        if line_index < len(lines):
                            line = lines[line_index]
                        while line_index < len(lines) and not line.startswith("newmtl"):
                            line = lines[line_index]
                            if line.endswith(TILE_TEXTURE_FILENAME):
                                # Rename the tile texture file to be unique for each tile
                                mtl_file.write("map_Kd %d_%d_%d.jpg\n\n" % (i, j, tile_min.zone))
                            else:
                                mtl_file.write(line)
                            line_index += 1
                line_index += 1
            f.close()

            # Copy the tile texture into the output directory
            tile_texture_path = os.path.join(tile_path, TILE_TEXTURE_FILENAME)
            output_texture_path = os.path.join(args.output_dir, "%d_%d_%d.jpg" % (i, j, tile_min.zone))
            # TODO why is subprocess not working here?
            os.system("copy %s %s" % (tile_texture_path, output_texture_path))

            # Log the status
            time_elapsed = time.time() - start_time
            num_complete += 1
            print(get_time_estimate_string(time_elapsed, num_complete, num_tiles))

    mtl_file.close()
    obj_file.close()

if __name__ == "__main__":
    main()