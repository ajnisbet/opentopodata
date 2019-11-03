import pytest
import numpy as np

from opentopodata import utils


class TestReprojectLatlons:
    def test_wgs84_invariance(self):
        lats = [-10, 0, 10]
        lons = [-170, 0, 100]
        wgs84_epsg = 4326
        xs, ys = utils.reproject_latlons(lats, lons, wgs84_epsg)
        assert lats == ys
        assert lons == xs

    def test_utm_conversion(self):
        lats = [10.5]
        lons = [120.8]
        epsg = 32651
        xs, ys = utils.reproject_latlons(lats, lons, epsg)
        x = 259212
        y = 1161538
        assert np.allclose(x, xs)
        assert np.allclose(y, ys)

    def test_bad_epsg(self):
        with pytest.raises(ValueError):
            lats = [10.5]
            lons = [120.8]
            epsg = 0
            xs, ys = utils.reproject_latlons(lats, lons, epsg)


class TestBaseFloor:
    def test_base_1_default(self):
        values = [-1, 0, 1, -0.6, -0.4, 0.4, 0.6, 99.91]
        for x in values:
            assert np.floor(x) == utils.base_floor(x)
            assert np.floor(x) == utils.base_floor(x, 1)

    def test_other_base(self):
        assert utils.base_floor(290.9, 50) == 250

    def test_negative_value(self):
        assert utils.base_floor(-5.1, 5) == -10
