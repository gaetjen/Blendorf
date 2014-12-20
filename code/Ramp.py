__author__ = 'Jo'

from enum import Enum
from Direction import Direction
from Terrain import TerrainType

class RampType (Enum):
    RAMP_0 = 0
    RAMP_1 = 1
    RAMP_2 = 2
    RAMP_CORNER = 3
    RAMP_4 = 4

class ConnectionType (Enum):
    Connect = 0
    WALL = 1
    END = 2

class Ramp:
    """contains more information about how the ramp is oriented and neighbors"""

    def __init__(self, tile):
        self.tops = []
        self.ramptype = RampType.RAMP_0
        self.rotate_direction = None
        self.find_tops(tile)
        self.left_dir = None
        self.right_dir = None
        self.left_connection = None
        self.right_connection = None
        assert self.rotate_direction is not None, "rotate direction was not set!"

    def find_tops(self, tile):
        self.add_naive_tops(tile)

        if len(self.tops) == 1:
            self.ramptype = RampType.RAMP_1
            self.rotate_direction = self.tops[0]

        if  len(self.tops) == 4:
            self.ramptype = RampType.RAMP_4
            self.rotate_direction = Direction.North

        if len(self.tops) == 0:
            self.rotate_direction = Direction.North
            self.find_diagonal_tops(tile)
            if len(self.tops) == 1:
                self.ramptype = RampType.RAMP_CORNER
                self.rotate_direction = self.tops[0][1]

        if len(self.tops) == 2:
            self.rotate_direction = self.tops[1]
            self.ramptype = RampType.RAMP_2
            self.decimate_tops_two()
            if len(self.tops) == 1:
                self.ramptype = RampType.RAMP_1
                self.rotate_direction = self.tops[0]

        if len(self.tops) == 3:
            self.ramptype = RampType.RAMP_2
            self.decimate_tops_three(tile)
            assert len(self.tops) < 3, "not decimated (3) properly"
            if len(self.tops) == 1:
                self.ramptype = RampType.RAMP_1
                self.rotate_direction = self.tops[0]
            else:
                self.rotate_direction = self.tops[1]

    def add_naive_tops(self, tile):
        for d in Direction:
            if tile.is_rampable([d]):
                self.tops.append(d)
        if self.tops == [0, 1, 3]:
            self.tops = [Direction.West, Direction.North, Direction.East]
        elif self.tops == [0, 2, 3]:
            self.tops = [Direction.South, Direction.West, Direction.North]
        elif self.tops == [0, 3]:
            self.tops = [Direction.West, Direction.North]

    def find_diagonal_tops(self, tile):
        diags = [Direction.West, Direction.North]
        for d in Direction:
            diags[1] = d
            if tile.is_rampable(diags):
                self.tops = [diags[:]]      # take [:] because diags gets changed later
            diags[0] = d

    def decimate_tops_two(self):
        rt = self.tops
        if (rt[0] + 2) % 4 == rt[1]:
            self.tops = rt[1:2]
        assert len(self.tops) == 1 or rt[0].next() == rt[1], "decimation 2 failed"

    def decimate_tops_three(self, tile):
        rt = self.tops

        neighbor_tile = tile.get_tile_in_direction([(rt[1] + 2) % 4])
        if not neighbor_tile is None and neighbor_tile.terrain_type() == TerrainType.RAMP:
            if neighbor_tile.terrain.rampinfo is None:
                neighbor_tile.terrain.rampinfo = Ramp(neighbor_tile)
        else:
            self.tops = rt[1:2]
            return

        nrt = neighbor_tile.terrain.rampinfo.tops
        assert len(nrt) not in [0, 4], "neighbor of 3ramp cannot have 0 or 4 tops!"

        if len(nrt) == 1 and isinstance(nrt[0], Direction):
            if nrt[0] == (rt[1] + 2) % 4:
                self.tops = rt[1:2]
            elif nrt[0] == rt[0]:
                self.tops = rt[0:2]
            else:
                self.tops = rt[1:3]
        elif len(nrt) == 1:
            if nrt[0][0] == rt[0]:
                self.tops = rt[0:2]
            elif nrt[0][1] == rt[2]:
                self.tops = rt[1:3]
            else:
                self.tops = rt[1:2]
        if len(nrt) == 2:
            if rt[1] == nrt[0]:
                self.tops = rt[0:2]
            else:
                self.tops = rt[1:3]
        if len(nrt) == 3:
            # case when two 3tops are next to each other
            if rt[1] == Direction.North or rt[1] == Direction.East:
                self.tops = rt[0:2]
            else:
                self.tops = rt[1:3]

    def make_connections(self, tile):
        rt = self.tops
        if len(rt) in [0, 4]:
            return
        assert len(rt) in [1, 2], "ramp tops were not removed properly!"

        if len(rt) == 1 and isinstance(rt[0], Direction):
            self.left_dir = rt[0].prev()
            self.right_dir = rt[0].next()
            self.find_connection(self.left_dir, tile, True)
            self.find_connection(self.right_dir, tile, False)
        elif len(rt) == 1:
            self.left_dir = rt[0][0]
            self.right_dir = rt[0][1]
            self.find_connection(self.left_dir, tile, True)
            self.find_connection(self.right_dir, tile, False)
        elif len(rt) == 2:
            self.left_dir = rt[0].prev()
            self.right_dir = rt[1].next()
            self.find_connection(self.left_dir, tile, True)
            self.find_connection(self.right_dir, tile, False)

    def find_connection(self, d, tile, is_left):
        if is_left:
            ramp_dir = d.next()
        else:
            ramp_dir = d.prev()

        neighbor_tile = tile.get_tile_in_direction([d])
        if neighbor_tile is None:
            self.connect(ConnectionType.END, is_left)
        elif neighbor_tile.terrain_type() == TerrainType.WALL:
            self.connect(ConnectionType.WALL, is_left)
        elif neighbor_tile.terrain_type() == TerrainType.RAMP:
            if self.connects_ramp(neighbor_tile, ramp_dir, is_left):
                self.connect(ConnectionType.Connect, is_left)
            else:
                self.connect(ConnectionType.END, is_left)
        else:
            self.connect(ConnectionType.END, is_left)

    def connects_ramp(self, tile, dir, is_left):
        if tile.terrain.rampinfo is None:
            tile.terrain.rampinfo = Ramp(tile)
        rt = tile.terrain.rampinfo.tops
        assert len(rt) in [0, 1, 2, 4], "ramp tops were not constructed properly!"
        if len(rt) in [0, 4]:
            return  False

        if len(rt) == 1 and isinstance(rt[0], Direction):
            # is_left irrelevant because symmetrical
            if rt[0] == dir:
                return True
            else:
                return False
        elif len(rt) == 1:
            if is_left:
                dir_ = rt[0][0]
            else:
                dir_ = rt[0][1]
            if dir == dir_:
                return True
            else:
                return False
        elif len(rt) == 2:
            # is_left should be irrelevant, because wrong 2ramp should be impossible
            if dir in rt:
                return True
            else:
                return False

    def connect(self, con_type, is_left):
        if is_left:
            self.left_connection = con_type
        else:
            self.right_connection = con_type

    def treat_ramp_as_wall_for_direction(self, d):
        # corner direction is always one to the left
        # so nw = n, ne = e, se = s, sw = w
        assert len(self.tops) in [0, 1, 2, 4], "ramp tops were not constructed properly, wrong length!"
        if len(self.tops) == 0:
            return False
        elif len(self.tops) == 4:
            return True
        elif len(self.tops) == 1 and isinstance(self.tops[0], Direction):
            if d == self.tops[0] or d == self.tops[0].next():
                return True
            else:
                return False
        elif len(self.tops) == 1:
            if d == self.tops[0][1]:
                return True
            else:
                return False
        elif len(self.tops) == 2:
            if self.tops[0].prev() == d:
                return False
            else:
                return True

