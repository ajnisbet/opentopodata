# GEBCO 2020 Bathymetry

[GEBCO](https://www.gebco.net/) maintains a high-quality, global bathymetry (sea floor depth) dataset.

GEBCO releases a new dataset most years, the 2020 dataset (released in May 2020) covers the entire globe at a 15 arc-second resolution, corresponding to 450m resolution at the equator.

## Coverage

Elevation is given for land areas, largely using a [15-degree version](https://topex.ucsd.edu/WWW_html/srtm15_plus.html) of [SRTM](srtm.md).

Seafloor data comes from a variety of bathymetric sources, see [GEBCO](https://www.gebco.net/data_and_products/gridded_bathymetry_data/) for more details.

<p style="text-align:center; padding: 1rem 0">
  <img src="/img/gebco-2020.png" alt="GEBCO 2020 elevation render.">
  <br>
  <em>Render of GEBCO 2020 elevation.</em>
</p>



## Adding GEBCO 2020 to Open Topo Data

Instructions are given for the 2020 version of the dataset: future versions might work a bit differently.

Make a new folder for the dataset:

```bash
mkdir ./data/gebco2020
```

Download the dataset from [GEBCO](https://www.gebco.net/data_and_products/gridded_bathymetry_data/). You'll want the `GEBCO_2020 Grid` version, in `Data GeoTiff` format. Extract raster tiles from the archive and delete everything else so there are just 8 `.tif` files in the `./data/gebco2020` folder.

The files are given as 90 degree tiles, we need to rename them to SRTM's `NxxSxx` format to work with Open Topo Data:
```bash
mv gebco_2020_n0.0_s-90.0_w0.0_e90.0.tif     S90E000.tif
mv gebco_2020_n0.0_s-90.0_w-180.0_e-90.0.tif S90W180.tif
mv gebco_2020_n0.0_s-90.0_w-90.0_e0.0.tif    S90W090.tif
mv gebco_2020_n0.0_s-90.0_w90.0_e180.0.tif   S90E090.tif
mv gebco_2020_n90.0_s0.0_w0.0_e90.0.tif      N00E000.tif
mv gebco_2020_n90.0_s0.0_w-180.0_e-90.0.tif  N00W180.tif
mv gebco_2020_n90.0_s0.0_w-90.0_e0.0.tif     N00W090.tif
mv gebco_2020_n90.0_s0.0_w90.0_e180.0.tif    N00E090.tif
```

Create a `config.yaml` file:

```yaml
datasets:
- name: gebco2020
  path: data/gebco2020/
  filename_tile_size: 90
```

Rebuild to enable the new dataset at [localhost:5000/v1/gebco2020](http://localhost:5000/v1/gebco2020?locations=37.653512,-119.410503).

```bash
make build && make run
```

### Buffering tiles

The tiles provided by GEBCO don't overlap and cover slightly less than a 90° x 90° square. This means you'll get a `null` result for coordinates along the tile edges (like `0,0`). 

For the public API I used the following code to add a 5px buffer to each tile.


```python
from glob import glob
import os

import rasterio


old_folder = 'gebco_2020_geotiff'
new_folder = 'gebco_2020_buffer'
buffer_ = 5


old_pattern = os.path.join(old_folder, '*.tif')
old_paths = list(glob(old_pattern))

cmd = 'gdalbuildvrt {}/all.vrt'.format(old_folder) + ' '.join(old_paths)
os.system(cmd)

for path in old_paths:
    new_path = path.replace(old_folder, new_folder)
    
    with rasterio.open(path) as f:
        new_bounds = (
            f.bounds.left - buffer_ * f.res[0],
            f.bounds.bottom - buffer_ * f.res[1],
            f.bounds.right + buffer_ * f.res[0],
            f.bounds.top + buffer_ * f.res[1],
        )

        new_shape = (
            f.shape[0] + buffer_ * 2,
            f.shape[1] + buffer_ * 2,
        )
    
    te = ' '.join(str(x) for x in new_bounds)
    ts = ' '.join(str(x) for x in new_shape)
    
    cmd = f'gdalwarp -te {te} -ts {ts} -r near -co NUM_THREADS=ALL_CPUS -co COMPRESS=DEFLATE  -co PREDICTOR=2 -co BIGTIFF=yes {old_folder}/all.vrt {new_path}'
    os.system(cmd)
```


## Public API

The Open Topo Data public API lets you query GEBCO 2020 for free:

```
curl https://api.opentopodata.org/v1/gebco2020?locations=37.6535,-119.4105
```

```json
{
  "results": [
    {
      "elevation": 3405.0, 
      "location": {
        "lat": 37.6535, 
        "lng": -119.4105
      },
      "dataset": "gebco2020"
    }
  ], 
  "status": "OK"
}
```

The public API uses the 2020 version of the dataset.


## Attribution

[GEBCO](https://www.gebco.net/data_and_products/gridded_bathymetry_data/gebco_2019/grid_terms_of_use.html) released the dataset into the public domain under the following terms:

* *Acknowledge the source of The GEBCO Grid. A suitable form of attribution is given in the documentation that accompanies The GEBCO Grid.*
* *Not use The GEBCO Grid in a way that suggests any official status or that GEBCO, or the IHO or IOC, endorses any particular application of The GEBCO Grid.*
* *Not mislead others or misrepresent The GEBCO Grid or its source.*