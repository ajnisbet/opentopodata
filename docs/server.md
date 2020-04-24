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



Instructions are provided for adding the various datasets used in the public API:

* [SRTM (30m or 90m)](/datasets/srtm/)
* [NED 10m](/datasets/ned/)
* [EU-DEM](/datasets/eudem/)
* [ETOPO1](/datasets/etopo1/)
* [ASTER](/datasets/aster/)
