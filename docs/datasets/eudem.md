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
gdalbuildvrt -tr 25 25 -tap -te 0 0 8000000 6000000 eudem.vrt ../eudem/*.TIF
cd ../../
```

The `tr`, `tap`, and `te` options in the above command ensure that slices from the VRT will use the exact values and grid of the source rasters.


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


### Buffering tiles (optional)

The tiles provided by EU-DEM don't overlap and cover slightly less than a 1000km square. This means you'll get a `null` result for coordinates along the tile edges.

The `.vrt` approach above solves the overlap issue, but for improved performance you can leave the tiles separate and add a buffer to each one. This is the code I used on the public API to do this:


```python
import os
from glob import glob
import subprocess

import rasterio


# Prepare paths.
input_pattern = 'data/eudem/*.TIF'
input_paths = sorted(glob(input_pattern))
assert input_paths
vrt_path = 'data/eudem-vrt/eudem.vrt'
output_dir = 'data/eudem-buffered/'
os.makedirs(output_dir, exist_ok=True)



# EU-DEM specific options.
tile_size = 1_000_000
buffer_size = 50

for input_path in input_paths:

    # Get tile bounds.
    with rasterio.open(input_path) as f:
        bottom = int(f.bounds.bottom)
        left = int(f.bounds.left)

    # For EU-DEM only: round this partial tile down to the nearest tile_size.
    if left == 943750:
        left = 0

    # New tile name in SRTM format.
    output_name = 'N' + str(bottom).zfill(7) + 'E' + str(left).zfill(7) + '.TIF'
    output_path = os.path.join(output_dir, output_name)

    # New bounds.
    xmin = left - buffer_size
    xmax = left + tile_size + buffer_size
    ymin = bottom - buffer_size
    ymax = bottom + tile_size + buffer_size

    # EU-DEM tiles don't cover negative locations.
    xmin = max(0, xmin)
    ymin = max(0, ymin)

    # Do the transformation.
    cmd = [
        'gdal_translate',
        '-a_srs', 'EPSG:3035',  # EU-DEM crs.
        '-co', 'NUM_THREADS=ALL_CPUS',
        '-co', 'COMPRESS=DEFLATE',
        '-co', 'BIGTIFF=YES',
        '--config', 'GDAL_CACHEMAX','512',
        '-projwin', str(xmin), str(ymax), str(xmax), str(ymin),
        vrt_path, output_path,
    ]
    r = subprocess.run(cmd)
    r.check_returncode()
```

These new files can be used in Open Topo Data with the following `config.yaml` file


```yaml
datasets:
- name: eudem25m
  path: data/eudem-buffered/
  filename_epsg: 3035
  filename_tile_size: 1000000
```

and rebuilding:

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
