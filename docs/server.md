# Open Topo Data Server Documentation


## Getting started with docker

```bash
git clone git@github.com:ajnisbet/opentopodata.git
cd opentopodata
make build
make run
```

This will start a server on `localhost:5000` with a small demo dataset called `test`. Check out the [API docs](api.md) for info about requests and responses.


## Configuration

Open Topo Data is configured by a `config.yaml` file. If that file is missing it will fallback to `example-config.yaml`.

A config might look like this:

```yaml
max_locations_per_request: 100 
datasets:
- name: test
  path: tests/data/datasets/test-etopo1-resampled-1deg/
- name: etopo1
  path: data/etopo1/
```

### Config spec

* `max_locations_per_request`: Requests with more than this many locations will return a 400 error. Default: `100`.
* `datasets[].name`: Dataset name, used in url. Required.
* `datasets[].path`: Path to folder containing the dataset. If the dataset is a single file it must be placed inside a folder. This path is relative to the repository directory inside docker. I suggest placing datasets inside the provided `data` folder, which is mounted in docker by `make run`. Required.



## Adding datasets

An important goal of Open Topo Data is make is easy to add new datasets. The included dataset is very low resolution (about 100km) and is intended only for testing.

Adding a new dataset takes two steps:

1. placing the dataset in the `data` directory
2. adding the path to the dataset in `config.yaml`.

Open Topo Data supports all georeferenced raster formats supported by GDAL (e.g, `.tiff`, `.hgt`, `.jp2`). Additionally, collections of multiple files are supported if they follow the SRTM naming convention (`N30W120.hgt`).


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

Rebuild to enable the new dataset at [localhost:5000/v1/etopo1?locations=27.98,86.92](http://localhost:5000/v1/etopo1?locations=27.98,86.92)

```bash
make build && make run
```




