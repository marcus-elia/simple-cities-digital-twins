#!/usr/bin/env python3

# Utility functions for tile ids.

import argparse
import numpy as np
import shapely
import utm

class TileID:
    # Every tile is 1000m x 1000m
    TILE_SIZE = 1000

    def __init__(self, arg1, arg2, zone=-1):
        """
        The arguments can be either lat, lon or utm_x, utm_y, zone.
        """
        if zone == -1:
            lat = arg1
            lon = arg2
            x, y, zone, letter = utm.from_latlon(lat, lon)
        else:
            x = arg1
            y = arg2
        self.i = int(np.floor(x / TileID.TILE_SIZE))
        self.j = int(np.floor(y / TileID.TILE_SIZE))
        self.zone = zone

    def center_utm(self):
        return ((self.i + 0.5) * TileID.TILE_SIZE, (self.j + 0.5) * TileID.TILE_SIZE, self.zone)

    def center_lat_lon(self):
        x, y, zone = self.center_utm()
        return utm.to_latlon(x, y, zone)

    def sw_corner(self):
        x, y, zone = self.center_utm()
        return (x - TileID.TILE_SIZE / 2, y - TileID.TILE_SIZE / 2)

    def polygon(self):
        size = TileID.TILE_SIZE
        return shapely.Polygon(((self.i * size, self.j * size),\
                ((self.i + 1) * size, self.j * size),\
                ((self.i + 1) * size, (self.j + 1) * size), \
                (self.i * size, (self.j + 1) * size), \
                (self.i * size, self.j * size)))

    def tile_indices_to_object(i, j, zone):
        """
        Since I couldn't hack a third type of constructor into the
        constructor, this is what I came up with. A static method
        that returns an object.
        """
        size = TileID.TILE_SIZE
        x = (i + 0.5) * size
        y = (j + 0.5) * size
        return TileID(x, y, zone)

def main():
    parser = argparse.ArgumentParser(description="Print out the information of the tile containing the given lat/lon.")
    parser.add_argument('lat') 
    parser.add_argument('lon')

    args = parser.parse_args()
    lat = float(args.lat.strip(','))
    lon = float(args.lon)
    tile_id = TileID(lat, lon)
    print("lat, lon = %f, %f" % (lat, lon))
    print("tile id = (%d, %d, %d)" % (tile_id.i, tile_id.j, tile_id.zone))
    print("tile center = (%f, %f)" % (tile_id.center_utm()[0], tile_id.center_utm()[1]))
    print(tile_id.polygon())

if __name__ == "__main__":
    main()
