from matplotlib import pyplot as plt
import numpy as np
import rasterio

fn = ''
ds = rasterio.open(fn)

out_meta = ds.meta.copy()
array = ds.read()
array[array == np.min(array)] = None

ds = None

# Convert values in the array
array = array * .3048

outpath = ''
with rasterio.open(outpath, "w", **out_meta) as dest:
    dest.write(array)
