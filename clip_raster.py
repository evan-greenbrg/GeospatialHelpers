import argparse
import glob
import os
import json

from osgeo import gdal
import ogr
import osr
import rasterio
import pandas
import numpy as np
from rasterio.mask import mask
from rasterio.merge import merge
from shapely import geometry
from shapely.geometry import box
import geopandas as gpd
from fiona.crs import from_epsg
from pycrs import parse as crsparse


def rename_path(input_path):
    path_sp = input_path.split('/')
    name_li = path_sp[-1].split('.')
    name_temp = name_li[0] + '_clip'
    name_li[0] = name_temp
    name = '.'.join(name_li)
    path_sp[-1] = name

    return '/'.join(path_sp)


def bounding_coordinates(ds):
    """
    Finds bounding coordinates from a geoTif file
    """
    width = ds.RasterXSize
    height = ds.RasterYSize
    gt = ds.GetGeoTransform()
    minx = gt[0]
    miny = gt[3] + width*gt[4] + height*gt[5]
    maxx = gt[0] + width*gt[1] + height*gt[2]
    maxy = gt[3]

    return minx, miny, maxx, maxy


def clip_raster(ipath, mask_path):
    """
    Clips raster file based on bounding box coordinates
    """
    opath = rename_path(ipath)
    data = rasterio.open(ipath)

    dsinput = gdal.Open(ipath)
    dsmask = gdal.Open(mask_path)

    mask_srs = osr.SpatialReference(wkt=dsmask.GetProjection())
    maskEPSG = int(mask_srs.GetAttrValue('AUTHORITY', 1))

    input_srs = osr.SpatialReference(wkt=dsinput.GetProjection())
    inputEPSG = int(input_srs.GetAttrValue('AUTHORITY', 1))

    minx0, miny0, maxx0, maxy0 = bounding_coordinates(dsmask)
    bbox = box(minx0, miny0, maxx0, maxy0)
    geo = gpd.GeoDataFrame(
        {'geometry': bbox},
        index=[0],
        crs=from_epsg(maskEPSG)
    )
    geo = geo.to_crs(crs=inputEPSG)
    coords = [json.loads(geo.to_json())['features'][0]['geometry']]

    out_img, out_transform = mask(
        dataset=data,
        shapes=coords,
        crop=True
    )

    out_meta = data.meta.copy()
    epsg_code = int(data.crs.data['init'][5:])

    try:
        out_meta.update(
            {
                "driver": "GTiff",
                "height": out_img.shape[1],
                "width": out_img.shape[2],
                "transform": out_transform,
                "crs": crsparse.from_epsg_code(epsg_code).to_proj4()
            }
        )
    except:
        print('Using manual proj string')
        proj_ = '+proj=stere +lat_0=90 +lat_ts=71 +lon_0=0 +k=1 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs'
        out_meta.update(
            {
                "driver": "GTiff",
                "height": out_img.shape[1],
                "width": out_img.shape[2],
                "transform": out_transform,
                "crs": proj_ 
            }
        )
 


    with rasterio.open(opath, "w", **out_meta) as dest:
        dest.write(out_img)

    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('ipath', metavar='i', type=str)
    parser.add_argument('mask_path', metavar='m', type=str)
    args = parser.parse_args()

    clip_raster(args.ipath, args.mask_path)
