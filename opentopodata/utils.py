from decimal import Decimal
import math

import numpy as np
import pyproj


WGS84_LATLON_EPSG = 4326

# There's significant overhead in pyproj when building a Transformer object.
# Without a cache a Transformer can be built many times per request, even for
# the same CRS.
_TRANSFORMER_CACHE = {}


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

    # Load transformer.
    to_crs = wkt or f"EPSG:{epsg}"
    if to_crs in _TRANSFORMER_CACHE:
        transformer = _TRANSFORMER_CACHE[to_crs]
    else:
        from_crs = f"EPSG:{WGS84_LATLON_EPSG}"
        transformer = pyproj.transformer.Transformer.from_crs(
            from_crs, to_crs, always_xy=True
        )
        _TRANSFORMER_CACHE[to_crs] = transformer

    # Do the transform.
    x, y = transformer.transform(lons, lats)

    return x, y


def base_floor(x, base=1):
    """Round number down to nearest multiple of base."""
    return base * np.floor(x / base)


def decimal_base_floor(x, base=1):
    """Round decimal down to nearest multiple of base."""
    if not isinstance(base, (Decimal, int)):
        raise ValueError("Base must be an integer or decimal.")
    integer = math.floor(x / float(base))
    return base * Decimal(integer)


def safe_is_nan(x):
    """Is the value NaN (not a number).

    Returns True for np.nan and nan python float. Returns False for anything
    else, including None and non-numeric types.

    Called safe because it won't raise a TypeError for non-numerics.


    Args:
        x: Object to check for NaN.

    Returns:
        Boolean whether the object is NaN.
    """
    try:
        return math.isnan(x)
    except TypeError:
        return False


def fill_na(a, value):
    """Replace NaN values in a with provided value.

    Args:
        a: Iterable, possibly containing NaN items.
        value: WHat NaN values should be replaced with.

    Returns:
        List same length as a, with NaN values replaced.
    """
    return [value if safe_is_nan(x) else x for x in a]
