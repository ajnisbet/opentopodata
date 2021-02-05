# Mapzen

Mapzen's terrain tiles are a global DEM dataset, including bathymetry. The dataset is an assimilation of [multiple open datasets](https://github.com/tilezen/joerd/blob/master/docs/data-sources.md). 

## Coverage and resolution

Data is provided at a 1 arc-second resolution, corresponding to a resolution of about 30m at the equator. However, parts of the dataset are interpolated from lower-resolution datasets. The resolution of the source datasets is shown below:


<p style="text-align:center; padding: 1rem 0">
  <img src="/img/mapzen-footprints.png" alt="Mapzen source datasets.">
  <br>
  <em>Resolution of Mapzen source datasets. Source: <a href="https://github.com/tilezen/joerd/blob/master/docs/data-sources.md">github.com/tilezen/joerd</a>.</em>
</p>



## Adding Mapzen to Open Topo Data

Make a new folder for the dataset:

```bash
mkdir ./data/mapzen
```

Download the tiles from AWS. I found it easiest to use the [aws cli](https://pypi.org/project/awscli/):

```bash
aws s3 cp --no-sign-request --recursive s3://elevation-tiles-prod/skadi ./data/mapzen
```

Extract all the `.hgt` files. Create a `config.yaml` file:

```yaml
datasets:
- name: mapzen
  path: data/mapzen/
```

Rebuild to enable the new dataset at [localhost:5000/v1/mapzen](http://localhost:5000/v1/mapzen?locations=51.575,-3.220).

```bash
make build && make run
```

!!! tip "Extra performance"
    `.hgt` files are extremely large. You'll get a large space reduction with little read penalty by converting to a compressed geotiff:

    ```
    gdal_translate -co COMPRESS=DEFLATE -co PREDICTOR=2 {hgt_filename} {tif_filename}
    ```


## Public API

The Open Topo Data public API lets you query the Mapzen dataset for free:

```
curl https://api.opentopodata.org/v1/mapzen?locations=57.688709,11.976404
```

```json
{
  "results": [
    {
      "elevation": 55.0, 
      "location": {
        "lat": 57.688709, 
        "lng": 11.976404
      },
      "dataset": "mapzen"
    }
  ], 
  "status": "OK"
}
```


The public API uses Version 1.1 of Mapzen, downloaded from AWS on May 2020