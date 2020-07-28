import os 
import urllib.request
import json

import pandas

from RemoteData import PullerASF
from RemoteData import PullerSentinel

terms = {
    "polygon": '47.155,-18.1842,47.5822,-18.1842,47.5822,-17.8342,47.155,-17.8342,47.155,-18.1842',
    "platform": "S1",
    "relativeOrbit": '166',
    "processingLevel": "SLC",
}
outdir = ''

puller = PullerASF()
puller.search_for_files(terms, outdir)

files = [
    'https://datapool.asf.alaska.edu/SLC/SA/S1A_IW_SLC__1SDV_20170110T022708_20170110T022735_014763_018098_00D6.zip',
    'https://datapool.asf.alaska.edu/SLC/SA/S1A_IW_SLC__1SDV_20170203T022708_20170203T022735_015113_018B5D_78AA.zip',
]
puller.get_files(files, '') 

files = [
    'https://datapool.asf.alaska.edu/GRD_HD/SA/S1A_IW_GRDH_1SDV_20170110T022709_20170110T022734_014763_018098_EC3B.zip',
    'https://datapool.asf.alaska.edu/GRD_HD/SA/S1A_IW_GRDH_1SDV_20170203T022708_20170203T022733_015113_018B5D_3B05.zip',
]
puller.get_files(files, '/Volumes/EGG-HD/remote_sensing/Madagascar_Lavaka/earthquake') 


puller = PullerSentinel()
files = [
    '\"https://scihub.copernicus.eu/dhus/odata/v1/Products(\'10253b05-ccb5-4c8f-8b24-a75d362592a6\')/$value\"',
]

puller.get_files(files, '') 
