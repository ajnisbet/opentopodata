<h1 style="text-align:center">Open Topo Data</h1>

<p style="text-align:center">
  <img width="378" hight="153" src="/img/elevation-land.png" alt="Open Topo Data">
</p>

<p style="text-align:center">
	<strong>Open Topo Data</strong> is an elevation API.<br> <a href="#host-your-own">Host your own</a> or use the free <a href="#public-api">public API</a>.
</p>

---

Open Topo Data is a REST API server for your elevation data.

```
curl https://api.opentopodata.org/v1/test-dataset?locations=56,123
```

```json
{
    "results": [{
        "elevation": 815.0,
        "location": {
            "lat": 56.0,
            "lng": 123.0
        },
        "dataset": "test-dataset"
    }],
    "status": "OK"
}
```

You can [self-host](server.md) with your own dataset or use the [free public API](#public-api) which is configured with a number of open elevation datasets. The API is largely compatible with the Google Maps Elevation API.

---

## Host your own

Install [docker](https://docs.docker.com/install/) and [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) then run:

```bash
git clone https://github.com/ajnisbet/opentopodata.git
cd opentopodata
make build
make run
```

This will start an Open Topo Data server on `http://localhost:5000/`.


Open Topo Data supports a wide range of raster file formats and tiling schemes, including most of those used by popular open elevation datasets.

See the [server docs](server.md) for more about configuration and adding datasets.

---

## Usage

Open Topo Data has a single endpoint: a point query endpoint that returns the elevation at a single point or a series of points.


```
curl https://api.opentopodata.org/v1/test-dataset?locations=56.35,123.90
```

```json
{
    "results": [{
        "elevation": 815.0,
        "location": {
            "lat": 56.0,
            "lng": 123.0
        },
        "dataset": "test-dataset"
    }],
    "status": "OK"
}
```

The interpolation algorithm used can be configured as a request parameter, and locations can also be provided in Google Polyline format.


See the [API docs](api.md) for more about request and response formats.

---

## Public API

I'm hosting a free public API at [api.opentopodata.org](https://api.opentopodata.org).

To keep the public API sustainable some limitations are applied.

* Max 100 locations per request.
* Max 1 call per second.
* Max 1000 calls per day.


The following datasets are available on the public API, with elevation shown for downtown Denver, Colorado (39.7471,&nbsp;-104.9963).


<table>
	<thead>
		<tr>
			<th>Dataset name</th>
			<th>Resolution</th>
			<th>Extent</th>
			<th>Source</th>
			<th>API link (Denver, CO)</th>
		</tr>
	</thead>
	<tbody >
		<tr>
			<td><a href="/datasets/nzdem/">nzdem8m</a></td>
			<td>8&nbsp;m</td>
			<td>New Zealand.</td>
			<td><a href="https://data.linz.govt.nz/layer/51768-nz-8m-digital-elevation-model-2012/">LINZ</a></td>
			<td><a href="https://api.opentopodata.org/v1/nzdem?locations=39.747114,-104.996334"><em>Not in dataset bounds</em></a></td>
		</tr>
		<tr>
			<td><a href="/datasets/ned/">ned10m</a></td>
			<td>~10&nbsp;m</td>
			<td>Continental USA, Hawaii, parts of Alaska.</td>
			<td><a href="https://www.sciencebase.gov/catalog/item/4f70aa9fe4b058caae3f8de5">USGS</a></td>
			<td><a href="https://api.opentopodata.org/v1/ned10m?locations=39.747114,-104.996334">1590&nbsp;m</a></td>
		</tr>
		<tr>
			<td><a href="/datasets/eudem/">eudem25m</a></td>
			<td>25&nbsp;m</td>
			<td>Europe.</td>
			<td><a href="https://www.eea.europa.eu/data-and-maps/data/copernicus-land-monitoring-service-eu-dem">EEA</a></td>
			<td><a href="https://api.opentopodata.org/v1/eudem25m?locations=39.747114,-104.996334"><em>Not in dataset bounds</em></a></td>
		</tr>
		<tr>
			<td><a href="/datasets/mapzen/">mapzen</a></td>
			<td>~30&nbsp;m</td>
			<td>Global, inluding bathymetry.</td>
			<td><a href="https://github.com/tilezen/joerd/tree/master/docs">Mapzen</a></td>
			<td><a href="https://api.opentopodata.org/v1/mapzen?locations=39.747114,-104.996334">1590&nbsp;m</a></td>
		</tr>
		<tr>
			<td><a href="/datasets/aster/">aster30m</a></td>
			<td>~30&nbsp;m</td>
			<td>Global.</td>
			<td><a href="https://asterweb.jpl.nasa.gov/gdem.asp">NASA</a></td>
			<td><a href="https://api.opentopodata.org/v1/aster30m?locations=39.747114,-104.996334">1591&nbsp;m</a></td>
		</tr>
		<tr>
			<td><a href="/datasets/srtm/">srtm30m</a></td>
			<td>~30&nbsp;m</td>
			<td>Latitudes -60 to 60.</td>
			<td><a href="https://lpdaac.usgs.gov/products/srtmgl1v003/">USGS</a></td>
			<td><a href="https://api.opentopodata.org/v1/srtm30m?locations=39.747114,-104.996334">1604&nbsp;m</a></td>
		</tr>
		<tr>
			<td><a href="/datasets/srtm/">srtm90m</a></td>
			<td>~90&nbsp;m</td>
			<td>Latitudes -60 to 60.</td>
			<td><a href="https://lpdaac.usgs.gov/products/srtmgl3v003/">USGS</a></td>
			<td><a href="https://api.opentopodata.org/v1/srtm90m?locations=39.747114,-104.996334">1603&nbsp;m</a></td>
		</tr>
		<tr>
			<td><a href="/datasets/bkg/">bkg200m</a></td>
			<td>200&nbsp;m</td>
			<td>Germany.</td>
			<td><a href="https://www.bkg.bund.de/">BKG</a></td>
			<td><a href="https://api.opentopodata.org/v1/bkg200m?locations=39.747114,-104.996334"><em>Not in dataset bounds</em></a></td>
		</tr>
		<tr>
			<td><a href="/datasets/etopo1/">etopo1</a></td>
			<td>~1.8&nbsp;km</td>
			<td>Global, including bathymetry and ice surface elevation near poles.</td>
			<td><a href="https://www.ngdc.noaa.gov/mgg/global/">NOAA</a></td>
			<td><a href="https://api.opentopodata.org/v1/etopo1?locations=39.747114,-104.996334">1596&nbsp;m</a></td>
		</tr>
		<tr>
			<td><a href="/datasets/gebco2020/">gebco2020</a></td>
			<td>~450m</td>
			<td>Global bathymetry and land elevation.</td>
			<td><a href="https://www.gebco.net/data_and_products/gridded_bathymetry_data/">GEBCO</a></td>
			<td><a href="https://api.opentopodata.org/v1/gebco2020?locations=39.747114,-104.996334">1603&nbsp;m</a></td>
		</tr>
		<tr>
			<td><a href="/datasets/emod2018/">emod2018</a></td>
			<td>~100m</td>
			<td>Bathymetry for ocean and sea in Europe.</td>
			<td><a href="https://www.emodnet-bathymetry.eu/data-products">EMODnet</a></td>
			<td><a href="https://api.opentopodata.org/v1/emod2018?locations=39.747114,-104.996334"><em>Not in dataset bounds</em></a></td>
		</tr>
	</tbody>
</table>


See the [API docs](api.md) for more about request formats and parameters.


---

## Support

Need some help getting Open Topo Data running? Send me an email at [andrew@opentopodata.org](mailto:andrew@opentopodata.org)!


---

## Paid hosting

If you need an elevation API service with high-quality 1m lidar data, check out my sister project [GPXZ](https://www.gpxz.io).

The GPXZ Elevation API offers the following features:

* Managed hosting, load balanced for redundancy
* [Seamless, global, hi-res elevation dataset](https://www.gpxz.io/dataset)
* [Drop-in replacement endpoint for the Google Maps Elevation API](https://www.gpxz.io/docs)
* Priority support
* No hard usage limits
* EU-only servers if needed
* CORS (so you can use the API in your frontend webapp)

For more details, reach out to [andrew@opentopodata.org](mailto:andrew@opentopodata.org).


Paid hosting funds the development of Open Topo Data and keeps the public API free.




<!-- If you'd like me to host and manage an Open Topo Data elevation API for your business, reach out to [andrew@opentopodata.org](mailto:andrew@opentopodata.org).

Paid hosting offers the following features:

* Managed hosting, load balanced for redundancy
* Priority support
* No hard usage limits
* Uptime SLA
* Custom dataset processing
* EU-only servers if needed
* GDPR compliance
* CORS (so you can use the API in your frontend webapp)

Paid hosting funds the development of Open Topo Data and keeps the public API free. -->