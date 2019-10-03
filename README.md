# Open Source Elevation Server

REST api for elevetion datasets.

* Supports single-file rasters, SRTM multi-file datasets.
* Interpolation.

For a hosted version, see [opentopodata.org](https://opentopodata.org).

## Documentation

### Getting started with docker

```bash
git clone git@github.com:ajnisbet/opentopodata.git
cd opentopodata
make build
make run
```

This will start a server on `localhost:5000` with a small demo dataset. Visit [localhost:5000/v1/test?locations=1,1](http://localhost:5000/v1/test?locations=1,1) to see an example of a response.


### Adding datasets

An important goal of opentopodata is to easily add new datasets. The included dataset is very low resolution (1 degree) and is intended only for testing.

Adding a new dataset involves placing the files somewhere accessible by docker (e.g., the `data` folder), then enabling the dataset in the config file.

Opentopodata supports all georeferenced raster formats supported by GDAL (e.g, `.tiff`, `.hgt`, `.jp2`). Additionally, collections of multiple files are supported if they have follow the SRTM naming convention (`N30W120.hgt`).


### Adding ETOPO1

Download the grid-registered `.tif` file from [noaa.gov](https://www.ngdc.noaa.gov/mgg/global/) to the `data` directory and unzip. 

```bash
mkdir ./data/etopo1
wget -P ./data/etopo1 https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO1/data/ice_surface/grid_registered/georeferenced_tiff/ETOPO1_Ice_g_geotiff.zip
unzip ./data/etopo1/ETOPO1_Ice_g_geotiff.zip
rm ./data/etopo1/ETOPO1_Ice_g_geotiff.zip
```

Then create a file `config.yaml` with the following contents
```yaml
datasets:
- name: etopo1
  path: data/etopo1/
```

Rebuild the docker image to enable the new dataset at [localhost:5000/v1/etopo1?locations=27.98,86.92](http://localhost:5000/v1/etopo1?locations=27.98,86.92)
```bash
make build && make run
```

### Adding SRTM

Make a new folder `data/srtm` and download the SRTM files. They should be named like `N35E120.hgt`, though the extension may differ. The config file will look like this
```yaml
datasets:
- name: srtm
  path: data/srtm/
  no_tile_value: 0
  lat_bounds: [-60, 60]
  lon_bounds: [-180, 180]
```

The additional options allow you to exclude tiles that are only water. If a location is passed with in the lat/lon bounds, the value for `no_tile_value` will be returned as the elevation, rather than throwing an error.

### Config options

`max_locations_per_request`: Requests with more than this many locations will return a 400 error.
`datasets[].name`: Dataset name, will be used in url.
`datasets[].path`: Path to folder containing the dataset.


## API documentation

### `GET /v1/<dataset_name>`

Reads the elevation from a given dataset. The dataset must match one of the options in `config.yaml`.

#### Args

* `locations`: List of `latitutde,longitude pairs`. Each pair is separated by `|`. Example: `locations=12.5,160.2|-10.6,130`. Required.
* `interpolation`: How to interpolate between the points in the dataset. Options: `nearest`, `bilinear`, `cubic`. Default: `nearest`.

#### Response

A json object.

* `status`: Will be `OK` for a successful request, `INVALID_REQUEST` for an input error, and `SERVER_ERROR` for a different error. Required.
* `error`: Description of what went wrong, when `status` isn't `OK`.
* `results`: List of elevations for each location, in same order as input. Only provided for `OK` status.
* `results[].latitude`: Latitude as parsed by opentopo.
* `results[].longitude`: Longitude as parsed by opentopo.
* `results[].elevation`: Elevation, using units and datum from the dataset.

#### Example

```
GET /v1/test?locations=-43.52,172.58|57.69,11.98&interpolation=cubic

{  
    "results":[  
        {  
            "elevation":315.8140869140625,
            "lat":-43.52,
            "lon":172.58
        },
        {  
            "elevation":80.2726821899414,
            "lat":57.69,
            "lon":11.98
        }
    ],
    "status":"OK"
}
```

