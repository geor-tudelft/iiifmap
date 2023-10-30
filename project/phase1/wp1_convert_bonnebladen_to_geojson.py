import pyproj
from geojson import MultiPoint, Feature, FeatureCollection, dump
import numpy as np

class RowDescription:
    def __init__(self, skip, count):
        self.skip = skip
        self.count = count

# parameters
n_rows = 52
n_cols = 27
n_of_sheets = 776

# make grid
grid = np.zeros((n_rows, n_cols))
# make list of sheets
sheetlist = list(range(1, n_of_sheets + 1))

# print(sheetlist[0])
# give the gaps (starts after sheet number,[list with right amount of zeros]
gaps = [
    (742, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    (733, [0, 0, 0, 0, 0, 0, 0]),
    (730, [0]),
    (720, [0, 0, 0, 0, 0]),
    (704, [0, 0, 0, 0])
]


# description of row per row (number of empty cells on the left, number of filled positions after the empty sheets also counting the gaps as filled)
rdesc = [
    RowDescription(20, 4),
    RowDescription(18, 7),
    RowDescription(14, 11),
    RowDescription(12, 13),
    RowDescription(11, 16),
    RowDescription(11, 16),
    RowDescription(10, 17),
    RowDescription(10, 17),
    RowDescription(9, 18),
    RowDescription(9, 18),
    RowDescription(9, 18),
    RowDescription(9, 18),
    RowDescription(9, 18),
    RowDescription(9, 18),
    RowDescription(9, 17),
    RowDescription(9, 17),
    RowDescription(9, 17),
    RowDescription(9, 17),
    RowDescription(9, 15),
    RowDescription(8, 16),
    RowDescription(8, 18),
    RowDescription(8, 18),
    RowDescription(8, 18),
    RowDescription(7, 19),
    RowDescription(7, 19),
    RowDescription(7, 19),
    RowDescription(6, 19),
    RowDescription(6, 18),
    RowDescription(5, 20),
    RowDescription(4, 21),
    RowDescription(4, 21),
    RowDescription(3, 20),
    RowDescription(2, 17),
    RowDescription(1, 19),
    RowDescription(1, 19),
    RowDescription(0, 20),
    RowDescription(0, 20),
    RowDescription(0, 21),
    RowDescription(0, 21),
    RowDescription(0, 21),
    RowDescription(0, 21),
    RowDescription(0, 20),
    RowDescription(0, 20),
    RowDescription(3, 18),
    RowDescription(17, 3),
    RowDescription(17, 3),
    RowDescription(17, 2),
    RowDescription(16, 4),
    RowDescription(16, 4),
    RowDescription(16, 4),
    RowDescription(16, 4),
    RowDescription(16, 4)
]

# put the gaps in the sheetlist
def insert_position(position, list1, list2):
    return list1[:position] + list2 + list1[position:]

for i in gaps:
    sheetlist = insert_position(i[0], sheetlist, i[1])

#print(sheetlist)

#function to make bonne coordinates from grid position
def bonnecoords(col, row):
    origin = (11, 38)
    dx = 10000
    dy = 6250
    ax = (col - origin[0]) * dx
    ay = (origin[1] - row) * dy
    a = (ax, ay)
    b = (ax + dx, ay)
    c = (ax, ay - dy)
    d = (ax + dx, ay - dy)
    return (a,b,c,d)


#list to collect points per sheet
features = []

#initiate transformation
bonne_WGS = pyproj.transformer.Transformer.from_pipeline(
    "+proj=pipeline +z=0 +step +proj=bonne +lat_1=51.5 +lon_0=0 +a=6376950.4 +rf=309.65 +pm=4.883882778 +inv +step " \
    "+proj=cart +a=6376950.4 +rf=309.65 +step +proj=helmert +convention=coordinate_frame +exact +x=932.9862 +y=86.2986 " \
    "+z=-197.9356 +rx=2.276813 +ry=1.478043 +rz=4.673555 +s=50.09450 +step +proj=noop +step +proj=cart +ellps=WGS84 +inv " )


# fill grid with sheet numbers according to index
sheet = 0
for row in range(n_rows):
    row_descriptor = rdesc[row]
    skip = row_descriptor.skip
    count = row_descriptor.count

    for col in range(n_cols):
        if skip > 0:  # this tile does not exist in this row, skip
            skip -= 1
        else:
            count -= 1
            if count >= 0:
                grid[row, col] = sheetlist[sheet] #give sheet number to the tile
                if sheetlist[sheet] != 0: # this tile has a valid sheet number
                    bc = bonnecoords(col,row) # get the bonne coordinates of the tile
                    a=bc[0]
                    b=bc[1]
                    c=bc[2]
                    d=bc[3]
                    #transform from bonne to WGS84
                    #  west = negative, oost = positive
                    bonnea = bonne_WGS.transform(a[0], a[1])  # O/W, N/Z
                    bonneb = bonne_WGS.transform(b[0], b[1])
                    bonnec = bonne_WGS.transform(c[0], c[1])
                    bonned = bonne_WGS.transform(d[0], d[1])
                    pointslonlat = MultiPoint((bonnea, bonneb, bonnec, bonned))  # O/W,N/Z

                    # add sheet to list
                    features.append(Feature(id=sheetlist[sheet], geometry=pointslonlat))

                    sheet += 1
                else:           # this tile is a gap
                    sheet += 1

#write the list of corner coordinates to geojson
feature_collection = FeatureCollection(features)
with open('results_wp1/WGS84coordsBBlad.geojson', 'w') as f:
    dump(feature_collection, f)



