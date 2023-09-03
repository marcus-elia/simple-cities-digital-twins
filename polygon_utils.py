#!/usr/bin/env python3

import shapely
import utm

def poly_latlon_to_utm(poly_latlon):
    # First, don't do anything to an empty polygon
    if len(poly_latlon.exterior.coords) == 0:
        return shapely.Polygon()

    # Get the UTM zone of the first point
    _, _, original_zone, _ = utm.from_latlon(poly_latlon.exterior.coords[0][0], poly_latlon.exterior.coords[0][1])

    # Iterate over the points and convert them
    utm_coords = []
    for latlon_point in poly_latlon.exterior.coords:
        # Convert
        x, y, zone, letter = utm.from_latlon(latlon_point[0], latlon_point[1])

        # Check for a UTM zone crossing
        if zone != original_zone:
            print("Polygon crosses from UTM zone %d to %d. Omitting." % (original_zone, zone))
            return shapely.Polygon()

        # If nothing bad happened, add the point to the new polygon
        utm_coords.append((x, y))
    return shapely.Polygon(utm_coords)

def main():
    print("Main function not implemented")

if __name__ == "__main__":
    main()
