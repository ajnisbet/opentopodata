from dataclasses import dataclass
import copy

import numpy as np
from geographiclib.geodesic import Geodesic
import rasterio
import rasterio.warp
from collections import namedtuple

from opentopodata import utils


_BoundingBox = namedtuple("_BoundingBox", ("left", "bottom", "right", "top"))


class _Tile:
    def __init__(
        self,
        bounds,
        shape,
        path,
        crs=rasterio.crs.CRS.from_epsg(utils.WGS84_LATLON_EPSG),
    ):
        self.shape = shape
        self.path = path
        self.crs = crs
        self.orig_bounds = _BoundingBox(*bounds)

        # Use WGS84 bounds as sindex bbox.
        bbox = rasterio.warp.transform_bounds(
            self.crs,
            rasterio.crs.CRS.from_epsg(utils.WGS84_LATLON_EPSG),
            *self.orig_bounds,
        )
        self.bbox = _BoundingBox(*bbox)

    @property
    def left(self):
        return self.bbox.left

    @property
    def bottom(self):
        return self.bbox.bottom

    @property
    def right(self):
        return self.bbox.right

    @property
    def top(self):
        return self.bbox.top

    @property
    def res(self):
        """Res in m / px"""
        geod = Geodesic.WGS84
        diag_m = geod.Inverse(self.bottom, self.left, self.top, self.right)["s12"]
        diag_px = (self.shape[0] ** 2 + self.shape[1] ** 2) ** 0.5
        return diag_m / diag_px

    def __hash__(self):
        return hash((self.path, self.bbox))

    def __eq__(self, other):
        return self.path == other.path and self.bbox == other.bbox


class BoundingBoxIndex:
    PREFILTER_THRESHOLD = 5

    def __init__(self, tiles):
        self.lefts = np.array([t.left for t in tiles])
        self.rights = np.array([t.right for t in tiles])
        self.tops = np.array([t.top for t in tiles])
        self.bottoms = np.array([t.bottom for t in tiles])
        self.tiles = copy.deepcopy(tiles)
        self.indices = np.arange(len(tiles))

    def query(self, lats, lons):

        n = len(lats)
        ix = None
        if n > self.PREFILTER_THRESHOLD:
            ix = self.indices.copy()
            ix = ix[self.lefts[ix] <= np.max(lons)]
            ix = ix[self.rights[ix] >= np.min(lons)]
            ix = ix[self.tops[ix] >= np.min(lats)]
            ix = ix[self.bottoms[ix] <= np.max(lats)]

        return [self._query_single(lat, lon, ix) for lat, lon in zip(lats, lons)]

    def _query_single(self, lat, lon, ix=None):
        tiles = self._query_single_all_intersecting(lat, lon, ix)
        tile = self._tie_break(tiles)
        return tile

    def _query_single_all_intersecting(self, lat, lon, ix=None):
        if ix is None:
            ix = self.indices.copy()
        else:
            ix = ix.copy()

        is_left = self.lefts[ix] <= lon
        ix = ix[is_left]
        if not ix.size:
            return []

        is_right = self.rights[ix] >= lon
        ix = ix[is_right]
        if not ix.size:
            return []

        is_top = self.tops[ix] >= lat
        ix = ix[is_top]
        if not ix.size:
            return []

        is_bottom = self.bottoms[ix] <= lat
        ix = ix[is_bottom]
        if not ix.size:
            return []

        return [self.tiles[i] for i in ix]

    def _tie_break(self, tiles):
        if not tiles:
            return []
        return tiles[0]

    @classmethod
    def from_paths(cls, tile_paths):

        tiles = []
        geod = Geodesic.WGS84

        # Start loading. For each raster, we need the path and the wgs84 bounds.
        for tile_path in tile_paths:
            with rasterio.open(tile_path) as f:
                tile = _Tile(f.bounds, f.shape, tile_path, bounds_crs=f.crs)
                tiles.append(tile)

        return cls(tiles)
