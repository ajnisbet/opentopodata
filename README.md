# Open Topo Data



Open Topo Data is a REST API server for your elevation data.


```
curl http://localhost:5000/v1/test-dataset?locations=56,123
```

```json
{
    "results": [{
        "elevation": 815.0,
        "location": {
            "lat": 56.0,
            "lng": 123.0
        }
    }],
    "status": "OK"
}
```


You can self-host with your own dataset or use the [free public API](https://www.opentopodata.org) which is configured with a number of open elevation datasets. The API is largely compatible with the Google Maps Elevation API.

__Documentation__: [www.opentopodata.org](https://www.opentopodata.org)



## Installation

Install [docker](https://docs.docker.com/install/) and [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) then run:

```bash
git clone https://github.com/ajnisbet/opentopodata.git
cd opentopodata
make build
make run
```

This will start an Open Topo Data server on `http://localhost:5000/`.


Open Topo Data supports a wide range of raster file formats and tiling schemes, including most of those used by popular open elevation datasets. See the [server docs](https://www.opentopodata.org/server/) for more about configuration and adding datasets.



## Usage

Open Topo Data has a single endpoint: a point query endpoint that returns the elevation at a single point or a series of points.


```
curl http://localhost:5000/v1/test-dataset?locations=56,123
```

```json
{
    "results": [{
        "elevation": 815.0,
        "location": {
            "lat": 56.0,
            "lng": 123.0
        }
    }],
    "status": "OK"
}
```

The interpolation algorithm used can be configured as a request parameter, and locations can also be provided in Google Polyline format.


See the [API docs](https://www.opentopodata.org/api/) for more about request and response formats.



## Public API

I'm hosting a free public API at [api.opentopodata.org](https://api.opentopodata.org).


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

The following datasets are available on the public API:

* [ASTER](https://www.opentopodata.org/datasets/aster/)
* [ETOPO1](https://www.opentopodata.org/datasets/etopo1/)
* [EU-DEM](https://www.opentopodata.org/datasets/eudem/)
* [Mapzen](https://www.opentopodata.org/datasets/mapzen/)
* [NED 10m](https://www.opentopodata.org/datasets/ned/)
* [NZ DEM](https://www.opentopodata.org/datasets/nzdem/)
* [SRTM (30m or 90m)](https://www.opentopodata.org/datasets/srtm/)
* [EMOD Bathymetry](https://www.opentopodata.org/datasets/emod2018/)
* [GEBCO Bathymetry](https://www.opentopodata.org/datasets/gebco2020/)




## License
[MIT](https://choosealicense.com/licenses/mit/)


## Support

Want help getting Open Topo Data running? Send me an email at [andrew@opentopodata.org](mailto:andrew@opentopodata.org).
