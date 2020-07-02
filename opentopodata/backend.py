from glob import glob
import collections
import math
import os
import re

from rasterio.enums import Resampling
import numpy as np
import rasterio

from opentopodata import utils

# Only a subset of rasterio's supported methods are currently activated. In
# the future I might do interpolation in backend.py instead if relying on
# gdal, and I don't want to commit to supporting an interpolation method that
# would be a pain to do in python.
INTERPOLATION_METHODS = {
    "nearest": Resampling.nearest,
    "bilinear": Resampling.bilinear,
    "cubic": Resampling.cubic,
    # 'cubic_spline': Resampling.cubic_spline,
    # 'lanczos': Resampling.lanczos,
}


class InputError(ValueError):
    """Invalid input data.

    The error message should be safe to pass back to the client.
    """

    pass


def _noop(x):
    return x


def _validate_points_lie_within_raster(xs, ys, lats, lons, bounds, res):
    """Check that querying the dataset won't throw an error.

    Args:
        xs, ys: Lists/arrays of x/y coordinates, in projection of file.
        lats, lons: Lists/arrays of lat/lon coordinates. Only used for error message.
        bounds: rastio BoundingBox object.
        res: Tuple of (x_res, y_res) resolutions.

    Raises:
        InputError: if one of the points lies outside bounds.
    """

    # Get actual extent. When storing point data in a pixel-based raster
    # format, the true extent is the centre of the outer pixels, but GDAL
    # reports the extent as the outer edge of the outer pixels. So need to
    # adjust by half the pixel width.
    #
    # Also add an epsilon to account for
    # floating point precision issues: better to validate an invalid point
    # which will error out on the reading anyway, than to invalidate a valid
    # point.
    atol = 1e-8
    x_min = min(bounds.left, bounds.right) + abs(res[0]) / 2 - atol
    x_max = max(bounds.left, bounds.right) - abs(res[0]) / 2 + atol
    y_min = min(bounds.top, bounds.bottom) + abs(res[1]) / 2 - atol
    y_max = max(bounds.top, bounds.bottom) - abs(res[1]) / 2 + atol

    # Check bounds.
    x_in_bounds = (xs >= x_min) & (xs <= x_max)
    y_in_bounds = (ys >= y_min) & (ys <= y_max)

    # Raise exception if out of bounds.
    if not all(y_in_bounds):
        i_oob = np.argmax(y_in_bounds)
        lat = lats[i_oob]
        lon = lons[i_oob]
        msg = "Location '{},{}' has latitude outside of raster bounds".format(lat, lon)
        raise InputError(msg)
    if not all(x_in_bounds):
        i_oob = np.argmax(x_in_bounds)
        lat = lats[i_oob]
        lon = lons[i_oob]
        msg = "Location '{},{}' has longitude outside of raster bounds".format(lat, lon)
        raise InputError(msg)


def _get_elevation_from_path(lats, lons, path, interpolation):
    """Read values at locations in a raster.

    Args:
        lats, lons: Arrays of latitudes/longitudes.
        path: GDAL supported raster location.
        interpolation: method name string.

    Returns:
        z_all: List of elevations, same length as lats/lons.
    """
    z_all = []
    interpolation = INTERPOLATION_METHODS.get(interpolation)
    lons = np.asarray(lons)
    lats = np.asarray(lats)

    with rasterio.open(path) as f:
        if f.crs is None:
            msg = "Dataset has no coordinate reference system."
            msg += " Check the file '{path}' is a geo raster."
            msg += " Otherwise you'll have to add the crs manually with a tool like gdaltranslate."
            raise InputError(msg)

        try:
            if f.crs.is_epsg_code:
                xs, ys = utils.reproject_latlons(lats, lons, epsg=f.crs.to_epsg())
            else:
                xs, ys = utils.reproject_latlons(lats, lons, wkt=f.crs.to_wkt())
        except ValueError:
            raise InputError("Unable to transform latlons to dataset projection.")

        # Check bounds.
        _validate_points_lie_within_raster(xs, ys, lats, lons, f.bounds, f.res)
        rows, cols = tuple(f.index(xs, ys, op=_noop))

        # Offset by 0.5 to convert from center coords (provided by
        # f.index) to ul coords (expected by f.read).
        rows = np.array(rows) - 0.5
        cols = np.array(cols) - 0.5

        # Because of floating point precision, indices may slightly exceed
        # array bounds. Because we've checked the locations are within the
        # file bounds,  it's safe to clip to the array shape.
        rows = rows.clip(0, f.height - 1)
        cols = cols.clip(0, f.width - 1)

        # Read the locations, using a 1x1 window. The `masked` kwarg makes
        # rasterio replace NODATA values with np.nan. The `boundless` kwarg
        # forces the windowed elevation to be a 1x1 array, even when it all
        # values are NODATA.
        for row, col in zip(rows, cols):
            window = rasterio.windows.Window(col, row, 1, 1)
            z_array = f.read(
                indexes=1,
                window=window,
                resampling=interpolation,
                out_dtype=float,
                boundless=True,
                masked=True,
            )
            z = np.ma.filled(z_array, np.nan)[0][0]
            z_all.append(z)
    return z_all


def get_elevation(lats, lons, dataset, interpolation="nearest"):
    """Read elevations from a dataset.

    A dataset may consist of multiple files, so need to determine which
    locations lies in which file, then loop over the files.

    Args:
        lats, lons: Arrays of latitudes/longitudes.
        dataset: config.Dataset object.
        interpolation: method name string.

    Returns:
        elevations: List of elevations, same length as lats/lons.
    """

    # Which paths we need results from.
    lats = np.array(lats)
    lons = np.array(lons)
    paths = dataset.location_paths(lats, lons)

    # Store mapping of tile path to point so we can merge back together later.
    elevations_by_path = {}
    path_to_point_index = collections.defaultdict(list)
    for i, path in enumerate(paths):
        path_to_point_index[path].append(i)

    # Batch results by path.
    for path, indices in path_to_point_index.items():
        if path is None:
            elevations_by_path[None] = [None] * len(indices)
            continue
        batch_lats = lats[path_to_point_index[path]]
        batch_lons = lons[path_to_point_index[path]]
        elevations_by_path[path] = _get_elevation_from_path(
            batch_lats, batch_lons, path, interpolation
        )

    # Put the results back again.
    elevations = [None] * len(paths)
    for path, path_elevations in elevations_by_path.items():
        for i_path, i_original in enumerate(path_to_point_index[path]):
            elevations[i_original] = path_elevations[i_path]

    return elevations
