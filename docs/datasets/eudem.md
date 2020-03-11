# EU-DEM

[EU-DEM](https://www.eea.europa.eu/data-and-maps/data/copernicus-land-monitoring-service-eu-dem) is an elevation dataset covering Europe at a 25 metre resolution.

The dataset was created by merging elevation data from the SRTM and ASTER global datasets, as well as from Soviet topo maps at high latitudes. The datum used is [EVRS2000](https://spatialreference.org/ref/epsg/evrf2000-height/).



## Coverage

The dataset covers European Environment Agency member states, plus some countries to the east. Coverage extends to small parts of Northern Africa. Unlike SRTM, EU-DEM includes the Scandinavian regions north of 60°.

<p style="text-align:center; padding: 1rem 0">
  <img src="/img/eudem.jpg" alt="EU-DEM elevation">
  <br>
  <em>Render of ETOPO1 elevation.</em>
</p>

## Accuracy

The stated vertical accuracy is ± 7m RMSE. Differences to SRTM and ASTER typically fall within this 7m range even with the datasets using slightly different vertical datums. Elevations for [Lake Geneva, Switzerland](https://www.google.com/maps/place/46%C2%B014'33.2%22N+6%C2%B010'32.1%22E/@46.2374461,6.1073519,12z/) are [370m](https://api.opentopodata.org/v1/srtm30m?locations=46.242557,206.175588), [374m](https://api.opentopodata.org/v1/aster30m?locations=46.242557,206.175588), and [372m](https://api.opentopodata.org/v1/eudem25m?locations=46.242557,206.175588) for SRTM, ASTER, and EU-DEM respectively.

## Water

The European Environment Agency says EU-DEM is produced by fusing SRTM and ASTER, with further editing over water. To assess this I looked at some areas in the fjords of [Stavanger, Norway](https://www.google.com/maps/place/Stavanger,+Norway), as DEM datasets often struggle with water and steep elevation gradients.

Some bodies of water seem to have been flattened, which is an improvement, but these flattened lakes tend to have overly-steep edges.

In the example below, EU-DEM removes the noise over the lake that exists in the other datasets, but incorrectly places a sharp elevation increase at the water's edge, rather than at the cliff to the south-west. It also places the lake 70m lower than the other datasets, which I think is wrong as this puts the lake below its outflow river.


<div style="display:flex; justify-content: space-between; font-style: italic; text-align: center; flex-wrap: wrap">
	<div style="max-width: 45%; padding-bottom: 2rem">
		<a href="/img/eudem-lake-eudem.jpg"><img src="/img/eudem-lake-eudem.jpg" alt="EU-DEM elevation over a lake"></a>
		<span>EU-DEM</span>
	</div>
	<div style="max-width: 45%; padding-bottom: 2rem">
		<a href="/img/eudem-lake-srtm.jpg"><img src="/img/eudem-lake-srtm.jpg" alt="SRTM 30m elevation over a lake"></a>
		<span>SRTM 30m</span>
	</div>
	<div style="max-width: 45%; padding-bottom: 2rem">
		<a href="/img/eudem-lake-aster.jpg"><img src="/img/eudem-lake-aster.jpg" alt="ASTER elevation over a lake"></a>
		<span>ASTER</span>
	</div>
	<div style="max-width: 45%; padding-bottom: 2rem">
		<a href="/img/eudem-lake-aerial.jpg"><img src="/img/eudem-lake-aerial.jpg" alt="Bing Aerial image over a lake"></a>
		<span>Bing Aerial</span>
	</div>
</div>



This processing can lead to spurious land bridges over the fjords in EU-DEM.

<div style="display:flex; justify-content: space-between; font-style: italic; text-align: center; flex-wrap: wrap">
	<div style="max-width: 45%; padding-bottom: 2rem">
		<a href="/img/eudem-bridge-eudem.jpg"><img src="/img/eudem-bridge-eudem.jpg" alt="EU-DEM elevation over a fjord"></a>
		<span>EU-DEM</span>
	</div>
	<div style="max-width: 45%; padding-bottom: 2rem">
		<a href="/img/eudem-bridge-srtm.jpg"><img src="/img/eudem-bridge-srtm.jpg" alt="SRTM 30m elevation over a fjord"></a>
		<span>SRTM 30m</span>
	</div>
	<div style="max-width: 45%; padding-bottom: 2rem">
		<a href="/img/eudem-bridge-aster.jpg"><img src="/img/eudem-bridge-aster.jpg" alt="ASTER elevation over a fjord"></a>
		<span>ASTER</span>
	</div>
	<div style="max-width: 45%; padding-bottom: 2rem">
		<a href="/img/eudem-bridge-aerial.jpg"><img src="/img/eudem-bridge-aerial.jpg" alt="Bing Aerial image over a fjord"></a>
		<span>Bing Aerial</span>
	</div>
</div>

In the example above there are three lakes visible, and only the middle one gets the flattening treatment in EU-DEM.

## Coastline

EU-DEM uses NODATA values for elevations over seas and oceans, where both ASTER and SRTM assign these areas an elevation of 0m. This means that Open Topo Data isn't able to interpolate elevations for locations very close to the coast and will return a value of `NaN` where SRTM and ASTER might return a 0m or 1m elevation. 




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
      }
    }
  ], 
  "status": "OK"
}
```

Open Topo Data hosts version 1.1 of the dataset (the latest version as of 2020-03-10).