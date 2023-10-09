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
from configuration import *
from general_utils import *
from geojson_utils import *
from latlon_to_utm import *
from svg_utils import *
from tile_id import *
from tiff_utils import *

def get_property_or_default(properties, key, default):
    if key in properties:
        return properties[key]
    else:
        return default

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
    parser.add_argument("--config-file", required=True, help="Path to the configuration file")
    parser.add_argument("-t", "--tile-directory", required=True, help="Name of tile directory")
    parser.add_argument("--city-name", required=True, help="Name of city (sub-directory of output directory)")
    parser.add_argument("--dem-path", required=True, help="Path to GeoTIFF DEM file")
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
    TERRAIN_MESH_RES = config.at["TERRAIN_MESH_RES"]
    TERRAIN_MESH_ROW_SIZE = int(TileID.TILE_SIZE / TERRAIN_MESH_RES)

    # Load the DEM
    dem = GeoTiffInterpolater(args.dem_path)

    # Load the tree mesh
    f = open("models/tree.obj", 'r')
    tree_obj_lines = f.readlines()
    f.close()
    f = open("models/tree.mtl", 'r')
    tree_mtl_lines = f.readlines()
    f.close()

    # Count the number of vertices in the tree file
    num_tree_points = sum([1 for line in tree_obj_lines if line.startswith('v')])

    # Iterate over every tile, creating an OBJ manually.
    start_time = time.time()
    num_complete = 0
    for i in range(min_i, max_i + 1):
        for j in range(min_j, max_j + 1):
            current_tile = TileID.tile_indices_to_object(i, j, tile_min.zone)
            sw_x, sw_y = current_tile.sw_corner()
            full_path = os.path.join(city_directory, "%d_%d_%d" % (i, j, tile_min.zone))

            # Load the buildings geojson file
            building_pwps = []
            try:
                f = open(os.path.join(full_path, BUILDINGS_FILENAME))
                buildings_geojson_contents = geojson.loads(f.read())
                f.close()
                for geojson_feature in buildings_geojson_contents['features']:
                    building_pwps += geojson_feature_to_pwps(geojson_feature)
            except FileNotFoundError:
                pass

            # Load the info about custom buildings
            osm_ids_to_ignore = []
            custom_building_filenames_to_centers = {}
            custom_buildings_full_path = os.path.join(full_path, CUSTOM_BUILDINGS_FILENAME)
            try:
                f = open(custom_buildings_full_path)
                for line in f.readlines():
                    if line.startswith("filename"):
                        name, x, y = line.split()[1:]
                        custom_building_filenames_to_centers[name] = (float(x), float(y.strip()))
                    elif line.startswith("id"):
                        osm_ids_to_ignore.append(int(line.split()[1].strip()))
                    else:
                        print("Unknown line prefix %s in %s" % (line, custom_buildings_full_path))
            except FileNotFoundError:
                pass

            # Load the trees geojson file
            tree_points = []
            try:
                f = open(os.path.join(full_path, "trees.geojson"))
                tree_geojson_contents = geojson.loads(f.read())
                f.close()
                for geojson_feature in tree_geojson_contents['features']:
                    tree_points += geojson_feature_to_shapely(geojson_feature)
            except FileNotFoundError:
                pass

            # Create the MTL file (the easy part)
            mtl_path = os.path.join(full_path, TILE_MTL_FILENAME)
            material_name = "%d_%d_%d" % (i, j, tile_min.zone)
            f = open(mtl_path, 'w')
            f.write("newmtl %s\n" % (material_name))
            f.write("Ka 1.0000 1.0000 1.0000\n")
            f.write("Kd 1.0000 1.0000 1.0000\n")
            f.write("illum 1\n")
            f.write("map_Kd %s\n\n" % TILE_TEXTURE_FILENAME)

            # Add colors for buildings
            # Get them from the config file
            material_color_map = {building_mat_name : config.at[BUILDING_MATERIAL_NAMES[building_mat_name]] for building_mat_name in BUILDING_MATERIAL_NAMES}
            for building_mat_name in material_color_map:
                f.write("newmtl %s\n" % building_mat_name)
                r,g,b = material_color_map[building_mat_name].split(',')
                f.write("Kd %s %s %s\n" % (r, g, b))
                f.write("illum 0\n\n")

            # Add colors from the tree model
            for line in tree_mtl_lines:
                f.write(line)
            if config.at["AUTUMN"]:
                f.write("newmtl tree_red\n")
                f.write("Kd 1.0000 0.0000 0.0000\n")
                f.write("illum 0\n")
                f.write("newmtl tree_yellow\n")
                f.write("Kd 1.0000 1.0000 0.0000\n")
                f.write("illum 0\n")
                f.write("newmtl tree_orange\n")
                f.write("Kd 1.0000 0.5000 0.0000\n")
                f.write("illum 0\n")
            f.close()

            # Start the OBJ file
            obj_path = os.path.join(full_path, TILE_OBJ_FILENAME)
            f = open(obj_path, 'w')

            # The header is always this
            f.write("mtllib %s\n" % (TILE_MTL_FILENAME))
            f.write("# Terrain vertices\n")

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
            for pwp in building_pwps:
                # Check if the building should be omitted
                osm_id = int(get_property_or_default(pwp.properties, "osm_id", 0))
                if osm_id in osm_ids_to_ignore:
                    continue

                # Determine the elevation/height properties
                building = pwp.polygon
                lowest_elevation, highest_elevation = query_building_elevations(building.convex_hull, dem)
                above_ground_height = float(get_property_or_default(pwp.properties, "height", 5.))
                height = above_ground_height + highest_elevation - lowest_elevation

                # The color
                if config.at["SINGLE_COLOR_BUILDINGS"]:
                    color = config.at["BUILDING_MESH_COLOR"]
                else:
                    color = get_property_or_default(pwp.properties, "mesh_color", "concrete")
                if config.at["SINGLE_COLOR_ROOFS"]:
                    roof_color = config.at["ROOF_MESH_COLOR"]
                else:
                    roof_color = get_property_or_default(pwp.properties, "roof_color", "roof_white")

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
                f.write("usemtl %s\n" % (color))

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

                # Write the header of the roof
                f.write("g roof of building\n")
                f.write("usemtl %s\n" % (roof_color))
                # Triangulate the top base of the building. Each vertex connects to the center.
                for face_index in range(len(vertices) - 1):
                    p1 = 1 + starting_vertex_index + (2 * face_index) + 1
                    p2 = p1 + 2
                    p3 = starting_vertex_index
                    f.write("f %d %d %d\n" % (p1, p2, p3))
                # Finish the last triangle at the end
                p1 = starting_vertex_index + 2
                p1 = 1 + starting_vertex_index + 2 * (len(vertices) - 1) + 1
                p2 = starting_vertex_index + 2
                p3 = starting_vertex_index
                f.write("f %d %d %d\n" % (p1, p2, p3))

                # Update the vertex index based on how many this building added
                starting_vertex_index += (2 * len(vertices) + 1)

            # Now add trees
            # TODO why subtract 1?
            starting_vertex_index -= 1
            # rng used for picking autumn colors
            rng = np.random.default_rng()
            for shapely_tree_point in tree_points:
                tree_x = shapely_tree_point.x - sw_x
                tree_y = shapely_tree_point.y - sw_y
                elevation = dem.interpolate(sw_x + tree_x, sw_y + tree_y)
                for line in tree_obj_lines:
                    if line.startswith('m') or line.startswith('#'):
                        continue
                    elif line.startswith('g'):
                        f.write(line)
                    elif line.startswith('u'):
                        if not config.at["AUTUMN"] or ("brown" in line):
                            f.write(line)
                        else:
                            rand = rng.random()
                            if rand < 0.33:
                                f.write("usemtl tree_red\n")
                            elif rand < 0.67:
                                f.write("usemtl tree_yellow\n")
                            elif rand < 0.98:
                                f.write("usemtl tree_orange\n")
                            else:
                                f.write(line)
                    elif line.startswith('v'):
                        coords = line.split()[1:]
                        x = float(coords[0]) + tree_x
                        y = float(coords[1]) + elevation
                        z = float(coords[2]) + (TileID.TILE_SIZE - tree_y)
                        f.write("v    %.6f    %.6f    %.6f\n" % (x, y, z))
                    elif line.startswith('f'):
                        indices = line.split()[1:]
                        a = int(indices[0]) + starting_vertex_index
                        b = int(indices[1]) + starting_vertex_index
                        c = int(indices[2]) + starting_vertex_index
                        f.write("f %d %d %d\n" % (a, b, c))
                starting_vertex_index += num_tree_points

            # For the last step, add in any custom buildings
            f.write("g custom buildings\n")
            f.write("usemtl %s\n" % ("brick"))
            for filename in custom_building_filenames_to_centers:
                center_x, center_y = custom_building_filenames_to_centers[filename]
                elevation = dem.interpolate(center_x, center_y)
                local_center_x = center_x - sw_x
                local_center_y = center_y - sw_y
                custom_building_full_path = os.path.join(full_path, filename)
                try:
                    building_file = open(custom_building_full_path)
                    lines = building_file.readlines()
                    building_file.close()
                except FileNotFoundError:
                    print("Failed to find %s" % (custom_building_full_path))
                    continue

                # Add lines to the tile's OBJ based on the lines in the custom building's OBJ
                num_building_points = 0
                for line in lines:
                    if line.startswith('v'):
                        coords = line.split()[1:]
                        x = float(coords[0]) + local_center_x
                        y = float(coords[1]) + elevation
                        z = float(coords[2]) + (TileID.TILE_SIZE - local_center_y)
                        f.write("v    %.6f    %.6f    %.6f\n" % (x, y, z))
                        num_building_points += 1
                    elif line.startswith('f'):
                        indices = line.split()[1:]
                        a = int(indices[0]) + starting_vertex_index
                        b = int(indices[1]) + starting_vertex_index
                        c = int(indices[2]) + starting_vertex_index
                        f.write("f %d %d %d\n" % (a, c, b)) # TODO: why reverse orientation?
                starting_vertex_index += num_building_points

            f.close()

            # Log the status
            time_elapsed = time.time() - start_time
            num_complete += 1
            print(get_time_estimate_string(time_elapsed, num_complete, num_tiles))

if __name__ == "__main__":
    main()
