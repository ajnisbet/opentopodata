# Release Notes

This is a list of changes to Open Topo Data between each release.


## Version 1.7.0 (7 Oct 2021)

* Support POST requests ([#49](https://github.com/ajnisbet/opentopodata/issues/49)).
* Dataset name can no longer be null for multi-dataset requests.



## Version 1.6.0 (7 Sep 2021)

* Added support for samples along a path ([#37](https://github.com/ajnisbet/opentopodata/issues/37)).
* Added version response header ([#47](https://github.com/ajnisbet/opentopodata/issues/47)).
* Enabled cors in example config file.

## Version 1.5.2 (17 Aug 2021)

* Updated dependencies.


## Version 1.5.1 (28 Apr 2021)

* Updated dependencies, including to rasterio 1.2.3.
* Fix some typos in scripts in the documentation.

## Version 1.5.0 (5 Feb 2021)

* Big performance improvements, thanks to caching expensive coordinate transforms, reducing the need to deserialise cached objects, and scaling processes to the machine being used.
* Add [BKG](datasets/bkg.md) data.
* Add [Multiple Dataset](notes/multiple-datasets.md) feature.
* Updated rasterio and pyproj dependencies.


## Version 1.4.1 (10 Dec 2020)

* [Increased](https://github.com/ajnisbet/opentopodata/issues/21) max URI length.
* [Support](https://github.com/ajnisbet/opentopodata/issues/19#issuecomment-741858650) datasets with `.prj` files.
* Docs fixes. 
* Small dependency updates.


## Version 1.4.0 (9 Nov 2020)

* Fixes bug [#13](https://github.com/ajnisbet/opentopodata/issues/13) where responses could return invalid json. This changes the NODATA value from `NaN` to `null`. The old behaviour can be enabled by sending a `nodata_value=nan` query parameter.
* Small dependency updates.

## Version 1.3.1 (23 Oct 2020)

* Improved code style and test coverage.
* Updated dependencies.
* Documentation for running on Windows.



## Version 1.3.0 (4 Sep 2020)

* Added `/health` endpoint.


## Version 1.2.4 (8 Aug 2020)

* Support for more raster filename formats, as raised in issue [#8](https://github.com/ajnisbet/opentopodata/issues/8).


## Version 1.2.3 (31 July 2020)

* Minor documentation fixes and dependency updates.


## Version 1.2.2 (2 July 2020)

* Documentation fixes.
* I'm now using [pip-tools](https://github.com/jazzband/pip-tools) to manage python dependencies, and I'm really liking it. Exact dependency versions are now pinned, but it's easy to update them to the latest version.
* Updated dependencies. 


## Version 1.2.1 (22 May 2020)

Improved documentation, plus some bug fixes:

* Fix floating-point precision issue that was breaking requests on dataset boundaries.
* Ignore common non-raster files.


## Version 1.2.0 (10 May 2020)

Added a bunch of new datasets to the public API:

* GEBCO bathymetry.
* EMOD bathymetry.
* NZ 8m DEM.
* Mapzen 30m DEM.


## Version 1.1.0 (25 April 2020)

* Added this changelog! Pushing to master now means a release with a changelog entry.
* Added VERSION.txt, docker images get tagged with version when built.
* Documented install instructions and a brief overview for the datasets used in the public API.
* Makefile improvements (suggested by a user, thank you!).
* Increased the public API daily request limit to 1000.
* Updated [NED](/datasets/ned/) on the public API.
* Added CORS header support.

