# ASTER

## Overview

The Advanced Spaceborne Thermal Emission and Reflection Radiometer ([ASTER](https://asterweb.jpl.nasa.gov/gdem.asp)) global DEM dataset is a joint effort between the Ministry of Economy, Trade, and Industry (METI) of Japan and the National Aeronautics and Space Administration (NASA) of the US.

ASTER GDEM is a 1 arc-second resolution, corresponding to a resolution of about 30m at the equator. Coverage is provided from from -83 to 83 degrees latitude.


<p style="text-align:center; padding: 1rem 0">
  <img src="/img/aster-colourised.png" alt="ASTER elevation map">
  <br>
  <em>Render of ASTER elevation. <a href="https://asterweb.jpl.nasa.gov/gdem.asp">Source.</a></em>
</p>

## Adding 30m ASTER to Open Topo Data

Make a new folder for the dataset:

```bash
mkdir ./data/aster30m
```

Download the files from [USGS](https://e4ftl01.cr.usgs.gov/) into `./data/aster30m` . Extract the zip archives keeping the `_dem.tif` files and removing the `_num.tif` files.

To make downloading a bit easier, here's a list of the 22,912 URLs: [aster30m_urls.txt](/datasets/aster30m_urls.txt).

Create a `config.yaml` file:

```yaml
datasets:
- name: aster30m
  path: data/aster30m/
```

Rebuild to enable the new dataset at [localhost:5000/v1/aster30m](http://localhost:5000/v1/aster30m?locations=51.575,-3.220).

```bash
make build && make run
```


## Public API

The Open Topo Data public API lets you query ASTER GDEM 30m for free:

```
curl https://api.opentopodata.org/v1/aster30m?locations=57.688709,11.976404
```

```json
{
  "results": [
    {
      "elevation": 45.0, 
      "location": {
        "lat": 57.688709, 
        "lng": 11.976404
      },
      "dataset": "aster30m"
    }
  ], 
  "status": "OK"
}
```

The Public API used version 3 of the DEM (GDEM 003).