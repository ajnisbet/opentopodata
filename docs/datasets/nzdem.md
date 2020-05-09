# NZ DEM

The [8m NZ DEM](https://data.linz.govt.nz/layer/51768-nz-8m-digital-elevation-model-2012/) is an interpolation of the 20m contours on the [1:50,000 scale LINZ topo maps](https://data.linz.govt.nz/layer/50768-nz-contours-topo-150k/).

## Coverage

The datasets covers all of New Zealand except Chatham Island at an 8 metre resolution.

<p style="text-align:center; padding: 1rem 0">
  <img src="/img/nzdem.png" alt="SRTM coverage">
  <br>
  <em>NZ DEM elevation rendering.</em>
</p>


## Adding NZ DEM to Open Topo Data


```bash
mkdir ./data/nzdem8m
```


As of May 2020, the 8m dataset could only be painstaking downloaded a single tile at a time through the [LINZ web interface](https://data.linz.govt.nz/layer/51768-nz-8m-digital-elevation-model-2012/). If you'd rather not do this send me an [email](mailto:andrew@opentopodata.org), I can send you the raw dataset.

Once you've obtained the 115 files, unzip the zip archives and delete anything without a `.tif` extension. 

For Open Topo Data to understand the grid arrangement of the files, they need to be renamed to the coordinates of the lower-left corner. Here's the Python script I used, I'm also adding a buffer to help with interpolation near tile borders:

```python
import os
from glob import glob

folder = './data/nzdem8m'


# Build vrt for all tifs.
pattern = os.path.join(folder, '*.tif')
tif_paths = list(glob(pattern))
vrt_path = os.path.join(folder, 'all.vrt')
assert not os.system('gdalbuildvrt {} {}'.format(vrt_path, ' '.join(tif_paths)))

buffer_ = 5
for tif_path in tif_paths:
    
    with rasterio.open(tif_path) as f:
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
    
        northing = f.bounds.bottom
        easting = f.bounds.left
        
        filename = 'N{}E{}.tif'.format(int(northing), int(easting))
        buffer_path = os.path.join(os.path.dirname(tif_path), filename)
        
    
    te = ' '.join(str(x) for x in new_bounds)
    ts = ' '.join(str(x) for x in new_shape)
    
    cmd = f'gdalwarp -te {te} -ts {ts} -r near -co NUM_THREADS=ALL_CPUS -co COMPRESS=DEFLATE  -co PREDICTOR=3 {vrt_path} {buffer_path}'
    assert not os.system(cmd)

assert not os.system(f'rm {vrt_path}')
```

Create a `comfig.yaml` file, setting the size of the tiles (65536 metres) and the projection system used ([NZ tranvers mercator](https://spatialreference.org/ref/epsg/nzgd2000-new-zealand-transverse-mercator-2000/):

```yaml
datasets:
- name: nzdem8m
  path: data/nzdem8m/
  filename_tile_size: 65536
  filename_epsg: 2193
```


Rebuild to enable the new dataset at [localhost:5000/v1/nzdem8m](http://localhost:5000/v1/nzdem8m?locations=37.653512,-119.410503).

```bash
make build && make run
```


## Public API

The Open Topo Data public API lets you query NZ DEM 8m for free:

```
curl https://api.opentopodata.org/v1/nzdem8m?locations=37.6535,-119.4105
```

```json
{
  "results": [
    {
      "elevation": 3498.298583984375, 
      "location": {
        "lat": 37.6535, 
        "lng": -119.4105
      }
    }
  ], 
  "status": "OK"
}
```

The data files used in the public API were downloaded from LINZ May 2020.
