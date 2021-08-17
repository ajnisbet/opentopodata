from decimal import Decimal
from glob import glob
from urllib.parse import urlparse
import abc
import os
import re
import yaml

import numpy as np
import rasterio

from opentopodata import utils

CONFIG_PATH = "config.yaml"
EXAMPLE_CONFIG_PATH = "example-config.yaml"
FILENAME_TILE_REGEX = r"^.*?([NS][\dx]+_?[WE][\dx]+).*?$"
AUX_EXTENSIONS = [".tfw", ".aux", ".aux.xml", ".rdd", ".jpw", ".ovr", ".prj"]

DEFAULTS = {
    "max_locations_per_request": 100,
    "dataset.filename_tile_size": 1,
    "dataset.filename_epsg": utils.WGS84_LATLON_EPSG,
    "access_control_allow_origin": None,
}


class ConfigError(ValueError):
    """Invalid config."""

    pass


def _find_config():
    """Path to the config file.

    Having a fallback path means the API can have some demo data without being
    configured, but also the used can easily override without messing up git
    or deleting the reference file.

    Returns:
        String path to config yaml file.

    """
    if os.path.exists(CONFIG_PATH):
        return CONFIG_PATH
    elif os.path.exists(EXAMPLE_CONFIG_PATH):
        return EXAMPLE_CONFIG_PATH
    return None


def _validate_cors(url):
    """Validate access-control-allow-origin header.

    Must be None, '*', or a protocol + domain (+ port).

    Raises exception if invalid.

    This is only a rough validation intended to help users avoid common conifg
    issues, not a guarantee the header will work or not crash flask.

    Args:
        url: Value to test (string or None).
    """

    if url is None or url == "*":
        return

    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ConfigError("Error parsing access_control_allow_origin.")
    if not parsed.scheme:
        raise ConfigError(
            "access_control_allow_origin must include protocol (e.g., https)" + url
        )
    if not parsed.netloc:
        raise ConfigError(
            "access_control_allow_origin must include domain (e.g., example.com)"
        )
    if parsed.path not in ("", "/"):
        raise ConfigError("access_control_allow_origin shouldn't include path.")

    return


def load_config():
    """Read and validate config file.

    Returns:
        config: dict of yaml file.

    Raises:
        ConfigError: if invalid.
    """
    path = _find_config()

    if not path:
        absolute_path = os.path.abspath(CONFIG_PATH)
        raise ConfigError("No config file found at {}.".format(absolute_path))

    try:
        with open(path) as f:
            config = yaml.safe_load(f)
    except Exception as e:
        raise ConfigError(str(e))

    # Validate datasets.
    if not config.get("datasets"):
        raise ConfigError("Config must contain at least one dataset.")
    if any("name" not in d for d in config["datasets"]):
        raise ConfigError("All datasets must have a 'name' attribute.")
    if any("path" not in d and "child_datasets" not in d for d in config["datasets"]):
        raise ConfigError("All datasets must have a 'path' attribute.")
    if any("," in d["name"] for d in config["datasets"]):
        msg = "Dataset can't contain the ',' character"
        msg += ", as this is used as a delimiter for multiple datasets."
        raise ConfigError(msg)

    # Check all child datasets are valid. This logic prevents cycles of
    # datasets: a child dataset can't be a MultiDataset.
    candidate_names = set()
    child_names = set()
    for d in config["datasets"]:
        if "child_datasets" in d:
            child_names.update(d["child_datasets"])
        else:
            candidate_names.add(d["name"])
    missing_child_names = child_names - candidate_names
    if missing_child_names:
        all_names = set(d["name"] for d in config["datasets"])
        msg = f"Child datasets {sorted(missing_child_names)} not in config."
        if len(missing_child_names) > len(missing_child_names - all_names):
            msg += " A child dataset can't be a MultiDataset."
        raise ConfigError(msg)

    # Set defaults.
    config["max_locations_per_request"] = config.get(
        "max_locations_per_request", DEFAULTS["max_locations_per_request"]
    )
    config["access_control_allow_origin"] = config.get(
        "access_control_allow_origin", DEFAULTS["access_control_allow_origin"]
    )

    # Validate CORS. Must have protocol, domain, and optionally port.
    _validate_cors(config["access_control_allow_origin"])

    return config


def load_datasets():
    """Init Dataset objects

    Returns:
        datasets: Dict of {dataset_name: Dataset object} from config.datasets.
    """
    config = load_config()
    datasets = {d["name"]: Dataset.from_config(**d) for d in config["datasets"]}
    return datasets


class MultiDataset:
    def __init__(self, name, child_dataset_names):
        if not child_dataset_names:
            raise ConfigError(f"child_datasets for {name} can't be empty.")
        self.name = name
        self.child_dataset_names = child_dataset_names


class Dataset(abc.ABC):
    """Base class for Dataset.

    The elevation data could be split over multiple files. This class exists
    to map a location to a particular file.
    """

    # By default, assume raster spans whole globe.
    wgs84_bounds = rasterio.coords.BoundingBox(-180, -90, 180, 90)

    @classmethod
    def _is_aux_file(cls, path):
        return any([path.lower().endswith(e) for e in AUX_EXTENSIONS])

    @classmethod
    def from_config(cls, name, path=None, **kwargs):
        """Initialise a Dataset from the config.

        Based on the filename format, the appropriate kind of Dataset will be
        initialised.

        Args:
            name: String used in request url and as datasets dictionary key.
            path: String path to directory containing dataset.
            kwargs: Passed to subclass __init__.

        Returns:
            Subclass of Dataset.
        """

        # Multi datasets are handled separately.
        if "child_datasets" in kwargs:
            return MultiDataset(name, kwargs["child_datasets"])

        # Check the dataset is there.
        if not os.path.isdir(path):
            raise ConfigError("No dataset folder found at location '{}'".format(path))

        # Find all the files in the dataset.
        pattern = os.path.join(path, "**", "*")
        all_paths = list(glob(pattern, recursive=True))
        all_files = [p for p in all_paths if os.path.isfile(p)]
        all_rasters = [p for p in all_files if not cls._is_aux_file(p)]
        if not all_rasters:
            raise ConfigError("Dataset folder '{}' seems to be empty.".format(path))

        # Build bounds.
        wgs84_bounds = None
        if "wgs84_bounds" in kwargs:
            wgs84_bounds = rasterio.coords.BoundingBox(
                kwargs["wgs84_bounds"]["left"],
                kwargs["wgs84_bounds"]["bottom"],
                kwargs["wgs84_bounds"]["right"],
                kwargs["wgs84_bounds"]["top"],
            )

        # Check for single file.
        if len(all_rasters) == 1:
            tile_path = all_rasters[0]
            try:
                with rasterio.open(tile_path):
                    pass
            except rasterio.RasterioIOError as e:
                raise ConfigError("Unsupported filetype for '{}'.".format(tile_path))
            return SingleFileDataset(
                name, tile_path=tile_path, wgs84_bounds=wgs84_bounds
            )

        # Check for SRTM-style naming.
        all_filenames = [os.path.basename(p) for p in all_rasters]
        is_srtm_raster = [
            re.match(FILENAME_TILE_REGEX, f, re.IGNORECASE) for f in all_filenames
        ]
        if all(is_srtm_raster):
            filename_epsg = kwargs.get(
                "filename_epsg", DEFAULTS["dataset.filename_epsg"]
            )
            filename_tile_size = kwargs.get(
                "filename_tile_size", DEFAULTS["dataset.filename_tile_size"]
            )
            return TiledDataset(
                name,
                path,
                tile_paths=all_rasters,
                filename_epsg=filename_epsg,
                filename_tile_size=filename_tile_size,
                wgs84_bounds=wgs84_bounds,
            )

        # Unable to identify dataset type.
        msg = f"Unknown dataset type for '{name}'. Dataset should either be a single file,"
        msg += " or split into tiles with the lower-left corner coord in the filename like 'N20W120'."
        msg += f" Unrecognised filename: '{all_filenames[np.argmin(is_srtm_raster)]}'."
        raise ConfigError(msg)

    @abc.abstractmethod
    def location_paths(self, lats, lons):
        """File corresponding to each location.

        Args:
            lats, lons: Lists of locations.

        Returns:
            List of filenames, same length as locations.
        """


class SingleFileDataset(Dataset):
    def __init__(self, name, tile_path, wgs84_bounds=None):
        """A dataset consisting of a single raster file.

        Args:
            name: String used in request url and as datasets dictionary key.
            tile_path: String path to single raster file.
        """
        self.name = name
        self.tile_path = tile_path
        if wgs84_bounds:
            self.wgs84_bounds = wgs84_bounds

    def location_paths(self, lats, lons):
        """File corresponding to each location.

        Args:
            lats, lons: Lists of locations.

        Returns:
            List of filenames, same length as locations.
        """
        assert len(lats) == len(lons)
        return [self.tile_path] * len(lats)


class TiledDataset(Dataset):
    def __init__(
        self,
        name,
        path,
        tile_paths,
        filename_epsg,
        filename_tile_size,
        wgs84_bounds=None,
    ):
        """A dataset of files named in SRTM format.

        Each file should be a square tile, named like N50W121 for the lower left (SW) corner.

        GDAL supports SRTM-named .hgt files individually (it can infer the
        bounds from the filename) but won't find the correct file for you. This does that.

        Args:
            name: String used in request url and as datasets dictionary key.
            tile_path: String path to single raster file.
            path: Path to folder containing SRTM files.
            tile_paths: List of individual raster file paths in the dataset.
            filename_epsg: Coordinate system of the filename.
            filename_tile_size: Size of each tile, in the coordinate system units. Used for
                rounding down the location to get the corner. Assumed to have an offset from zero.
        """
        self.name = name
        self.path = path
        self.filename_epsg = filename_epsg

        # Bounds.
        if wgs84_bounds:
            self.wgs84_bounds = wgs84_bounds

        # Validate tile size.
        if isinstance(filename_tile_size, float):
            if filename_tile_size.is_integer():
                filename_tile_size = int(filename_tile_size)
            else:
                msg = "Non-integer tile sizes should be specified as a string like "
                msg += f" filename_tile_size: '{str(filename_tile_size)}"
                msg += " to avoiding floating point precision issues."
                raise ConfigError(msg)

        # Parse tile size.
        try:
            self.filename_tile_size = Decimal(filename_tile_size)
        except Exception as e:
            msg = f"Unable to parse filename_tile_size {filename_tile_size}"
            raise ConfigError(msg)

        # Build tile lookup.
        corners = [self._filename_to_tile_corner(p) for p in tile_paths]
        if len(corners) > len(set(corners)):
            msg = "SRTM-type tile coords must be unique,"
            msg += " cannot be the same tile with different extensions."
            raise ConfigError(msg)
        self._tile_lookup = dict(zip(corners, tile_paths))

    @classmethod
    def _filename_to_tile_corner(cls, filename):
        """Exctract the corner lat/lon or y/x location from a filename.


        Args:
            filename: Name of an SRTM style tile (like N50W25).

        Returns:
            y, x: decimal.Decimal location of lower-left corner.
        """
        # Normalise if a full path is passed.
        filename = os.path.basename(filename)

        # Extract components.
        northing_str = (
            re.search(r"([NS][\dx]+)_?[WE]", filename, re.IGNORECASE)[1]
            .lower()
            .replace("x", ".")
        )
        easting_str = (
            re.search(r"[NS][\dx]+_?([WE][\dx]+)", filename, re.IGNORECASE)[1]
            .lower()
            .replace("x", ".")
        )

        # Positive or negative.
        northing_sign = 1 if northing_str.startswith("n") else -1
        easting_sign = 1 if easting_str.startswith("e") else -1

        # Numerics.
        northing = northing_sign * Decimal(northing_str[1:])
        easting = easting_sign * Decimal(easting_str[1:])

        return northing, easting

    @classmethod
    def _location_to_tile_corner(cls, xs, ys, tile_size=1):
        """Convert locations to SRTM tile corner.

        For example, (-120.5, 40.1) becomes (-120, 40). The lower left corner
        of the tile is used. Decimals are used to preserve precsion for
        fractional tile sizes.

        Args:
            xs, ys: Lists of x and y coordinates.
            tile_size: Which value to round the tiles to. Int or Decimal.

        Returns:
            tile_names: List of (Decimal, Decimal) northing, easting tuples.
        """

        northings = [utils.decimal_base_floor(y, tile_size) for y in ys]
        eastings = [utils.decimal_base_floor(y, tile_size) for y in xs]

        return list(zip(northings, eastings))

    def location_paths(self, lats, lons):
        """File corresponding to each location.

        Args:
            lats, lons: Lists of locations.

        Returns:
            List of filenames, same length as locations.
        """
        lats = np.asarray(lats)
        lons = np.asarray(lons)

        # Convert to filename projection.
        xs, ys = utils.reproject_latlons(lats, lons, epsg=self.filename_epsg)

        # Find corresponding tile.
        filenames = self._location_to_tile_corner(xs, ys, self.filename_tile_size)
        paths = [self._tile_lookup.get(f) for f in filenames]

        return paths
