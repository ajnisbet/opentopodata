import os
import yaml
from glob import glob
import rasterio
import re
import numpy as np

from opentopodata import utils

CONFIG_PATH = "config.yaml"
EXAMPLE_CONFIG_PATH = "example-config.yaml"
FILENAME_TILE_REGEX = r"^[NS]\d+[WE]\d+.*?$"

DEFAULTS = {
    "max_locations_per_request": 100,
    "dataset.filename_tile_size": 1,
    "dataset.filename_epsg": utils.WGS84_LATLON_EPSG,
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

    return config


def load_datasets():
    """Init Dataset objects

    Returns:
        datasets: Dict of {dataset_name: Dataset obejct} from config.datasets.
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
    def from_config(self, name, path, **kwargs):
        """Initialise a Dataset from the config.

        Based on the filename format, the appropriate kind of Dataset will be
        initialised.
    
        Args:
            name: String used in request url and as datasets dictionary key.
            path: String path to diractory containing dataset.
            kwargs: Passed to sublclass __init__.

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
        if not all_files:
            raise ConfigError("Dataset folder '{}' seems to be empty.".format(path))

        # Check for single file.
        if len(all_files) == 1:
            tile_path = all_files[0]
            try:
                with rasterio.open(tile_path):
                    pass
            except rasterio.RasterioIOError as e:
                raise ConfigError("Unsupported filetype for '{}'.".format(tile_path))
            return SingleFileDataset(name, tile_path=tile_path)

        # Check for srtm.
        all_filenames = [os.path.basename(p) for p in all_files]
        if all([re.match(FILENAME_TILE_REGEX, f) for f in all_filenames]):
            filename_epsg = kwargs.get(
                "filename_epsg", DEFAULTS["dataset.filename_epsg"]
            )
            filename_tile_size = kwargs.get(
                "filename_tile_size", DEFAULTS["dataset.filename_tile_size"]
            )
            return SRTMDataset(
                name,
                path,
                tile_paths=all_files,
                filename_epsg=filename_epsg,
                filename_tile_size=filename_tile_size,
            )

        raise ConfigError("Unknown dataset type for '{}'.".format(name))

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


class SRTMDataset(Dataset):
    LAT_MIN = -60
    LAT_MAX = 60
    FILL_VALUE = np.nan

    def __init__(self, name, path, tile_paths, filename_epsg, filename_tile_size):
        """A dataset of files named in SRTM format.

        GDAL supports SRTM-named .hgt files indivudially (it can infer the
        bounds from the filename) but won't find the correct file for you. This does that.

        Args:
            name: String used in request url and as datasets dictionary key.
            tile_path: String path to single raster file.
            path: Path to folder containing SRTM files.
            tile_paths: List of infividial raster file paths in the dataset.
        """
        self.name = name
        self.path = path
        self.filename_epsg = filename_epsg
        self.filename_tile_size = filename_tile_size

        # Build lookup from filename without extension to path.
        tile_filenames = [os.path.basename(p).split(".")[0] for p in tile_paths]
        if len(tile_filenames) != len(set(tile_filenames)):
            msg = "SRTM filenames must be unique,"
            msg += " cannot be the same tile with different extentions."
            raise ConfigError(msg)

        # Find if the filenames use fixed-width zerop padding.
        ns = [re.search(r"[NS](\d+)[WE]", x)[1] for x in tile_filenames]
        ew = [re.search(r"[WE](\d+)", x)[1] for x in tile_filenames]
        ns_lens = set(len(x) for x in ns)
        ew_lens = set(len(x) for x in ew)
        self.ns_fixed_width = ns_lens.pop() if len(ns_lens) == 1 else 0
        self.ew_fixed_width = ew_lens.pop() if len(ew_lens) == 1 else 0

        self._tile_lookup = dict(zip(tile_filenames, tile_paths))

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
        xs, ys, = utils.reproject_latlons(lats, lons, self.filename_epsg)

        n_or_s = np.where(ys >= 0, "N", "S")
        e_or_w = np.where(xs >= 0, "E", "W")

        ns_value = (
            np.abs(utils.base_floor(ys, self.filename_tile_size))
            .astype(int)
            .astype(str)
        )
        ew_value = (
            np.abs(utils.base_floor(xs, self.filename_tile_size))
            .astype(int)
            .astype(str)
        )

        ns_value = np.char.zfill(ns_value, self.ns_fixed_width)
        ew_value = np.char.zfill(ew_value, self.ew_fixed_width)

        filenames = np.char.add(n_or_s, ns_value)
        filenames = np.char.add(filenames, e_or_w)
        filenames = np.char.add(filenames, ew_value)

        paths = [self._tile_lookup.get(f) for f in filenames]

        return paths
