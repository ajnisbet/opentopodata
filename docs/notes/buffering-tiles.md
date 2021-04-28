# Adding a Buffer to Tiles

Most tiled elevation datasets have an overlap: a 1 pixel overlap lets you interpolate locations between pixels at the edge, and some datasets (like those produced by USGS) have larger datasets that give more flexibility with interpolation and resampling.

However not all datasets come with an overlap, which makes it impossible to interpolate locations within 1 pixel of the edge of a tile without opening multiple files. Because Open Topo Data only opens one file for each location, it may return `null` for these border locations in non-overlapping datasets.

This isn't a problem for everyone: if your tiles are large enough, only a very small fraction of pixels lie on the edges so you may never notice issues.

But to fix this problem you can add a buffer to the tile files. I'll use EU-DEM as an example, as the tiles by default have no overlap.

Start by downloading the 27 `.TIF` files into `./data/eudem`. You'll also need to install the [gdal](https://gdal.org/) commandline tools.

Next we'll make a VRT file for the rasters

```bash
mkdir ./data/eudem-vrt
cd ./data/eudem-vrt
gdalbuildvrt -tr 25 25 -tap -te 0 0 8000000 6000000 -co VRT_SHARED_SOURCE=0 eudem.vrt ../eudem/*.TIF
cd ../../
```

The `tr`, `tap`, and `te` options in the above command ensure that slices from the VRT will use the exact values and grid of the source rasters.


Now we could actually stop here: if we add the `eudem-vrt` as a single-file dataset, Open Topo Data will handle the boundaries just fine. But for a slight performance improvement we can slice the VRT back into it's original tiles with an overlap. The following code will make put buffered tiles into `data/eudem-buffered`:


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
buffer_size = 25

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

after rebuilding:

```bash
make build && make run
```
