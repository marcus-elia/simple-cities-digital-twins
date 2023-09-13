#!/usr/bin/env python3

# Map geojson files containing buildings
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
from general_utils import *
from geojson_utils import *
from latlon_to_utm import *
from polygon_utils import *
from tile_id import *

def filter_properties(pwp):
    filtered = {}
    for key,value in pwp.properties.items():
        if key == "height" and value != None:
            # OSM annotators could have put m or M after the number
            filtered[key] = value.strip('m').strip('M').strip()
        elif key == "building" and value != None:
            filtered[key] = value
        elif key == "building:material" and value != None:
            filtered[key] = value
        elif (key == "building:color" or key == "building:colour") and value != None:
            filtered["building:color"] = value
        elif key == "roof:shape" and value != None:
            filtered[key] = value
        elif (key == "roof:color" or key == "roof:colour") and value != None:
            filtered["roof:color"] = value
        elif key == "roof:material" and value != None:
            filtered[key] = value
    # Set the required things
    if not "height" in filtered:
        filtered["height"] = 5
    if not "building:color" in filtered:
        if "building:material" in filtered:
            # If there is a material, choose a color from that
            material = filtered["building:material"]
            if material == "glass":
                filtered["building:color"] = "blue"
            elif material == "brick":
                filtered["building:color"] = "red"
            elif material == "stone" or material == "concrete":
                filtered["building:color"] = "gray"
            elif material == "plaster" or material == "marble":
                filtered["building:color"] = "white"
            else:
                filtered["building:color"] = "gray"
        elif float(filtered["height"]) > 90:
            # Tall buildings without materials are assumed to be glass skyscrapers
            filtered["building:color"] = "blue"
        else:
            filtered["building:color"] = "gray"

        return filtered

def main():
    parser = argparse.ArgumentParser(description="Map geojson polygons into tiles.")
    parser.add_argument("-i", "--input-filepath", required=True, help="Path to input geojson file")  
    parser.add_argument("-t", "--tile-directory", required=True, help="Name of tile directory")
    parser.add_argument("-c", "--city-name", required=True, help="Name of city (sub-directory of output directory that will be created)")
    parser.add_argument("--sw", required=True, help='SW corner formatted as "lat,lon" or "lat, lon"')
    parser.add_argument("--ne", required=True, help='NE corner formatted as "lat,lon" or "lat, lon"')
    parser.add_argument("--offset-x", required=False, type=float, default=0., help='Offset x coord of each point')
    parser.add_argument("--offset-y", required=False, type=float, default=0., help='Offset y coord of each point')

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
    city_directory = os.path.join(args.tile_directory, args.city_name)

    # Try to create the directory, in case it doesn't exist
    p = subprocess.Popen(['mkdir', args.tile_directory], shell=True)
    p.communicate()
    p = subprocess.Popen(['mkdir', city_directory], shell=True)
    p.communicate()

    geojson.geometry.DEFAULT_PRECISION = 10

    # Read the contents of the geojson file
    f = open(args.input_filepath, encoding="utf8")
    geojson_contents = geojson.loads(f.read())
    f.close()

    # Start by mapping every tile to an empty polygon
    tile_to_pwps_map = {}
    print("Initializing an empty multipolygon for all %d tiles." % (num_tiles))
    for i in range(min_i, max_i + 1):
        for j in range(min_j, max_j + 1):
            tile_to_pwps_map[(i, j)] = []

    # Collect info for logging
    start_time = time.time()
    num_polygons = num_polygons_in_geojson_file(geojson_contents)
    num_completed = 0

    # Now iterate over every polygon in the geojson, intersecting only with relevant tiles
    for geojson_feature in geojson_contents['features']:
        pwps_lonlat = geojson_feature_to_pwps(geojson_feature)
        for pwp_lonlat in pwps_lonlat:
            pwp_utm = PolygonWithProperties(poly_lonlat_to_utm(pwp_lonlat.polygon, offset=(args.offset_x, args.offset_y)), pwp_lonlat.properties)

            # Filter out unused properties and set the required ones
            pwp_utm.properties = filter_properties(pwp_utm)

            center_x, center_y = pwp_utm.polygon.centroid.x, pwp_utm.polygon.centroid.y
            containing_tile = TileID(center_x, center_y, tile_min.zone)

            # Add it to the tile's list of polygons
            try:
                tile_to_pwps_map[(containing_tile.i, containing_tile.j)].append(pwp_utm)
            except KeyError:
                # If the polygon's center is not in the tile area, ignore it
                continue
 
            # Log the status
            num_completed += 1
            time_elapsed = int(time.time() - start_time)
            print(get_time_estimate_string(time_elapsed, num_completed, num_polygons))

    # The tile to polygon map is complete. Write each tile's geojson file.
    print("Storing files in tiles.")
    for i in range(min_i, max_i + 1):
        for j in range(min_j, max_j + 1):
            geojson_features = []
            for pwp in tile_to_pwps_map[(i, j)]:
                geojson_feature = polygon_with_properties_to_geojson(pwp)
                geojson_features.append(geojson_feature)

            # Create the tile's directory, in case it doesn't exist yet
            full_path = os.path.join(city_directory, "%d_%d_%d" % (i, j, tile_min.zone))
            p = subprocess.Popen(['mkdir', full_path], shell=True)
            p.communicate()

            # Dump the geojson object into a string
            dump = geojson.dumps(geojson.FeatureCollection(features=geojson_features, crs=geojson_crs))

            # Finally, write to the file
            full_path = os.path.join(full_path, "buildings.geojson")
            f = open(full_path, 'w')
            f.write(dump)
            f.close()
    print("Stored %d %s files in %s." % (num_tiles, "buildings.geojson", full_path))

if __name__ == "__main__":
    main()
