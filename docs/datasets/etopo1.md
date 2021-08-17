# ETOPO1

## Overview

[ETOPO1](https://www.ngdc.noaa.gov/mgg/global/global.html) is a global elevation dataset developed by NOAA. Unlike many DEM datasets, ETOPO1 contains bathymetry (water depth). There are two variants of the dataset, which vary in how elevation is calculated for the Antartic and Greenland ice sheets: an ice-surface variant, and a bedrock-level variant.

The dataset has a 1 arc-minute resolution, which corresponds to a resolution of about 1.8km at the equator. 

ETOPO1 was made by aggregating many other datasets. The bulk of the land elevation comes from SRTM30, while most bathymetry is sourced from [GEBCO](https://www.gebco.net/data_and_products/gridded_bathymetry_data/). The comprising datasets were normalised to the same vertical datum (sea level) and horizontal datum (WGS84).

## Accuracy

The accuracy of ETOPO1 varies spatially depending on the underlying source data. NOAA estimates the vertical accuracy is no better than 10m.

The quality of ETOPO1 is high: there are no missing values or holes (holes in the SRTM30 source were fixed by hand). Transitions between source datasets are smooth.

<p style="text-align:center; padding: 1rem 0">
  <img src="/img/etopo1.png" alt="ETOPO1 elevation">
  <br>
  <em>Pseudocolour render of ETOPO1 elevation.</em>
</p>




## Adding ETOPO1 to Open Topo Data

Download the grid-registered `.tif` file from [noaa.gov](https://www.ngdc.noaa.gov/mgg/global/) to the `data` directory and unzip. 

```bash
mkdir ./data/etopo1
wget -P ./data/etopo1 https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO1/data/ice_surface/grid_registered/georeferenced_tiff/ETOPO1_Ice_g_geotiff.zip
unzip ./data/etopo1/ETOPO1_Ice_g_geotiff.zip
rm ./data/etopo1/ETOPO1_Ice_g_geotiff.zip
```

The provided `.tif` file doesn't include projection information, which is needed for Open Topo Data. It can be added with GDAL:

```bash
gdal_translate -a_srs EPSG:4326 ./data/etopo1/ETOPO1_Ice_g_geotiff.tif ./data/etopo1/ETOPO1.tif
rm ./data/etopo1/ETOPO1_Ice_g_geotiff.tif
```

Create a file `config.yaml` with the following contents

```yaml
datasets:
- name: etopo1
  path: data/etopo1/
```

Rebuild to enable the new dataset at [localhost:5000/v1/etopo1?locations=27.98,86.92](http://localhost:5000/v1/etopo1?locations=27.98,86.92)

```bash
make build && make run
```

## Public API

The Open Topo Data public API lets you query ETOPO1 for free:

```
curl https://api.opentopodata.org/v1/etopo1?locations=39.747114,-104.996334
```

```json
{
  "results": [
    {
      "elevation": 1596.0, 
      "location": {
        "lat": 39.747114, 
        "lng": -104.996334
      },
      "dataset": "etopo1"
    }
  ], 
  "status": "OK"
}
```

Open Topo Data hosts the ice-elevation version of the dataset (the same as seen in the image above).

## Attribution

[doi:10.7289/V5C8276M](https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ngdc.mgg.dem:316)