# Code to find the pixel and line location in an Xarray image for a given set of geographic coordinates
# This works even if the Xarray raster is rotated
# Adapted from https://github.com/ornldaac/above-airborne-avirisng-python/blob/master/above-airborne-avirisng-python.ipynb and from code by Alexey Shiklomanov

import xarray as xr
import math 
import affine
from osgeo import ogr,osr, gdal
from matplotlib import pyplot as plt

## Set up data

dat = xr.open_dataset("reference://",engine="zarr",backend_kwargs={
    "consolidated": False,
    "storage_options": {"fo":"FILEPATH-TO-JSON"}
})

# get rfl_meta, a dict containing all the ENVI header metadata.
rfl_meta = dat.attrs

# get individual attributes
proj_name = rfl_meta["map info"][0]
ref_x = int(rfl_meta["map info"][1])
ref_y = int(rfl_meta["map info"][2])
px_easting = float(rfl_meta["map info"][3])
px_northing = float(rfl_meta["map info"][4])
x_size = float(rfl_meta["map info"][5])
y_size = float(rfl_meta["map info"][6])
utm_zone = rfl_meta["map info"][7]
north_south = rfl_meta["map info"][8]
datum = rfl_meta["map info"][9]
units = rfl_meta["map info"][10].lstrip("units=")
rotation_deg = float(rfl_meta["map info"][11].lstrip("rotation="))
rotation = (math.pi / 180) * rotation_deg

GT = (
    px_easting,
    math.cos(rotation) * x_size,
    math.sin(rotation) * x_size,
    px_northing,
    math.sin(rotation)*y_size,
    -math.cos(rotation)*y_size
)

## Transform coordinates to UTM

#starting with lat/long
point = ogr.CreateGeometryFromWkt("POINT (43.09885 -89.40545)")
ll_coordinates = str(point.GetX())+", "+str(point.GetY())

# establish transformation
source = osr.SpatialReference()
source.ImportFromEPSG(4326) #lat/long CRS

target = osr.SpatialReference()
target.ImportFromEPSG(32615) # CRS for WGS 84 / UTM 15N because the image is in zone 15 - change this to match your image

transform = osr.CoordinateTransformation(source, target)
point.Transform(transform)
print(point)

# get the x and y UTM coordinates for the pixel
x,y = point.GetX(), point.GetY()

## Transform from UTM to pixel location 

# affine forward transform
affine_transform = affine.Affine.from_gdal(*GT)     

# invert transform
inverse_transform = ~affine_transform 
                                
# apply to x,y coordinates
px, py = inverse_transform * (x, y)                                    

# get new x,y as integers
px, py = int(px + 0.5), int(py + 0.5)                                  

## Show results
# print the three coordinates (UTM, geographic, image)
print( "\n".join(["The pixel's UTM coordinates (x,y): "+"\t"*4+str((x,y)),
       " are equal to geographic coordinates (lng,lat): \t"+str(ll_coordinates),
       " and fall within image coordinates (pixel,line):\t"+str((px,py))]) )
