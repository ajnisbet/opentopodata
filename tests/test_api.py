import pytest
from flask_caching import Cache

from opentopodata import api
from opentopodata import backend
from opentopodata import config

from unittest.mock import patch
import rasterio


GEOTIFF_PATH = 'tests/data/datasets/test-etopo1-resampled-1deg/ETOPO1_Ice_g_geotiff.resampled-1deg.tif'
INTERPOLATION_METHODS = ['nearest', 'bilinear', 'cubic']
DEFAULT_INTERPOLATION_METHOD = 'bilinear'
TEST_CONFIG_PATH = 'tests/data/configs/test-config.yaml'
ETOPO1_DATASET_NAME = 'etopo1deg'
MAX_N_POINTS = 100

# Mock changing config.
@pytest.fixture
def patch_config():
    with patch('opentopodata.config.CONFIG_PATH', TEST_CONFIG_PATH):
        yield



class TestValidateInterpolation():
    def test_default_interpolation_is_valid(self):
        api._validate_interpolation(api.DEFAULT_INTERPOLATION_METHOD)

    def test_supported_methods_are_valid(self):
        for method in backend.INTERPOLATION_METHODS.keys():
            api._validate_interpolation(method)


class TestParseLocations():
    def test_empty_input(self):
        with pytest.raises(api.ClientError):
            api._parse_locations('', MAX_N_POINTS)

    def test_invalid_point(self):
        with pytest.raises(api.ClientError):
            api._parse_locations('0,0|Test', MAX_N_POINTS)

    def test_invalid_lat(self):
        with pytest.raises(api.ClientError):
            api._parse_locations('0,0|Test,0', MAX_N_POINTS)

    def test_invalid_lon(self):
        with pytest.raises(api.ClientError):
            api._parse_locations('0,0|0,Test', MAX_N_POINTS)

    def test_lat_lon_wrong_order(self):
        with pytest.raises(api.ClientError):
            api._parse_locations('180,90', MAX_N_POINTS)

    def test_small_lat(self):
        with pytest.raises(api.ClientError):
            api._parse_locations('-91,0', MAX_N_POINTS)
    
    def test_large_lat(self):
        with pytest.raises(api.ClientError):
            api._parse_locations('91,0', MAX_N_POINTS)
    
    def test_small_lon(self):
        with pytest.raises(api.ClientError):
            api._parse_locations('0,-181', MAX_N_POINTS)
    
    def test_large_lon(self):
        with pytest.raises(api.ClientError):
            api._parse_locations('0, 181', MAX_N_POINTS)

    def test_locations(self):
        locations = '0,0|-90,-180|90,180|0.1,0.1'
        lats, lons = api._parse_locations(locations, MAX_N_POINTS)
        assert lats == [0, -90, 90, 0.1]
        assert lons == [0, -180, 180, 0.1]

class TestGetDataset:
    def test_valid_dataset(self, patch_config):
        with api.app.test_request_context():
            dataset = api._get_dataset(ETOPO1_DATASET_NAME)
            assert dataset.name == ETOPO1_DATASET_NAME

    def test_missing_dataset(self):
        with api.app.test_request_context():
            with pytest.raises(api.ClientError):
                api._get_dataset('Invalid name')
    
class TestGetElevation():
    test_api = api.app.test_client()
    with rasterio.open(GEOTIFF_PATH) as f:
        geotiff_z  = f.read(1)

    def test_single_location(self, patch_config):
        url = '/v1/etopo1deg?locations=90,-180'
        response = self.test_api.get(url)
        rjson = response.json
        z = self.geotiff_z[0, 0]
        assert response.status_code == 200
        assert rjson['status'] == 'OK'
        assert len(rjson['results']) == 1
        assert rjson['results'][0]['location']['lat'] == 90
        assert rjson['results'][0]['location']['lng'] == -180
        assert rjson['results'][0]['elevation'] == z

    def test_repeated_locations(self, patch_config):
        url = '/v1/etopo1deg?locations=1.5,0.1|1.5,0.1&interpolation=cubic'
        response = self.test_api.get(url)
        rjson = response.json
        assert response.status_code == 200
        assert rjson['status'] == 'OK'
        assert len(rjson['results']) == 2
        assert rjson['results'][0] == rjson['results'][1]

    def test_interpolation_methods(self, patch_config):
        for method in INTERPOLATION_METHODS:
            url = '/v1/etopo1deg?locations=-10.1,0.001|90,180&interpolation=' + method
            response = self.test_api.get(url)
            rjson = response.json
            assert response.status_code == 200
            assert rjson['status'] == 'OK'

    def test_invalid_interpolation_method(self, patch_config):
        url = '/v1/etopo1deg?locations=-10.1,0.001|90,180&interpolation=bad_value'
        response = self.test_api.get(url)
        rjson = response.json
        assert rjson['status'] == 'INVALID_REQUEST'
        assert 'error' in rjson
        assert response.status_code == 400

    def test_default_interpolation_method(self, patch_config):
        url_1 = '/v1/etopo1deg?locations=-90,-180|-10.12345,50.67'
        url_2 = '/v1/etopo1deg?locations=-90,-180|-10.12345,50.67&interpolation=' + DEFAULT_INTERPOLATION_METHOD
        response_1 = self.test_api.get(url_1)
        response_2 = self.test_api.get(url_2)
        assert response_1.get_data() == response_2.get_data()

    def test_too_many_points(self, patch_config):
        n_too_many_points = 101
        url = '/v1/etopo1deg?locations=' + '|'.join(['0,0'] * n_too_many_points)
        response = self.test_api.get(url)
        rjson = response.json
        assert rjson['status'] == 'INVALID_REQUEST'
        assert 'error' in rjson
        assert response.status_code == 400

    def test_invalid_dataset(self):
        url = '/v1/invalid_dataset_name?locations=1,1'
        response = self.test_api.get(url)
        rjson = response.json
        assert rjson['status'] == 'INVALID_REQUEST'
        assert 'error' in rjson
        assert response.status_code == 400

    def test_example_config(self):
        url = '/v1/test?locations=1,1'
        response = self.test_api.get(url)
        rjson = response.json
        assert response.status_code == 200
        assert rjson['status'] == 'OK'
        assert len(rjson['results']) == 1


