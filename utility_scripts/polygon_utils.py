#!/usr/bin/env python3

import shapely
import utm

class PolygonWithProperties:
    def __init__(self, polygon, properties):
        self.polygon = polygon
        self.properties = properties

def point_lonlat_to_utm(point_lonlat, offset=(0,0)):
    x, y, zone, letter = utm.from_latlon(point_lonlat.y, point_lonlat.x)
    return shapely.Point(x + offset[0], y + offset[1])

def poly_lonlat_to_utm(poly_lonlat, offset=(0,0)):
    """
    Convert a shapely polygon from lat/lon to UTM. This does both
    the exterior and the holes. If an offset is specified, it is
    added to every point (in UTM).
    """
    # First, don't do anything to an empty polygon
    if len(poly_lonlat.exterior.coords) == 0:
        return shapely.Polygon()

    # Get the UTM zone of the first point
    _, _, original_zone, _ = utm.from_latlon(poly_lonlat.exterior.coords[0][1], poly_lonlat.exterior.coords[0][0])

    # Iterate over the outer boundary and convert it
    outer_boundary_utm = []
    for lonlat_point in poly_lonlat.exterior.coords:
        # Convert
        x, y, zone, letter = utm.from_latlon(lonlat_point[1], lonlat_point[0])

        # Check for a UTM zone crossing
        if zone != original_zone:
            print("Polygon crosses from UTM zone %d to %d. Omitting." % (original_zone, zone))
            return shapely.Polygon()

        # If nothing bad happened, add the point to the new polygon
        outer_boundary_utm.append((x + offset[0], y + offset[1]))

    # Do the holes
    holes_utm = []
    for hole in poly_lonlat.interiors:
        hole_utm = []
        for lonlat_point in hole.coords:
            # Convert
            x, y, zone, letter = utm.from_latlon(lonlat_point[1], lonlat_point[0])

            # Check for a UTM zone crossing
            if zone != original_zone:
                print("Polygon crosses from UTM zone %d to %d. Omitting." % (original_zone, zone))
                continue

            # If nothing bad happened, add the point to the new polygon
            hole_utm.append((x + offset[0], y + offset[1]))
        holes_utm.append(hole_utm)


    return shapely.Polygon(outer_boundary_utm, holes_utm)

def polygon_list_contains(polygon_list, point):
    for polygon in polygon_list:
        if polygon.contains(point):
            return True
    return False

def main():
    print("Main function not implemented")

if __name__ == "__main__":
    main()
