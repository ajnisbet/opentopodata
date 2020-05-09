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

Next, Open Topo Data needs the filenames to match the SRTM format: the filename should be the coordinates of the lower-left corner, in NS-WE order. For EU-DEM this means two changes to the filenames:

* swapping the order of the northing and easting,
* and adding 5 trailing zeroes to each coordinate that Copernicus removed for simplicity.

So `eu_dem_v11_E00N20.TIF` becomes `N2000000E0000000.tif`. Here's a Python script to do the transformation, but it might be just as easy to do by hand:

```python
from glob import glob
import os
import re

old_pattern = '.data/eudem/eu_dem_v11_E*N*.TIF'
old_paths = list(glob(old_pattern))
print('Found {} files'.format(len(old_paths)))

for old_path in old_paths:
    folder = os.path.dirname(old_path)
    old_filename = os.path.basename(old_path)

    # Extract north and east coords, pad with zeroes.
    res = re.search(r'(E\d\d)(N\d\d)', old_filename)
    easting, northing = res.groups()
    northing = northing + '00000'
    easting = easting + '00000'

    # Rename in place.
    new_filename = '{}{}.tif'.format(northing, easting)
    new_path = os.path.join(folder, new_filename)
    os.rename(old_path, new_path)
```

You should have the following 27 files:

```
N0000000E1000000.tif
N1000000E1000000.tif
N1000000E2000000.tif
N1000000E3000000.tif
N1000000E4000000.tif
N1000000E5000000.tif
N1000000E6000000.tif
N2000000E0000000.tif
N2000000E1000000.tif
N2000000E2000000.tif
N2000000E3000000.tif
N2000000E4000000.tif
N2000000E5000000.tif
N2000000E6000000.tif
N2000000E7000000.tif
N3000000E2000000.tif
N3000000E3000000.tif
N3000000E4000000.tif
N3000000E5000000.tif
N4000000E2000000.tif
N4000000E3000000.tif
N4000000E4000000.tif
N4000000E5000000.tif
N5000000E2000000.tif
N5000000E3000000.tif
N5000000E4000000.tif
N5000000E5000000.tif
```

Create a `config.yaml` file:

```yaml
datasets:
- name: eudem25m
  path: data/eudem/
  filename_epsg: 3035
  filename_tile_size: 1000000
```

Rebuild to enable the new dataset at [localhost:5000/v1/eudem25m?locations=51.575,-3.220](http://localhost:5000/v1/eudem25m?locations=51.575,-3.220).

```bash
make build && make run
```

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