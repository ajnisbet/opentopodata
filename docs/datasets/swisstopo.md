# Swisstopo


The [Swisstopo](https://www.swisstopo.admin.ch/en/swisstopo/organisation.html) Federal Office of Topography publishes a number of datasets, including very high quality elevation data for the whole of Switzerland at 0.5m and 2m resolutions under the name [swissALTI](https://www.swisstopo.admin.ch/en/geodata/height/alti3d.html). The data is regularly updated.



## Adding 2m Swiss DEM to Open Topo Data

(The procedure is the same for the 0.5m product as the tiles are the same 1km extent).

Make a new folder for the dataset:

```bash
mkdir ./data/swisstopo-2m
```

Download the urls of each tile from [swisstopo](https://www.swisstopo.admin.ch/en/geodata/height/alti3d.html). When I did this in 2021 there were 43,579 tiles.

Download each tile. `wget` can do this. Consider doing the downloads sequentially with a rate-limit to avoid overloading their servers.

```bash
wget --input-file ch.swisstopo.swissalti3d-xxxxx.csv --no-clobber --limit-rate 1M
```



Open Topo Data needs files to be named with the lower-left corner coordinates. The files from swisstopo are named like this, but in km instead of metres. I use the following Python script to take a file named like

```txt
swissalti3d_2019_2622-1264_2_2056_5728.tif
```

and rename it to 

```txt
swissalti3d_2019_2622-1264_2_2056_5728.N1264000E2622000.tif
```


```python
from glob import glob
import os


dataset_folder = './data/swisstopo-2m/'
pattern = os.path.join(dataset_folder, '**', '*.tif')
paths = sorted(glob(pattern, recursive=True))


for old_path in paths:

    # Extract lower-left corder from filename.
    old_filename = os.path.basename(old_path)
    extent = old_filename.split('_')[2]
    northing = extent.split('-')[1]
    easting = extent.split('-')[0]

    # Convert from km to m.
    northing = int(northing) * 1000
    easting = int(easting) * 1000
    
    # Build new filename.
    new_filename = old_filename.rsplit('.', 1)[0]
    new_filename = new_filename + f'.N{northing}E{easting}.tif'
    new_path = os.path.join(os.path.dirname(old_path), new_filename)
    
    # Rename the file.
    os.rename(old_path, new_path)
```


The final step is adding the to `config.yaml`:

```yaml
- name: swisstopo-2m
  path: data/swisstopo-2m/
  filename_epsg: 2056
  filename_tile_size: 1000
```


## Public API

The Open Topo Data public server is full to the brim with elevation data at the moment! Swisstopo is first on the waiting list to be added once I upgrade the server. 

2m Swiss elevation data is included in [GPXZ](https://www.gpxz.io/)

## Attribution

[©swisstopo](https://www.swisstopo.admin.ch/en/home/meta/conditions/geodata/ogd.html) 




