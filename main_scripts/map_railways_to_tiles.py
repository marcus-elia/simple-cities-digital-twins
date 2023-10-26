#!/usr/bin/env python3

# Map line/multi-line geojson files (containing railways)
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
from configuration import *
from general_utils import *
from geojson_utils import *
from latlon_to_utm import *
from polygon_utils import *
from tile_id import *

def map_shapely_line_into_tile(tile, shapely_line_latlon, manual_offset=(0.,0.)):
    shapely_line_utm = line_latlon_to_utm(shapely_line_latlon, offset=manual_offset)
    clipped_line = tile.polygon().intersection(shapely_line_utm)
    return clipped_line

def get_overlapping_tiles(shapely_line_utm, zone):
    x_min, y_min, x_max, y_max = shapely_line_utm.bounds
    min_tile = TileID(x_min, y_min, zone)
    max_tile = TileID(x_max, y_max, zone)
    return (min_tile.i, min_tile.j, max_tile.i, max_tile.j)

def main():
    parser = argparse.ArgumentParser(description="Map geojson polygons into tiles.")
    parser.add_argument("-i", "--input-filepath", required=True, help="Path to input geojson file")  
    parser.add_argument("-t", "--tile-directory", required=True, help="Name of tile directory")
    parser.add_argument("--city-name", required=True, help="Name of city (sub-directory of output directory that will be created)")
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

    output_filename = RAILWAY_FILENAME

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
    f = open(args.input_filepath)
    geojson_contents = geojson.loads(f.read())
    f.close()

    # Start by mapping every tile to an empty linestring
    tile_to_line_map = {}
    print("Initializing an empty linestring for all %d tiles." % (num_tiles))
    for i in range(min_i, max_i + 1):
        for j in range(min_j, max_j + 1):
            tile_to_line_map[(i, j)] = shapely.LineString()

    # Collect info for logging
    start_time = time.time()
    num_lines = num_features_in_geojson_file(geojson_contents)
    num_completed = 0

    # Now iterate over every line in the geojson, intersecting only with relevant tiles
    for geojson_feature in geojson_contents['features']:
        shapely_lines = geojson_feature_to_shapely(geojson_feature)
        for shapely_line_lonlat in shapely_lines:
            shapely_line_utm = line_lonlat_to_utm(shapely_line_lonlat, offset=(args.offset_x, args.offset_y))
            if shapely_line_utm.is_empty:
                # If the line crossed UTM zones, it could be empty
                continue

            # With the line in UTM, determine which tiles overlap with its bbox.
            # Also, make sure it doesn't go beyond the user-specified tile area.
            bbox_i_min, bbox_j_min, bbox_i_max, bbox_j_max = get_overlapping_tiles(shapely_line_utm, tile_min.zone)
            bbox_i_min = max(bbox_i_min, min_i)
            bbox_j_min = max(bbox_j_min, min_j)
            bbox_i_max = min(bbox_i_max, max_i)
            bbox_j_max = min(bbox_j_max, max_j)

            # Intersect it with each of those tiles
            for i in range(bbox_i_min, bbox_i_max + 1):
                for j in range(bbox_j_min, bbox_j_max + 1):
                    current_tile = TileID.tile_indices_to_object(i, j, tile_min.zone)
                    try:
                        clipped_line = current_tile.polygon().intersection(shapely_line_utm)
                        tile_to_line_map[(i, j)] = tile_to_line_map[(i, j)].union(clipped_line)
                    except shapely.errors.GEOSException:
                        print("Error intersecting linestring with tile. Skipping")
                        pass

            # Log the status
            num_completed += 1
            time_elapsed = int(time.time() - start_time)
            print(get_time_estimate_string(time_elapsed, num_completed, num_lines))

    # The tile to linestring map is complete. Write each tile's geojson file.
    print("Storing files in tiles.")
    print(min_i)
    print(max_i)
    print(min_j)
    print(max_j)
    for i in range(min_i, max_i + 1):
        for j in range(min_j, max_j + 1):
            tile_union = tile_to_line_map[(i, j)]
            # If the tile union is somehow a "geometry collection", make it not that
            if type(tile_union) == shapely.geometry.collection.GeometryCollection:
                line_union = shapely.Line()
                for geom in tile_union.geoms:
                    if type(geom) == shapely.geometry.line.Line:
                        line_union = line_union.union(geom)
                    else:
                        pass
                # Now it should be either a Line or MultiLine
                tile_union = line_union

            # Convert the multiline from shapely to geojson
            if type(tile_union) == shapely.geometry.multilinestring.MultiLineString:
                geojson_tile_union = shapely_multiline_to_geojson(tile_union)
            elif type(tile_union) == shapely.geometry.linestring.LineString:
                geojson_tile_union = shapely_line_to_geojson(tile_union)
            else:
                print("Unknown shapely type %s" % (type(tile_union)))
            features = [geojson.Feature(geometry=geojson_tile_union)]

            # Create the tile's directory, in case it doesn't exist yet
            full_path = os.path.join(city_directory, "%d_%d_%d" % (i, j, tile_min.zone))
            p = subprocess.Popen(['mkdir', full_path], shell=True)
            p.communicate()

            # Dump the geojson object into a string
            dump = geojson.dumps(geojson.FeatureCollection(features=features, crs=geojson_crs))

            # Finally, write to the file
            full_path = os.path.join(full_path, output_filename)
            f = open(full_path, 'w')
            f.write(dump)
            f.close()
    print("Stored %d %s files in %s." % (num_tiles, output_filename, args.tile_directory))

if __name__ == "__main__":
    main()
