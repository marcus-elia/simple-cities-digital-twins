#!/usr/bin/env python3

import shapely
import utm

def poly_latlon_to_utm(poly_latlon, offset=(0,0)):
    """
    Convert a shapely polygon from lat/lon to UTM. This does both
    the exterior and the holes. If an offset is specified, it is
    added to every point (in UTM).
    """
    # First, don't do anything to an empty polygon
    if len(poly_latlon.exterior.coords) == 0:
        return shapely.Polygon()

    # Get the UTM zone of the first point
    _, _, original_zone, _ = utm.from_latlon(poly_latlon.exterior.coords[0][0], poly_latlon.exterior.coords[0][1])

    # Iterate over the outer boundary and convert it
    outer_boundary_utm = []
    for latlon_point in poly_latlon.exterior.coords:
        # Convert
        x, y, zone, letter = utm.from_latlon(latlon_point[0], latlon_point[1])

        # Check for a UTM zone crossing
        if zone != original_zone:
            print("Polygon crosses from UTM zone %d to %d. Omitting." % (original_zone, zone))
            return shapely.Polygon()

        # If nothing bad happened, add the point to the new polygon
        outer_boundary_utm.append((x + offset[0], y + offset[1]))

    # Do the holes
    holes_utm = []
    for hole in poly_latlon.interiors:
        hole_utm = []
        for latlon_point in hole.coords:
            # Convert
            x, y, zone, letter = utm.from_latlon(latlon_point[0], latlon_point[1])

            # Check for a UTM zone crossing
            if zone != original_zone:
                print("Polygon crosses from UTM zone %d to %d. Omitting." % (original_zone, zone))
                continue

            # If nothing bad happened, add the point to the new polygon
            hole_utm.append((x + offset[0], y + offset[1]))
        holes_utm.append(hole_utm)


    return shapely.Polygon(outer_boundary_utm, holes_utm)

def main():
    print("Main function not implemented")

if __name__ == "__main__":
    main()
