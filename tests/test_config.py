from decimal import Decimal
import os
import re

import numpy as np
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


class TestValidateCors:
    def test_none(self):
        assert config._validate_cors(None) is None

    def test_all(self):
        assert config._validate_cors("*") is None

    def test_valid_domains(self):
        urls = [
            "http://example.com",
            "https://example.com/",
            "https://sub.domain.example.com/",
            "https://sub.domain.example.com:8080/",
            "https://sub.domain.example.com:8080",
            "http://192.168.0.1:71",
            "http://192.168.0.1:71/",
        ]
        for u in urls:
            assert config._validate_cors(u) is None

    def test_invalid_domains(self):
        urls = [
            True,
            "True",
            "",
            "https://",
            "example.com",
            "http://example.com/some-page",
            "http://1.example.com/ http://1.example.com/",
            ["http://1.example.com/", "http://1.example.com/"],
            "http://1.example.com/, http://1.example.com/",
        ]
        for u in urls:
            with pytest.raises(config.ConfigError):
                config._validate_cors(u)


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
        assert len(conf["datasets"]) == 7

    def test_defaults_get_overridden(self):
        path = "tests/data/configs/non-default-values.yaml"
        with patch("opentopodata.config.CONFIG_PATH", path):
            conf = config.load_config()
            assert (
                conf["max_locations_per_request"]
                != config.DEFAULTS["max_locations_per_request"]
            )
            assert (
                conf["access_control_allow_origin"]
                != config.DEFAULTS["access_control_allow_origin"]
            )

    def test_defaults(self):
        path = "tests/data/configs/no-optional-params.yaml"
        with patch("opentopodata.config.CONFIG_PATH", path):
            conf = config.load_config()
            assert (
                conf["max_locations_per_request"]
                == config.DEFAULTS["max_locations_per_request"]
            )
            assert (
                conf["access_control_allow_origin"]
                == config.DEFAULTS["access_control_allow_origin"]
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
        matching_filenames = [
            "S01W170.tif",
            "N80E001.hgt",
            "ASTGTMV003_N00E019.tif",
            "S100000W900000.tif",
            "USGS_13_n20w160.tif",
            "fraction_N20x25w160x75.tif",
            "underscore_frac_sep_N20x25_w160x75.tif",
            "S01W170.geotiff.zip",
            "lowercase_s01w170_cruft.zip",
        ]
        for f in matching_filenames:
            assert re.match(config.FILENAME_TILE_REGEX, f, re.IGNORECASE)

        # Not matching.
        assert not re.match(config.FILENAME_TILE_REGEX, "junk.tif", re.IGNORECASE)

    def test_aux_case(self):
        for e in config.AUX_EXTENSIONS:
            assert e.islower()

    def test_aux_format(self):
        for e in config.AUX_EXTENSIONS:
            assert e.startswith(".")

    def test_valid_aux(self):
        assert config.Dataset._is_aux_file("raster.AUX.XML")

    def test_invalid_aux(self):
        assert not config.Dataset._is_aux_file("raster.tif")


class TestSingleFileDataset:
    def test_location_paths(self):
        dataset = config.SingleFileDataset(ETOPO1_DATASET_NAME, ETOPO1_GEOTIFF_PATH)
        lats = [0, 1]
        lons = [-100, 100]
        tile_paths = dataset.location_paths(lats, lons)
        assert all([p == ETOPO1_GEOTIFF_PATH for p in tile_paths])


class TestTiledDataset:
    def test_float_fractional_tile_size(self):
        with pytest.raises(config.ConfigError):
            dataset = config.TiledDataset(
                name="test",
                path=SRTM_FOLDER,
                tile_paths=[],
                filename_epsg=None,
                filename_tile_size=0.25,
            )

    def test_float_whole_tile_size(self):
        tile_size = 2.0
        dataset = config.TiledDataset(
            name="test",
            path=SRTM_FOLDER,
            tile_paths=[],
            filename_epsg=None,
            filename_tile_size=tile_size,
        )
        assert dataset.filename_tile_size == int(tile_size)
        assert isinstance(dataset.filename_tile_size, Decimal)

    def test_string_tile_size(self):
        tile_size = "2.5"
        dataset = config.TiledDataset(
            name="test",
            path=SRTM_FOLDER,
            tile_paths=[],
            filename_epsg=None,
            filename_tile_size=tile_size,
        )
        assert dataset.filename_tile_size == Decimal(tile_size)

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

    @pytest.mark.parametrize(
        "filename,northing,easting",
        [
            ("N40E060", 40, 60),
            ("USGS_13_S40W60.tif", -40, -60),
            ("n001000w500000.geotiff.zip", 1000, -500_000),
            ("ASTGTMV003_N00E019", 0, 19),
            ("fraction_N50x5W20x25", Decimal("50.5"), Decimal("-20.25")),
            ("underscore_sep_N50X5_E20X25", Decimal("50.5"), Decimal("20.25")),
        ],
    )
    def test_filename_to_tile_corner(self, filename, northing, easting):
        assert (northing, easting) == config.TiledDataset._filename_to_tile_corner(
            filename
        )

    # @pytest.mark.parametrize(
    #     "xs,ys,tile_size,ns_fixed_width,ew_fixed_width,result",
    #     [
    #         ([120.1], [40.9], 1, None, None, ["N40E120"]),
    #         ([120.1], [40.9], 1, 0, 0, ["N40E120"]),
    #         ([120.1], [-40.9], 1, None, None, ["S41E120"]),
    #         ([-120.1], [40.9], 1, None, None, ["N40W121"]),
    #         ([-120.1], [-40.9], 1, None, None, ["S41W121"]),
    #         ([120.1], [0.2], 1, None, None, ["N0E120"]),
    #         ([9], [21], 5, None, None, ["N20E5"]),
    #         ([120.1], [0.2], 1, 2, None, ["N00E120"]),
    #         ([120.1], [0.2], 1, 0, None, ["N0E120"]),
    #         ([13], [-7], 1, 2, 3, ["S07E013"]),
    #     ],
    # )
    # def test_location_to_tile_name(
    #     self, xs, ys, tile_size, ns_fixed_width, ew_fixed_width, result
    # ):
    #     xs = np.array(xs)
    #     ys = np.array(ys)
    #     assert (
    #         config.TiledDataset._location_to_tile_name(
    #             xs, ys, tile_size, ns_fixed_width, ew_fixed_width
    #         )
    #         == result
    #     )
