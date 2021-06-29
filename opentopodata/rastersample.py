from rasterio.enums import Resampling
from rasterio.enums import Compression
import numpy as np
import rasterio
import tifffile
import zarr


# Compression algorithms supported by imagecodecs, defined using rasterio enum.
ZARR_SUPPORTED_COMPRESSION = [
    Compression.zstd,
    Compression.lzw,
    Compression.deflate,
    Compression.packbits,
    Compression.lzma,
    Compression.none,
]

# Resampling algorithms supported by rastersample.
ZARR_SUPPORTED_RESAMPLING = [
    Resampling.nearest,
    Resampling.bilinear,
]


def _bilinear_interpolation(squares, rows, cols):
    """Bilinear interpolation within 2x2 windowed reads.

    TODO: handle nan values exactly like rasterio."""

    # Check input shapes.
    n_points = len(rows)
    assert squares.shape[0] == n_points
    assert squares.shape[1] == 2
    assert squares.shape[2] == 2

    # Use fractional rows/cols to simplify formula.
    r = rows % 1
    c = cols % 1

    # Do interpolation.
    f = np.asarray(squares)
    bl = np.zeros(n_points, dtype=squares.dtype)
    bl += f[:, 0, 0] * (1 - r) * (1 - c)
    bl += f[:, 1, 0] * r * (1 - c)
    bl += f[:, 0, 1] * (1 - r) * c
    bl += f[:, 1, 1] * r * c
    return bl


def _buffer_indices_to_squares(rows, cols):
    r_squares = []
    c_squares = []
    for row, col in zip(rows, cols):
        r = int(row)
        c = int(col)
        r_squares.append(np.array([[r, r], [r + 1, r + 1]]))
        c_squares.append(np.array([[c, c + 1], [c, c + 1]]))
    r_squares = np.array(r_squares)
    c_squares = np.array(c_squares)
    return r_squares, c_squares


def sample(rows, cols, rasterio_fh, path, interpolation):
    """Query a raster in muliple points.

    Instead of

    ```
    z = []
    for x, y in zip(xs, ys):
        z.append(f.sample(x, y))
    ```

    you can do

    ```
    z = sample(rows, cols, f)
    ```

    Compared to rasterio's sample, this function has some convenience features:

    * Pass array indices instead of georeferenced indices.
    * Support non-integer indices with interpolation.
    * Configurable interpolation method.


    But the main benefit is increased performance. This function falls back to
    rasterio, but when conditions are right:

    * geotiff format.
    * Supported compression (ZSTD, LZW, DEFLATE, none, Packbits) (no LERC).
    * Supported interpolation (nearest, bilinear).

    then performance is improved by

    * Reading with zarr+tifffile instead of rasterio.
    * Doing interpolation in numpy instead of gdal.
    * Disabling boundless reads in rasterio.

    TOTO:
    * Extract as a library.
    * Reorder rasterio points by block.
    * Accept path as well as fh.
    * Accept georeferenced coordinates.
    * GTIFF_VIRTUAL_MEM_IO=YES (but only for nearest interpolation).
    * Auto test
        * Cols: 3 different files
        * RowsL sparse, zstd, lerc, deflate, lzw

    Args:
        rows, cols: Iterables of array indices.
        rasterio_fh: Filehandle from rasterio.open().
        path: Location of file, needed by zarr.
        interpolation: A rasterio interpolation method.

    Returns:
        z: Numpy array of raster values.
    """
    # Early exit for no data.
    if len(rows) == 0:
        return np.array([], dtype=np.float32)

    # Get elevation.
    sample_function = _select_optimal_sample_function(rasterio_fh, interpolation)
    z_all = sample_function(rows, cols, rasterio_fh, path, interpolation)
    z_all = np.asarray(z_all)
    return z_all


def _select_optimal_sample_function(rasterio_fh, interpolation):
    """Choose the best function.

    rasterio is the convservative choice.
    """
    if rasterio_fh.compression not in ZARR_SUPPORTED_COMPRESSION:
        return _sample_rasterio

    if interpolation not in ZARR_SUPPORTED_RESAMPLING:
        return _sample_rasterio

    if rasterio_fh.driver != "GTiff":
        return _sample_rasterio

    return _sample_zarr


def _sample_rasterio(rows, cols, fh, path, interpolation):
    """
    Read the locations, using a 1x1 window.

    The `masked` kwarg makes
    rasterio replace NODATA values with np.nan.

    The `boundless` kwarg forces the windowed elevation to be a 1x1 array,
    even when it all values are NODATA, though it is very slow. Requred for
    correctness.
    """
    z_all = []
    for i, (row, col) in enumerate(zip(rows, cols)):
        window = rasterio.windows.Window(col, row, 1, 1)
        z_array = fh.read(
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


def _sample_zarr(rows, cols, fh, path, interpolation):
    rows = np.asarray(rows)
    cols = np.asarray(cols)
    try:
        f = tifffile.imread(path, aszarr=True)
        za = zarr.open(f, mode="r")

        # Manual interpolation.
        if interpolation == Resampling.nearest:
            rows = np.round(rows).astype(int)
            cols = np.round(cols).astype(int)
            z_all = za.get_coordinate_selection((rows, cols))
            if fh.nodata:
                z_all[np.isclose(z_all, fh.nodata)] = np.nan
        elif interpolation == Resampling.bilinear:
            r_squares, c_squares = _buffer_indices_to_squares(rows, cols)
            r_flat = r_squares.flatten()
            c_flat = c_squares.flatten()
            squares_flat = za.get_coordinate_selection((r_flat, c_flat))
            squares = squares_flat.reshape(r_squares.shape)
            if fh.nodata:
                squares[np.isclose(squares, fh.nodata)] = np.nan
            z_all = _bilinear_interpolation(squares, rows, cols)
        else:
            raise ValueError("Unsupported interpolation method.")

        return z_all

    finally:
        try:
            f.close()
        except:
            pass
