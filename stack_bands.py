import glob
import rasterio
from osgeo import gdal

p = 'LC08_L1TP_159073_20160804_20170322_01_T1'
# Full path
g = ''.format(p=p)
file_list = glob.glob(g)

file_list = [
    'MississippiDEM_Resample25.tif',
    'MississippiSlope_Resample25.tif',
    'MississippiAspect_Resample25.tif',
]

# METHOD 1: With Rasterio
# Read metadata of first file
with rasterio.open(file_list[0]) as src0:
    meta = src0.meta

# Update meta to reflect the number of layers
meta.update(count = len(file_list))

# Get Name of the stack
outname = g.split('/')[-2] + '_STACK.tif'
outname = 'MississippiScroll_Stack_Resample25.tif'
# Read each layer and write it to stack
with rasterio.open(outname, 'w', **meta) as dst:
    for id, layer in enumerate(file_list, start=1):
        with rasterio.open(layer) as src1:
            dst.write_band(id, src1.read(1))


# METHOD 2: With GDAL
outname = g.split('/')[-2] + '_STACK.tif'
outname = 'MississippiScroll_Stack.tif'
outvrt = '/vsimem/stacked.vrt' #/vsimem is special in-memory virtual "directory"
tifs = file_list
#or for all tifs in a dir
#import glob
#tifs = glob.glob('dir/*.tif')

outds = gdal.BuildVRT(outvrt, tifs, separate=True)
outds = gdal.Translate(outname, outds)
