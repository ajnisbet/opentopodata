import numpy as np
import pyproj


WGS84_LATLON_EPSG = 4326


def reproject_latlons(lats, lons, epsg):
    """Convert WGS84 latlons to another projection.

    Args:
        lats, lons: Lists/arrays of latitude/longitude numbers.
        epsg: Integer EPSG code.

    """
    if epsg == WGS84_LATLON_EPSG:
        return lons, lats

    # Validate EPSG.
    if not 1024 <= epsg <= 32767:
        raise ValueError("Dataset has invalid projection.")

    # Do the transform. Pyproj assumes EPSG:4326 as default source projection.
    projection = pyproj.Proj(init=f"EPSG:{epsg}")
    x, y = projection(lons, lats)

    return x, y


def base_floor(x, base=1):
    return base * np.floor(x / base)
