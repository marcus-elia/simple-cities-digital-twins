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

def query_building_elevations(shapely_building_polygon, dem_interpolater):
    """
    Determine the lowest and highest elevations along the perimeter of
    the building. This only queries at vertices and does not get the
    exact answer.
    """
    lowest = sys.float_info.max
    highest = sys.float_info.min
    for x, y in shapely_building_polygon.exterior.coords:
        elevation = dem_interpolater.interpolate(x, y)
        lowest = min(lowest, elevation)
        highest = max(highest, elevation)

    return (lowest, highest)

def get_convex_hull_reflected_across_tile_x(polygon, tile):
    sw_x, sw_y = tile.sw_corner()
    tile_max_x = sw_x + TileID.TILE_SIZE
    original_convex_hull = polygon.convex_hull.exterior.coords
    reflected_convex_hull = []
    for x, y in original_convex_hull:
        new_x = sw_x + (tile_max_x - x)
        reflected_convex_hull.append((new_x, y))
    return shapely.Polygon(reflected_convex_hull)

def get_convex_hull_reflected_across_tile_y(polygon, tile):
    sw_x, sw_y = tile.sw_corner()
    tile_max_y = sw_y + TileID.TILE_SIZE
    original_convex_hull = polygon.convex_hull.exterior.coords
    reflected_convex_hull = []
    for x, y in original_convex_hull:
        new_y = sw_y + (tile_max_y - y)
        reflected_convex_hull.append((x, new_y))
    return shapely.Polygon(reflected_convex_hull)

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
    BUILDINGS_FILENAME = "buildings.geojson"
    city_directory = os.path.join(args.tile_directory, args.city_name)
    MTL_FILENAME = "tile.mtl"
    OBJ_FILENAME = "tile.obj"
    TERRAIN_MESH_RES = 25
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

            # Load the buildings geojson file
            shapely_building_polygons = []
            try:
                f = open(os.path.join(full_path, BUILDINGS_FILENAME))
                buildings_geojson_contents = geojson.loads(f.read())
                f.close()
                for geojson_multipolygon in buildings_geojson_contents['features']:
                    shapely_building_polygons += geojson_multipoly_to_shapely(geojson_multipolygon['geometry']['coordinates'])
            except FileNotFoundError:
                pass

            # Create the MTL file (the easy part)
            mtl_path = os.path.join(full_path, MTL_FILENAME)
            material_name = "%d_%d_%d" % (i, j, tile_min.zone)
            f = open(mtl_path, 'w')
            f.write("newmtl %s\n" % (material_name))
            f.write("Ka 1.0000 1.0000 1.0000\n")
            f.write("Kd 1.0000 1.0000 1.0000\n")
            f.write("illum 1\n")
            f.write("map_Kd %s\n\n" % TILE_TEXTURE_FILENAME)
            # Add white for buildings (temporary)
            f.write("newmtl white\n")
            f.write("Kd 1.0000 1.0000 1.0000\n")
            f.write("illum 0\n")
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
                    elevation = dem.interpolate(sw_x + local_x, sw_y + local_y)
                    # The z (y) coordinate is flipped here. Do OBJs have -z being up?
                    f.write("v    %.6f    %.6f    %.6f\n" % (local_x, elevation, TileID.TILE_SIZE - local_y))

                    # Compute and write the UV for this vertex
                    f.write("vt    %.6f    %.6f\n" % (local_x / TileID.TILE_SIZE, local_y / TileID.TILE_SIZE))

            # Now we have to do the faces, which is harder. This is triangulating.
            f.write("g terrain\n")
            f.write("usemtl %s\n" % (material_name))
            # Each terrain square is a bottom right triangle and a top left triangle
            # (diagonal edge goes from SW to NE corner of the square)
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

            # Add all of the buildings
            # This variable tracks which index the building's vertices starts with
            starting_vertex_index = (TERRAIN_MESH_ROW_SIZE + 1) * (TERRAIN_MESH_ROW_SIZE + 1) + 1
            for building in shapely_building_polygons:
                # Determine the elevation/height properties
                lowest_elevation, highest_elevation = query_building_elevations(building.convex_hull, dem)
                above_ground_height = 5
                height = above_ground_height + highest_elevation - lowest_elevation

                # Write the vertices of the building
                # Use a flipped convex hull because OBJs are -z up (I think that's why)
                convex_hull = get_convex_hull_reflected_across_tile_y(building, current_tile)
                # Add a point at the center of the top face for triangulating
                f.write("# Building vertices\n")
                f.write("v    %.6f    %.6f    %.6f\n" % (convex_hull.centroid.x - sw_x, lowest_elevation + height, convex_hull.centroid.y - sw_y))
                # Slice to avoid the duplicated starting point
                vertices = list(convex_hull.exterior.coords)[:-1]
                for x, y in vertices:
                    # Point on the base of the building
                    f.write("v    %.6f    %.6f    %.6f\n" % (x - sw_x, lowest_elevation, y - sw_y))
                    # Point on the top of the building
                    f.write("v    %.6f    %.6f    %.6f\n" % (x - sw_x, lowest_elevation + height, y - sw_y))
                    # For now, buildings don't have textures, just colors. So no UVs.

                # Write the header of the building
                f.write("g a building with %d vertices\n" % (len(vertices)))
                f.write("usemtl white\n")

                # Once again, doing the triangulation is tricky
                # For the sides of the building, each face is a bottom right triangle and a top left triangle
                # On the top base of the building, each vertex connects to the center
                for face_index in range(len(vertices) - 1):
                    # Bottom right triangle
                    p1 = 1 + starting_vertex_index + (2 * face_index)
                    p2 = p1 + 2
                    p3 = p2 + 1
                    f.write("f %d %d %d\n" % (p1, p2, p3))
                    # Top left triangle
                    p2 = p3
                    p3 = p1 + 1
                    f.write("f %d %d %d\n" % (p1, p2, p3))
                    # Top base triangle
                    p1 = p3
                    p3 = starting_vertex_index
                    f.write("f %d %d %d\n" % (p1, p2, p3))

                # Connect to the end to the beginning
                # Bottom right triangle
                p1 = 1 + starting_vertex_index + 2 * (len(vertices) - 1)
                p2 = starting_vertex_index + 1
                p3 = p2 + 1
                f.write("f %d %d %d\n" % (p1, p2, p3))
                # Top left triangle
                p2 = p3
                p3 = p1 + 1
                f.write("f %d %d %d\n" % (p1, p2, p3))
                # Top base triangle
                p1 = p3
                p3 = starting_vertex_index
                f.write("f %d %d %d\n" % (p1, p2, p3))

                # Update the vertex index based on how many this building added
                starting_vertex_index += (2 * len(vertices) + 1)
            f.close()

            # Log the status
            time_elapsed = time.time() - start_time
            num_complete += 1
            print(get_time_estimate_string(time_elapsed, num_complete, num_tiles))

if __name__ == "__main__":
    main()
