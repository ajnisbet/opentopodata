# Invalid SRTM zips over the Caspian sea

If you're working with SRTM tiles in `.hgt.zip` format you might have found some files that can't be processed by gdal (and therefore can't be processed by Open Topo Data):

```bash
gdalinfo N44E049.SRTMGL1.hgt.zip
```

```
ERROR 4: `N44E049.SRTMGL1.hgt.zip' not recognized as a supported file format.
gdalinfo failed - unable to open 'N44E049.SRTMGL1.hgt.zip'.
```

There are 16 tiles with this issue

```
N37E051
N37E052
N38E050
N38E051
N38E052
N39E050
N39E051
N40E051
N41E050
N41E051
N42E049
N42E050
N43E048
N43E049
N44E048
N44E049
```

all of which cover no-land areas of the Caspian Sea

<p style="text-align:center; padding: 1rem 0">
  <img src="/img/srtm-invalid-caspian-zips.png" alt="Map showing location of invalid SRTM zips">
  <br>
  <em>Invalid tiles shown in pink. Basemap is Bing aerial imagery.</em>
</p> 

and have a constant elevation of -29m

```bash
gdalinfo -mm N44E049.hgt | grep Min
```

```
Computed Min/Max=-29.000,-29.000
```



## What's the issue

Normal `.hgt.zip` files are a zip archive containing a file named like `NxxEyyy.hgt`

```bash
unzip -l N37E011.SRTMGL1.hgt.zip
```

```
Archive:  N37E011.SRTMGL1.hgt.zip
  Length      Date    Time    Name
---------  ---------- -----   ----
 25934402  2012-10-08 15:44   N37E011.hgt
---------                     -------
 25934402                     1 file

```

But the zips over the Caspian sea contain a file named like `NxxEyyy.SRTMGL1.hgt`

```bash
unzip -l N44E049.SRTMGL1.hgt.zip
```

```
Archive:  N44E049.SRTMGL1.hgt.zip
  Length      Date    Time    Name
---------  ---------- -----   ----
 25934402  2015-08-10 10:24   N44E049.SRTMGL1.hgt
---------                     -------
 25934402                     1 file
```

and unfortunately while GDAL will read `NxxEyyy[.something].hgt` and `NxxEyyy[.something].hgt.zip` files just fine, the `.hgt` file inside the `.zip` file must be named `NxxEyyy.hgt`.


Because these tiles all have a constant value (the elevation of the Caspian sea, which is about -29m) and weren't even included in the previous version of SRTM, I'm guessing the files went through a different pipeline to the rest of the datasets. I'm not sure if this is a bug with gdal or the dataset itself.

## How to fix these files

The 16 invalid tiles can be fixed by renaming the `.hgt` file contained within:

```bash
unzip N44E049.SRTMGL1.hgt.zip
mv N44E049.SRTMGL1.hgt N44E049.hgt
zip N44E049.SRTMGL1.repacked.hgt.zip N44E049.hgt
```





## Which datasets are affected

Both the 30m and 90m resolutions of SRTM version 3 hosted on [usgs.gov/MEASURES](https://e4ftl01.cr.usgs.gov/MEASURES/) are affected.

[Version 2](https://dds.cr.usgs.gov/srtm/version2_1/SRTM3/) of SRTM just excludes the 16 tiles over the Caspian sea: 


<p style="text-align:center; padding: 1rem 0">
  <img src="/img/srtm-v2-caspian-files-screenshot.png" alt="Missing srtm v2 files.">
  <br>
  <em><a href="https://dds.cr.usgs.gov/srtm/version2_1/SRTM3/Eurasia/">dds.cr.usgs.gov/srtm/version2_1/SRTM3/Eurasia/</a></em>
</p> 


The [Cigar version 4.1](https://cgiarcsi.community/data/srtm-90m-digital-elevation-database-v4-1/) of SRTM has the correct elevation.

