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
FOREST_FILENAME = "forest_polygons.geojson"
RUNWAY_FILENAME = "runway_polygons.geojson"
PARK_FILENAME = "parks_polygons.geojson"
DOWNTOWN_FILENAME = "downtown_polygons.geojson"
RESIDENTIAL_FILENAME = "residential_polygons.geojson"
SVG_FILENAME = "tile_texture.svg"
JPG_FILENAME = "tile_texture.jpg"
TILE_MTL_FILENAME = "tile.mtl"
TILE_OBJ_FILENAME = "tile.obj"
TILE_TEXTURE_FILENAME = "tile_texture.jpg"
BUILDINGS_FILENAME = "buildings.geojson"
CUSTOM_BUILDINGS_FILENAME = "custom_buildings.txt"

# This maps the name of the material we write in the MTL files to
# the material's name in the config file
BUILDING_MATERIAL_NAMES = {"glass" : "GLASS_COLOR",\
        "brick" : "BRICK_COLOR",\
        "concrete" : "CONCRETE_COLOR",\
        "marble" : "MARBLE_COLOR",\
        "plaster" : "PLASTER_COLOR",\
        "metal" : "METAL_COLOR",\
        "vinyl_tan" : "VINYL_TAN_COLOR",\
        "vinyl_white" : "VINYL_WHITE_COLOR",\
        "vinyl_gray" : "VINYL_GRAY_COLOR",\
        "vinyl_brown" : "VINYL_BROWN_COLOR",\
        "vinyl_yellow" : "VINYL_YELLOW_COLOR",\
        "vinyl_blue" : "VINYL_BLUE_COLOR",\
        "vinyl_green" : "VINYL_GREEN_COLOR",\
        "roof_black" : "ROOF_BLACK_COLOR",\
        "roof_gray" : "ROOF_GRAY_COLOR",\
        "roof_white" : "ROOF_WHITE_COLOR"}

KEY_TO_TYPE = {\
        # Booleans
        "SINGLE_COLOR_BUILDINGS" : bool,\
        "BUILDING_MESH_COLOR" : str,\
        "SINGLE_COLOR_ROOFS" : bool,\
        "ROOF_MESH_COLOR" : str,\
        "AUTUMN" : bool,\
        # SVG colors
        "GRASS_COLOR" : str,\
        "WATER_COLOR" : str,\
        "ROAD_COLOR" : str,\
        "SIDEWALK_COLOR" : str,\
        "PARKING_COLOR" : str,\
        "DOWNTOWN_COLOR" : str,\
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
        "METAL_COLOR" : str,\
        "VINYL_TAN_COLOR" : str,\
        "VINYL_WHITE_COLOR" : str,\
        "VINYL_GRAY_COLOR" : str,\
        "VINYL_BROWN_COLOR" : str,\
        "VINYL_YELLOW_COLOR" : str,\
        "VINYL_BLUE_COLOR" : str,\
        "VINYL_GREEN_COLOR" : str,\
        "ROOF_BLACK_COLOR" : str,\
        "ROOF_GRAY_COLOR" : str,\
        "ROOF_WHITE_COLOR" : str,\
        # Material probabilities
        "SKYSCRAPER_GLASS_PROB" : float,\
        "SKYSCRAPER_CONCRETE_PROB" : float,\
        "SKYSCRAPER_METAL_PROB" : float,\
        "HOUSE_VINYL_PROB" : float,\
        "HOUSE_BRICK_PROB" : float,\
        "APARTMENTS_BRICK_PROB" : float,\
        "APARTMENTS_CONCRETE_PROB" : float,\
        "APARTMENTS_METAL_PROB" : float,\
        "VINYL_TAN_PROB" : float,\
        "VINYL_WHITE_PROB" : float,\
        "VINYL_GRAY_PROB" : float,\
        "VINYL_BROWN_PROB" : float,\
        "VINYL_YELLOW_PROB" : float,\
        "VINYL_BLUE_PROB" : float,\
        "VINYL_GREEN_PROB" : float,\
        "ROOF_BLACK_PROB" : float,\
        "ROOF_GRAY_PROB" : float,\
        "ROOF_WHITE_PROB" : float,\
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
                elif expected_type == bool:
                    self.at[key] = True if value == "True" else False
                else:
                    print("What is the expected type?")
            else:
                print("Unknown key %s" % (key))
