import pandas
import osr, ogr


def transform_coordinates(pointX, pointY, iEPSG, oEPSG):
    """
    Transforms set of coordinates from one coordinate system to another
    """
    # create a geometry from coordinates
    point = ogr.Geometry(ogr.wkbPoint)
    point.AddPoint(pointX, pointY)
    # create coordinate transformation
    inSpatialRef = osr.SpatialReference()
    srs = inSpatialRef.ImportFromEPSG(iEPSG)

    outSpatialRef = osr.SpatialReference()
    srs = outSpatialRef.ImportFromEPSG(oEPSG)

    coordTransform = osr.CoordinateTransformation(
        inSpatialRef, 
        outSpatialRef
    )

    # transform point
    point.Transform(coordTransform)

    return point.GetX(), point.GetY()


# Transforming the centerline coordinates
iepsg = 26914 
oepsg = 4326
df = pandas.read_csv('riograndeTX_centerline.csv')
df = df[['lon', 'lat']]
xs = []
ys = []
for idx, row in df.iterrows():
    x, y = transform_coordinates(row['lon'], row['lat'], iepsg, oepsg)
    xs.append(x)
    ys.append(y)
df['lat_'] = xs
df['lon_'] = ys

df_lats = df[['lon_', 'lat_']]

df = df_lats.to_csv('RioGrandeCenterlineLats.csv')

# Transforming the bar coordinates
iepsg = 32614 
oepsg = 4326
df = pandas.read_csv('PlatteBarCoords.csv')
df = df.astype('double')
us_xs = []
us_ys = []
ds_xs = []
ds_ys = []
for idx, row in df.iterrows():
    usx, usy = transform_coordinates(
        row['us_easting'], 
        row['us_northing'], 
        iepsg, 
        oepsg
    )
    us_xs.append(usx)
    us_ys.append(usy)

    dsx, dsy = transform_coordinates(
        row['ds_easting'], 
        row['ds_northing'], 
        iepsg, 
        oepsg
    )
    ds_xs.append(dsx)
    ds_ys.append(dsy)

df['us_lat'] = us_xs
df['us_lon'] = us_ys
df['ds_lat'] = ds_xs
df['ds_lon'] = ds_ys

df_lats = df[[
    'us_lat',
    'us_lon',
    'ds_lat',
    'ds_lon'
]]

df = df_lats.to_csv('PlatteBarCoordsLats.csv')

