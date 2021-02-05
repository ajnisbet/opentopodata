# Open Topo Data Server Documentation


## Getting started

The easiest way to run Open Topo Data is with Docker. [Install docker](https://docs.docker.com/install/) then run the following commands:

```bash
git clone https://github.com/ajnisbet/opentopodata.git
cd opentopodata
make build
make run
```

This will start a server on `localhost:5000` with a small demo dataset called `test-dataset`. Check out the [API docs](api.md) for info about the format of requests and responses.


## Getting started on Windows

On Windows you'll probably need to run the build and run commands without make:

```bash
git clone https://github.com/ajnisbet/opentopodata.git
cd opentopodata
docker build --tag opentopodata --file docker/Dockerfile . 
docker run --rm -it --volume C:/path/to/opentopodata/data:/app/data:ro -p 5000:5000 opentopodata sh -c "/usr/bin/supervisord -c /app/docker/supervisord.conf"
```

For more details see [this note on windows support](notes/windows-support.md).


## Dataset support

Open Topo Data supports all georeferenced raster formats supported by GDAL (e.g, `.tiff`, `.hgt`, `.jp2`).

Datasets can take one of two formats:

* A single raster file.
* A collection of square raster tiles which follow the SRTM naming convention: the file is named for the lower left corner. So a file named `N30W120.tiff` would span from 30 to 31 degrees latitude, and -120 to -119 degrees longitude. By default tiles are 1° by 1° and the coordinates are in WGS84, but this can be configured.


If your dataset consists of multiple files that aren't on a nice grid, you can create a `.vrt` file pointing to the files that Open Topo Data will treat as a single-file dataset. For an example of this process, see the documentation for configuring [EMODnet](datasets/emod2018.md).


## Configuration

Open Topo Data is configured by a `config.yaml` file. If that file is missing it will look for `example-config.yaml` instead.

A config might look like:

```yaml
max_locations_per_request: 100 
access_control_allow_origin: '*'
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
* `access_control_allow_origin`: Value for the `Access-Control-Allow-Origin` CORS header. Set to `*` or a domain to allow in-browser requests from a different origin. Set to `null` to send no `Access-Control-Allow-Origin` header. Default: `null`.
* `datasets[].name`: Dataset name, used in url. Required.
* `datasets[].path`: Path to folder containing the dataset. If the dataset is a single file it must be placed inside a folder. This path is relative to the repository directory inside docker. I suggest placing datasets inside the provided `data` folder, which is mounted in docker by `make run`. Files can be nested arbitrarily inside the dataset path. Required.
* `datasets[].filename_epsg`: For tiled datasets, the projection of the filename coordinates. The default value is `4326`, which is latitude/longitude with the [WGS84 datum](https://spatialreference.org/ref/epsg/wgs-84/).
* `datasets[].filename_tile_size`: For tiled datasets, how large each square tile is in the units of `filename_epsg`. For example, a lat,lon location of `38.2,121.2` would lie in the tile `N38W121` for a tile size of 1, but lie in `N35W120` for a tile size of 5. For non-integer tile sizes like `2.5`, specify them as a string to avoid floating point parsing issues: `"2.5"`. Default: `1`.
* `datasets[].wgs84_bounds.left`: Leftmost (westmost) longitude of the dataset, in WGS84. Used as a performance optimisation for [Multi datasets]('../notes/multiple-datasets.md'). Default: `-180`.
* `datasets[].wgs84_bounds.right`: Rightmost (eastmost) longitude of the dataset. Default: `180`.
* `datasets[].wgs84_bounds.bottom`: Bottommost (southmost) latitude of the dataset. Default: `-90`.
* `datasets[].wgs84_bounds.top`: Topmost (northmost) latitude of the dataset. Default: `90`.
* `datasets[].child_datasets[]`: A list of names of other datasets. Querying this MultiDataset will check each dataset in `child_datasets` in order until a non-null elevation is found. For more information see [Multi datasets]('../notes/multiple-datasets.md'). 


## Adding datasets

An important goal of Open Topo Data is make is easy to add new datasets. The included dataset is very low resolution (about 100km) and is intended only for testing.

Adding a new dataset takes two steps:

1. placing the dataset in the `data` directory
2. adding the path to the dataset in `config.yaml`.



Instructions are provided for adding the various datasets used in the public API:


* [ASTER](datasets/aster.md)
* [ETOPO1](datasets/etopo1.md)
* [EU-DEM](datasets/eudem.md)
* [Mapzen](datasets/mapzen.md)
* [NED 10m](datasets/ned.md)
* [NZ DEM](datasets/nzdem.md)
* [SRTM (30m or 90m)](datasets/srtm.md)
* [EMOD Bathymetry](datasets/emod2018.md)
* [GEBCO Bathymetry](datasets/gebco2020.md)
* [BKG Germany (200m)](datasets/bkg.md)




