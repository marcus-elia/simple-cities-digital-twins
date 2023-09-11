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
from tiff_utils import *

def main():
    parser = argparse.ArgumentParser(description="Create tile mesh OBJ files.")
    parser.add_argument("-t", "--tile-directory", required=True, help="Name of tile directory")
    parser.add_argument("-c", "--city-name", required=True, help="Name of city (sub-directory of output directory)")
    parser.add_argument("--dem-path", required=True, help="Path to GeoTIFF DEM file")
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
    city_directory = os.path.join(args.tile_directory, args.city_name)
    MTL_FILENAME = "tile.mtl"
    OBJ_FILENAME = "tile.obj"
    TERRAIN_MESH_RES = 100
    TERRAIN_MESH_ROW_SIZE = int(TileID.TILE_SIZE / TERRAIN_MESH_RES)

    # Load the DEM
    dem = GeoTiffInterpolater(args.dem_path)
 
    # Iterate over every tile, creating an OBJ manually.
    start_time = time.time()
    num_complete = 0
    for i in range(min_i, max_i + 1):
        for j in range(min_j, max_j + 1):
            current_tile = TileID.tile_indices_to_object(i, j, tile_min.zone)
            sw_x, sw_y = current_tile.sw_corner()
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

            # The header is always this
            f.write("mtllib %s\n" % (MTL_FILENAME))

            # Add the terrain. Use the DEM.
            for local_x in range(0, TileID.TILE_SIZE + TERRAIN_MESH_RES, TERRAIN_MESH_RES):
                for local_y in range(0, TileID.TILE_SIZE + TERRAIN_MESH_RES, TERRAIN_MESH_RES):
                    # Compute the elevation and write the vertex's coordinates
                    # TODO explain why x is flipped here
                    elevation = dem.interpolate(sw_x + TileID.TILE_SIZE - local_x, sw_y + local_y)
                    f.write("v    %.6f    %.6f    %.6f\n" % (local_x, elevation, local_y))

                    # Compute and write the UV for this vertex
                    f.write("vt    %.6f    %.6f\n" % (local_y / TileID.TILE_SIZE, local_x / TileID.TILE_SIZE))

            # Now we have to do the faces, which is harder. This is triangulating.
            f.write("g terrain\n")
            f.write("usemtl %s\n" % (material_name))
            for x_index in range(TERRAIN_MESH_ROW_SIZE):
                column_min_index = 1 + x_index * (TERRAIN_MESH_ROW_SIZE + 1)
                for y_index in range(TERRAIN_MESH_ROW_SIZE):
                    # Bottom right triangle
                    p1 = column_min_index + y_index
                    p2 = p1 + TERRAIN_MESH_ROW_SIZE + 1
                    p3 = p2 + 1
                    f.write("f %d/%d %d/%d %d/%d\n" % (p1, p1, p2, p2, p3, p3))
                    # Top left triangle
                    p1 = p1
                    p2 = p3
                    p3 = p1 + 1
                    f.write("f %d/%d %d/%d %d/%d\n" % (p1, p1, p2, p2, p3, p3))
            f.close()

            # Log the status
            time_elapsed = time.time() - start_time
            num_complete += 1
            print(get_time_estimate_string(time_elapsed, num_complete, num_tiles))


if __name__ == "__main__":
    main()
