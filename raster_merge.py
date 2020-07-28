import rasterio
from rasterio.merge import merge
import glob
import os


def files_to_mosaic(fps, outpath, write=True):
    src_files_to_mosaic = []
    for fp in fps:
        src = rasterio.open(fp)
        src_files_to_mosaic.append(src)

    mosaic, out_trans = merge(src_files_to_mosaic)

    out_meta = src.meta.copy()
    out_meta.update(
        {
            "driver": "GTiff",
            "height": mosaic.shape[1],
            "width": mosaic.shape[2],
            "transform": out_trans
        }
    )

    if write:
        with rasterio.open(outpath, "w", **out_meta) as dest:
            dest.write(mosaic)

    return mosaic


rootdir = ''
search_c = 'USGS*.tif'
q = os.path.join(rootdir, search_c)
fps = glob.glob(q)

outdir = ''
temp = 'tombigbee_26914.tif'
outpath = os.path.join(outdir, temp)

files_to_mosaic(fps, outpath)


