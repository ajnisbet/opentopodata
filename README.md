# Open Topo Data


__Documentation__: [www.opentopodata.org](https://www.opentopodata.org)

Open Topo Data is a REST API server for your elevation data. You can self-host with your own dataset or use the free public API. The API is largely compatible with the Google Maps Elevation API.


## Host your own

Install [docker](https://docs.docker.com/install/) and [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) then run:

```bash
git clone git@github.com:ajnisbet/opentopodata.git
cd opentopodata
make build
make run
curl http://localhost:5000/v1/test-dataset?locations=56.35,123.90
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


See the [server docs](https://www.opentopodata.org/server.md) for more about configuration and adding datasets.

---

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

* [ASTER](https://www.opentopodata.org/datasets/aster.md)
* [ETOPO1](https://www.opentopodata.org/datasets/etopo1.md)
* [EU-DEM](https://www.opentopodata.org/datasets/eudem.md)
* [Mapzen](https://www.opentopodata.org/datasets/mapzen.md)
* [NED 10m](https://www.opentopodata.org/datasets/ned.md)
* [NZ DEM](atasets/nzdem.m)
* [SRTM (30m or 90m)](https://www.opentopodata.org/datasets/srtm.md)
* [EMOD Bathymetry](https://www.opentopodata.org/datasets/emod2018.md)
* [GEBCO Bathymetry](https://www.opentopodata.org/datasets/gebco2020.md)



See the [API docs](https://www.opentopodata.org/api.md) for more about request formats and parameters.


---

## Support

Want help getting Open Topo Data running? Send me an email at [andrew@opentopodata.org](mailto:andrew@opentopodata.org).




