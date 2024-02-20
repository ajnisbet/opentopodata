# EU-DEM

[EU-DEM](https://www.eea.europa.eu/data-and-maps/data/copernicus-land-monitoring-service-eu-dem) is an elevation dataset covering Europe at a 25 metre resolution.

The dataset was created by merging elevation data from the SRTM and ASTER global datasets, as well as from Soviet topo maps at high latitudes. The datum used is [EVRS2000](https://spatialreference.org/ref/epsg/evrf2000-height/).



## Coverage

The dataset covers European Environment Agency member states, plus some countries to the east. Coverage extends to small parts of Northern Africa. Unlike SRTM, EU-DEM includes the Scandinavian regions north of 60°.

<p style="text-align:center; padding: 1rem 0">
  <img src="/img/eudem.jpg" alt="EU-DEM elevation">
  <br>
  <em>Render of EU-DEM elevation.</em>
</p>

## Accuracy

The stated vertical accuracy is ± 7m RMSE. Differences to SRTM and ASTER typically fall within this 7m range even with the datasets using slightly different vertical datums. Elevations for [Lake Geneva, Switzerland](https://www.google.com/maps/place/46%C2%B014'33.2%22N+6%C2%B010'32.1%22E/@46.2374461,6.1073519,12z/) are [370m](https://api.opentopodata.org/v1/srtm30m?locations=46.242557,206.175588), [374m](https://api.opentopodata.org/v1/aster30m?locations=46.242557,206.175588), and [372m](https://api.opentopodata.org/v1/eudem25m?locations=46.242557,206.175588) for SRTM, ASTER, and EU-DEM respectively.


## Coastline

EU-DEM uses `NODATA` values for elevations over seas and oceans, where both ASTER and SRTM assign these areas an elevation of 0m. This means that Open Topo Data isn't able to interpolate elevations for locations very close to the coast and will return a value of `NaN` in places where SRTM and ASTER might return a 0m or 1m elevation.

The advantage of the `NODATA` oceans is that you cane use EU-DEM without clipping to a coastline shapefile.


## Adding EU-DEM to Open Topo Data

As of Jan 2024, EU-DEM is no longer available to download via copernicus.eu. 

I have uploaded my version of the dataset at [https://files.gpxz.io/eudem_buffered.zip](https://files.gpxz.io/eudem_buffered.zip), see [EUDEM download](https://www.gpxz.io/blog/eudem) for more details.

Download and unzip the folder into:

```bash
mkdir ./data/eudem
```
There are 27 files.

Then create a `config.yaml` file:

```yaml
datasets:
- name: eudem25m
  path: data/eudem
  filename_epsg: 3035
  filename_tile_size: 1000000
```

Finally, rebuild to enable the new dataset at [localhost:5000/v1/eudem25m?locations=51.575,-3.220](http://localhost:5000/v1/eudem25m?locations=51.575,-3.220).

```bash
make build && make run
```


!!! note "Avoiding gdal"
    If you don't have gdal installed, you can use the tiles directly. There are instructions for this [here](https://github.com/ajnisbet/opentopodata/blob/f012ec136bebcd97e1dc05645e91a6d2487127dc/docs/datasets/eudem.md#adding-eu-dem-to-open-topo-data), but because the EU-DEM tiles don't come with an overlap you will get a `null` elevation at locations within 0.5 pixels of tile edges. 




## Public API

The Open Topo Data public API lets you query EU-DEM for free:

```
curl https://api.opentopodata.org/v1/eudem25m?locations=57.688709,11.976404
```

```json
{
  "results": [
    {
      "elevation": 54.576168060302734,
      "location": {
        "lat": 57.688709,
        "lng": 11.976404
      },
      "dataset": "eudem25m"
    }
  ],
  "status": "OK"
}
```

Open Topo Data hosts version 1.1 of the dataset.


## Attribution

Released by [Copernicus](http://land.copernicus.eu/) under the following terms:


*Access to data is based on a principle of full, open and free access as established by the Copernicus data and information policy Regulation (EU) No 1159/2013 of 12 July 2013. This regulation establishes registration and licensing conditions for GMES/Copernicus users. Free, full and open access to this data set is made on the conditions that:*

1. *When distributing or communicating Copernicus dedicated data and Copernicus service information to the public, users shall inform the public of the source of that data and information.*

2. *Users shall make sure not to convey the impression to the public that the user's activities are officially endorsed by the Union.*

3. *Where that data or information has been adapted or modified, the user shall clearly state this.*

4. *The data remain the sole property of the European Union. Any information and data produced in the framework of the action shall be the sole property of the European Union. Any communication and publication by the beneficiary shall acknowledge that the data were produced "with funding by the European Union".*
