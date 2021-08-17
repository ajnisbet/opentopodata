# BKG

[BKG](https://www.bkg.bund.de/) (Bundesamt für Kartographie und Geodäsie) has published a number of elevation datasets for Germany. The [200m](http://gdz.bkg.bund.de/index.php/default/digitale-geodaten/digitale-gelandemodelle/digitales-gelandemodell-gitterweite-200-m-dgm200.html) and [1000m](https://gdz.bkg.bund.de/index.php/default/digitale-geodaten/digitale-gelandemodelle/digitales-gelandemodell-gitterweite-1000-m-dgm1000.html) resolutions are freely available, while resolutions [up to 5m](https://gdz.bkg.bund.de/index.php/default/digitale-geodaten/digitale-gelandemodelle.html) can be purchased for a small fee.



<p style="text-align:center; padding: 1rem 0">
  <img src="/img/bkg200m.png" alt="EU-DEM elevation">
  <br>
  <em>Render of BKG 200m DTM elevation.</em>
</p>


## Adding 200m BKG Digital Terrain Model to Open Topo Data

Make a new folder for the dataset:

```bash
mkdir ./data/bkg200m
```

Download the [dataset](https://daten.gdz.bkg.bund.de/produkte/dgm/dgm200/aktuell/dgm200.utm32s.gridascii.zip), the link here is for the UTM referenced dataset in `.asc` format. Extract the zip and copy only `dgm200_utm32s.asc` and `dgm200_utm32s.prj` into `./data/bkg200m`. 

Add the dataset to `config.yaml`:

```yaml
- name: bkg200m
  path: data/bkg200m
```

Finally, rebuild to enable the new dataset at [localhost:5000/v1/bkg200m?locations=49.427,7.753](http://localhost:5000/v1/bkg200m?locations=49.427,7.753).

```bash
make build && make run
```




## Adding 5m Germany DEM to Open Topo Data

I don't have access to the higher-resolution datasets, but one user managed to get them working with Open Topo Data in issues [#22](https://github.com/ajnisbet/opentopodata/issues/22) and [#24](https://github.com/ajnisbet/opentopodata/issues/24).

The files come with a projection format that isn't supported by GDAL and with non-overlapping tiles so queries near the edges will return `null` data. Probably the easiest way to handle these issues is to merge all the files into one big geotiff:


```bash
gdalbuildvrt -tap -a_srs epsg:3044 -o bkg-dgm5.vrt dgm5/*.asc
gdaltranslate -co COMPRESS=DEFLATE -co BIGTIFF=YES -co NUM_THREADS=ALL_CPUS bkg-dgm5.vrt bkg-dgm5.tif
```

You could also [add a buffer](../notes/buffering-tiles.md) to each tile, fixing the projection with `-a_srs epsg:3044`.

If anyone has got this working and would like to share their steps, please open an [issue](https://github.com/ajnisbet/opentopodata/issues) or [pull request](https://github.com/ajnisbet/opentopodata/pulls)!



## Public API

The Open Topo Data public API lets you query 200m BKG DEM over Germany for free:

```
curl https://api.opentopodata.org/v1/bkg200m?locations=49.427,7.753
```

```json
{
  "results": [
    {
      "elevation": 269.9404602050781, 
      "location": {
        "lat": 49.427, 
        "lng": 7.753
      },
      "dataset": "bkg200m"
    }
  ], 
  "status": "OK"
}
```

## Attribution

© GeoBasis-DE / BKG (Jahr des Datenbezugs)

[Datenlizenz Deutschland – Namensnennung – Version 2.0](https://www.govdata.de/dl-de/by-2-0)



