# Querying multiple datasets

From v1.5.0, Open Topo Data has the ability to request the "best" elevation from multiple datasets in a single query.

I'm still improving the functionality, please open an issue if you find a problem.

!!! warning "Warning"
    While Open Topo Data lets you query multiple datasets seamlessly, it doesn't ensure that the datasets you're using share the same vertical datum or have seamless transitions.

    A great usecase for Multi Datasets would be if your usage is mostly focussed on an area with contiguous DEM coverage (like the island nation of New Zealand), but you want to technically be able to query worldwide. 

    A bad usecase for Multi Datasets is layering a bunch of patchy 10cm lidar data on top of a 1.8km base DEM and using it to draw small scale elevation profiles.


Say your `config.yaml` looks like this:


```yaml
# Hi-res New Zealand.
- name: nzdem8m
  path: data/nzdem8m/
  filename_tile_size: 65536
  filename_epsg: 2193

# Mapzen global.
- name: mapzen
  path: data/mapzen/
```


You want the following:

* If you query a location in New Zealand, return the hi-res **nzdem** result.
* If you query a location in New Zealand and nzdem is `null` at that location, return the **mapzen** result for that location.
* If you query a location outside New Zealand, return the **mapzen** result for that location.


There are two ways to do this.


### Putting multiple datasets in the url

```bash
curl https://api.opentopodata.org/v1/nzdem8m,mapzen?locations=-43.801,172.968|-18.143,178.444
```

```json
{
  "results": [
    {
      "dataset": "nzdem8m", 
      "elevation": 1.4081547260284424, 
      "location": {
        "lat": -43.801, 
        "lng": 172.968
      }
    }, 
    {
      "dataset": "mapzen", 
      "elevation": 23.0, 
      "location": {
        "lat": -18.143, 
        "lng": 178.444
      }
    }
  ], 
  "status": "OK"
}
```

For each location, the first non-null dataset elevation is returned.


### Defining multi dataset in `config.yaml`

If you have a lot of datasets you want to merge, it's a pain to put them all in the url. Instead you can define a MultiDataset in `config.yaml`:



```yaml
# Hi-res New Zealand.
- name: nzdem8m
  path: data/nzdem8m/
  filename_tile_size: 65536
  filename_epsg: 2193

# Mapzen global.
- name: mapzen
  path: data/mapzen/


# NZ with mapzen fallback.
- name: nz-global
  child_datasets:
	- nzdem8m
	- mapzen
```

Now you can query **nz-global** for the same result.

```bash
curl https://api.opentopodata.org/v1/nz-global?locations=-43.801,172.968|-18.143,178.444
```

```json
{
  "results": [
    {
      "dataset": "nzdem8m", 
      "elevation": 1.4081547260284424, 
      "location": {
        "lat": -43.801, 
        "lng": 172.968
      }
    }, 
    {
      "dataset": "mapzen", 
      "elevation": 23.0, 
      "location": {
        "lat": -18.143, 
        "lng": 178.444
      }
    }
  ], 
  "status": "OK"
}
```



## Performance optimisation

Querying multiple datasets is more performance-intensive than querying a single one. For a Multi Dataset with 10 child datasets where the first 9 are `null` at the queried location, Open Topo Data will have to cover the lat/lon coordinates into the CRS of all 10 datasets to try to find a tile. Worst case, if those 10 tiles exist, Open Topo Data will have to open and read from all 10 files sequentially.

To reduce the number of checks Open Topo Data has to do, you can manually specify the bounds of each dataset, in WGS84 format. If a location is outside those bounds, Open Topo Data doesn't need to check that dataset.

If your `config.yaml` file looks like

```yaml
# Hi-res New Zealand.
- name: nzdem8m
  path: data/nzdem8m/
  filename_tile_size: 65536
  filename_epsg: 2193
    wgs84_bounds:
    left: 165
    right: 180
    bottom: -48
    top: -33

# Mapzen global.
- name: mapzen
  path: data/mapzen/
```

then querying `nzdem8m,mapzen` with a location in Europe will go straight to mapzen without needing to convert the location to `epsg:2193` and check for a tile.