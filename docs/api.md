# API Documentation

A public API is available for testing at [api.opentopodata.org](https://api.opentopodata.org/v1/test-dataset).

## `GET /v1/<dataset_name>`

Reads the elevation from a given dataset. The dataset must match one of the options in `config.yaml`.

### Args

* `locations`: Required. Either 
    * `latitutde,longitude` pairs, each separated by a pipe character `|`. Example: `locations=12.5,160.2|-10.6,130`. Or, 
    * [Google polyline format](https://developers.google.com/maps/documentation/utilities/polylinealgorithm). Example: `locations=gfo}EtohhU`.
* `interpolation`: How to interpolate between the points in the dataset. Options: `nearest`, `bilinear`, `cubic`. Default: `nearest`.

### Response

A json object, compatible with the Google Maps Elevation API.

* `status`: Will be `OK` for a successful request, `INVALID_REQUEST` for an input error, and `SERVER_ERROR` for a different error. Required.
* `error`: Description of what went wrong, when `status` isn't `OK`.
* `results`: List of elevations for each location, in same order as input. Only provided for `OK` status.
* `results[].elevation`: Elevation, using units and datum from the dataset.
* `results[].location.lat`: Latitude as parsed by opentopodata.
* `results[].location.lng`: Longitude as parsed by opentopodata.

### Example

`GET` <a href="https://api.opentopodata.org/v1/srtm90m?locations=-43.5,172.5|27.6,1.98&interpolation=cubic">api.opentopodata.org/v1/srtm90m?locations=-43.5,172.5|27.6,1.98&interpolation=cubic</a>




```json
{
    "results": [
        {
            "elevation": 45,
            "location": {
                "lat": -43.5,
                "lng": 172.5
            }
        },
        {
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
