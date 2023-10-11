import os
import ee
import fiona
from shapely.geometry import Polygon, LineString, mapping, MultiPolygon
import numpy as np

# ee.Authenticate()
ee.Initialize()


def get_watershed(poly):
    sheds = ee.FeatureCollection("WWF/HydroSHEDS/v1/Basins/hybas_7")
    # Get sheds in the area of your polygon
    ds = ee.FeatureCollection(
        "WWF/HydroSHEDS/v1/Basins/hybas_7"
    ).filterBounds(
        poly
    )

    # Get basin ids of the polygon sheds
    basin_ids = []
    for feature in ds.getInfo()['features']:
        basin_id = feature['properties']['HYBAS_ID']
        basin_ids.append(basin_id)

    upstreams = basin_ids

    # Find all the upstream basin ids
    new_upstreams = [1]
    while len(new_upstreams):
        new_upstreams = []
        for upstream in upstreams:
            shed_filter = sheds.filter(
                # ee.Filter.eq('NEXT_DOWN', upstream)
                ee.Filter.eq('NEXT_DOWN', upstream)
            )
            upstreams = []
            for feature in shed_filter.getInfo()['features']:
                new_upstreams.append(feature['properties']['HYBAS_ID'])

        upstreams = new_upstreams
        basin_ids += new_upstreams

    # Make sure there are no duplicates
    basin_ids = list(set(basin_ids))

    # Filter dataset for just the identified sheds
    shed_polys = []
    for basin_id in basin_ids:
        shed = sheds.filter(
            ee.Filter.eq('HYBAS_ID', basin_id)
        ).getInfo()['features'][0]['geometry']

        if shed['type'] == 'MultiPolygon':
            for coords in shed['coordinates']:
                shed_polys.append(
                    ee.Feature(ee.Geometry.Polygon(coords))
                )
        else:
            shed_polys.append(
                ee.Feature(ee.Geometry.Polygon(shed['coordinates']))
            )

    # Merge em
    fcShed = ee.FeatureCollection(shed_polys)

    return fcShed.union(1).geometry()


polygon_path = '/Users/greenberg/Documents/PHD/Writing/ComparitiveMobility/Figures/Bermejo/BermejoDownstream.gpkg'
out_root = '/Users/greenberg/Documents/PHD/Writing/ComparitiveMobility/Figures/Bermejo'
polygon_name = polygon_path.split('/')[-1].split('.')[0]
with fiona.open(polygon_path, layer=polygon_name) as layer:
    for feature in layer:
        # river = feature['properties']['River']
        geom = feature['geometry']
        poly = ee.Geometry.Polygon(
            geom['coordinates'],
        )
        watershed = get_watershed(poly)

        save = np.array(watershed.getInfo()['coordinates'])
        if len(save.shape) == 1:
            polys = []
            for shape in save:
                polys.append(Polygon(np.array(shape)))
        else:
            save_watershed = np.squeeze(
                np.array(watershed.getInfo()['coordinates']),
                0
            )
            polys = [Polygon(save_watershed)]

        schema = {
            'geometry': 'Polygon',
            'properties': {'id': 'int'},
        }
        out = os.path.join(out_root, f'Bermejoi_watershed.shp')
        with fiona.open(out, 'w', 'ESRI Shapefile', schema) as c:
           ## If there are multiple geometries, put the "for" loop here
           for i, poly in enumerate(polys):
               c.write({
                   'geometry': mapping(poly),
                   'properties': {'id': i},
                })                   
