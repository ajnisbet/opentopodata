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

To keep the public API sustainable, some limitations are applied. I hope to raise these limits as I get a better sense of demand.

* Max 100 locations per request.
* Max 1 call per second.
* Max 100 calls per day.


The following datasets are available on the public API, with elevation shown for <span class="location-name">downtown Denver, Colorado (39.7471,&nbsp;-104.9963)</span>.

<table>
    <thead>
        <tr>
            <th>Dataset name</th>
            <th>Resolution</th>
            <th>Extent</th>
            <th>Source</th>
            <th>Elevation</th>
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



<style>
    .point-form {
        background-color: #f9f9f9;
        padding: 19px;
        margin-bottom: 30px;
    }

    .point-form legend {
        display: block;
        width: 100%;
        padding: 0;
        margin-bottom: 23px;
        font-size: 19.5px;
        line-height: inherit;
        color: #212121;
        border: 0;
        border-bottom: 1px solid #e5e5e5;
    }

    .point-form .form-group {
        margin-right: -15px;
        margin-left: -15px;
        margin-bottom: 15px;
    }

    .point-form .form-group:before {
        display: table;
        content: " ";
    }

    .point-form label {
        float: left;
        position: relative;
        min-height: 1px;
        padding-right: 15px;
        padding-left: 15px;
        padding-top: 7px;
        width: 16.66666667%;
        font-weight: normal;
        display: inline-block;
        max-width: 100%;
        font-size: 13px;
        line-height: 1.846;
        text-align: right;
    }

    .point-form .input-wrap {
        width: 83.33333333%;
        float: left;
        position: relative;
        min-height: 1px;
        padding-right: 15px;
        padding-left: 15px;
    }

    .point-form input {
        display: block;
        width: 10em;
        height: 37px;
        padding: 6px 16px;
        font-size: 13px;
        line-height: 1.846;
        color: #666666;
        background-color: transparent;
        background-image: none;
        border: 1px solid transparent;
        border-radius: 3px;
        box-shadow: inset 0 1px 1px rgba(0, 0, 0, 0.075);
        transition: border-color ease-in-out .15s, box-shadow ease-in-out .15s;
        padding: 0;
        border: none;
        border-radius: 0;
        -webkit-appearance: none;
        box-shadow: inset 0 -1px 0 #dddddd;
        font-size: 16px;
    }

    .btn-primary:hover {
        color: #ffffff;
        background-color: #0c7cd5;
        border-color: rgba(0, 0, 0, 0);
    }

    .btn-primary:hover, .btn-primary:active:hover {
        background-color: #0d87e9;
    }
    .btn-primary:active:hover, .btn-primary.active:hover, .open > .dropdown-toggle.btn-primary:hover, .btn-primary:active:focus, .btn-primary.active:focus, .open > .dropdown-toggle.btn-primary:focus, .btn-primary:active.focus, .btn-primary.active.focus, .open > .dropdown-toggle.btn-primary.focus {
        color: #ffffff;
        background-color: #0a68b4;
        border-color: rgba(0, 0, 0, 0);
    }
    .btn-primary:active {
        background-color: #0b76cc;
        background-image: radial-gradient(circle, #0b76cc 10%, #2196f3 11%);
        background-repeat: no-repeat;
        background-size: 1000% 1000%;
        box-shadow: 2px 2px 4px rgba(0, 0, 0, 0.4);
    }
    .btn-primary:active, .btn-primary.active, .open > .dropdown-toggle.btn-primary {
        color: #ffffff;
        background-color: #0c7cd5;
        background-image: none;
        border-color: rgba(0, 0, 0, 0);
    }
    
    .btn:active, .btn.active {
        background-image: none;
        outline: 0;
        box-shadow: inset 0 3px 5px rgba(0, 0, 0, 0.125);
    }
    .btn:hover, .btn:focus, .btn.focus {
        color: #444444;
        text-decoration: none;
    }
    .btn {
        text-transform: uppercase;
        border: none;
        box-shadow: 1px 1px 4px rgba(0, 0, 0, 0.4);
        transition: all 0.4s;
    }
    .btn-primary {
        background-size: 200% 200%;
        background-position: 50%;
    }
    .btn-primary {
        color: #ffffff;
        background-color: #2196f3;
        border-color: transparent;
    }
    .btn {
        display: inline-block;
        margin-bottom: 0;
        font-weight: normal;
        text-align: center;
        white-space: nowrap;
        vertical-align: middle;
        touch-action: manipulation;
        cursor: pointer;
        background-image: none;
        border: 1px solid transparent;
        padding: 6px 16px;
        font-size: 13px;
        line-height: 1.846;
        border-radius: 3px;
        user-select: none;
    }
    input, button {
        -webkit-font-smoothing: antialiased;
        letter-spacing: .1px;
    }
    input, button, select, textarea {
        font-family: inherit;
        font-size: inherit;
        line-height: inherit;
    }
    button, html input[type="button"], input[type="reset"], input[type="submit"] {
        -webkit-appearance: button;
        cursor: pointer;
    }
    button, select {
        text-transform: none;
    }
    button {
        overflow: visible;
    }
    button, input, optgroup, select, textarea {
        color: inherit;
        font: inherit;
        margin: 0;
    }
    .btn-primary:hover {
        color: #ffffff;
        background-color: #0c7cd5;
        border-color: rgba(0, 0, 0, 0);
    }
    .btn-offset {
        margin-left: 16.66666667%;
    }
</style>

<form class="point-form" action="#!">
    <legend>Modify location</legend>
    <div class="form-group">
        <label for="lat">Latitude</label>
        <div class="input-wrap">
            <input type="text" name="lat" value="39.7471"><br>
        </div>
    </div>
    <div class="form-group">
        <label for="lat">Longitude</label>
        <div class="input-wrap">
            <input type="text" name="lat" value="39.7471"><br>
        </div>
    </div>
    <div class="btn-offset">
        <button type="submit" class="btn btn-primary"><span>Submit</span></button>
        
    </div>
</form>



See the [API docs](api.md) for more about request formats and parameters.


