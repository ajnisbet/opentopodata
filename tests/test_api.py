import math

import pytest
from flask_caching import Cache
import rasterio
from unittest.mock import patch
import numpy as np
from flask import request

from opentopodata import api
from opentopodata import backend
from opentopodata import config


GEOTIFF_PATH = "tests/data/datasets/test-etopo1-resampled-1deg/ETOPO1_Ice_g_geotiff.resampled-1deg.tif"
INTERPOLATION_METHODS = ["nearest", "bilinear", "cubic"]
DEFAULT_INTERPOLATION_METHOD = "bilinear"
TEST_CONFIG_PATH = "tests/data/configs/test-config.yaml"
INVALID_CONFIG_PATH = "tests/data/configs/no-datasets.yaml"
ETOPO1_DATASET_NAME = "etopo1deg"
MAX_N_POINTS = 100

# Mock changing config.
@pytest.fixture
def patch_config():
    with patch("opentopodata.config.CONFIG_PATH", TEST_CONFIG_PATH):
        yield


class TestCORS:
    def test_default_cors(self):
        test_api = api.app.test_client()
        url = "/v1/etopo1deg?locations=90,-180"
        response = test_api.get(url)
        assert response.headers.get("access-control-allow-origin") == "*"

    def test_no_cors(self, patch_config):
        test_api = api.app.test_client()
        url = "/v1/etopo1deg?locations=90,-180"
        response = test_api.get(url)
        assert response.headers.get("access-control-allow-origin") is None


class TestFindRequestAgument:
    def test_no_argument(self, patch_config):
        url = f"/v1/{ETOPO1_DATASET_NAME}"
        with api.app.test_request_context(url):
            assert api._find_request_argument(request, "no-arg") is None

    def test_get_argument(self, patch_config):
        arg_name = "test-arg"
        arg_value = "test-value"
        url = f"/v1/{ETOPO1_DATASET_NAME}?{arg_name}={arg_value}"
        with api.app.test_request_context(url):
            assert api._find_request_argument(request, arg_name) == arg_value

    def test_post_argument_json(self, patch_config):
        arg_name = "test-arg"
        arg_value = "test-value"
        url = f"/v1/{ETOPO1_DATASET_NAME}"
        with api.app.test_request_context(
            url, method="POST", json={arg_name: arg_value}
        ):
            assert api._find_request_argument(request, arg_name) == arg_value

    def test_post_argument_form(self, patch_config):
        arg_name = "test-arg"
        arg_value = "test-value"
        url = f"/v1/{ETOPO1_DATASET_NAME}"
        with api.app.test_request_context(
            url, method="POST", data={arg_name: arg_value}
        ):
            assert api._find_request_argument(request, arg_name) == arg_value

    def test_post_invalid_json(self, patch_config):
        arg_name = "test-arg"
        arg_value = "test-value"
        url = f"/v1/{ETOPO1_DATASET_NAME}"
        with api.app.test_request_context(
            url,
            method="POST",
            data={arg_name: arg_value},
            headers={"content-type": "application/json"},
        ):
            with pytest.raises(api.ClientError):
                assert api._find_request_argument(request, arg_name) == arg_value

    def test_post_query_args_are_ignored(self, patch_config):
        arg_name = "test-arg"
        arg_value = "test-value"
        url = f"/v1/{ETOPO1_DATASET_NAME}?{arg_name}={arg_value}"
        with api.app.test_request_context(url, method="POST"):
            assert api._find_request_argument(request, arg_name) is None


class TestParseInterpolation:
    def test_default_interpolation_is_valid(self):
        assert (
            api._parse_interpolation(api.DEFAULT_INTERPOLATION_METHOD)
            == api.DEFAULT_INTERPOLATION_METHOD
        )

    def test_supported_methods_are_valid(self):
        for method in backend.INTERPOLATION_METHODS.keys():
            assert api._parse_interpolation(method) == method

    def test_default(self):
        assert api._parse_interpolation(None) == api.DEFAULT_INTERPOLATION_METHOD

    def test_non_numeric(self):
        with pytest.raises(api.ClientError):
            api._parse_interpolation("Non numeric string")


class TestParseNodataValue:
    def test_default_value(self):
        assert api._parse_nodata_value(None) == api._parse_nodata_value(
            api.DEFAULT_NODATA_VALUE
        )

    def test_null(self):
        assert api._parse_nodata_value("null") is None

    def test_nan(self):
        for x in ["NaN", "nan"]:
            assert math.isnan(api._parse_nodata_value(x))

    def test_ints(self):
        assert api._parse_nodata_value("-9999") == -9999
        assert api._parse_nodata_value("0") == 0
        assert api._parse_nodata_value("1") == 1

    def test_non_numeric(self):
        with pytest.raises(api.ClientError):
            api._parse_nodata_value("Non numeric string")


class TestParseLocations:
    def test_empty_input(self):
        with pytest.raises(api.ClientError):
            api._parse_locations("", MAX_N_POINTS)

    def test_invalid_point(self):
        with pytest.raises(api.ClientError):
            api._parse_locations("0,0|Test", MAX_N_POINTS)

    def test_invalid_lat(self):
        with pytest.raises(api.ClientError):
            api._parse_locations("0,0|Test,0", MAX_N_POINTS)

    def test_invalid_lon(self):
        with pytest.raises(api.ClientError):
            api._parse_locations("0,0|0,Test", MAX_N_POINTS)

    def test_invalid_polyline(self):
        with pytest.raises(api.ClientError):
            api._parse_locations("$$$", MAX_N_POINTS)

    def test_lat_lon_wrong_order(self):
        with pytest.raises(api.ClientError):
            api._parse_locations("180,90", MAX_N_POINTS)

    def test_small_lat(self):
        with pytest.raises(api.ClientError):
            api._parse_locations("-91,0", MAX_N_POINTS)

    def test_large_lat(self):
        with pytest.raises(api.ClientError):
            api._parse_locations("91,0", MAX_N_POINTS)

    def test_small_lon(self):
        with pytest.raises(api.ClientError):
            api._parse_locations("0,-181", MAX_N_POINTS)

    def test_large_lon(self):
        with pytest.raises(api.ClientError):
            api._parse_locations("0, 181", MAX_N_POINTS)

    def test_valid_latlons(self):
        locations = "0,0|-90,-180|90,180|0.1,0.1"
        lats, lons = api._parse_locations(locations, MAX_N_POINTS)
        assert lats == [0, -90, 90, 0.1]
        assert lons == [0, -180, 180, 0.1]

    def test_too_many_latlon_locations(self):
        with pytest.raises(api.ClientError):
            api._parse_locations("10,10|5,5", 1)

    def test_valid_polyline(self):
        locations = "tpmjFukpm`@hvwMh|i@rlZefC"
        lats, lons = api._parse_locations(locations, MAX_N_POINTS)
        assert lats == [-38.57691, -40.99728, -41.13770]
        assert lons == [175.39787, 175.17814, 175.19977]

    def test_too_many_polyline_locations(self):
        with pytest.raises(api.ClientError):
            api._parse_locations("kzn_JmmvhAjdIelA", 1)

    def test_strip_enc_prefix(self):
        p1 = "enc:gfo}EtohhUxD@bAxJmGF"
        p2 = "gfo}EtohhUxD@bAxJmGF"
        assert api._parse_locations(p1, MAX_N_POINTS) == api._parse_locations(
            p2, MAX_N_POINTS
        )


class TestGetDatasets:
    def test_valid_dataset(self, patch_config):
        with api.app.test_request_context():
            dataset = api._get_datasets(ETOPO1_DATASET_NAME)[0]
            assert dataset.name == ETOPO1_DATASET_NAME

    def test_missing_dataset(self):
        with api.app.test_request_context():
            with pytest.raises(api.ClientError):
                api._get_datasets("Invalid dataset name")

    def test_multi_dataset(self, patch_config):
        with api.app.test_request_context():
            datasets = api._get_datasets("multi_eudem_etopo1")
            names = [d.name for d in datasets]
            assert names == ["nodata", "eudemsubset", "etopo1deg"]

    def test_comma_datasets(self, patch_config):
        names = ["srtm90subset", "eudemsubset", "nodata"]
        with api.app.test_request_context():
            datasets = api._get_datasets(",".join(names))
            assert names == [d.name for d in datasets]

    def test_repeated_dataset_error(self, patch_config):
        with api.app.test_request_context():
            with pytest.raises(api.ClientError):
                api._get_datasets(f"{ETOPO1_DATASET_NAME},{ETOPO1_DATASET_NAME}")

    def test_nonexistent_dataset_error(self, patch_config):
        with api.app.test_request_context():
            with pytest.raises(api.ClientError):
                api._get_datasets(f"{ETOPO1_DATASET_NAME},unreal_dataset,another")

    def test_invalid_multi_dataset_error(self, patch_config):
        with api.app.test_request_context():
            with pytest.raises(api.ClientError):
                api._get_datasets(f",  ,, , , ")


class TestGetElevation:
    test_api = api.app.test_client()
    with rasterio.open(GEOTIFF_PATH) as f:
        geotiff_z = f.read(1)

    def test_single_location(self, patch_config):
        url = "/v1/etopo1deg?locations=90,-180"
        response = self.test_api.get(url)
        rjson = response.json
        z = self.geotiff_z[0, 0]
        assert response.status_code == 200
        assert rjson["status"] == "OK"
        assert len(rjson["results"]) == 1
        assert rjson["results"][0]["location"]["lat"] == 90
        assert rjson["results"][0]["location"]["lng"] == -180
        assert rjson["results"][0]["elevation"] == z

    def test_post(self, patch_config):
        url = "/v1/etopo1deg"
        response = self.test_api.post(url, data={"locations": "90,-180"})
        rjson = response.json
        z = self.geotiff_z[0, 0]
        assert response.status_code == 200
        assert rjson["status"] == "OK"
        assert len(rjson["results"]) == 1
        assert rjson["results"][0]["location"]["lat"] == 90
        assert rjson["results"][0]["location"]["lng"] == -180
        assert rjson["results"][0]["elevation"] == z

    def test_repeated_locations(self, patch_config):
        url = "/v1/etopo1deg?locations=1.5,0.1|1.5,0.1&interpolation=cubic"
        response = self.test_api.get(url)
        rjson = response.json
        assert response.status_code == 200
        assert rjson["status"] == "OK"
        assert len(rjson["results"]) == 2
        assert rjson["results"][0] == rjson["results"][1]

    def test_polyline_latlon_equivalence(self, patch_config):
        url_latlon = "/v1/etopo1deg?locations=-90,180|1.5,0.1"
        url_polyline = "/v1/etopo1deg?locations=~bidP_gsia@_bnmP~u_ia@"
        response_latlon = self.test_api.get(url_latlon)
        response_polyline = self.test_api.get(url_polyline)
        rjson_latlon = response_latlon.json
        rjson_polyline = response_polyline.json
        assert response_latlon.status_code == 200
        assert response_latlon.status_code == response_polyline.status_code
        assert rjson_latlon == rjson_polyline

    def test_interpolation_methods(self, patch_config):
        for method in INTERPOLATION_METHODS:
            url = "/v1/etopo1deg?locations=-10.1,0.001|90,180&interpolation=" + method
            response = self.test_api.get(url)
            rjson = response.json
            assert response.status_code == 200
            assert rjson["status"] == "OK"

    def test_invalid_interpolation_method(self, patch_config):
        url = "/v1/etopo1deg?locations=-10.1,0.001|90,180&interpolation=bad_value"
        response = self.test_api.get(url)
        rjson = response.json
        assert rjson["status"] == "INVALID_REQUEST"
        assert "error" in rjson
        assert response.status_code == 400

    def test_default_interpolation_method(self, patch_config):
        url_1 = "/v1/etopo1deg?locations=-90,-180|-10.12345,50.67"
        url_2 = (
            "/v1/etopo1deg?locations=-90,-180|-10.12345,50.67&interpolation="
            + DEFAULT_INTERPOLATION_METHOD
        )
        response_1 = self.test_api.get(url_1)
        response_2 = self.test_api.get(url_2)
        assert response_1.get_data() == response_2.get_data()

    def test_too_many_points(self, patch_config):
        n_too_many_points = 101
        url = "/v1/etopo1deg?locations=" + "|".join(["0,0"] * n_too_many_points)
        response = self.test_api.get(url)
        rjson = response.json
        assert rjson["status"] == "INVALID_REQUEST"
        assert "error" in rjson
        assert response.status_code == 400

    def test_invalid_dataset(self):
        url = "/v1/invalid_dataset_name?locations=1,1"
        response = self.test_api.get(url)
        rjson = response.json
        assert rjson["status"] == "INVALID_REQUEST"
        assert "error" in rjson
        assert response.status_code == 400

    def test_example_config(self):
        url = "/v1/test-dataset?locations=1,1"
        response = self.test_api.get(url)
        rjson = response.json
        assert response.status_code == 200
        assert rjson["status"] == "OK"
        assert len(rjson["results"]) == 1

    def test_default_nodata(self, patch_config):
        url = "/v1/nodata?locations=0,1"
        response = self.test_api.get(url)
        rjson = response.json
        assert response.status_code == 200
        assert rjson["status"] == "OK"
        assert len(rjson["results"]) == 1
        assert rjson["results"][0]["elevation"] is None

    def test_null_nodata(self, patch_config):
        url = "/v1/nodata?locations=0,1&nodata_value=null"
        response = self.test_api.get(url)
        rjson = response.json
        assert response.status_code == 200
        assert rjson["status"] == "OK"
        assert len(rjson["results"]) == 1
        assert rjson["results"][0]["elevation"] is None
        assert "null" in response.get_data(as_text=True)

    def test_nan_nodata(self, patch_config):
        url = "/v1/nodata?locations=0,1&nodata_value=nan"
        response = self.test_api.get(url)
        rjson = response.json
        assert response.status_code == 200
        assert rjson["status"] == "OK"
        assert len(rjson["results"]) == 1
        assert np.isnan(rjson["results"][0]["elevation"])

    def test_int_nodata(self, patch_config):
        url = "/v1/nodata?locations=0,1&nodata_value=-9999"
        response = self.test_api.get(url)
        rjson = response.json
        assert response.status_code == 200
        assert rjson["status"] == "OK"
        assert len(rjson["results"]) == 1
        assert rjson["results"][0]["elevation"] == -9999

    def test_null_in_json(self, patch_config):
        url = "/v1/srtm90subset?locations=50,100"
        response = self.test_api.get(url)
        rjson = response.json
        assert response.status_code == 200
        assert rjson["status"] == "OK"
        assert len(rjson["results"]) == 1
        assert rjson["results"][0]["elevation"] is None

    def test_config_error(self):
        with patch("opentopodata.config.CONFIG_PATH", INVALID_CONFIG_PATH):
            url = "/v1/srtm90subset?locations=50,100"
            response = self.test_api.get(url)
            rjson = response.json
            assert response.status_code == 500
            assert rjson["status"] == "SERVER_ERROR"
            assert "config" in rjson["error"].lower()

    def test_multi_dataset(self, patch_config):
        url = "/v1/multi_eudem_etopo1?locations=47.625765,9.418759|-70,-170|0,1"
        response = self.test_api.get(url)
        rjson = response.json
        assert response.status_code == 200
        assert rjson["status"] == "OK"
        assert rjson["results"][0]["dataset"] == "eudemsubset"
        assert rjson["results"][1]["dataset"] == "etopo1deg"
        assert rjson["results"][2]["dataset"] == "etopo1deg"

    def test_comma_dataset_name(self, patch_config):
        url = (
            "/v1/nodata,eudemsubset,etopo1deg?locations=47.625765,9.418759|-70,-170|0,1"
        )
        response = self.test_api.get(url)
        rjson = response.json
        assert response.status_code == 200
        assert rjson["status"] == "OK"
        assert rjson["results"][0]["dataset"] == "eudemsubset"
        assert rjson["results"][1]["dataset"] == "etopo1deg"
        assert rjson["results"][2]["dataset"] == "etopo1deg"

    def test_version(self, patch_config):
        url = (
            "/v1/nodata,eudemsubset,etopo1deg?locations=47.625765,9.418759|-70,-170|0,1"
        )
        response = self.test_api.get(url)
        assert response.headers["x-opentopodata-version"]

    def test_samples(self, patch_config):
        n_samples = 10
        url = f"/v1/etopo1deg?locations=-30,16|-18,112&samples={n_samples}"
        response = self.test_api.get(url)
        rjson = response.json
        assert response.status_code == 200
        assert rjson["status"] == "OK"
        assert len(rjson["results"]) == n_samples

    def test_invalid_samples(self, patch_config):
        url = "/v1/etopo1deg?locations=-30,16|-18,112&samples=blah"
        response = self.test_api.get(url)
        rjson = response.json
        assert response.status_code == 400

    def test_single_samples(self, patch_config):
        url = "/v1/etopo1deg?locations=-30,16|-18,112&samples=1"
        response = self.test_api.get(url)
        rjson = response.json
        assert response.status_code == 400

    def test_too_many_samples(self, patch_config):
        n_too_many_points = 101
        url = f"/v1/etopo1deg?locations=-30,16|-18,112&samples={n_too_many_points}"
        response = self.test_api.get(url)
        rjson = response.json
        assert response.status_code == 400


class TestGetHelpMessage:
    test_api = api.app.test_client()
    urls = ["/", "/v1/"]

    def test_response(self):
        for url in self.urls:
            response = self.test_api.get(url)
            rjson = response.json
            assert response.status_code == 404
            assert rjson["status"] == "INVALID_REQUEST"
            assert "error" in rjson

    def test_trailing_slash_redirect(self):
        url = "/v1"
        response = self.test_api.get(url, follow_redirects=True)
        rjson = response.json
        assert response.status_code == 404
        assert rjson["status"] == "INVALID_REQUEST"
        assert "error" in rjson


class TestGetHealthStatus:
    test_api = api.app.test_client()

    def test_healthy_response(self):
        url = "/health"
        response = self.test_api.get(url)
        rjson = response.json
        assert response.status_code == 200
        assert rjson["status"] == "OK"

    def test_unhealthy_response(self):
        with patch("opentopodata.config.CONFIG_PATH", INVALID_CONFIG_PATH):
            url = "/health"
            response = self.test_api.get(url)
            rjson = response.json
            assert response.status_code == 500
            assert rjson["status"] == "SERVER_ERROR"
