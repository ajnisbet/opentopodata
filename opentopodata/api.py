import logging
import os

from flask import Flask, jsonify, request
from flask_caching import Cache
import polyline

from opentopodata import backend, config, utils


app = Flask(__name__)
app.json.compact = False

DEFAULT_INTERPOLATION_METHOD = "bilinear"
DEFAULT_NODATA_VALUE = "null"
MEMCACHED_SOCKET = "/tmp/memcached.sock"
LAT_MIN = -90
LAT_MAX = 90
LON_MIN = -180
LON_MAX = 180
VERSION_PATH = "VERSION"


# Memcache is used to store the latlon -> filename lookups, which can take a
# while to compute for datasets made up of many files. Memcache needs to be
# disabled for testing as it breaks tests which change the config. It can also
# be disabled if not installed for local development.
if os.environ.get("DISABLE_MEMCACHE"):
    cache = Cache(config={"CACHE_TYPE": "NullCache", "CACHE_NO_NULL_WARNING": True})
else:
    cache = Cache(
        config={
            "CACHE_TYPE": "MemcachedCache",
            "CACHE_MEMCACHED_SERVERS": [MEMCACHED_SOCKET],
            "CACHE_DEFAULT_TIMEOUT": 0,
        }
    )
cache.init_app(app)


# Memcache has significant deserialisation overhead for large datasets. It
# seems like a waste to do the exact same deserialisation work for each
# request: instead it can be cached in a module-level dict that will persist
# between requests. This isn't threadsafe but neither is flask_caching's
# memcache. It will be fine as long as the value for a key will never change.
# TODO: drop the dependency on flask_caching, make a merged simple and
# memcached cache object.
_SIMPLE_CACHE = {}


def _load_config():
    """Config file as a dict.

    Returns:
        Config dict.
    """
    if os.environ.get("DISABLE_MEMCACHE") or "config" not in _SIMPLE_CACHE:
        _SIMPLE_CACHE["config"] = _load_config_memcache()
    return _SIMPLE_CACHE["config"]


@cache.cached(key_prefix="_load_config")
def _load_config_memcache():
    return config.load_config()


@app.after_request
def apply_cors(response):
    """Set CORs header.

    Supporting CORSs enables browsers to make XHR requests. Applies the value
    of the access_control_allow_origin config option.
    """
    try:
        if _load_config()["access_control_allow_origin"]:
            response.headers["access-control-allow-origin"] = _load_config()[
                "access_control_allow_origin"
            ]
    except config.ConfigError:
        # If the config isn't loading, allow the request to complete without
        # CORS so user can see error message.
        pass

    return response


class ClientError(ValueError):
    """Invalid input data.

    A 400 error should be raised. The error message should be safe to pass
    back to the client.
    """


def _find_request_argument(request, arg):
    """Find an argument of a request.

    For GET requests, will check query arguments.

    For POST requests, will check form data first, and json body data second.
    Query args aren't checked for POST requests. JSON arguments are cast to
    strings for consistency.

    Args:
        request: Flask request object.
        arg: Argument name string.

    Returns:
        String argument value.
    """

    # First GET requests.
    if request.method != "POST":
        return request.args.get(arg)

    # For post requests, try form.
    if arg in request.form:
        return request.form[arg]

    # Also try json. is_json just checks mimetype, still need to handle error
    # for malformed json.
    if request.is_json:
        try:
            json_data = request.get_json()
            if arg in json_data:
                return str(json_data[arg])
        except:
            raise ClientError("Invalid JSON.")


def _parse_interpolation(method):
    """Check the interpolation method is supported.

    Args:
        method: Name of the interpolation method, or None for default.

    Returns:
        method: A valid interpolation method.

    Raises:
        ClientError: Method is not supported.
    """

    if not method:
        method = DEFAULT_INTERPOLATION_METHOD

    if method not in backend.INTERPOLATION_METHODS:
        msg = f"Invalid interpolation method '{method}'."
        msg += " The valid interpolation methods are: "
        msg += ", ".join(backend.INTERPOLATION_METHODS.keys()) + "."
        raise ClientError(msg)

    return method


def _parse_n_samples(samples_str, max_n_locations):
    """Check the number if interpolated samples.

    Args:
        samples_str: String representing number of samples.
        max_n_locations: The max allowable number of locations, to keep query times reasonable.

    Returns:
        n_samples: Integer number of samples, or None if no samples provided.

    Raises:
        ClientError: Invalid n_samples.
    """
    if not samples_str:
        return None

    # Try to parse.
    try:
        n_samples = int(samples_str)
    except Exception as e:
        msg = f"Invalid value for samples argument '{samples_str}'."
        msg += " Samples should be an integer."
        raise ClientError(msg)

    # Must give 2+ samples.
    if n_samples < 2:
        msg = "Must provide at least 2 samples."
        msg += " The ends of the path are included as samples."
        raise ClientError(msg)

    # N samples will become the number of locations, so need to revalidate that.
    if n_samples > max_n_locations:
        msg = (
            f"Too many samples requested ({n_samples}), the limit is {max_n_locations}."
        )
        raise ClientError(msg)

    return n_samples


def _parse_nodata_value(nodata_value):
    """Check the nodata replacement value is valid.

    Must be 'null', 'nan', or a string of an integer.

    I'm not currently allowing floats for now. Parsing them has a lot of
    edgecases in Python (https://stackoverflow.com/a/20929983/2446304) and
    it's probably a bad idea to use floats as special values.


    Args:
        nodata_value: String value for nodata, or None for default.

    Returns:
        A valid NODATA replacement value.

    Raises:
        ClientError: Provided NODATA replacement value isn't supported.
    """
    if nodata_value is None:
        nodata_value = DEFAULT_NODATA_VALUE

    # A Python None is represented as null in json.
    if nodata_value == "null":
        return None

    # NaN isn't a valid value in json, but it's supported by some packages
    # (including Python), and is allowed here for backwards compatibility.
    if nodata_value.lower() == "nan":
        return float("NaN")

    # Integers are properly supported in json.
    try:
        int_value = int(nodata_value)
        return int_value
    except ValueError:
        pass

    # Invalid value.
    msg = f"Invalid nodata value '{nodata_value}'."
    msg += " Valid nodata values are 'null', 'nan', or an integer."
    raise ClientError(msg)


def _parse_locations(locations, max_n_locations):
    """Parse and validate the locations GET argument.

    The "locations" argument of the query should be "lat,lon" pairs delimited
    by "|" characters, or a string in Google polyline format.


    Args:
        locations: The location query string.
        max_n_locations: The max allowable number of locations, to keep query times reasonable.

    Returns:
        lats: List of latitude floats.
        lons: List of longitude floats.

    Raises:
        ClientError: If too many locations are given, or if the location string can't be parsed.
    """
    if not locations:
        msg = "No locations provided."
        msg += " Add locations in a query string: ?locations=lat1,lon1|lat2,lon2."
        raise ClientError(msg)

    # "," isbn't a valid character in a polyline.
    if "," in locations:
        return _parse_latlon_locations(locations, max_n_locations)
    else:
        return _parse_polyline_locations(locations, max_n_locations)


def _parse_polyline_locations(locations, max_n_locations):
    """Parse and validate locations in Google polyline format.

    The "locations" argument of the query should be a string of ascii characters above 63.


    Args:
        locations: The location query string.
        max_n_locations: The max allowable number of locations, to keep query times reasonable.

    Returns:
        lats: List of latitude floats.
        lons: List of longitude floats.

    Raises:
        ClientError: If too many locations are given, or if the location string can't be parsed.
    """

    # The Google maps API prefixes their polylines with 'enc:'.
    if locations and locations.startswith("enc:"):
        locations = locations[4:]

    try:
        latlons = polyline.decode(locations)
    except Exception as e:
        msg = "Unable to parse locations as polyline."
        raise ClientError(msg)

    # Polyline result in in list of (lat, lon) tuples.
    lats = [p[0] for p in latlons]
    lons = [p[1] for p in latlons]

    # Check number.
    n_locations = len(lats)
    if n_locations > max_n_locations:
        msg = f"Too many locations provided ({n_locations}), the limit is {max_n_locations}."
        raise ClientError(msg)

    return lats, lons


def _parse_latlon_locations(locations, max_n_locations):
    """Parse and validate "lat,lon" pairs delimited by "|" characters.


    Args:
        locations: The location query string.
        max_n_locations: The max allowable number of locations, to keep query times reasonable.

    Returns:
        lats: List of latitude floats.
        lons: List of longitude floats.

    Raises:
        ClientError: If too many locations are given, or if the location string can't be parsed.
    """

    # Check number of points.
    locations = locations.strip("|").split("|")
    n_locations = len(locations)
    if n_locations > max_n_locations:
        msg = f"Too many locations provided ({n_locations}), the limit is {max_n_locations}."
        raise ClientError(msg)

    # Parse each location.
    lats = []
    lons = []
    for i, loc in enumerate(locations):
        if "," not in loc:
            msg = f"Unable to parse location '{loc}' in position {i+1}."
            msg += " Add locations like lat1,lon1|lat2,lon2."
            raise ClientError(msg)

        # Separate lat & lon.
        parts = loc.split(",", 1)
        lat = parts[0]
        lon = parts[1]

        # Cast to numeric.
        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            msg = f"Unable to parse location '{loc}' in position {i+1}."
            raise ClientError(msg)

        # Check bounds.
        if not (LAT_MIN <= lat <= LAT_MAX):
            msg = f"Unable to parse location '{loc}' in position {i+1}."
            msg += f" Latitude must be between {LAT_MIN} and {LAT_MAX}."
            msg += " Provide locations in lat,lon order."
            raise ClientError(msg)
        if not (LON_MIN <= lon <= LON_MAX):
            msg = f"Unable to parse location '{loc}' in position {i+1}."
            msg += f" Longitude must be between {LON_MIN} and {LON_MAX}."
            raise ClientError(msg)

        lats.append(lat)
        lons.append(lon)

    return lats, lons


def _load_datasets():
    """Load datasets defined in config.

    Returns:
        Dict of {dataset_name: config.Dataset object} items.
    """
    if os.environ.get("DISABLE_MEMCACHE") or "datasets" not in _SIMPLE_CACHE:
        _SIMPLE_CACHE["datasets"] = _load_datasets_memcache()
    return _SIMPLE_CACHE["datasets"]


@cache.cached(key_prefix="_load_datasets")
def _load_datasets_memcache():
    return config.load_datasets()


def _get_datasets(name):
    """Retrieve datasets with error handling.

    If the name refers to a MultiDataset, load all child datasets.

    Args:
        name: Dataset name string (as used in request url and config file).

    Returns:
        List of config.Dataset object.

    Raises:
        ClientError: If the name isn't defined in the config.
    """

    all_datasets = _load_datasets()

    # Multiple datasets are separated by a comma.
    names = name.strip(",").split(",")
    names = [n.strip() for n in names]
    names = [n for n in names if n]
    if not names:
        raise ClientError("No valid dataset names provided.")
    if len(set(names)) < len(names):
        raise ClientError("Duplicate dataset names provided.")

    # Check all names exist.
    unfound_names = [n for n in names if n not in all_datasets]
    if len(unfound_names) == 1:
        raise ClientError(f"Dataset '{unfound_names[0]}' not in config.")
    elif len(unfound_names) > 1:
        raise ClientError(f"Datasets '{', '.join(unfound_names)}' not in config.")

    # Turn names into datasets.
    datasets = []
    for dataset_name in names:
        dataset = all_datasets[dataset_name]
        if isinstance(dataset, config.MultiDataset):
            datasets += [all_datasets[d] for d in dataset.child_dataset_names]
        else:
            datasets.append(dataset)

    # Ensure uniqueness after resolving multidatasets.
    dataset_names = [d.name for d in datasets]
    if len(dataset_names) > len(set(dataset_names)):
        raise ConfigError("Datasets must be unique after resolving MultiDatasets.")

    return datasets


@app.route("/", methods=["GET", "POST", "OPTIONS", "HEAD"])
@app.route("/v1/", methods=["GET", "POST", "OPTIONS", "HEAD"])
def get_help_message():
    msg = "No dataset name provided."
    msg += " Try a url like '/v1/test-dataset?locations=-10,120' to get started,"
    msg += " and see https://www.opentopodata.org for full documentation."
    return jsonify({"status": "INVALID_REQUEST", "error": msg}), 404


@app.route("/health", methods=["GET", "OPTIONS", "HEAD"])
def get_health_status():
    """Status endpoint for e.g., uptime check or load balancing."""
    try:
        _load_config()
        _load_datasets()
        data = {"status": "OK"}
        return jsonify(data)
    except Exception:
        data = {"status": "SERVER_ERROR"}
        return jsonify(data), 500


@app.route("/datasets", methods=["GET", "OPTIONS", "HEAD"])
def get_datasets_info():
    """List of datasets on the server."""
    try:
        all_datasets = _load_datasets()
        results = []
        for dataset in all_datasets.values():
            d = {}
            d["name"] = dataset.name
            if isinstance(dataset, config.MultiDataset):
                d["child_datasets"] = dataset.child_dataset_names
            else:
                d["child_datasets"] = []
            results.append(d)
        results.sort(key=lambda x: x["name"])
        return jsonify({"results": results, "status": "OK"})
    except Exception as e:
        data = {"status": "SERVER_ERROR"}
        return jsonify(data), 500


@app.route("/v1/<dataset_name>", methods=["GET", "POST", "OPTIONS", "HEAD"])
def get_elevation(dataset_name):
    """Calculate the elevation for the given locations.

    Args:
        dataset_name: String matching a dataset in the config file.

    Returns:
        Response.
    """

    try:
        # Parse inputs.
        interpolation = _parse_interpolation(
            _find_request_argument(request, "interpolation")
        )
        nodata_value = _parse_nodata_value(
            _find_request_argument(request, "nodata_value")
        )
        lats, lons = _parse_locations(
            _find_request_argument(request, "locations"),
            _load_config()["max_locations_per_request"],
        )

        # Check if need to do sampling.
        n_samples = _parse_n_samples(
            _find_request_argument(request, "samples"),
            _load_config()["max_locations_per_request"],
        )
        if n_samples:
            lats, lons = utils.sample_points_on_path(lats, lons, n_samples)

        # Get the z values.
        datasets = _get_datasets(dataset_name)
        elevations, dataset_names = backend.get_elevation(
            lats, lons, datasets, interpolation, nodata_value
        )

        # Build response.
        results = []
        for z, dataset_name, lat, lon in zip(elevations, dataset_names, lats, lons):
            results.append(
                {
                    "elevation": z,
                    "dataset": dataset_name,
                    "location": {"lat": lat, "lng": lon},
                }
            )
        data = {"status": "OK", "results": results}
        return jsonify(data)

    except (ClientError, backend.InputError) as e:
        return jsonify({"status": "INVALID_REQUEST", "error": str(e)}), 400
    except config.ConfigError as e:
        return (
            jsonify({"status": "SERVER_ERROR", "error": "Config Error: {}".format(e)}),
            500,
        )
    except Exception as e:
        if app.debug:
            raise e
        app.logger.error(e)
        msg = "Unhandled server error, see server logs for details."
        return jsonify({"status": "SERVER_ERROR", "error": msg}), 500


@app.after_request
def add_version(response):
    if "version" not in _SIMPLE_CACHE:
        with open(VERSION_PATH) as f:
            version = f.read().strip()
        _SIMPLE_CACHE["version"] = version
    response.headers["x-opentopodata-version"] = _SIMPLE_CACHE["version"]
    return response
