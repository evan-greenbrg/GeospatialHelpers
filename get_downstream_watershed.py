import os
import ee
import fiona
from shapely.geometry import Polygon, LineString, mapping, MultiPolygon
import numpy as np

# ee.Authenticate()
ee.Initialize()


def get_watershed(poly):
    sheds = ee.FeatureCollection("WWF/HydroSHEDS/v1/Basins/hybas_5")
    # Get sheds in the area of your polygon
    ds = ee.FeatureCollection(
        "WWF/HydroSHEDS/v1/Basins/hybas_5"
    ).filterBounds(
        poly
    )

    # Get basin ids of the polygon sheds
    basin_ids = []
    for basin in ds.getInfo()['features']:
        main_bas = basin['properties']['MAIN_BAS']
        shed_filter = sheds.filter(
            ee.Filter.eq('MAIN_BAS', main_bas)
        )
        for feature in shed_filter.getInfo()['features']:
            basin_ids.append(feature['properties']['HYBAS_ID'])

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

    return fcShed.union().geometry()


polygon_path = '/Users/greenberg/Documents/PHD/Writing/ComparitiveMobility/Figures/Bermejo/BermejoDownstream.gpkg'
out_root = '/Users/greenberg/Documents/PHD/Writing/ComparitiveMobility/Figures/Bermejo'
polygon_name = polygon_path.split('/')[-1].split('.')[0]
rivers = []
finished_rivers = []
with fiona.open(polygon_path, layer=polygon_name) as layer:
    for feature in layer:
        # river = feature['properties']['River']
        # if river == 'Shyok_River':
        #     continue
        # if river == 'Indus_River':
        #     continue
        # rivers.append(river)
        # print(river)
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
        elif len(save.shape) == 3:
            save_watershed = np.squeeze(
                np.array(watershed.getInfo()['coordinates']),
                0
            )
            polys = [Polygon(save_watershed)]
        else:
            save = save[:,0]
            polys = []
            for shape in save:
                polys.append(Polygon(np.array(shape)))

        schema = {
            'geometry': 'Polygon',
            'properties': {'id': 'int'},
        }
        out = os.path.join(out_root, f'Bermejo_watershed.shp')
        with fiona.open(out, 'w', 'ESRI Shapefile', schema) as c:
           ## If there are multiple geometries, put the "for" loop here
           for i, poly in enumerate(polys):
               c.write({
                   'geometry': mapping(poly),
                   'properties': {'id': i},
                })                   
