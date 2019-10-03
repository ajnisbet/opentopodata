<h1 style="text-align:center">Open Topo Data</h1>

<p style="text-align:center">
  <img width="378" hight="153" src="https://www.andrewnisbet.nz/img/elevation-land.png" alt="Open Topo Data">
</p>

<p style="text-align:center">
	<strong>Open Topo Data</strong> is a REST API server for your elevation data.<br> <a href="#host-your-own">Host your own</a> or use the free <a href="#public-api">public API</a>.
</p>

---

## Host your own

```bash
git clone github.com/ajnisbet/opentopodata
cd opentopodata
make build
make run
curl http://localhost:8000/v1/test?locations=56.35,123.90
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

To keep the public API sustainable, some limitations are applied. I hope to raise these limits as I get a better sense of demand.

* Max 100 locations per request.
* Max 1 call per second.
* Max 100 calls per day.


The following datasets are available on the public API, with elevation shown for downtown Denver, Colorado (39.7471,&nbsp;-104.9963).


<table>
	<thead>
		<tr>
			<th>Dataset name</th>
			<th>Resolution</th>
			<th>Extent</th>
			<th>Source</th>
			<th>Denver elevation</th>
		</tr>
	</thead>
	<tbody>
		<tr>
			<td>etopo1</td>
			<td>1.8&nbsp;km</td>
			<td>Global, including bathymetry and ice surface elevation near poles.</td>
			<td><a href="https://www.ngdc.noaa.gov/mgg/global/">NOAA</a></td>
			<td><a href="https://api.opentopodata.org/v1/etopo1?locations=39.747114,-104.996334">1596&nbsp;m</a></td>
		</tr>
		<tr>
			<td>srtm90m</td>
			<td>90&nbsp;m</td>
			<td>Latitudes -60 to 60.</td>
			<td><a href="http://opentopo.sdsc.edu/raster?opentopoID=OTSRTM.042013.4326.1">NASA</a></td>
			<td><a href="https://api.opentopodata.org/v1/srtm90m?locations=39.747114,-104.996334">1603&nbsp;m</a></td>
		</tr>
		<tr>
			<td>srtm30m</td>
			<td>30&nbsp;m</td>
			<td>Latitudes -60 to 60.</td>
			<td><a href="https://earthdata.nasa.gov/nasa-shuttle-radar-topography-mission-srtm-version-3-0-global-1-arc-second-data-released-over-asia-and-australia">NASA</a></td>
			<td><a href="https://api.opentopodata.org/v1/srtm30m?locations=39.747114,-104.996334">1604&nbsp;m</a></td>
		</tr>
	</tbody>
</table>


See the [API docs](api.md) for more about request formats and parameters.


