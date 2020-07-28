#!/bin/bash

# Path to img file
P=""
find $P -type f -name "*.img" -exec sh -c 'gdal_translate -of GTiff "$1" "${1%.img}.tif"' _ {} \;


gdal_translate -of GTiff "ibwc11-1m_2904394.img" "ibwc11-1m_2904394.tif"
