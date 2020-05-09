<h1 style="text-align:center">Open Topo Data</h1>

<p style="text-align:center">
  <img width="378" hight="153" src="/img/elevation-land.png" alt="Open Topo Data">
</p>

<p style="text-align:center">
	<strong>Open Topo Data</strong> is an elevation API.<br> <a href="#host-your-own">Host your own</a> or use the free <a href="#public-api">public API</a>.
</p>

---

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


See the [server docs](server.md) for more about configuration and adding datasets.

---

## Public API

I'm hosting a public API at [api.opentopodata.org](https://api.opentopodata.org). 

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

Want help getting Open Topo Data running? Or just want to chat about elevation data? Send me an email at [andrew@opentopodata.org](mailto:andrew@opentopodata.org).


