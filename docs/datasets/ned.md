# NED

The National Elevation Dataset (NED) is a collection of DEMs covering the USA at different resolutions. 


## Resolution and Coverage

NED comes in several different resolutions, each with a different coverage area.

The most commonly used resolutions are 1 arcsecond (covering North America and Mexico) and 1/3 arcsecond (covering CONUS, HI, PR, and parts of AK). The 1/3 arcsecond dataset is used in the Open Topo Data public API.

<div style="display:flex; justify-content: space-between; font-style: italic; text-align: center; flex-wrap: wrap">
  <div style="max-width: 49%; padding-bottom: 2rem">
    <a href="/img/ned-1-sec.png"><img src="/img/ned-1-sec.png" alt="NED 1 arcsecond coverage."></a>
    <span>1 arcsecond (30m).</span>
  </div>
  <div style="max-width: 49%; padding-bottom: 2rem">
    <a href="/img/ned-13-sec.png"><img src="/img/ned-13-sec.png" alt="NED 1/3 arcsecond coverage."></a>
    <span>1/3 arcsecond (10m).</span>
  </div>
</div>


Two higher resolutions have partial coverage focused on more urbanised areas.


<div style="display:flex; justify-content: space-between; font-style: italic; text-align: center; flex-wrap: wrap">
  <div style="max-width: 49%; padding-bottom: 2rem">
    <a href="/img/ned-19-sec.png"><img src="/img/ned-19-sec.png" alt="NED 1/9 arcsecond coverage."></a>
    <span>1/9 arcsecond (3m).</span>
  </div>
  <div style="max-width: 49%; padding-bottom: 2rem">
    <a href="/img/ned-1-m.png"><img src="/img/ned-1-m.png" alt="NED 1 meter coverage."></a>
    <span>1m.</span>
  </div>
</div>

And there are separate datasets with full coverage of Alaska at 2 arseconds (60m) and 5m.


<div style="display:flex; justify-content: space-between; font-style: italic; text-align: center; flex-wrap: wrap">
  <div style="max-width: 49%; padding-bottom: 2rem">
    <a href="/img/ned-2-sec-alaska.png"><img src="/img/ned-2-sec-alaska.png" alt="NED 2 arcsecond coverage."></a>
    <span>2 arcsecond (60m).</span>
  </div>
  <div style="max-width: 49%; padding-bottom: 2rem">
    <a href="/img/ned-5-m-alaska.png"><img src="/img/ned-5-m-alaska.png" alt="NED 5 meter coverage."></a>
    <span>5m.</span>
  </div>
</div>

Coverage screenshots are from [The National Map](https://viewer.nationalmap.gov/basic/).


## Adding NED 10m to Open Topo Data

Make a new folder for the dataset:

```bash
mkdir ./data/ned10m
```

Download the files from [USGS](https://prd-tnm.s3.amazonaws.com/index.html?prefix=StagedProducts/Elevation/13/TIFF/) into `./data/ned10m`. You want the `USGS_13_xxxxxxx.tif` files.

Next, Open Topo Data needs the filenames to match the SRTM format: the filename should be the coordinates of the lower-left corner. Here's the Python code I used to do the conversion.

```python
from glob import glob
import os
import re

old_pattern = './data/ned10m/USGS_13_*.tif'
old_paths = list(glob(old_pattern))
print('Found {} files'.format(len(old_paths)))

for old_path in old_paths:
    folder = os.path.dirname(old_path)
    old_filename = os.path.basename(old_path)

    # Extract northing.
    res = re.search(r'([ns]\d\d)', old_filename)
    old_northing = res.groups()[0]

    # Fix the NS 
    n_or_s = old_northing[0]
    ns_value = int(old_northing[1:3])
    if old_northing[:3] == 'n00':
        new_northing = 's01' + old_northing[3:]
    elif n_or_s == 'n':
        new_northing = 'n' + str(ns_value - 1).zfill(2) + old_northing[3:]
    elif n_or_s == 's':
        new_northing = 's' + str(ns_value + 1).zfill(2) + old_northing[3:]
    new_filename = old_filename.replace(old_northing, new_northing)
    assert new_northing in new_filename

    # Prevent new filename from overwriting old tiles.
    parts = new_filename.split('.')
    parts[0] = parts[0] + '_renamed'
    new_filename = '.'.join(parts)

    # Rename in place.
    new_path = os.path.join(folder, new_filename)
    os.rename(old_path, new_path)
```

Create a `config.yaml` file:

```yaml
datasets:
- name: ned10m
  path: data/ned10m/
  filename_epsg: 4269
```

Rebuild to enable the new dataset at [localhost:5000/v1/ned10m](http://localhost:5000/v1/ned10m?locations=37.653512,-119.410503).

```bash
make build && make run
```



## Public API

The Open Topo Data public API lets you query NED 10m for free:

```
curl https://api.opentopodata.org/v1/ned10m?locations=37.6535,-119.4105
```

```json
{
  "results": [
    {
      "elevation": 3498.298583984375, 
      "location": {
        "lat": 37.6535, 
        "lng": -119.4105
      },
      "dataset": "ned10m"
    }
  ], 
  "status": "OK"
}
```

NED is still being updated by USGS. The dataset used by the public API was last updated 2020-04-23.

