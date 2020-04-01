# Open Topo Data Server Documentation


## Getting started

The easiest way to run Open Topo Data is with Docker. [Install docker](https://docs.docker.com/install/) then run the following commands:

```bash
git clone git@github.com:ajnisbet/opentopodata.git
cd opentopodata
make build
make run
```

This will start a server on `localhost:5000` with a small demo dataset called `test-dataset`. Check out the [API docs](api.md) for info about requests and responses.

## Dataset support

Open Topo Data supports all georeferenced raster formats supported by GDAL (e.g, `.tiff`, `.hgt`, `.jp2`).

Datasets can take one of two formats:

* A single raster file.
* A collection of square raster tiles which follow the SRTM naming convention: the file is named for the lower left corner. So a file named `N30W120.tiff` would span from 30 to 31 degrees latitude, and -120 to -119 degrees longitude. By default tiles are 1° by 1° and the coordinates are in WGS84, but this can be configured.


## Configuration

Open Topo Data is configured by a `config.yaml` file. If that file is missing it will fallback to `example-config.yaml`.

A config might look like:

```yaml
max_locations_per_request: 100 
datasets:
- name: etopo1
  path: data/etopo1/
- name: srtm90m
  path: data/srtm-90m-v3/
  filename_epsg: 4326
  filename_tile_size: 1
```

corresponding to a directory structure:

```
opentopodata
|
└───data
    |
    ├───etopo1
    |   |
    |   └───etopo1-dem.geotiff
    |
    └───srtm-90m-v3
        |
        ├───N00E000.hgt 
        ├───N00E001.hgt 
        ├───N00E002.hgt 
        ├───etc...
```


which would expose `localhost:5000/v1/etopo1` and `localhost:5000/v1/srtm90m`.

### Config spec

* `max_locations_per_request`: Requests with more than this many locations will return a 400 error. Default: `100`.
* `datasets[].name`: Dataset name, used in url. Required.
* `datasets[].path`: Path to folder containing the dataset. If the dataset is a single file it must be placed inside a folder. This path is relative to the repository directory inside docker. I suggest placing datasets inside the provided `data` folder, which is mounted in docker by `make run`. Files can be nested arbitrarily inside the dataset path. Required.
* `datasets[].filename_epsg`: For tiled datasets, the projection of the filename coordinates. The default value is `4326`, which is latitude/longitude with the WGS84 datum.
* `datasets[].filename_tile_size`: For tiled datasets, how large each square tile is, in the units of `filename_epsg`. For example, a lat,lon location of `38.2,121.2` would lie in the tile `N38W121` for a tile size of 1, but lie in `N35W120` for a tile size of 5. Default: `1`.


## Adding datasets

An important goal of Open Topo Data is make is easy to add new datasets. The included dataset is very low resolution (about 100km) and is intended only for testing.

Adding a new dataset takes two steps:

1. placing the dataset in the `data` directory
2. adding the path to the dataset in `config.yaml`.



### Adding ETOPO1

Download the grid-registered `.tif` file from [noaa.gov](https://www.ngdc.noaa.gov/mgg/global/) to the `data` directory and unzip. 

```bash
mkdir ./data/etopo1
wget -P ./data/etopo1 https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO1/data/ice_surface/grid_registered/georeferenced_tiff/ETOPO1_Ice_g_geotiff.zip
unzip ./data/etopo1/ETOPO1_Ice_g_geotiff.zip
rm ./data/etopo1/ETOPO1_Ice_g_geotiff.zip
```

Create a file `config.yaml` with the following contents

```yaml
datasets:
- name: etopo1
  path: data/etopo1/
```

The provided `.TIF` file doesn't include projection information, which is needed for Open Topo Data. This metadata can be added with GDAL:

```bash
gdal_translate -a_srs EPSG:4326 ./data/etopo1/ETOPO1_Ice_g_geotiff.tif ./data/etopo1/ETOPO1.tif
rm ./data/etopo1/ETOPO1_Ice_g_geotiff.tif
```

Rebuild to enable the new dataset at [localhost:5000/v1/etopo1?locations=27.98,86.92](http://localhost:5000/v1/etopo1?locations=27.98,86.92)

```bash
make build && make run
```

## Adding EU-DEM


Make a new folder for the dataset:

```bash
mkdir ./data/eudem
```

Download the dataset from [Copernicus](https://land.copernicus.eu/imagery-in-situ/eu-dem/eu-dem-v1.1?tab=download). There are 27 files. Unzip them and move all the `.TIF` files into the data folder (you don't need the `.aux.xml`, `.ovr`, or `.TFw` files). 

Your data folder should now contain only 27 TIF files:

```bash
ls ./data/eudem

# eu_dem_v11_E00N20.TIF
# eu_dem_v11_E10N00.TIF
# eu_dem_v11_E10N10.TIF
# ...
```

Next, Open Topo Data needs the filenames to match the SRTM format: the filename should be the coordinates of the lower-left corner, in NS-WE order. For EU-DEM this means two changes to the filenames:

* swapping the order of the northing and easting,
* and adding 5 trailing zeroes to each coordinate that Copernicus removed for simplicity.

So `eu_dem_v11_E00N20.TIF` becomes `N2000000E0000000.tif`. Here's a Python script to do the transformation, but it might be just as easy to do by hand:

```python
from glob import glob
import os
import re

old_pattern = '.data/eudem/eu_dem_v11_E*N*.TIF'
old_paths = list(glob(old_pattern))
print('Found {} files'.format(len(old_paths)))

for old_path in old_paths:
    folder = os.path.dirname(old_path)
    old_filename = os.path.basename(old_path)

    # Extract north and east coords, pad with zeroes.
    res = re.search(r'(E\d\d)(N\d\d)', old_filename)
    easting, northing = res.groups()
    northing = northing + '00000'
    easting = easting + '00000'

    # Rename in place.
    new_filename = '{}{}.tif'.format(northing, easting)
    new_path = os.path.join(folder, new_filename)
    os.rename(old_path, new_path)
```

You should have the following 27 files:

```
N0000000E1000000.tif
N1000000E1000000.tif
N1000000E2000000.tif
N1000000E3000000.tif
N1000000E4000000.tif
N1000000E5000000.tif
N1000000E6000000.tif
N2000000E0000000.tif
N2000000E1000000.tif
N2000000E2000000.tif
N2000000E3000000.tif
N2000000E4000000.tif
N2000000E5000000.tif
N2000000E6000000.tif
N2000000E7000000.tif
N3000000E2000000.tif
N3000000E3000000.tif
N3000000E4000000.tif
N3000000E5000000.tif
N4000000E2000000.tif
N4000000E3000000.tif
N4000000E4000000.tif
N4000000E5000000.tif
N5000000E2000000.tif
N5000000E3000000.tif
N5000000E4000000.tif
N5000000E5000000.tif
```

Create a config file:

```yaml
datasets:
- name: eudem25m
  path: data/eudem/
  filename_epsg: 3035
  filename_tile_size: 1000000
```

Rebuild to enable the new dataset at [localhost:5000/v1/eudem25m?locations=51.575,-3.220](http://localhost:5000/v1/eudem25m?locations=51.575,-3.220).


```bash
make build && make run
```