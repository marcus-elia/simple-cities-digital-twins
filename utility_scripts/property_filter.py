#!/usr/bin/env python3

# Functions for setting/cleaning the properties of buildings

from enum import Enum
import numpy as np
import sys

sys.path.insert(1, 'C:/Users/mse93/Documents/simple-cities-digital-twins/utility_scripts')
from polygon_utils import polygon_list_contains

class BuildingClassification(Enum):
    House = 1
    Skyscraper = 2
    Apartments = 3
    School = 4
    MidsizedCommercial = 5
    DowntownMiscellaneous = 6
    SmallNonHouse = 7

class PropertyFilter:
    """
    This class handles the properties that were read from the original
    geojson file of buildings. Currently height and mesh:color are
    required for creating a mesh, so those are randomly chosen based on
    the configuration file variables if not present.
    """
    def __init__(self, configuration):
        self.config = configuration
        self.rng = np.random.default_rng(1)

        # Set the probabilities for materials of skyscrapers
        glass_cutoff = self.config.at["SKYSCRAPER_GLASS_PROB"]
        concrete_cutoff = glass_cutoff + self.config.at["SKYSCRAPER_CONCRETE_PROB"]
        metal_cutoff = concrete_cutoff + self.config.at["SKYSCRAPER_METAL_PROB"]
        if abs(metal_cutoff - 1.) > 0.01:
            print("Error: skyscraper material probabilities don't add to 1. Check the config file.")
        self.skyscraper_material_probs = (("glass", glass_cutoff), ("concrete", concrete_cutoff), ("metal", metal_cutoff))

        # Set the probabilities for materials of apartments
        brick_cutoff = self.config.at["APARTMENTS_BRICK_PROB"]
        concrete_cutoff = brick_cutoff + self.config.at["APARTMENTS_CONCRETE_PROB"]
        metal_cutoff = concrete_cutoff + self.config.at["APARTMENTS_METAL_PROB"]
        if abs(metal_cutoff - 1.) > 0.01:
            print("Error: apartment material probabilities don't add to 1. Check the config file.")
        self.apartment_material_probs = (("brick", brick_cutoff), ("concrete", concrete_cutoff), ("metal", metal_cutoff))

        # Set the probabilities for materials of houses
        vinyl_cutoff = self.config.at["HOUSE_VINYL_PROB"]
        brick_cutoff = vinyl_cutoff + self.config.at["HOUSE_BRICK_PROB"]
        if abs(brick_cutoff - 1.) > 0.01:
            print("Error: house material probabilities don't add to 1. Check the config file.")
        self.house_material_probs = (("vinyl", vinyl_cutoff), ("brick", brick_cutoff))

        # Set the probabilities for vinyl colors
        tan_cutoff = self.config.at["VINYL_TAN_PROB"]
        white_cutoff = tan_cutoff + self.config.at["VINYL_WHITE_PROB"]
        gray_cutoff = white_cutoff + self.config.at["VINYL_GRAY_PROB"]
        brown_cutoff = gray_cutoff + self.config.at["VINYL_BROWN_PROB"]
        yellow_cutoff = brown_cutoff + self.config.at["VINYL_YELLOW_PROB"]
        blue_cutoff = yellow_cutoff + self.config.at["VINYL_BLUE_PROB"]
        green_cutoff = blue_cutoff + self.config.at["VINYL_GREEN_PROB"]
        if abs(green_cutoff - 1.) > 0.01:
            print("Error: vinyl color probabilities don't add to 1. Check the config file.")
        self.vinyl_color_probs = (("tan", tan_cutoff), ("white", white_cutoff), ("gray", gray_cutoff),\
                ("brown", brown_cutoff), ("yellow", yellow_cutoff), ("blue", blue_cutoff), ("green", green_cutoff))

        # Set the probabilities for materials of houses
        black_cutoff = self.config.at["ROOF_BLACK_PROB"]
        gray_cutoff = black_cutoff + self.config.at["ROOF_GRAY_PROB"]
        white_cutoff = gray_cutoff + self.config.at["ROOF_WHITE_PROB"]
        if abs(white_cutoff - 1.) > 0.01:
            print("Error: roof material probabilities don't add to 1. Check the config file.")
        self.roof_material_probs = (("roof_black", black_cutoff), ("roof_gray", gray_cutoff), ("roof_white", white_cutoff))

    def choose_random(self, name_cutoff_pairs):
        r = self.rng.random()
        for name,cutoff in name_cutoff_pairs:
            if r < cutoff:
                return name
        raise ValueError("Failed to randomly choose a material/color. Verify that the config probabilities add to 1.")

    def random_skyscraper_material(self):
        return self.choose_random(self.skyscraper_material_probs)
    def random_apartments_material(self):
        return self.choose_random(self.apartment_material_probs)
    def random_house_material(self):
        random_material = self.choose_random(self.house_material_probs)
        if random_material == "vinyl":
            return "vinyl_" + self.random_vinyl_color()
        else:
            return random_material
    def random_vinyl_color(self):
        return self.choose_random(self.vinyl_color_probs)
    def random_roof_material(self):
        return self.choose_random(self.roof_material_probs)

    def random_downtown_height(self):
        r = self.rng.random()
        return self.config.at["MIN_DOWNTOWN_HEIGHT"] + r * (self.config.at["MAX_DOWNTOWN_HEIGHT"] - self.config.at["MIN_DOWNTOWN_HEIGHT"])

    def random_apartments_height(self):
        r = self.rng.random()
        return self.config.at["MIN_APARTMENTS_HEIGHT"] + r * (self.config.at["MAX_APARTMENTS_HEIGHT"] - self.config.at["MIN_APARTMENTS_HEIGHT"])

    def random_house_height(self):
        r = self.rng.random()
        return self.config.at["MIN_HOUSE_HEIGHT"] + r * (self.config.at["MAX_HOUSE_HEIGHT"] - self.config.at["MIN_HOUSE_HEIGHT"])

    def filter(self, pwp, downtown_multipolygon, park_multipolygon, residential_multipolygon):
        building_footprint = pwp.polygon
        raw_properties = pwp.properties

        # Check for containment in downtown, residential zones, or parks
        in_downtown = polygon_list_contains(downtown_multipolygon, building_footprint.centroid)
        in_park = polygon_list_contains(park_multipolygon, building_footprint.centroid)
        in_residential = polygon_list_contains(residential_multipolygon, building_footprint.centroid)

        # Keep only the keys that we care about
        filtered = {}
        for key,value in raw_properties.items():
            if key == "height" and value != None:
                # OSM annotators could have put m or M after the number
                value = value.strip('m').strip('M').strip()
                try:
                    _ = float(value)
                    filtered[key] = value
                except ValueError:
                    print("Bad OSM height value %s" % (value))
                    pass
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
            elif key == "osm_id" and value != None:
                filtered[key] = value
            elif key == "building:levels" or key == "levels":
                filtered["levels"] = value

        # Classify the building type. We will use this for estimating the height.
        # Set building=yes if no building tag is present
        if not "building" in filtered:
            filtered["building"] = "yes"
                    # If there is a "building=" property, that could be a clue about the height
        building_type = filtered["building"]
        if building_type == "house" or building_type == "garage":
            # Normal house
            building_classification = BuildingClassification.House
        elif building_type == "apartments" and not in_downtown:
            # Normal apartment complex
            building_classification = BuildingClassification.Apartments
        elif building_type == "apartments" and in_downtown:
            # Apartments in downtown are tall
            building_classification = BuildingClassification.Skyscraper
        elif "height" in filtered and float(filtered["height"]) > self.config.at["MIN_SKYSCRAPER_HEIGHT"]:
            # If we know the height, we can conclude it is a skyscraper
            building_classification = BuildingClassification.Skyscraper
        elif in_downtown and not (in_park or in_residential):
            # Downtown buildings not in parks or residential are tall
            # (residential shouldn't overlap with downtown, but just in case)
            building_classification = BuildingClassification.DowntownMiscellaneous
            guessed_height = self.random_downtown_height()
        elif building_type == "school":
            building_classification = BuildingClassification.School
        elif building_type == "industrial" or\
                building_type == "warehouse" or\
                building_type == "hospital" or\
                building_type == "hotel":
            # Miscellaneous building types that should be taller than houses get the apartments height
            building_classification = BuildingClassification.MidsizedCommercial
        elif in_residential:
            building_classification = BuildingClassification.House
        elif in_park:
            building_classification = BuildingClassification.SmallNonHouse
        else:
            # If we have nothing, assume it's a house
            building_classification = BuildingClassification.House

        # Do the height first, as that can affect the color.
        if not "height" in filtered:
            # If we know the levels, compute the height from that
            height_from_levels = False
            if "levels" in filtered and filtered["levels"]:
                try:
                    levels = int(filtered["levels"])
                    if levels == 1:
                        filtered["height"] = 4
                    else:
                        filtered["height"] = 3 * levels
                        height_from_levels = True
                except ValueError:
                    pass
            # If we didn't set the height from the levels, guess it from the classification
            if not height_from_levels:
                if building_classification == BuildingClassification.House:
                    guessed_height = self.random_house_height()
                elif building_classification == BuildingClassification.Skyscraper:
                    guessed_height = self.random_downtown_height()
                    print("Error: building classified as skyscraper doesn't have height set?")
                elif building_classification == BuildingClassification.Apartments:
                    guessed_height = self.random_apartments_height()
                elif building_classification == BuildingClassification.School:
                    guessed_height = self.random_apartments_height()
                elif building_classification == BuildingClassification.MidsizedCommercial:
                    guessed_height = self.random_apartments_height()
                elif building_classification == BuildingClassification.DowntownMiscellaneous:
                    guessed_height = self.random_downtown_height()
                else:
                    guessed_height = self.random_house_height()
                filtered["height"] = guessed_height

        # Choose a mesh_color.
        osm_acceptable_materials = ("glass", "brick", "concrete", "marble", "plaster", "metal")
        if "building:material" in filtered and filtered["building:material"] in osm_acceptable_materials:
            mesh_color = filtered["building:material"]
        elif float(filtered["height"]) > self.config.at["MIN_SKYSCRAPER_HEIGHT"] or building_classification == BuildingClassification.Skyscraper:
            mesh_color = self.random_skyscraper_material()
        elif building_classification == BuildingClassification.House:
            mesh_color = self.random_house_material()
        elif building_classification == BuildingClassification.Apartments:
            mesh_color = self.random_apartments_material()
        elif building_classification == BuildingClassification.School:
            mesh_color = "brick"
        elif building_classification == BuildingClassification.MidsizedCommercial:
            mesh_color = self.random_apartments_material()
        elif building_classification == BuildingClassification.DowntownMiscellaneous:
            mesh_color = self.random_apartments_material()
        else:
            mesh_color = self.random_apartments_material() 
        filtered["mesh_color"] = mesh_color

        # Choose a roof_color
        filtered["roof_color"] = self.random_roof_material()
        return filtered
