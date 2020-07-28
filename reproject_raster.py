import argparse

import numpy as np
import rasterio
from rasterio import Affine as A
import os

from rasterio.warp import reproject, Resampling
from osgeo import gdal


def reproject(ipath, to_epsg):
    pathc = ipath.split('/')
    iname = pathc.pop(-1)

    oname = iname.split('.')
    oname[0] = '{0}_{1}'.format(oname[0], to_epsg)
    oname = '.'.join(oname)

    opath = '/'.join(pathc + [oname])

    input_raster = gdal.Open(ipath)

    gdal.Warp(opath ,input_raster,dstSRS='EPSG:{}'.format(to_epsg))

    return True


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('ipath', metavar='i', type=str)
    parser.add_argument('epsg', metavar='e', type=int)
    args = parser.parse_args()

    reproject(args.ipath, args.epsg)

