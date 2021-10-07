# API Documentation

A public API is available for testing at [api.opentopodata.org](https://api.opentopodata.org/v1/test-dataset).


## `GET /v1/<dataset_name>`

Reads the elevation from a given dataset.

The dataset name must match one of the options in `config.yaml`. 

Multiple datasets can be provided separated by commas: in this case, for each point, each dataset is queried in order until a non-null elevation is found. For more information see [Multi datasets]('../notes/multiple-datasets.md').

Latitudes and longitudes should be in `EPSG:4326` (also known as WGS-84 format), they will be converted internally to whatever the dataset uses.

### Query Args

* `locations`: Required. Either 
    * `latitutde,longitude` pairs, each separated by a pipe character `|`. Example: `locations=12.5,160.2|-10.6,130`.
    * [Google polyline format](https://developers.google.com/maps/documentation/utilities/polylinealgorithm). Example: `locations=gfo}EtohhU`.
* `samples`: If provided, instead of using `locations` directly, query elevation for `sample` [equally-spaced points](https://www.gpxz.io/blog/sampling-points-on-a-line) along the path specified by `locations`. Example: `samples=5`.
* `interpolation`: How to interpolate between the points in the dataset. Options: `nearest`, `bilinear`, `cubic`. Default: `bilinear`.
* `nodata_value`: What elevation to return if the dataset has a [NODATA](https://desktop.arcgis.com/en/arcmap/10.3/manage-data/raster-and-images/nodata-in-raster-datasets.htm) value at the requested location. Options: `null`, `nan`, or an integer like `-9999`. Default: `null`.
    * The default option `null` makes NODATA indistinguishable from a location outside the dataset bounds. 
    * `NaN` (not a number) values aren't valid in json and will break some clients. The `nan` option was default before version 1.4 and is provided only for backwards compatibility. 


 

### Response

A json object, compatible with the Google Maps Elevation API.

* `status`: Will be `OK` for a successful request, `INVALID_REQUEST` for an input (4xx) error, and `SERVER_ERROR` for anything else (5xx). Required.
* `error`: Description of what went wrong, when `status` isn't `OK`.
* `results`: List of elevations for each location, in same order as input. Only provided for `OK` status.
* `results[].elevation`: Elevation, using units and datum from the dataset. Will be `null` if the given location is outside the dataset bounds. May be `null` for NODATA values depending on the `nodata_value` query argument.
* `results[].location.lat`: Latitude as parsed by Open Topo Data.
* `results[].location.lng`: Longitude as parsed by Open Topo Data.
* `results[].dataset`: The name of the dataset which the returned elevation is from.

Some notes about the elevation value:

* If the raster has an integer data type, the interpolated elevation will be rounded to the nearest integer. This is a limitation of rasterio/gdal.
* If the request location isn't covered by any raster in the dataset, Open Topo Data will return `null`.
* Unless the `nodata_value` parameter is set, a `null` elevation could either mean the location is outside the dataset bounds, or a NODATA within the raster bounds. 



### Example

`GET` <a href="https://api.opentopodata.org/v1/srtm90m?locations=-43.5,172.5|27.6,1.98&interpolation=cubic">api.opentopodata.org/v1/srtm90m?locations=-43.5,172.5|27.6,1.98&interpolation=cubic</a>




```json
{
    "results": [
        {
            "dataset": "srtm90m",
            "elevation": 45,
            "location": {
                "lat": -43.5,
                "lng": 172.5
            }
        },
        {
            "dataset": "srtm90m",
            "elevation": 402,
            "location": {
                "lat": 27.6,
                "lng": 1.98
            }
        }
    ],
    "status": "OK"
}
```

---



## `POST /v1/<dataset_name>`

When querying many locations in a single request, you can run into issues fitting them all in one url. To avoid these issues, you can also send a POST request to `/v1/<dataset_name>`.

The arguments are the same, but must be provided either as json-encoded data or form data instead of url query parameters.

The response is the same.

Other solutions for fitting many points in a URL are polyline encoding and rounding your coordinates.


### Example 

With json:

```python
import requests

url = "https://api.opentopodata.org/v1/srtm90m"
data = {
    "locations": "-43.5,172.5|27.6,1.98",
     "interpolation": "cubic",
}
response = requests.post(url json=data)
```


With form data:


```python
import requests

url = "https://api.opentopodata.org/v1/srtm90m"
data = {
    "locations": "-43.5,172.5|27.6,1.98",
     "interpolation": "cubic",
}
response = requests.post(url data=data)
```

The response is the same as for GET requests:

```json
{
    "results": [
        {
            "dataset": "srtm90m",
            "elevation": 45,
            "location": {
                "lat": -43.5,
                "lng": 172.5
            }
        },
        {
            "dataset": "srtm90m",
            "elevation": 402,
            "location": {
                "lat": 27.6,
                "lng": 1.98
            }
        }
    ],
    "status": "OK"
}
```



---


## `GET /health`


Healthcheck endpoint, for use with load balancing or monitoring.


### Response

A json object.

* `status`: Will be `OK` if the server is running and the config file can be loaded. Otherwise the value will be `SERVER_ERROR`.

The status code is 200 if healthy, otherwise 500.

### Example

`GET` <a href="https://api.opentopodata.org/health">api.opentopodata.org/health</a>

```
{
    "status": "OK"
}
```
