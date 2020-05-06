# GEBCO 2020 Bathymetry

[GEBCO](https://www.gebco.net/) maintains a high-quality, global bathymetry (sea floor depth) dataset.

GEBCO releases a new dataset most years, the 2020 dataset (released in May 2020) covers the entire globe at a 15 arc-second resolution, corresponding to 450m resolution at the equator.

## Coverage

Elevation is given for land areas, largely using a [15-degree version](https://topex.ucsd.edu/WWW_html/srtm15_plus.html) of [SRTM](/datasets/srtm/).

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

Create a `comfig.yaml` file:

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