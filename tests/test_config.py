import os
import re

import pytest
from opentopodata import config
from unittest.mock import patch


ETOPO1_DATASET_NAME = "etopo1deg"
ETOPO1_GEOTIFF_PATH = "tests/data/datasets/test-etopo1-resampled-1deg/ETOPO1_Ice_g_geotiff.resampled-1deg.tif"
SRTM_FOLDER = "tests/data/datasets/test-srtm90m-subset/"
TEST_CONFIG_PATH = "tests/data/configs/test-config.yaml"
MISSING_CONFIG_PATH = "tests/data/configs/invalid_path"


@pytest.fixture
def patch_config():
    with patch("opentopodata.config.CONFIG_PATH", TEST_CONFIG_PATH):
        yield


class TestFindConfig:
    def test_example_config(self):
        with patch("opentopodata.config.CONFIG_PATH", MISSING_CONFIG_PATH):
            assert config._find_config() == config.EXAMPLE_CONFIG_PATH

    def test_main_config(self, patch_config):
        assert config._find_config() == TEST_CONFIG_PATH

    def test_missing_config(self):
        with patch("opentopodata.config.CONFIG_PATH", MISSING_CONFIG_PATH):
            with patch("opentopodata.config.EXAMPLE_CONFIG_PATH", MISSING_CONFIG_PATH):
                assert config._find_config() is None


class TestLoadConfig:
    def test_missing_file(self):
        with pytest.raises(config.ConfigError):
            with patch("opentopodata.config.CONFIG_PATH", MISSING_CONFIG_PATH):
                with patch(
                    "opentopodata.config.EXAMPLE_CONFIG_PATH", MISSING_CONFIG_PATH
                ):
                    config.load_config()

    def test_no_datasets(self):
        path = "tests/data/configs/no-datasets.yaml"
        with pytest.raises(config.ConfigError):
            with patch("opentopodata.config.CONFIG_PATH", path):
                config.load_config()

    def test_unnamed_dataset(self):
        path = "tests/data/configs/no-name-dataset.yaml"
        with pytest.raises(config.ConfigError):
            with patch("opentopodata.config.CONFIG_PATH", path):
                config.load_config()

    def test_nopath_dataset(self):
        path = "tests/data/configs/no-path-dataset.yaml"
        with pytest.raises(config.ConfigError):
            with patch("opentopodata.config.CONFIG_PATH", path):
                config.load_config()

    def test_complete_dataset(self, patch_config):
        conf = config.load_config()
        assert "datasets" in conf
        assert len(conf["datasets"]) == 5

    def test_defaults_get_overridden(self):
        path = "tests/data/configs/non-default-values.yaml"
        with patch("opentopodata.config.CONFIG_PATH", path):
            conf = config.load_config()
            assert (
                conf["max_locations_per_request"]
                != config.DEFAULTS["max_locations_per_request"]
            )

    def test_defaults(self):
        path = "tests/data/configs/no-optional-params.yaml"
        with patch("opentopodata.config.CONFIG_PATH", path):
            conf = config.load_config()
            assert (
                conf["max_locations_per_request"]
                == config.DEFAULTS["max_locations_per_request"]
            )


class TestLoadDatasets:
    def test(self):
        config.load_datasets()


class TestDataset:
    def test_missing_dataset(self):
        with pytest.raises(config.ConfigError):
            config.Dataset.from_config(name=None, path=MISSING_CONFIG_PATH)

    def test_single_file(self, patch_config):
        name = "test"
        folder = os.path.dirname(ETOPO1_GEOTIFF_PATH)
        dataset = config.Dataset.from_config(name, folder)
        assert isinstance(dataset, config.SingleFileDataset)
        assert dataset.name == name
        assert dataset.tile_path == ETOPO1_GEOTIFF_PATH

    def test_srtm(self, patch_config):
        name = "test"
        dataset = config.Dataset.from_config(name=name, path=SRTM_FOLDER)
        assert isinstance(dataset, config.TiledDataset)
        assert dataset.name == name

    def test_filename_tile_regex(self):
        assert re.match(config.FILENAME_TILE_REGEX, "N80E001.hgt")
        assert re.match(config.FILENAME_TILE_REGEX, "S01W170.tif")
        assert re.match(config.FILENAME_TILE_REGEX, "S100000W900000.tif")
        assert re.match(config.FILENAME_TILE_REGEX, "S01W170.geotiff.zip")
        assert not re.match(config.FILENAME_TILE_REGEX, "junk.tif")


class TestSingleFileDataset:
    def test_location_paths(self):
        dataset = config.SingleFileDataset(ETOPO1_DATASET_NAME, ETOPO1_GEOTIFF_PATH)
        lats = [0, 1]
        lons = [-100, 100]
        tile_paths = dataset.location_paths(lats, lons)
        assert all([p == ETOPO1_GEOTIFF_PATH for p in tile_paths])


class TestTiledDataset:
    def test_location_paths(self):
        dataset = config.Dataset.from_config(name="srtm", path=SRTM_FOLDER)
        lats = [0.1, 0.9]
        lons = [10.99, 11.1]
        paths = dataset.location_paths(lats, lons)
        filenames = [os.path.basename(p) for p in paths]
        assert filenames[0].startswith("N00E010")
        assert filenames[1].startswith("N00E011")
        assert len(paths) == 2

    def test_missing_path(self):
        dataset = config.Dataset.from_config(name="srtm", path=SRTM_FOLDER)
        lats = [10]
        lons = [100]
        paths = dataset.location_paths(lats, lons)
        assert len(paths) == 1
        assert paths[0] is None
