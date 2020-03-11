import pytest
import numpy as np

from opentopodata import utils

WGS84_LATLON_WKT = 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]]'
WGS84_LATLON_EPSG = 4326


class TestReprojectLatlons:
    def test_wgs84_invariance(self):
        lats = [-10, 0, 10]
        lons = [-170, 0, 100]
        wgs84_epsg = WGS84_LATLON_EPSG
        xs, ys = utils.reproject_latlons(lats, lons, epsg=wgs84_epsg)
        assert lats == ys
        assert lons == xs

    def test_utm_conversion(self):
        lats = [10.5]
        lons = [120.8]
        epsg = 32651
        xs, ys = utils.reproject_latlons(lats, lons, epsg=epsg)
        x = 259212
        y = 1161538
        assert np.allclose(x, xs)
        assert np.allclose(y, ys)

    def test_bad_epsg(self):
        with pytest.raises(ValueError):
            lats = [10.5]
            lons = [120.8]
            epsg = 0
            xs, ys = utils.reproject_latlons(lats, lons, epsg=epsg)

    def test_no_projection_provided(self):
        with pytest.raises(ValueError):
            lats = [10.5]
            lons = [120.8]
            xs, ys = utils.reproject_latlons(lats, lons)

    def test_both_projections_provided(self):
        lats = [-10, 0, 1.43534, 10]
        lons = [-170, 0, -16.840, 100]
        epsg = WGS84_LATLON_EPSG
        wkt = WGS84_LATLON_WKT
        epsg_xs, epsg_ys = utils.reproject_latlons(lats, lons, epsg=epsg)
        wkt_xs, wkt_ys = utils.reproject_latlons(lats, lons, wkt=wkt)

        assert np.allclose(epsg_xs, wkt_xs)
        assert np.allclose(epsg_ys, wkt_ys)

    def test_epsg_wkt_equivalence(self):
        lats = [-10, 0, 10]
        lons = [-170, 0, 100]


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
