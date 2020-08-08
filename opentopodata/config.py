from glob import glob
from urllib.parse import urlparse
import os
import re
import yaml

import numpy as np
import rasterio

from opentopodata import utils

CONFIG_PATH = "config.yaml"
EXAMPLE_CONFIG_PATH = "example-config.yaml"
FILENAME_TILE_REGEX = r"^.*?([NSns]\d+[WEwe]\d+).*?$"
AUX_EXTENSIONS = [".tfw", ".aux", ".aux.xml", ".rdd", ".jpw", ".ovr"]

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
    if any("path" not in d for d in config["datasets"]):
        raise ConfigError("All datasets must have a 'path' attribute.")

    # Set defualts.
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


class Dataset:
    """Base class for Dataset.

    The elevation data could be split over multiple files. This class exists
    to map a location to a particular file.
    """

    @classmethod
    def _is_aux_file(cls, path):
        return any([path.lower().endswith(e) for e in AUX_EXTENSIONS])

    @classmethod
    def from_config(cls, name, path, **kwargs):
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

        # Check for single file.
        if len(all_rasters) == 1:
            tile_path = all_rasters[0]
            try:
                with rasterio.open(tile_path):
                    pass
            except rasterio.RasterioIOError as e:
                raise ConfigError("Unsupported filetype for '{}'.".format(tile_path))
            return SingleFileDataset(name, tile_path=tile_path)

        # Check for SRTM-style naming.
        all_filenames = [os.path.basename(p) for p in all_rasters]
        if all([re.match(FILENAME_TILE_REGEX, f) for f in all_filenames]):
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
            )

        raise ConfigError(
            "Unknown dataset type for '{}'. Dataset should either be a single file, or split up into tiles with the lower-left corner coordinate in the filename like 'N20W120'.".format(
                name
            )
        )

    def location_paths(self, lats, lons):
        raise NotImplementedError


class SingleFileDataset(Dataset):
    def __init__(self, name, tile_path):
        """A dataset consisting of a single raster file.

        Args:
            name: String used in request url and as datasets dictionary key.
            tile_path: String path to single raster file.
        """
        self.name = name
        self.tile_path = tile_path

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
    def __init__(self, name, path, tile_paths, filename_epsg, filename_tile_size):
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
        self.filename_tile_size = filename_tile_size

        # Build lookup from filename without extension to path.
        tile_filenames = [os.path.basename(p).split(".")[0] for p in tile_paths]
        tile_names = [
            re.match(FILENAME_TILE_REGEX, f).groups()[0].upper() for f in tile_filenames
        ]
        if len(tile_names) != len(set(tile_names)):
            msg = "SRTM-type tile coords must be unique,"
            msg += " cannot be the same tile with different extensions."
            raise ConfigError(msg)

        # Find if the filenames use fixed-width zero padding.
        ns = [re.search(r"[NS](\d+)[WE]", x)[1] for x in tile_names]
        ew = [re.search(r"[WE](\d+)", x)[1] for x in tile_names]
        ns_lens = set(len(x) for x in ns)
        ew_lens = set(len(x) for x in ew)
        self.ns_fixed_width = ns_lens.pop() if len(ns_lens) == 1 else None
        self.ew_fixed_width = ew_lens.pop() if len(ew_lens) == 1 else None

        self._tile_lookup = dict(zip(tile_names, tile_paths))

    @classmethod
    def _location_to_tile_name(
        cls, xs, ys, tile_size=1, ns_fixed_width=None, ew_fixed_width=None
    ):
        """Convert locations to SRTM tile name.

        For example, (-120.5, 40.1) becomes N40W121. The lower left corner of
        the tile is used. The numbers can be padded with leading zeroes to all
        be the same width.

        Args:
            xs, ys: Lists of x and y coordinates.
            tile_size: Which value to round the tiles to.
            ns_fixed_width, ew_fixed_width: Integer to pad with zeroes. None means no padding.

        Returns:
            tile_names: List of strings.
        """

        n_or_s = np.where(ys >= 0, "N", "S")
        e_or_w = np.where(xs >= 0, "E", "W")

        ns_value = np.abs(utils.base_floor(ys, tile_size)).astype(int).astype(str)
        ew_value = np.abs(utils.base_floor(xs, tile_size)).astype(int).astype(str)

        ns_fixed_width = ns_fixed_width or 0
        ew_fixed_width = ew_fixed_width or 0

        ns_value = [x.zfill(ns_fixed_width) for x in ns_value]
        ew_value = [x.zfill(ew_fixed_width) for x in ew_value]

        tile_names = np.char.add(n_or_s, ns_value)
        tile_names = np.char.add(tile_names, e_or_w)
        tile_names = np.char.add(tile_names, ew_value)

        return tile_names

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
        xs, ys, = utils.reproject_latlons(lats, lons, epsg=self.filename_epsg)

        # Use to look up.
        filenames = self.__class__._location_to_tile_name(
            xs, ys, self.filename_tile_size, self.ns_fixed_width, self.ew_fixed_width
        )
        paths = [self._tile_lookup.get(f) for f in filenames]

        return paths
