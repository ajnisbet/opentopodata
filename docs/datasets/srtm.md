# SRTM



## Overview

[SRTM](https://lpdaac.usgs.gov/products/srtmgl1v003/) is a near-global elevation dataset, with coverage from -60 to 60 degrees latitude. 

SRTM comes in multiple resolutions. The resolution is 1 arc-second, which corresponds to a resolution of about 30m at the equator. The 3 arc-second (90m) version is also frequently used.

## Coverage

SRTM has coverage from -60 to 60 degrees latitude. The dataset is released in 1 degree tiles. Ocean areas covered by a tile have an elevation of 0m. Open Topo Data will return `null` for locations not covered by a tile.


<p style="text-align:center; padding: 1rem 0">
  <img src="/img/srtm-coverage.png" alt="SRTM coverage">
  <br>
  <em>SRTM coverage (green area).</em>
</p>



## Adding 30m SRTM to Open Topo Data

Make a new folder for the dataset:

```bash
mkdir ./data/srtm30m
```

Download the files from [USGS](https://e4ftl01.cr.usgs.gov/MEASURES/) into `./data/srtm30m`. You want the `xxxxxxx.SRTMGL1.hgt.zip` files. To make downloading a bit easier, here's a list of the 14,297 URLs: [srtm30m_urls.txt](/datasets/srtm30m_urls.txt).

Create a `comfig.yaml` file:

```yaml
datasets:
- name: srtm30m
  path: data/srtm30m/
```

Rebuild to enable the new dataset at [localhost:5000/v1/srtm30m](http://localhost:5000/v1/srtm30m?locations=51.575,-3.220).

```bash
make build && make run
```

!!! note "Extra performance"
    `.hgt.zip` files are extremely slow for random reads. I got a 10x read speedup and a 10% size reduction from converting to a compressed geotiff:

    ```bash
    gdal_translate -co COMPRESS=DEFLATE -co PREDICTOR=2 {hgtzip_filename} {tif_filename}
    ```

## Adding 90m SRTM to Open Topo Data

The process is the same as for 30m. The dataset is hosted on USGS [here](https://e4ftl01.cr.usgs.gov/MEASURES/SRTMGL3.003/2000.02.11/), and a list of the tile urls is here: [srtm90m_urls.txt](/datasets/srtm90m_urls.txt).

## Public API

The Open Topo Data public API lets you query SRTM 30m for free:

```
curl https://api.opentopodata.org/v1/srtm30m?locations=57.688709,11.976404
```

```json
{
  "results": [
    {
      "elevation": 55.0, 
      "location": {
        "lat": 57.688709, 
        "lng": 11.976404
      }
    }
  ], 
  "status": "OK"
}
```

as well as SRTM 90m:

```
curl https://api.opentopodata.org/v1/srtm90m?locations=57.688709,11.976404
```

```json
{
  "results": [
    {
      "elevation": 55.0, 
      "location": {
        "lat": 57.688709, 
        "lng": 11.976404
      }
    }
  ], 
  "status": "OK"
}
```


The public API uses Version 3 of SRTM for both resolutions.