import numpy as np
import pyproj


WGS84_LATLON_EPSG = 4326


def reproject_latlons(lats, lons, epsg=None, wkt=None):
    """Convert WGS84 latlons to another projection.

    Args:
        lats, lons: Lists/arrays of latitude/longitude numbers.
        epsg: Integer EPSG code.

    """
    if epsg is None and wkt is None:
        raise ValueError("Must provide either epsg or wkt.")

    if epsg and wkt:
        raise ValueError("Must provide only one of epsg or wkt.")

    if epsg == WGS84_LATLON_EPSG:
        return lons, lats

    # Validate EPSG.
    if epsg is not None and (not 1024 <= epsg <= 32767):
        raise ValueError("Dataset has invalid epsg projection.")

    # Do the transform. Pyproj assumes EPSG:4326 as default source projection.
    if epsg:
        projection = pyproj.Proj(f"EPSG:{epsg}")
    else:
        projection = pyproj.Proj(wkt)
    x, y = projection(lons, lats)

    return x, y


def base_floor(x, base=1):
    return base * np.floor(x / base)
