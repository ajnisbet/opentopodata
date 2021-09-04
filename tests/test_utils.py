from decimal import Decimal
import pytest
import numpy as np

from opentopodata import utils

WGS84_LATLON_WKT = 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]]'
WGS84_LATLON_EPSG = 4326
NAD83_WKT = 'GEOGCS["NAD83",DATUM["North_American_Datum_1983",SPHEROID["GRS 1980",6378137,298.257222101,AUTHORITY["EPSG","7019"]],AUTHORITY["EPSG","6269"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.01745329251994328,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4269"]]'


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

    def test_epsg_wkt_equivalence(self):
        lats = [-10, 0, 1.43534, 10]
        lons = [-170, 0, -16.840, 100]
        epsg = WGS84_LATLON_EPSG
        wkt = WGS84_LATLON_WKT
        epsg_xs, epsg_ys = utils.reproject_latlons(lats, lons, epsg=epsg)
        wkt_xs, wkt_ys = utils.reproject_latlons(lats, lons, wkt=wkt)

        assert np.allclose(epsg_xs, wkt_xs)
        assert np.allclose(epsg_ys, wkt_ys)

    def test_only_one_projection_format_can_be_provided(self):
        with pytest.raises(ValueError):
            lats = [-10, 0, 10]
            lons = [-170, 0, 100]
            xs, ys = utils.reproject_latlons(
                lats, lons, epsg=WGS84_LATLON_EPSG, wkt=WGS84_LATLON_WKT
            )

    def test_cache_gets_populated(self):
        lats = [10.5]
        lons = [120.8]
        assert NAD83_WKT not in utils._TRANSFORMER_CACHE
        utils.reproject_latlons(lats, lons, wkt=NAD83_WKT)
        assert NAD83_WKT in utils._TRANSFORMER_CACHE


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


class TestDecimalBaseFloor:
    def test_base_1_default(self):
        values = [-1, 0, 1, -0.6, -0.4, 0.4, 0.6, 99.91]
        for x in values:
            assert np.floor(x) == utils.decimal_base_floor(x)
            assert np.floor(x) == utils.decimal_base_floor(x, 1)

    def test_other_base(self):
        assert utils.decimal_base_floor(290.9, 50) == 250

    def test_negative_value(self):
        assert utils.decimal_base_floor(-5.1, 5) == -10

    def test_fractional_base(self):
        assert utils.decimal_base_floor(5.6, Decimal("0.25")) == Decimal("5.5")


class TestSafeIsNan:
    def test_numpy_nan(self):
        assert utils.safe_is_nan(np.nan) == True

    def test_python_nan(self):
        assert utils.safe_is_nan(float("nan")) == True

    def test_float(self):
        assert utils.safe_is_nan(12.5) == False

    def test_int(self):
        assert utils.safe_is_nan(-99999) == False

    def test_none(self):
        assert utils.safe_is_nan(None) == False

    def test_non_numeric(self):
        assert utils.safe_is_nan("some string") == False

    def test_string(self):
        assert utils.safe_is_nan("nan") == False


class TestFillNa:
    def test_no_replacement(self):
        a = [-12.5, None, 9, "string", True, False, 0, 1, "NaN"]
        assert a == utils.fill_na(a, "na_value")

    def test_replacement(self):
        na_value = -9999
        values = [np.nan, float("nan"), 0]
        replaced_values = [na_value, na_value, 0]
        assert utils.fill_na(values, na_value) == replaced_values


class TestSamplePointsOnPath:
    def test_two_points(self):
        start = (12.3, -45.6)
        middle = (12.7, 45.1)
        end = (12.9, 45.9)
        lats = [start[0], middle[0], end[0]]
        lons = [start[1], middle[1], end[1]]
        rlats, rlons = utils.sample_points_on_path(lats, lons, 2)
        assert len(rlats) == 2
        assert len(rlons) == 2
        assert (rlats[0], rlons[0]) == start
        assert (rlats[1], rlons[1]) == end

    def test_start_end(self):
        start = (12.3, -45.6)
        end = (12.9, -45.9)
        lats = [start[0], end[0]]
        lons = [start[1], end[1]]
        rlats, rlons = utils.sample_points_on_path(lats, lons, 2)
        assert len(rlats) == 2
        assert len(rlons) == 2
        assert (rlats[0], rlons[0]) == start
        assert (rlats[1], rlons[1]) == end

    def test_lat_wraparound(self):
        """Path should take short route over the north pole."""
        lat = 88
        n_points = 7
        start = (lat, -90)
        end = (lat, 90)
        lats = [start[0], end[0]]
        lons = [start[1], end[1]]
        rlats, rlons = utils.sample_points_on_path(lats, lons, n_points)
        assert len(rlats) == n_points
        assert len(rlons) == n_points
        assert all(rlat >= lat for rlat in rlats)

    def test_lon_wraparound(self):
        """Path should take short route over date line."""
        lon = 178
        n_points = 18
        start = (1, -lon)
        end = (-1, lon)
        lats = [start[0], end[0]]
        lons = [start[1], end[1]]
        rlats, rlons = utils.sample_points_on_path(lats, lons, n_points)
        assert len(rlats) == n_points
        assert len(rlons) == n_points
        assert all(rlon >= lon or rlon <= -lon for rlon in rlons)
