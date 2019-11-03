from opentopodata import backend
import rasterio
import pytest
import numpy as np
from unittest.mock import patch

from opentopodata import config


ETOPO1_GEOTIFF_PATH = "tests/data/datasets/test-etopo1-resampled-1deg/ETOPO1_Ice_g_geotiff.resampled-1deg.tif"
ETOPO1_DATASET_NAME = "test-dataset"
SRTM_DATASET_NAME = "srtm90subset"
SRTM_UTM_DATASET_NAME = "srtm90utm"
NO_FILL_VALUE_CONFIG_PATH = "tests/data/configs/no-fill-value.yaml"
TEST_CONFIG_PATH = "tests/data/configs/test-config.yaml"
SRTM_FILL_VALUE = np.nan


@pytest.fixture
def patch_config():
    with patch("opentopodata.config.CONFIG_PATH", TEST_CONFIG_PATH):
        yield


def test_noop():
    x = "Test"
    assert backend._noop(x) == x


class TestValidatePointsLieWithinRaster:
    bounds = rasterio.coords.BoundingBox(-101, -51, 101, 51)  # L,B,R,T
    res = (2, 2)

    def test_valid_points_on_boundary(self):
        lats = np.array([0, -50, 50])
        lons = np.array([0, -100, 100])
        backend._validate_points_lie_within_raster(
            lons, lats, lats, lons, self.bounds, self.res
        )

    def test_invalid_bottom(self):
        lats = np.array([self.bounds.bottom])
        lons = np.array([0])
        with pytest.raises(backend.InputError):
            backend._validate_points_lie_within_raster(
                lons, lats, lats, lons, self.bounds, self.res
            )

    def test_invalid_top(self):
        lats = np.array([self.bounds.top])
        lons = np.array([0])
        with pytest.raises(backend.InputError):
            backend._validate_points_lie_within_raster(
                lons, lats, lats, lons, self.bounds, self.res
            )

    def test_invalid_left(self):
        lats = np.array([0])
        lons = np.array([self.bounds.left])
        with pytest.raises(backend.InputError):
            backend._validate_points_lie_within_raster(
                lons, lats, lats, lons, self.bounds, self.res
            )

    def test_invalid_right(self):
        lats = np.array([0])
        lons = np.array([self.bounds.right])
        with pytest.raises(backend.InputError):
            backend._validate_points_lie_within_raster(
                lons, lats, lats, lons, self.bounds, self.res
            )

    def test_invalid_xy_valid_latlons(self):
        # Only x/y should be used for testing, latlon should be independent.
        x = np.array([self.bounds.right])
        y = np.array([0])
        lats = y
        lons = np.array([0])
        with pytest.raises(backend.InputError):
            backend._validate_points_lie_within_raster(
                x, y, lats, lons, self.bounds, self.res
            )

    def test_valid_xy_invalid_latlons(self):
        xs = np.array([0, -100, 100])
        ys = np.array([0, -50, 50])
        lats = np.array([1000, 1000, -1000])
        lons = np.array([1000, 1000, -1000])
        backend._validate_points_lie_within_raster(
            xs, ys, lats, lons, self.bounds, self.res
        )


class TestGetElevationFromPath:
    with rasterio.open(ETOPO1_GEOTIFF_PATH) as f:
        geotiff_z = f.read(1)

    def test_all_interpolation_methods(self):
        lats = [0.5]
        lons = [0.4]
        for method in backend.INTERPOLATION_METHODS.keys():
            backend._get_elevation_from_path(lats, lons, ETOPO1_GEOTIFF_PATH, method)

    def test_read_ul_corner(self):
        lats = [90]
        lons = [-180]
        z = backend._get_elevation_from_path(
            lats, lons, ETOPO1_GEOTIFF_PATH, "bilinear"
        )
        assert z[0] == self.geotiff_z[0, 0]

    def test_read_lr_corner(self):
        lats = [-90]
        lons = [180]
        z = backend._get_elevation_from_path(
            lats, lons, ETOPO1_GEOTIFF_PATH, "bilinear"
        )
        assert z[0] == self.geotiff_z[-1, -1]

    def test_nearest_interpolation(self):
        lats = [89.51]
        lons = [-179.51]
        z = backend._get_elevation_from_path(lats, lons, ETOPO1_GEOTIFF_PATH, "nearest")
        assert z[0] == self.geotiff_z[0, 0]

    def _interp_bilinear(self, x, y, z):
        return (
            z[0][0] * (1 - x) * (1 - y)
            + z[1][0] * x * (1 - y)
            + z[0][1] * (1 - x) * y
            + z[1][1] * x * y
        )

    def test_bilinear_interpolation(self):
        lats = [89.6]
        lons = [-179.7]
        z = backend._get_elevation_from_path(
            lats, lons, ETOPO1_GEOTIFF_PATH, "bilinear"
        )
        assert pytest.approx(z[0]) == self._interp_bilinear(
            0.4, 0.3, self.geotiff_z[:2, :2]
        )

    def test_error_outside_dataset(self):
        lats = [0, 0, -90.1, 90.1]
        lons = [-180.1, 180.1, 0, 0]
        for lat, lon in zip(lats, lons):
            with pytest.raises(backend.InputError):
                z = backend._get_elevation_from_path(
                    [lat], [lon], ETOPO1_GEOTIFF_PATH, interpolation="lanczos"
                )


class TestGetElevation:
    def test_single_file_dataset(self):
        lats = [0.1, -9]
        lons = [-50.5, 12.11]
        interpolation = "cubic"
        dataset = config.load_datasets()[ETOPO1_DATASET_NAME]
        elevations_by_dataset = backend.get_elevation(
            lats, lons, dataset, interpolation
        )
        elevations_by_path = backend._get_elevation_from_path(
            lats, lons, ETOPO1_GEOTIFF_PATH, interpolation
        )
        assert elevations_by_dataset == elevations_by_path

    def test_fill_value_oob(self, patch_config):
        lats = [1.5, -0.5, 0.5, 0.5]
        lons = [10.5, 11.5, 9.5, 12.5]
        dataset = config.load_datasets()[SRTM_DATASET_NAME]
        z = backend.get_elevation(lats, lons, dataset)
        assert all([np.isnan(x) for x in z])

    def test_srtm_tiles(self, patch_config):
        lats = [0.1, 0.9]
        lons = [10.5, 11.5]
        dataset = config.load_datasets()[SRTM_DATASET_NAME]
        z = backend.get_elevation(lats, lons, dataset)
        assert all(z)
        assert all([not np.isnan(x) for x in z])

    def test_utm(self, patch_config):
        lats = [0.2, 0.8, 0.6]
        lons = [10.2, 10.8, 11.5]

        dataset = config.load_datasets()[SRTM_DATASET_NAME]
        z = backend.get_elevation(lats, lons, dataset)

        dataset_utm = config.load_datasets()[SRTM_UTM_DATASET_NAME]
        z_utm = backend.get_elevation(lats, lons, dataset_utm)

        assert np.allclose(z, z_utm)

    def test_out_of_srtm_bounds(self, patch_config):
        lats = [70]
        lons = [10.5]
        dataset = config.load_datasets()[SRTM_DATASET_NAME]
        z = backend.get_elevation(lats, lons, dataset)
        assert np.isnan(z)

    def test_out_of_srtm_bounds_utm(self, patch_config):
        lats = [70]
        lons = [10.5]
        dataset = config.load_datasets()[SRTM_DATASET_NAME]
        z = backend.get_elevation(lats, lons, dataset)
        assert np.isnan(z)
