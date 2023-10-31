import pyproj
from geojson import MultiPoint, Feature, FeatureCollection, dump
import re


# initiate transformation
bonne_WGS = pyproj.transformer.Transformer.from_pipeline(
    "+proj=pipeline +z=0 +step +proj=bonne +lat_1=51.5 +lon_0=0 +a=6376950.4 +rf=309.65 +pm=4.883882778 +inv +step " \
    "+proj=cart +a=6376950.4 +rf=309.65 +step +proj=helmert +convention=coordinate_frame +exact +x=932.9862 +y=86.2986 " \
    "+z=-197.9356 +rx=2.276813 +ry=1.478043 +rz=4.673555 +s=50.09450 +step +proj=noop +step +proj=cart +ellps=WGS84 +inv " )


#list of lists of points per sheet
features = []

#get coord from csv
with open('../resources/sheet_index_TMK.csv', 'r') as bonnecoords:
    next(bonnecoords)

    for row in bonnecoords:
        parts = re.split(';', row)
        sheet = int(parts[0])
        aNZ = int(parts[1])
        aOW = int(parts[2])
        bNZ = int(parts[3])
        bOW = int(parts[4])
        cNZ = int(parts[5])
        cOW = int(parts[6])
        dNZ = int(parts[7])
        dOW = int(parts[8])

        #transform coordinates
        #  west = negative, oost = positive
        a = bonne_WGS.transform(aOW, aNZ)  # O/W, N/Z
        b = bonne_WGS.transform(bOW, bNZ)
        c = bonne_WGS.transform(cOW, cNZ)
        d = bonne_WGS.transform(dOW, dNZ)
        pointslonlat = MultiPoint((a,b,c,d))#O/W,N/Z

        # add sheet to list
        features.append(Feature(id=sheet, geometry=pointslonlat)) #what properties to add

# write everything to geojson

feature_collection = FeatureCollection(features)
with open('results_wp1/WGS84coordsTMK.geojson', 'w') as f:
    dump(feature_collection, f)