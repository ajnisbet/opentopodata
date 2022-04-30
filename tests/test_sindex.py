import rasterio

from opentopodata import sindex


class TestBoundingBox:
    def test_attributes(self):
        left = 1
        bottom = 2
        right = 3
        top = 4
        bbox = sindex._BoundingBox(left, bottom, right, top)
        assert bbox.left == left
        assert bbox.bottom == bottom
        assert bbox.right == right
        assert bbox.top == top

    def test_rasterio_compat(self):
        left = 1
        bottom = 2
        right = 3
        top = 4
        tup = (left, bottom, right, top)
        otd_bbox = sindex._BoundingBox(*tup)
        rio_bbox = rasterio.coords.BoundingBox(*tup)
        assert otd_bbox.left == rio_bbox.left
        assert otd_bbox.bottom == rio_bbox.bottom
        assert otd_bbox.right == rio_bbox.right
        assert otd_bbox.top == rio_bbox.top


class TestTile:
    def test_bbox(self):
        left = 1
        bottom = 2
        right = 3
        top = 4
        bbox = sindex._BoundingBox(left, bottom, right, top)
        tile = sindex._Tile(bbox, None, None)
        assert bbox.left == tile.left
        assert bbox.bottom == tile.bottom
        assert bbox.right == tile.right
        assert bbox.top == tile.top

    def test_hash(self):
        left = 1
        bottom = 2
        right = 3
        top = 4
        bbox = sindex._BoundingBox(left, bottom, right, top)
        t1 = sindex._Tile(bbox, shape=(10, 10), path="/p/1")
        t2 = sindex._Tile(bbox, shape=(10, 10), path="/p/2")
        t3 = sindex._Tile(bbox, shape=(10, 10), path="/p/3")
        assert len(set([t1, t2, t3, t1, t2, t3])) == 3

    def test_res(self):
        left = 1
        bottom = 2
        right = 3
        top = 4
        bbox = sindex._BoundingBox(left, bottom, right, top)
        t1 = sindex._Tile(bbox, shape=(10, 10), path="/p/1")
        t2 = sindex._Tile(bbox, shape=(9, 9), path="/p/2")
        assert t2.res > t1.res


class TestBoundingBoxIndex:
    def test_single_tile(self):
        tile = sindex._BoundingBox(-10, -10, 10, 10)
        bbi = sindex.BoundingBoxIndex([tile])
        res = bbi._query_single_all_intersecting(0, 0)
        assert tile in res
        assert len(res) == 1

    def test_no_tile(self):
        tile = sindex._BoundingBox(-10, -10, 10, 10)
        bbi = sindex.BoundingBoxIndex([tile])
        res = bbi._query_single(11, 11)
        assert not res

    def test_multi(self):
        t1 = sindex._Tile((-1, -1, 1, 1), shape=(1, 1), path="/p1")
        t2 = sindex._Tile((-2, -2, 2, 2), shape=(1, 1), path="/p1")
        t3 = sindex._Tile((4, 4, 5, 5), shape=(1, 1), path="/p1")
        bbi = sindex.BoundingBoxIndex([t1, t2, t3])
        lats = [0, 1.5, 4.5, 9]
        lons = [0, 1.5, 4.5, 9]
        res = bbi.query(lats, lons)
        assert res[0] == t1 or res[0] == t2
        assert res[1] == t2
        assert res[2] == t3
        assert not res[3]

    def test_multi_prefilter(self):
        t1 = sindex._Tile((-1, -1, 1, 1), shape=(1, 1), path="/p1")
        t2 = sindex._Tile((-2, -2, 2, 2), shape=(1, 1), path="/p1")
        t3 = sindex._Tile((4, 4, 5, 5), shape=(1, 1), path="/p1")
        bbi = sindex.BoundingBoxIndex([t1, t2, t3])
        oob = 89
        lats = [0, 1.5, 4.5, 9] + [oob] * bbi.PREFILTER_THRESHOLD
        lons = [0, 1.5, 4.5, 9] + [oob] * bbi.PREFILTER_THRESHOLD
        res = bbi.query(lats, lons)
        assert res[0] == t1 or res[0] == t2
        assert res[1] == t2
        assert res[2] == t3
        assert not res[3]
        assert all(not r for r in res[4:])

    def _query_single_all_intersecting(self):
        t1 = sindex._Tile((-1, -1, 1, 1), shape=(1, 1), path="/p1")
        t2 = sindex._Tile((-2, -2, 2, 2), shape=(1, 1), path="/p1")
        t3 = sindex._Tile((4, 4, 5, 5), shape=(1, 1), path="/p1")
        bbi = sindex.BoundingBoxIndex([t1, t2, t3])
        res = bbi._query_single_all_intersecting(0, 0)
        assert len(res) == 2
        assert t1 in res
        assert t2 in res
