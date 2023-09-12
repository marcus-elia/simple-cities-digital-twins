#!/usr/bin/env python3

import shapely

from tile_id import *

def create_tile_svg(tile, color_polygons_pairs, output_filepath):
    f = open(output_filepath, 'w')

    # Determine the bounds and write the header
    x_min, y_min = tile.sw_corner()
    x_max = x_min + TileID.TILE_SIZE
    y_max = y_min + TileID.TILE_SIZE
    f.write('<svg viewBox="%d %d %d %d" xmlns="http://www.w3.org/2000/svg">\n' % (0, 0, TileID.TILE_SIZE, TileID.TILE_SIZE))

    for color, shapely_polygons in color_polygons_pairs:
        for shapely_polygon in shapely_polygons:
            f.write('\t<path\n')
            f.write('\t\tfill-rule="evenodd"\n')
            f.write('\t\tstroke="%s"\n' % (color))
            f.write('\t\tfill="%s"\n' % (color))
            vertices_string = '\t\td="M '
            for x,y in shapely_polygon.exterior.coords:
                vertices_string += '%f,%f ' % (x - x_min, TileID.TILE_SIZE - (y - y_min))
            vertices_string += 'z\n'
            for hole in shapely_polygon.interiors:
                vertices_string += 'M '
                for x,y in hole.coords:
                    vertices_string += '%f,%f ' % (x - x_min, TileID.TILE_SIZE - (y - y_min))
                vertices_string += 'z\n'
            vertices_string += '" />\n'
            f.write(vertices_string)

    f.write('</svg>')
