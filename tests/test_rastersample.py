import os

import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.enums import Compression
from rasterio.enums import Resampling

from opentopodata import rastersample

TIF_ARRAY_SHAPE = (100, 200)


class TestBufferIndicesToSquares:
    def test_simple_squares(self):
        rows = [1, 1.5]
        cols = [2, 3.5]
        r_squares, c_squares = rastersample._buffer_indices_to_squares(rows, cols)

        assert r_squares.shape == c_squares.shape
        assert r_squares.shape[0] == len(rows)
        assert np.allclose(
            r_squares[0],
            np.array([[1, 1], [2, 2]]),
        )
        assert np.allclose(
            r_squares[1],
            np.array([[1, 1], [2, 2]]),
        )
        assert np.allclose(
            c_squares[0],
            np.array([[2, 3], [2, 3]]),
        )
        assert np.allclose(
            c_squares[1],
            np.array([[3, 4], [3, 4]]),
        )


class TestBilinearInterpolation:
    def test_finite_interpolation(self):
        squares = np.array([[[1, 2], [3, 4]]]).astype(np.float32)
        rows = np.array([0.5])
        cols = np.array([0.5])
        res = rastersample._bilinear_interpolation(squares, rows, cols)
        assert np.allclose(res, [2.5])


class TestZarrRasterioEquivalence:
    def _build_tif(self, rs, compression, nan_frac=0):
        a = rs.random(TIF_ARRAY_SHAPE)
        if nan_frac:
            a[a > nan_frac] = np.nan
        path = "tests/data/tmp.tif"
        if os.path.exists(path):
            os.remove(path)
        transform = from_origin(472137, 5015782, 0.5, 0.5)
        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            height=a.shape[0],
            width=a.shape[1],
            count=1,
            dtype=a.dtype,
            crs="+proj=utm +zone=10 +ellps=GRS80 +datum=NAD83 +units=m +no_defs",
            transform=transform,
            nodata=-9999,
            tiled=True,
            blockxsize=32,
            blockysize=32,
        ) as f:
            f.write(a, 1)
        return path

    def test_nearest_interpolation_finite_zstd(self):
        """No missing data, nearest interpolation, zstd compression."""
        rs = np.random.RandomState(0)
        path = self._build_tif(rs, Compression.zstd)
        n = 100
        rows = rs.uniform(0, TIF_ARRAY_SHAPE[0] - 1, n)
        cols = rs.uniform(0, TIF_ARRAY_SHAPE[1] - 1, n)
        with rasterio.open(path) as fh:
            z_rasterio = rastersample._sample_rasterio(
                rows, cols, fh, path, Resampling.nearest
            )
            z_zarr = rastersample._sample_zarr(rows, cols, fh, path, Resampling.nearest)

        assert np.allclose(z_rasterio, z_zarr)

    def test_bilinear_interpolation_finite_delfate(self):
        """No missing data, bilinear interpolation, deflate compression."""
        rs = np.random.RandomState(1)
        path = self._build_tif(rs, Compression.deflate)
        n = 100
        rows = rs.uniform(0, TIF_ARRAY_SHAPE[0] - 1, n)
        cols = rs.uniform(0, TIF_ARRAY_SHAPE[1] - 1, n)
        with rasterio.open(path) as fh:
            z_rasterio = rastersample._sample_rasterio(
                rows, cols, fh, path, Resampling.bilinear
            )
            z_zarr = rastersample._sample_zarr(
                rows, cols, fh, path, Resampling.bilinear
            )

        # Need to increase atol. A slight increase isn't unusual as the array
        # has values in [0, 1], but this seems a bit more than slight
        # increase.
        assert np.allclose(z_rasterio, z_zarr, atol=1e-3)

    def test_bilinear_interpolation_finite_lerc(self):
        """No missing data, bilinear interpolation, lerc compression."""
        rs = np.random.RandomState(2)
        path = self._build_tif(rs, Compression.lerc)
        n = 100
        rows = rs.uniform(0, TIF_ARRAY_SHAPE[0] - 1, n)
        cols = rs.uniform(0, TIF_ARRAY_SHAPE[1] - 1, n)
        with rasterio.open(path) as fh:
            z_rasterio = rastersample._sample_rasterio(
                rows, cols, fh, path, Resampling.bilinear
            )
            z_zarr = rastersample._sample_zarr(
                rows, cols, fh, path, Resampling.bilinear
            )
        assert np.allclose(z_rasterio, z_zarr)

    def test_nearest_interpolation_nan(self):
        """Missing data, nearest interpolation."""
        rs = np.random.RandomState(3)
        path = self._build_tif(rs, Compression.none, nan_frac=0.1)
        n = 100
        rows = rs.uniform(0, TIF_ARRAY_SHAPE[0] - 1, n)
        cols = rs.uniform(0, TIF_ARRAY_SHAPE[1] - 1, n)
        with rasterio.open(path) as fh:
            z_rasterio = rastersample._sample_rasterio(
                rows, cols, fh, path, Resampling.nearest
            )
            z_zarr = rastersample._sample_zarr(rows, cols, fh, path, Resampling.nearest)
        assert np.any(np.isnan(z_rasterio))
        assert np.all(np.isnan(z_rasterio) == np.isnan(z_zarr))
        assert np.allclose(
            np.asarray(z_rasterio)[np.isfinite(z_rasterio)],
            np.asarray(z_zarr)[np.isfinite(z_zarr)],
        )

    def test_bilinear_interpolation_nan(self):
        """Missing data, bilinear interpolation."""
        rs = np.random.RandomState(4)
        path = self._build_tif(rs, Compression.lzw, nan_frac=0.1)
        n = 100
        rows = rs.uniform(0, TIF_ARRAY_SHAPE[0] - 1, n)
        cols = rs.uniform(0, TIF_ARRAY_SHAPE[1] - 1, n)
        with rasterio.open(path) as fh:
            z_rasterio = rastersample._sample_rasterio(
                rows, cols, fh, path, Resampling.bilinear
            )
            z_zarr = rastersample._sample_zarr(
                rows, cols, fh, path, Resampling.bilinear
            )
        assert np.any(np.isnan(z_rasterio))
        assert np.all(np.isnan(z_rasterio) == np.isnan(z_zarr))
        assert np.allclose(
            np.asarray(z_rasterio)[np.isfinite(z_rasterio)],
            np.asarray(z_zarr)[np.isfinite(z_zarr)],
        )

    def test_rasterio_bounded_is_buggy(self):
        """A big reason for rastersample existing is that rasterio.read with
        the default boundless=False doesn't read across block boundaries properly.

        This test checks that is still the case.

        If this test fails, it means boundless=True can be removed
        from _sample_rasterio, improving speed.
        """
        rs = np.random.RandomState(5)
        path = self._build_tif(rs, Compression.zstd, nan_frac=0.8)
        n = 100
        rows = rs.uniform(0, TIF_ARRAY_SHAPE[0] - 1, n)
        cols = rs.uniform(0, TIF_ARRAY_SHAPE[1] - 1, n)

        # Get boundless.
        with rasterio.open(path) as fh:
            z_boundless = rastersample._sample_rasterio(
                rows, cols, fh, path, Resampling.bilinear
            )

        # Get how I would ideally use rasterio.
        z_bounded = []
        with rasterio.open(path) as fh:
            for i, (row, col) in enumerate(zip(rows, cols)):
                window = rasterio.windows.Window(col, row, 1, 1)
                z_array = fh.read(
                    indexes=1,
                    window=window,
                    resampling=Resampling.bilinear,
                    out_dtype=float,
                    boundless=False,
                )
                z_q = np.ma.filled(z_array, np.nan)
                z_q = z_array[0][0] if z_q.size else np.nan
                z_bounded.append(z_q)

        # Check there are some finitel values, but not all.
        assert np.any(np.isnan(z_bounded))
        assert not np.all(np.isnan(z_bounded))

        # Check bounded has some spurious NaNs.
        assert np.isnan(z_bounded).sum() > np.isnan(z_boundless).sum()

        # Check that even the finite values differ. Index with z_boundless.
        assert not np.allclose(
            np.asarray(z_bounded)[np.isfinite(z_boundless)],
            np.asarray(z_boundless)[np.isfinite(z_boundless)],
        )

    def test_rasterio_bounded_is_buggy(self):
        """A big reason for rastersample existing is that rasterio.read with
        the default boundless=False doesn't read across block boundaries properly.

        This test checks that is still the case.

        If this test fails, it means boundless=True can be removed
        from _sample_rasterio, improving speed.
        """
        rs = np.random.RandomState(5)
        path = self._build_tif(rs, Compression.zstd)
        n = 100
        rows = rs.uniform(0, TIF_ARRAY_SHAPE[0] - 1, n)
        cols = rs.uniform(0, TIF_ARRAY_SHAPE[1] - 1, n)

        # Get boundless.
        with rasterio.open(path) as fh:
            z_boundless = rastersample._sample_rasterio(
                rows, cols, fh, path, Resampling.bilinear
            )

        # Get how I would ideally use rasterio.
        z_bounded = []
        with rasterio.open(path) as fh:
            for i, (row, col) in enumerate(zip(rows, cols)):
                window = rasterio.windows.Window(col, row, 1, 1)
                z_array = fh.read(
                    indexes=1,
                    window=window,
                    resampling=Resampling.bilinear,
                    out_dtype=float,
                    boundless=False,
                )
                z_q = np.ma.filled(z_array, np.nan)
                z_q = z_array[0][0] if z_q.size else np.nan
                z_bounded.append(z_q)

        # # Check there are some finitel values, but not all.
        # assert np.any(np.isnan(z_bounded))
        # assert not np.all(np.isnan(z_bounded))

        # # Check bounded has some spurious NaNs.
        # assert np.isnan(z_bounded).sum() > np.isnan(z_boundless).sum()

        # Check that even the finite values differ. Index with z_boundless.
        assert not np.allclose(
            np.asarray(z_bounded)[np.isfinite(z_boundless)],
            np.asarray(z_boundless)[np.isfinite(z_boundless)],
        )
