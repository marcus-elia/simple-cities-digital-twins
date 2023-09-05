#!/usr/bin/env python3

# Utility functions for tile ids.

import argparse
import shapely
import utm

class TileID:
    # Every tile is 100m x 100m
    TILE_SIZE = 1000

    def __init__(self, arg1, arg2, zone=-1):
        if zone == -1:
            lat = arg1
            lon = arg2
            x, y, zone, letter = utm.from_latlon(lat, lon)
        else:
            x = arg1
            y = arg2
        self.i = x // TileID.TILE_SIZE
        self.j = y // TileID.TILE_SIZE
        self.zone = zone

    def centerUTM(self):
        return ((self.i + 0.5) * TileID.TILE_SIZE, (self.j + 0.5) * TileID.TILE_SIZE, self.zone)

    def centerLatLon(self):
        x, y, zone = self.centerUTM()
        return utm.to_latlon(x, y, zone)

    def polygon(self):
        size = TileID.TILE_SIZE
        return shapely.Polygon(((self.i * size, self.j * size),\
                ((self.i + 1) * size, self.j * size),\
                ((self.i + 1) * size, (self.j + 1) * size), \
                (self.i * size, (self.j + 1) * size), \
                (self.i * size, self.j * size)))

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
    print("tile center = (%f, %f)" % (tile_id.centerUTM()[0], tile_id.centerUTM()[1]))
    print(tile_id.polygon())

if __name__ == "__main__":
    main()
