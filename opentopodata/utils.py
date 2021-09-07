from decimal import Decimal
import math

from geographiclib.geodesic import Geodesic
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


def sample_points_on_path(path_lats, path_lons, n_samples):
    """Find points along a path.

    Args:
        path_lats, path_lons: path coordinates.
        n_samples: number of points to sample.

    Returns:
        points: list of Points.
    """

    # Early exit for 1 or 2 points.
    if n_samples == 2:
        lats = [path_lats[0], path_lats[-1]]
        lons = [path_lons[0], path_lons[-1]]
        return lats, lons

    # Zip paths together.
    path = list(zip(path_lats, path_lons))

    # Get distance between each path.
    geod = Geodesic.WGS84
    path_distances = [0]
    for (start_lat, start_lon), (end_lat, end_lon) in zip(path[:-1], path[1:]):
        path_distances.append(
            geod.Inverse(start_lat, start_lon, end_lat, end_lon)["s12"]
        )

    # Cumulative distance.
    path_distances_cum = np.cumsum(path_distances)

    # For each point, how far along the path should they be?
    point_distances = np.linspace(0, path_distances_cum[-1], n_samples)

    # For each point, find the path locations it lies between, then calculate
    # distance along line.
    points = []
    for point_distance in point_distances:

        # Find start.
        i_start = np.argwhere(point_distance >= path_distances_cum)[:, 0][-1]

        # Early exit for ends.
        if np.isclose(point_distance, path_distances_cum[i_start]):
            points.append(path[i_start])
            continue
        elif i_start == len(path) - 1 or np.isclose(
            point_distance, path_distances_cum[-1]
        ):
            points.append(path[-1])
            continue

        # Helper vars.
        start_lat, start_lon = path[i_start]
        end_lat, end_lon = path[i_start + 1]
        pd_between = point_distance - path_distances_cum[i_start]

        # Now do the computation.
        line = geod.InverseLine(start_lat, start_lon, end_lat, end_lon)
        g_point = line.Position(pd_between, Geodesic.STANDARD | Geodesic.LONG_UNROLL)
        points.append((g_point["lat2"], g_point["lon2"]))

    # Validation.
    assert len(points) == n_samples

    lats = [p[0] for p in points]
    lons = [p[1] for p in points]
    return lats, lons
