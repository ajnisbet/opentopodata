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


Make a new folder for the dataset:

```bash
mkdir ./data/eudem
```

Download the dataset from [Copernicus](https://land.copernicus.eu/imagery-in-situ/eu-dem/eu-dem-v1.1?tab=download). There are 27 files. Unzip them and move all the `.TIF` files into the data folder (you don't need the `.aux.xml`, `.ovr`, or `.TFw` files).

Your data folder should now contain only 27 TIF files:

```bash
ls ./data/eudem

# eu_dem_v11_E00N20.TIF
# eu_dem_v11_E10N00.TIF
# eu_dem_v11_E10N10.TIF
# ...
```


If you have [gdal](https://gdal.org) installed, the easiest thing to do here is build a [VRT](https://gdal.org/drivers/raster/vrt.html) - a single raster file that links to the 27 tiles and which Open Topo Data can treat as a single-file dataset.

```bash
mkdir ./data/eudem-vrt
cd ./data/eudem-vrt
gdalbuildvrt -tr 25 25 -tap -te 0 0 8000000 6000000 eudem.vrt ../data/eudem/*.TIF
cd ../../
```


Then create a `config.yaml` file:

```yaml
datasets:
- name: eudem25m
  path: data/eudem-vrt/
```

Finally, rebuild to enable the new dataset at [localhost:5000/v1/eudem25m?locations=51.575,-3.220](http://localhost:5000/v1/eudem25m?locations=51.575,-3.220).

```bash
make build && make run
```

!!! note "Avoiding gdal"
    If you don't have gdal installed, you can use the tiles directly. There are instructions for this [here](https://github.com/ajnisbet/opentopodata/blob/f012ec136bebcd97e1dc05645e91a6d2487127dc/docs/datasets/eudem.md#adding-eu-dem-to-open-topo-data), but because the EU-DEM tiles don't come with an overlap you will get a `null` elevation at locations within 0.5 pixels of tile edges. 


!!! tip "Extra performance"
    `.vrt` files are slightly slower than `.tif` files. You can use the tiles directly, but you need to [add a 1 pixel buffer](../notes/buffering-tiles.md) to each raster as the EU-DEM tiles don't come with overlap.



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

Open Topo Data hosts version 1.1 of the dataset.
