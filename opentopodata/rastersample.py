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
    None,
]

# Resampling algorithms supported by rastersample.
ZARR_SUPPORTED_RESAMPLING = [
    Resampling.nearest,
    Resampling.bilinear,
]

# How many points are needed until zarr is faster than rasterio.
ZARR_MIN_POINTS = 1


class UnsupportedZarrFile(IOError):
    pass


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

    Will try to use zarr (which is much faster), falling back to rasterio.

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

    # Early exit for small queries (which are faster with rasterio).
    if len(rows) < ZARR_MIN_POINTS:
        return _sample_rasterio(rows, cols, rasterio_fh, path, interpolation)

    # Get elevation.
    try:
        return _sample_zarr(rows, cols, rasterio_fh, path, interpolation)
    except UnsupportedZarrFile:
        return _sample_rasterio(rows, cols, rasterio_fh, path, interpolation)
    except Exception as e:
        return _sample_rasterio(rows, cols, rasterio_fh, path, interpolation)

    return z_all


def _sample_rasterio(rows, cols, fh, path, interpolation):
    """Read raster using rasterio.

    Read the locations, using a 1x1 window. The `masked` kwarg makes rasterio
    replace NODATA values with np.nan. The `boundless` kwarg forces the
    windowed elevation to be a 1x1 array, even when it all values are NODATA,
    though it is very slow. Requred for correctness.
    """
    z_all = []
    for i, (row, col) in enumerate(zip(rows, cols)):
        window = rasterio.windows.Window(col, row, 1, 1)
        z_array = fh.read(
            indexes=1,
            window=window,
            resampling=interpolation,
            out_dtype=float,
            boundless=False,
            masked=True,
        )
        z = np.ma.filled(z_array, np.nan)[0][0]
        z_all.append(z)
    return np.asarray(z_all)


def _sample_zarr(rows, cols, fh, path, interpolation):
    # First, validate.
    print(fh.meta)
    if driver := fh.meta.get("driver") != "GTiff":
        raise UnsupportedZarrFile(f"Tifffile requires a geotiff file, not {driver}.")
    if (compression := fh.meta.get("compression")) not in ZARR_SUPPORTED_COMPRESSION:
        raise UnsupportedZarrFile(f"Unsupported compression {compression}")
    if interpolation not in ZARR_SUPPORTED_RESAMPLING:
        raise UnsupportedZarrFile(f"Unsupported interpolation {interpolation}")

    # Load using zarr.
    rows = np.asarray(rows)
    cols = np.asarray(cols)
    try:
        f = tifffile.imread(path, aszarr=True)
        za = zarr.open(f, mode="r")

        # Manual interpolation.
        if interpolation == Resampling.nearest:
            rows = np.round(rows).astype(int)
            cols = np.round(cols).astype(int)
            z_all = za.get_coordinate_selection((rows, cols)).astype(np.float32)
            if fh.nodata:
                z_all[np.isclose(z_all, fh.nodata)] = np.nan
        elif interpolation == Resampling.bilinear:
            r_squares, c_squares = _buffer_indices_to_squares(rows, cols)
            r_flat = r_squares.flatten()
            c_flat = c_squares.flatten()
            squares_flat = za.get_coordinate_selection((r_flat, c_flat)).astype(
                np.float32
            )
            squares = squares_flat.reshape(r_squares.shape)
            if fh.nodata:
                squares[np.isclose(squares, fh.nodata)] = np.nan
            z_all = _bilinear_interpolation(squares, rows, cols)

        return z_all

    finally:
        try:
            f.close()
        except:
            pass
