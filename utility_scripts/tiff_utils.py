#!/usr/bin/env python3

from geotiff import GeoTiff
import numpy as np

class GeoTiffInterpolater:
    """
    This class opens a GeoTiff file and has access methods to
    perform bilinear interpolation. The CRS of the tif must
    be the same UTM zone that the city is in.
    """
    def __init__(self, filepath):
        self.geo_tiff = GeoTiff(filepath)
        self.min_x, self.min_y = self.geo_tiff.tif_bBox[0]
        self.max_x, self.max_y = self.geo_tiff.tif_bBox[1]
        self.array = np.array(self.geo_tiff.read())
        self.cols, self.rows = self.array.shape
        self.res_x = (self.max_x - self.min_x) / self.cols
        self.res_y = (self.max_y - self.min_y) / self.rows

    def interpolate(self, x, y):
        i_below = int((x - self.min_x) / self.res_x)
        i_above = i_below + 1
        j_below = int((y - self.min_y) / self.res_y)
        j_above = j_below + 1
        print("interpolating between indices %d %d %d %d" % (i_below, j_below, i_above, j_above))

        # If out of bounds, return 0
        if i_below < 0 or i_above >= self.cols or j_below < 0 or j_above >= self.rows:
            print("OOB interpolate")
            return 0

        # Access the 4 values we are interpolating between
        sw = self.array[i_below, j_below]
        se = self.array[i_above, j_below]
        ne = self.array[i_above, j_above]
        nw = self.array[i_below, j_above]
        print("values are %f %f %f %f" % (sw, se, ne, nw))

        # Determine how far the point is from the raster grid
        dist_x_below = abs(x - (self.min_x + self.res_x * i_below))
        dist_x_above = abs(x - (self.min_x + self.res_x * i_above))
        dist_y_below = abs(y - (self.min_y + self.res_y * j_below))
        dist_y_above = abs(y - (self.min_y + self.res_y * j_above))

        # Interpolate along the x-axis
        interpolated_x_above = nw * dist_x_below / abs(self.res_x) + ne * dist_x_above / abs(self.res_x)
        interpolated_x_below = sw * dist_x_below / abs(self.res_x) + se * dist_x_above / abs(self.res_x)

        # Interpolate between those two values along the y-axis
        return interpolated_x_above * dist_y_above / abs(self.res_y) + interpolated_x_below * dist_y_below / abs(self.res_y)
