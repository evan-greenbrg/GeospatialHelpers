from osgeo import ogr, gdal
import subprocess


InputVector = 'North_site.shp'
OutputImage = 'North_site.tif'

RefImage = 'dem_wgs84.TIF'

gdalformat = 'GTiff'
datatype = gdal.GDT_Byte
burnVal = 1 #value for the output image pixels
##########################################################
# Get projection info from reference image
Image = gdal.Open(RefImage, gdal.GA_ReadOnly)

# Open Shapefile
Shapefile = ogr.Open(InputVector)
Shapefile_layer = Shapefile.GetLayer()

# Rasterise
print("Rasterising shapefile...")
Output = gdal.GetDriverByName(
    gdalformat
).Create(
    OutputImage, 
    Image.RasterXSize, 
    Image.RasterYSize, 
    1, 
    datatype, 
    options=['COMPRESS=DEFLATE']
)
Output.SetProjection(Image.GetProjectionRef())
Output.SetGeoTransform(Image.GetGeoTransform()) 

# Write data to band 1
Band = Output.GetRasterBand(1)
Band.SetNoDataValue(0)
gdal.RasterizeLayer(Output, [1], Shapefile_layer, burn_values=[burnVal])

# Close datasets
Band = None
Output = None
Image = None
Shapefile = None

# Build image overviews
subprocess.call(
    "gdaladdo --config COMPRESS_OVERVIEW DEFLATE "+OutputImage+" 2 4 8 16 32 64", 
shell=True
)
print("Done.")

ds = rasterio.open(OutputImage)
dsar = ds.read(1)
ref = rasterio.open(RefImage)
meta = ref.meta.copy()

ref = gdal.Open(RefImage)
meta = ref.GetMetadata()

