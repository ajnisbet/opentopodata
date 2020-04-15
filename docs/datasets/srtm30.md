# SRTM (30m)

!!! warning "Work in progress!"
    I'm working on improving the install instructions and dataset overview.


## Adding SRTM 30m to Open Topo Data

Make a new folder for the dataset:

```bash
mkdir ./data/srtm30m
```

Download the files from [USGS](https://e4ftl01.cr.usgs.gov/MEASURES/SRTMGL1.003/2000.02.11/) into `./data/srtm30m`. You want the `xxxxxxx.SRTMGL1.hgt.zip` files.

Create a `comfig.yaml` file:

```yaml
datasets:
- name: srtm30m
  path: data/srtm30m/
```

Rebuild to enable the new dataset at [localhost:5000/v1/srtm30m](http://localhost:5000/v1/eudem25m?locations=51.575,-3.220).


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

