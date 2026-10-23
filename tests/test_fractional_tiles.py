from decimal import Decimal
import math

import pytest

from opentopodata import config, utils


@pytest.mark.parametrize(
    "value,base,expected",
    [
        (0.3, Decimal("0.1"), Decimal("0.3")),
        (0.6, Decimal("0.2"), Decimal("0.6")),
        (-0.3, Decimal("0.1"), Decimal("-0.3")),
        (-0.31, Decimal("0.1"), Decimal("-0.4")),
        (0.31, Decimal("0.1"), Decimal("0.3")),
        (math.nextafter(0.3, 0), Decimal("0.1"), Decimal("0.2")),
        (Decimal("0.3"), Decimal("0.1"), Decimal("0.3")),
        (3, 2, Decimal("2")),
    ],
)
def test_decimal_floor_preserves_tile_boundaries(value, base, expected):
    assert utils.decimal_base_floor(value, base) == expected


def test_decimal_floor_rejects_float_base():
    with pytest.raises(ValueError, match="Base must be an integer or decimal"):
        utils.decimal_base_floor(0.3, 0.1)


def test_fractional_tile_lookup_at_boundary():
    paths = ["synthetic/N0x2E0x2.tif", "synthetic/N0x3E0x3.tif"]
    dataset = config.TiledDataset(
        "synthetic",
        "synthetic",
        tile_paths=paths,
        filename_epsg=4326,
        filename_tile_size="0.1",
    )

    assert dataset.location_paths([0.3], [0.3]) == [paths[1]]
