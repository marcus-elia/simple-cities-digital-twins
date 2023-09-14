#!/usr/bin/env python3

# Load all of the configuration variables
# into memory so they can be accessed.

# Filenames that are stored in tiles
ROAD_FILENAME = "road_polygons.geojson"
SIDEWALK_FILENAME = "sidewalk_polygons.geojson"
PARKING_FILENAME = "parking_polygons.geojson"
WATER_FILENAME = "water_polygons.geojson"
BEACH_FILENAME = "beach_polygons.geojson"
BASEBALL_FILENAME = "baseball_polygons.geojson"
TRACK_FILENAME = "track_polygons.geojson"
POOL_FILENAME = "pool_polygons.geojson"
PARK_FILENAME = "parks_polygons.geojson"
DOWNTOWN_FILENAME = "downtown_polygons.geojson"
SVG_FILENAME = "tile_texture.svg"
JPG_FILENAME = "tile_texture.jpg"
TILE_MTL_FILENAME = "tile.mtl"
TILE_OBJ_FILENAME = "tile.obj"
TILE_TEXTURE_FILENAME = "tile_texture.jpg"
BUILDINGS_FILENAME = "buildings.geojson"
BUILDING_MATERIAL_NAMES = {"glass" : "GLASS_COLOR",\
        "brick" : "BRICK_COLOR",\
        "concrete" : "CONCRETE_COLOR",\
        "marble" : "MARBLE_COLOR",\
        "plaster" : "PLASTER_COLOR",\
        "roof_brown" : "ROOF_BROWN_COLOR",\
        "roof_black" : "ROOF_BLACK_COLOR",\
        "roof_gray" : "ROOF_GRAY_COLOR",\
        "roof_white" : "ROOF_WHITE_COLOR"}

KEY_TO_TYPE = {\
        # SVG colors
        "GRASS_COLOR" : str,\
        "WATER_COLOR" : str,\
        "ROAD_COLOR" : str,\
        "SIDEWALK_COLOR" : str,\
        "PARKING_COLOR" : str,\
        "BASEBALL_COLOR" : str,\
        "TRACK_COLOR" : str,\
        "POOL_COLOR" : str,\
        "BEACH_COLOR" : str,\
        # MTL colors
        "GLASS_COLOR" : str,\
        "BRICK_COLOR" : str,\
        "CONCRETE_COLOR" : str,\
        "MARBLE_COLOR" : str,\
        "PLASTER_COLOR" : str,\
        "ROOF_BROWN_COLOR" : str,\
        "ROOF_BLACK_COLOR" : str,\
        "ROOF_GRAY_COLOR" : str,\
        "ROOF_WHITE_COLOR" : str,\
        # Height things
        "MIN_SKYSCRAPER_HEIGHT" : float,\
        "MIN_DOWNTOWN_HEIGHT" : float,\
        "MAX_DOWNTOWN_HEIGHT" : float,\
        "MIN_HOUSE_HEIGHT" : float,\
        "MAX_HOUSE_HEIGHT" : float,\
        "MIN_APARTMENTS_HEIGHT" : float,\
        "MAX_APARTMENTS_HEIGHT" : float,\
        # Data sizes
        "JPG_SIZE" : int,\
        "TERRAIN_MESH_RES" : int}
        
class Configuration:
    def __init__(self, filepath):
        self.at = {}
        f = open(filepath, 'r')
        for line in f:
            key, value = line.split()
            if key in KEY_TO_TYPE:
                expected_type = KEY_TO_TYPE[key]
                if expected_type == str:
                    self.at[key] = value
                elif expected_type == float:
                    self.at[key] = float(value)
                elif expected_type == int:
                    self.at[key] = int(value)
                else:
                    print("What is the expected type?")
            else:
                print("Unknown key %s" % (key))
