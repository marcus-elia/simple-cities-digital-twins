#!/usr/bin/env python3

# A command line tool to convert between UTM and LL.

import argparse
import utm

def parse_latlon_string(latlon_string):
    lat,lon = latlon_string.split(',')
    return (float(lat.strip()), float(lon.strip()))

def main():
    parser = argparse.ArgumentParser(description="Convert UTM to Lat/Lon.")
    parser.add_argument('lat') 
    parser.add_argument('lon')

    args = parser.parse_args()
    lat = float(args.lat.strip(','))
    lon = float(args.lon)
    print(utm.from_latlon(lat, lon))

if __name__ == "__main__":
    main()
