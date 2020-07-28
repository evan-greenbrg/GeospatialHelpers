import datetime
import glob

import os
from osgeo import gdal
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
# from mpl_toolkits.basemap import Basemap
import numpy

import numpy              ##Matrix calculations


def create_vrt(basename, file_folder, outroot):
    """
    Creates simplified vrt files in the vrt directory
    Once all vrt files are made run:
        !gdaltindex -f KML ProductBoundaries.kml VRT/*.unw.vrt
    This is a unix command to build index from list of files

    Edited from isce-2-docs notebook
    """

    #Create VRT folder if it doesn't exist
    if not os.path.isdir(outroot + 'VRT'):
        os.makedirs(outroot + 'VRT')

    # Get the file paths for the phase and correlation files
    unwsrc = basename + file_folder + 'filt_topophase.unw.geo.vrt'
    corsrc = basename + file_folder + 'phsig.cor.geo.vrt'

    # Get the dates for the master and slave files
    master_slave = basename.split('/')[-2].split('_')
    masterdate = master_slave[0]
    slavedate = master_slave[1]

    # Simplified filenames to work with
    unwdest = os.path.join(
        outroot, 
        'VRT', 
        masterdate + '-' + slavedate + '.unw.vrt'
    )
    cordest = os.path.join(
        outroot, 
        'VRT', 
        masterdate + '-' + slavedate + '.cor.vrt'
    )

    ##Create simple file names - ensuring nodata value is set
    gdal.Translate(unwdest, unwsrc, format='VRT', bandList=[2], noData=0.)
    gdal.Translate(cordest, corsrc, format='VRT', bandList=[1], noData=0.)


    ###Let's create amplitude layer for visualization
    ampfile = unwdest.replace('unw', 'amp')
    gdal.Translate(ampfile, unwsrc, bandList=[1], noData=0.)


def set_up_dirs(root):
    insarDir  =  os.path.join(root, 'VRT')
    alignedDir = os.path.join(root, 'aligned_insar')
    giantDir = os.path.join(root, 'GIAnT')

    ##Check if output directories already exist. If not create them
    if not os.path.isdir(alignedDir):
        os.makedirs(alignedDir)
        
    if not os.path.isdir(giantDir):
        os.makedirs(giantDir)

    return true


def stringToDate(instr):
    '''
    This is a simple function that will allow us to convert yyyymmdd 
    to a python datetime object
    '''
    return datetime.datetime.strptime(instr, '%Y%m%d')


def latLonToLinePixel(infile, latlon):
    '''
    This is a simple function that will read in lat, lon coordinates
    and return corresponding line, pixel coordinates in a geocoded file
    '''
    
    # Open, read and close file
    ds = gdal.Open(infile, gdal.GA_ReadOnly) 
    trans = ds.GetGeoTransform()
    ds = None                                 

#    This is an excerpt from GDAL Documentation 
#    (http://www.gdal.org/gdal_tutorial.html)
#    For Geocoded images that are oriented North Top and West Left
#    adfGeoTransform[0] /* top left x */
#    adfGeoTransform[1] /* w-e pixel resolution */ 
#    adfGeoTransform[2] /* 0 */
#    adfGeoTransform[3] /* top left y */
#    adfGeoTransform[4] /* 0 */
#    adfGeoTransform[5] /* n-s pixel resolution (negative value) */
    
    line = int(numpy.round((latlon[0] - trans[3])/trans[5]))
    pixel = int(numpy.round((latlon[1] - trans[0])/trans[1]))
    
    return (line, pixel)


def alignImageToRegion(infile, outfile, virtual=True, band=1):
    '''
    Align an input image to a specified region (snwe).

    If virtual is False, output is in VRT format which is a simple XML 
    and uses no extra disk space.

    If virtual is True, output is in ENVI binary format which 
    creates new files with subsets.

    Additional options for regridding data, if products are on 
    different grid sizes can also be accommodated.
    '''
    
    ##Pick output format based on virtual flag
    if virtual:
        fmt = 'VRT'
    else:
        fmt = 'ENVI'
    
    #Set up options for gdal_translate command
    opts = gdal.TranslateOptions(
        format=fmt, 
        bandList=[band],
    )

    #Open input file
    ds = gdal.Open(infile, gdal.GA_ReadOnly)
    
    #Translate
    gdal.Translate(outfile, ds, options=opts)
    
    #Close input file
    ds = None

    return True


def gather_data(insarDir):

    # First list all subfolders of insarDir
    ifgDirs = glob.glob(insarDir + '/*unw.vrt')
    print('Number of identified interferogram folders: {0}'.format(
        len(ifgDirs)
    ))

    # Variable to store interferogram information
    ifgList = []
    dateList = []

    # Loop over interferograms
    for ifg in ifgDirs:
        subdirName = os.path.basename(ifg)
        master, slave = subdirName.split('.')[0].split('-')
        
        # Start gathering data about the pair
        data = {
            'masterDate' : master,
            'slaveDate'  : slave,
            'folder'     : os.path.abspath(os.path.dirname(ifg))
        }
                
        # Load some of the sensor data in as constants.
        data['sensor'] = 'S1'
        data['bperp'] = 0.0
        data['btemp'] = ((stringToDate(master) - stringToDate(slave)).days)
        
        # Build list of IFG data
        if True:
            dateList.append(master)
            dateList.append(slave)
            ifgList.append(data)

    ###Determine unique dates
    dateList = sorted(list(set(dateList)))
    print('Number of unique SAR scenes: {0}'.format(len(dateList)))
    print('Number of interferograms retained: {0}'.format(len(ifgList)))
    
    return ifgList, dateList


def connected_network(ifgList, dateList):
    """
    Generates plot showing connectivity between interferograms
    """
    Jmat = numpy.zeros((len(ifgList), len(dateList)))
    for ind, ifg in enumerate(ifgList):
        Jmat[ind, dateList.index( ifg['masterDate'])] = 1
        Jmat[ind, dateList.index( ifg['slaveDate'])] = -1
        
    print(
        'Number of connected components in interferogram network: {0}'.format(
            len(dateList) - numpy.linalg.matrix_rank(Jmat)
        )
    )

    ##Sort ifg list by dates.
    ifgList = sorted(ifgList, key = lambda x: x['slaveDate'])

    ###Make a quick network coverage plot
    plt.figure('Coverage plot', figsize=(10,6))

    for ind, ifg in enumerate(ifgList):
        plt.plot(
            [
                stringToDate(ifg['masterDate']), 
                stringToDate(ifg['slaveDate'])
            ], 
            [
                ind + 1, 
                ind + 1
            ]
        )

    plt.xlabel('Acquisition time')
    plt.ylabel('Interferogram number')
    # Can be replaced with plt.savefig('coverage.pdf', format='pdf')
    plt.show()   
    

def align_imagery(ifgList, alignedDir):
    for ifg in ifgList:     ##For each interferogram
        # Align unwrapped phase
        alignImageToRegion(
            os.path.join(
                ifg['folder'], 
                ifg['masterDate'] + '-' + ifg['slaveDate'] + '.unw.vrt'
            ),
            os.path.join(
                alignedDir, 
                ifg['masterDate'] + '_' + ifg['slaveDate'] + '_unw.vrt'
            ),
            regionOfInterest
            band=1
        )
        
        # Align coherence
        alignImageToRegion(
            os.path.join(
                ifg['folder'], 
                ifg['masterDate'] + '-' + ifg['slaveDate'] + '.cor.vrt'
            ),
            os.path.join(
                alignedDir, 
                ifg['masterDate'] + '_' + ifg['slaveDate'] + '_cor.vrt'
            ),
            regionOfInterest
            band=1
        )

    return True


def write_ifg_list(ifgList, root):
    with open( os.path.join(root, 'GIAnT', 'ifg.list'), 'w') as fid:
        for ifg in ifgList:
            fid.write(
                '{masterDate}  {slaveDate}  {bperp}  {sensor}\n'.format(
                    **ifg
                )
            )


def write_roi_pac(root, alignedDir, ifgList, giandDir, fn):
    # Until I can get better values:
    heading_deg = -12.0
    wavelength = 0.031228381041666666
    centerline_utc = 43200
    fn = 'example.rsc'

    ##We will use one of the aligned output files to get dimensions
    exampleAlignedFile = os.path.join(
        root,
        alignedDir, 
        ifgList[0]['masterDate'] + '_' + ifgList[0]['slaveDate'] + '_unw.vrt'
    )
    ds = gdal.Open(exampleAlignedFile, gdal.GA_ReadOnly)
    nLines = ds.RasterYSize
    nPixels = ds.RasterXSize

    print(nLines, nPixels, 'SIZE')
    trans = ds.GetGeoTransform()
    ds = None

    with open(os.path.join(root, giantDir, fn), 'w') as fid:
        fid.write('WIDTH     {0}\n'.format(nPixels))
        fid.write('FILE_LENGTH    {0}\n'.format(nLines))
        
        ##These fields can be obtained from metadata in each product when available
        fid.write('HEADING_DEG    {0}\n'.format(heading_deg))
        fid.write('WAVELENGTH    {0}\n'.format(wavelength))
        fid.write('CENTER_LINE_UTC    {0}\n'.format(centerline_utc))

    return nPixels, nLines


def write_userfn(root, alignedDir, giantDir):
    relDir = os.path.relpath(
        os.path.join(root, alignedDir),
        os.path.join(root, giantDir)
    )
    userfnTemplate = """
    #!/usr/bin/env python
    import os 

    def makefnames(dates1, dates2, sensor):
        dirname = '{0}'
        root = os.path.join(dirname, dates1+'_'+dates2)
        unwname = root+'_unw.vrt'
        corname = root+'_cor.vrt'
        return unwname, corname
    """

    with open(os.path.join(root, giantDir, 'userfn.py'), 'w') as fid:
        fid.write(userfnTemplate.format(relDir))


def write_prepdataxml(root, giantDir, exampleAlignedFile, 
                      refRegionCenter, refRegionSize, nPixels, nLines):
    prepdataTemplate = """
    #!/usr/bin/env python

    import tsinsar as ts
    import argparse
    import numpy as np

    if __name__ == '__main__':

        ######Prepare the data.xml
        g = ts.TSXML('data')
        g.prepare_data_xml(
            'example.rsc', 
            proc='RPAC',
            xlim=[0,{0}], 
            ylim=[0, {1}],
            rxlim = [{2},{3}], 
            rylim=[{4},{5}],
            latfile='', 
            lonfile='', 
            hgtfile='',
            inc = 21., 
            cohth=0.3, 
            chgendian='False',
            unwfmt='GRD', 
            corfmt='GRD'
        )
        g.writexml('data.xml')
    """

    refLine, refPixel = latLonToLinePixel(
        exampleAlignedFile, 
        refRegionCenter
    )

    with open( os.path.join(root, giantDir, 'prepdataxml.py'), 'w') as fid:
        fid.write(prepdataTemplate.format(
            nPixels, 
            nLines,
            refPixel-refRegionSize[1]//2, 
            refPixel+refRegionSize[1]//2, 
            refLine-refRegionSize[0]//2, 
            refLine+refRegionSize[0]//2
        ))


def write_prepsbasxml(root, giantDir, ifgList):
    prepsbasTemplate  = """
    #!/usr/bin/env python

    import tsinsar as ts
    import argparse
    import numpy as np

    if __name__ == '__main__':
        g = ts.TSXML('params')
        g. prepare_sbas_xml(nvalid = {0}, 
                            netramp=False,   ##No deramping requested
                            atmos='',        ##No troposphere correction requested
                            demerr = False,  ##No dem error correction requested
                            uwcheck=False,   ##For future, not implemented yet
                            regu=True,       ##For Mints. Not relevant for tutorial
                            filt = 0.05)     ##Filter length in years
        g.writexml('sbas.xml')
    """

    with open( os.path.join(root, giantDir, 'prepsbasxml.py'), 'w') as fid:
        fid.write(prepsbasTemplate.format( int(0.6*len(ifgList))))


# SNWE ocnvention
regionOfInterest = [-18.15111, -17.791944, 47.561667, 48.4641667]
# Reference region is a region of little deformation
refRegionSize    = [5,5]
refRegionCenter  = [-18.1118, 47.2800]

# SCRATCH
pairs = [
    '20160204_20160228',
    '20160228_20160323',
    '20160323_20160416',
    '20160416_20160510',
    '20160510_20160603',
    '20160603_20160721',
    '20160721_20160814',
    '20160814_20161001',
    '20161001_20161025',
]

for pair in pairs:
    outroot = ''
    basename = ''.format(pair)
    file_folder = 'merged/'
    create_vrt(basename, file_folder, outroot)

