__author__ = 'Jo'

from enum import IntEnum
from Direction import Direction

class RampType (IntEnum):
    RAMP_0 = 0
    RAMP_1 = 1
    RAMP_2 = 2
    RAMP_CORNER = 3
    RAMP_4 = 4


class Ramp:
    """contains more information about how the ramp is oriented and neighbors"""

    def __init__(self, tile):
        self.tops = []
        self.ramptype = RampType.RAMP_0
        self.rotate_direction = None
        self.find_tops(tile)
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

        nrt = neighbor_tile.tops
        assert len(nrt) not in [0, 4], "neighbor of 3ramp cannot have 0 or 4 tops!"

        if len(nrt) == 1 and isinstance(nrt[0], Direction):
            if nrt[0] == (rt[1] + 2) % 4:
                self.tops = rt[1:2]
            elif nrt[0] == rt[0]:
                self.tops = rt[0:2]
            else:
                self.tops = rt[1:3]

        if len(nrt) == 1 and type(nrt[0]) is list:
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
    ######################################################
    # def build_ramp_bmesh(self):
    #     rtn = bmesh.new()
    #     center = (1, -1, 0)
    #     # determine number and direction of ramp tops
    #     if not hasattr(self, 'ramp_tops'):
    #         self.find_ramp_tops()
    #
    #     rt = self.ramp_tops
    #
    #     if len(rt) == 4:
    #         rtn.from_object(bpy.data.objects['RAMP_4'], bpy.context.scene)
    #         return rtn
    #
    #     elif len(rt) == 0:
    #         rtn.from_object(bpy.data.objects['RAMP_0'], bpy.context.scene)
    #         return rtn
    #
    #     elif len(rt) == 1:
    #         if type(rt[0]) is Tile.Direction:
    #             objectid = "RAMP_1"
    #             rtn.from_object(bpy.data.objects[objectid], bpy.context.scene)
    #             objectid += "_R"
    #             try:
    #                 if self.get_tile_in_direction([(rt[0]+2) % 4]).terrain_type() == TerrainType.WALL:
    #                     rtn.from_object(bpy.data.objects['RAMP_1_FWALL'], bpy.context.scene)
    #
    #                 if self.get_tile_in_direction([self.Direction(rt[0]).next()]).terrain_type() == TerrainType.WALL:
    #                     objectid += "WALL"
    #                 elif self.get_tile_in_direction([self.Direction(rt[0]).next()]).terrain_type() == TerrainType.RAMP:
    #                     if self.ramp_connects_right():
    #                         objectid += "RAMP"
    #                     else:
    #                         objectid += "END"
    #                 else:
    #                     objectid += "END"
    #             except AttributeError:
    #                 objectid += "END"
    #
    #             rtn.from_object(bpy.data.objects[objectid], bpy.context.scene)
    #
    #             objectid = "RAMP_1_L"
    #             try:
    #                 if self.get_tile_in_direction([self.Direction(rt[0]).prev()]).terrain_type() == TerrainType.WALL:
    #                     objectid += "WALL"
    #                 elif self.get_tile_in_direction([self.Direction(rt[0]).prev()]).terrain_type() == TerrainType.RAMP:
    #                     if self.ramp_connects_left():
    #                         objectid += "RAMP"
    #                     else:
    #                         objectid += "END"
    #                 else:
    #                     objectid += "END"
    #             except AttributeError:
    #                 objectid += "END"
    #             rtn.from_object(bpy.data.objects[objectid], bpy.context.scene)
    #
    #             bmesh.ops.rotate(rtn, verts=rtn.verts, cent=center, matrix=self.rot_dict[rt[0]])
    #         else:
    #             objectid = "RAMP_CORNER"
    #             rtn.from_object(bpy.data.objects[objectid], bpy.context.scene)
    #
    #             if self.ramp_connects_right():
    #                 objectid += "_RRAMP"
    #             else:
    #                 objectid += "_REND"
    #             rtn.from_object(bpy.data.objects[objectid], bpy.context.scene)
    #             objectid = "RAMP_CORNER"
    #             if self.ramp_connects_left():
    #                 objectid += "_LRAMP"
    #             else:
    #                 objectid += "_LEND"
    #             rtn.from_object(bpy.data.objects[objectid], bpy.context.scene)
    #
    #             bmesh.ops.rotate(rtn, verts=rtn.verts, cent=center, matrix=self.rot_dict[rt[0][1]])
    #
    #     elif len(rt) == 2:
    #             objectid = "RAMP_2"
    #             rtn.from_object(bpy.data.objects[objectid], bpy.context.scene)
    #             objectid += "_R"
    #             dleft = self.Direction(rt[0]).prev()
    #             dright = self.Direction(rt[1]).next()
    #
    #             neighbor = self.get_tile_in_direction([dright])
    #             if not neighbor is None and neighbor.terrain_type() == TerrainType.WALL:
    #                 objectid += "WALL"
    #             elif not neighbor is None and neighbor.terrain_type() == TerrainType.RAMP:
    #                 if self.ramp_connects_right():
    #                     objectid += "RAMP"
    #                 else:
    #                     objectid += "END"
    #             else:
    #                 objectid += "END"
    #             rtn.from_object(bpy.data.objects[objectid], bpy.context.scene)
    #
    #             objectid = "RAMP_2_L"
    #             neighbor = self.get_tile_in_direction([dleft])
    #             if not neighbor is None and neighbor.terrain_type() == TerrainType.WALL:
    #                 objectid += "WALL"
    #             elif not neighbor is None and neighbor.terrain_type() == TerrainType.RAMP:
    #                 if self.ramp_connects_left():
    #                     objectid += "RAMP"
    #                 else:
    #                     objectid += "END"
    #             else:
    #                 objectid += "END"
    #
    #             rtn.from_object(bpy.data.objects[objectid], bpy.context.scene)
    #
    #             bmesh.ops.rotate(rtn, verts=rtn.verts, cent=center, matrix=self.rot_dict[rt[1]])
    #
    #     return rtn
    #
    # def ramp_connects_left(self):
    #     rt = self.ramp_tops
    #     if len(rt) == 1 and type(rt[0]) is Tile.Direction:
    #         neighbortile = self.get_tile_in_direction([self.Direction(rt[0]).prev()])
    #         if not hasattr(neighbortile, "ramp_tops"):
    #             neighbortile.find_ramp_tops()
    #         nrt = neighbortile.ramp_tops
    #         topdir = rt[0]
    #     elif len(rt) == 1:
    #         neighbortile = self.get_tile_in_direction([rt[0][0]])
    #         if not hasattr(neighbortile, "ramp_tops"):
    #             neighbortile.find_ramp_tops()
    #         nrt = neighbortile.ramp_tops
    #         topdir = rt[0][1]
    #     elif len(rt) == 2:
    #         neighbortile = self.get_tile_in_direction([self.Direction(rt[1]).prev()])
    #         if not hasattr(neighbortile, "ramp_tops"):
    #             neighbortile.find_ramp_tops()
    #         nrt = neighbortile.ramp_tops
    #         topdir = rt[0]
    #
    #     assert not len(nrt) in [0, 3, 4], "number of ramptops not possible!"
    #     if len(nrt) == 2:
    #         if topdir == nrt[1]:
    #             return True
    #         else:
    #             return False
    #     if len(nrt) == 1:
    #         if type(nrt[0]) is Tile.Direction:
    #             if topdir == nrt[0]:
    #                 return True
    #             else:
    #                 return False
    #         else:
    #             if topdir == nrt[0][0]:
    #                 return True
    #             else:
    #                 return False
    #
    # def ramp_connects_right(self):
    #     rt = self.ramp_tops
    #     if len(rt) == 1 and isinstance(rt[0], Tile.Direction):
    #         neighbortile = self.get_tile_in_direction([self.Direction(rt[0]).next()])
    #         if not hasattr(neighbortile, "ramp_tops"):
    #             neighbortile.find_ramp_tops()
    #         nrt = neighbortile.ramp_tops
    #         topdir = rt[0]
    #     elif len(rt) == 1:
    #         neighbortile = self.get_tile_in_direction([rt[0][1]])
    #         if not hasattr(neighbortile, "ramp_tops"):
    #             neighbortile.find_ramp_tops()
    #         nrt = neighbortile.ramp_tops
    #         topdir = rt[0][0]
    #     elif len(rt) == 2:
    #         assert rt[0].next() == rt[1], rt
    #         neighbortile = self.get_tile_in_direction([self.Direction(rt[1]).next()])
    #         if not hasattr(neighbortile, "ramp_tops"):
    #             neighbortile.find_ramp_tops()
    #         nrt = neighbortile.ramp_tops
    #         topdir = rt[1]
    #
    #     assert not len(neighbortile.ramp_tops) in [0, 3, 4], "number of neighbor ramp tops impossible"
    #
    #     if len(nrt) == 2:
    #         if topdir == nrt[0]:
    #             return True
    #         else:
    #             return False
    #     if len(nrt) == 1:
    #         if type(nrt[0]) is Tile.Direction:
    #             if topdir == nrt[0]:
    #                 return True
    #             else:
    #                 return False
    #         else:
    #             if topdir == nrt[0][1]:
    #                 return True
    #             else:
    #                 return False




