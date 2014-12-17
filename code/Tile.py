__author__ = 'JoeJoe'

import proto.Tile_pb2
from Terrain import Terrain, TerrainType
import bpy
import bmesh
import math
from mathutils import Matrix
from BmeshFactory import BmeshFactory
from Direction import Direction

class Tile:
    """A class that contains information on a specific Tile in the map

    Attributes:
        map_tiles       a class variable for access to neighboring Tiles
        proto_tile      the instance of the protobuf object the Tile is created from
        global_x        x coordinate in the map
        global_y        y coordinate in the map
        global_z        z coordinate in the map
        material        string identifying the terrain material
        terrain         Terrain object containing more detailed terrain information
        mesh_dict       dictionary for access to bmeshes of different terrain types
        ramp_tops       list containing the directions in which the ramp goes
    Attribute-like functions:
        liquid_type()   water or magma
        flow_size()     amount of liquid [1..7]
        base_mat()      base material of protobuf Tile
        terrain_type()  exposes the terrain_type attribute of the terrain attribute
    """
    map_tiles = []
    N = Direction.North
    E = Direction.East
    S = Direction.South
    W = Direction.West

    def __init__(self, proto_tile=None, block=None, mat_library=None):
        # obj_meshes = ['BOULDER', 'BROOK_BED', 'RAMP', 'SAPLING', 'SHRUB',
        #               'STAIR_DOWN', 'STAIR_UP', 'STAIR_UPDOWN', 'TREE']
        #
        # mesh_dict = {s: bmesh.new() for s in obj_meshes}
        # for k in mesh_dict:
        #     mesh_dict[k].from_object(bpy.data.objects[k], bpy.context.scene)

        if not (proto_tile is None or block is None or mat_library is None):
            self.proto_tile = proto_tile
            self.global_x = block.x * 16 + proto_tile.x
            self.global_y = block.y * 16 + proto_tile.y
            self.global_z = block.z
            typeindex = getattr(self.proto_tile, 'material_type', None)
            matindex = getattr(self.proto_tile, 'material_index', None)
            if typeindex is None or matindex is None:
                self.material = proto.Tile_pb2.Tile.TileMaterialType.Name(self.proto_tile.tile_material)
            else:
                try:
                    self.material = mat_library[typeindex][matindex]
                except IndexError:
                    self.material = 'unknown'
            self.terrain = Terrain(proto_tile.type)

    def liquid_type(self):
        return proto.Tile_pb2.Tile.LiquidType.Name(self.proto_tile.liquid_type)

    def flow_size(self):
        return self.proto_tile.flow_size

    def base_mat(self):
        return proto.Tile_pb2.Tile.TileMaterialType.Name(self.proto_tile.tile_material)

    def terrain_type(self):
        return self.terrain.terrain_type

    def terrainful(self):
        return self.terrain.terrainful

    def add_ceiling(self):
        self.terrain.add_ceiling()

    def build_bmesh(self):
        return BmeshFactory.build(self)

    def get_tile_in_direction(self, directions, z=0):
        x = self.global_x
        y = self.global_y
        for d in directions:
            if d == self.N:
                y -= 1
            elif d == self.E:
                x += 1
            elif d == self.S:
                y += 1
            elif d == self.W:
                x -= 1
        try:
            return self.map_tiles[x][y][self.global_z + z]
        except IndexError:
            return None

    def build_ramp_bmesh(self):
        rtn = bmesh.new()
        center = (1, -1, 0)
        # determine number and direction of ramp tops
        if not hasattr(self, 'ramp_tops'):
            self.find_ramp_tops()

        rt = self.ramp_tops

        if len(rt) == 4:
            rtn.from_object(bpy.data.objects['RAMP_4'], bpy.context.scene)
            return rtn

        elif len(rt) == 0:
            rtn.from_object(bpy.data.objects['RAMP_0'], bpy.context.scene)
            return rtn

        elif len(rt) == 1:
            if type(rt[0]) is Tile.Direction:
                objectid = "RAMP_1"
                rtn.from_object(bpy.data.objects[objectid], bpy.context.scene)
                objectid += "_R"
                try:
                    if self.get_tile_in_direction([(rt[0]+2) % 4]).terrain_type() == TerrainType.WALL:
                        rtn.from_object(bpy.data.objects['RAMP_1_FWALL'], bpy.context.scene)

                    if self.get_tile_in_direction([self.Direction(rt[0]).next()]).terrain_type() == TerrainType.WALL:
                        objectid += "WALL"
                    elif self.get_tile_in_direction([self.Direction(rt[0]).next()]).terrain_type() == TerrainType.RAMP:
                        if self.ramp_connects_right():
                            objectid += "RAMP"
                        else:
                            objectid += "END"
                    else:
                        objectid += "END"
                except AttributeError:
                    objectid += "END"

                rtn.from_object(bpy.data.objects[objectid], bpy.context.scene)

                objectid = "RAMP_1_L"
                try:
                    if self.get_tile_in_direction([self.Direction(rt[0]).prev()]).terrain_type() == TerrainType.WALL:
                        objectid += "WALL"
                    elif self.get_tile_in_direction([self.Direction(rt[0]).prev()]).terrain_type() == TerrainType.RAMP:
                        if self.ramp_connects_left():
                            objectid += "RAMP"
                        else:
                            objectid += "END"
                    else:
                        objectid += "END"
                except AttributeError:
                    objectid += "END"
                rtn.from_object(bpy.data.objects[objectid], bpy.context.scene)

                bmesh.ops.rotate(rtn, verts=rtn.verts, cent=center, matrix=self.rot_dict[rt[0]])
            else:
                objectid = "RAMP_CORNER"
                rtn.from_object(bpy.data.objects[objectid], bpy.context.scene)

                if self.ramp_connects_right():
                    objectid += "_RRAMP"
                else:
                    objectid += "_REND"
                rtn.from_object(bpy.data.objects[objectid], bpy.context.scene)
                objectid = "RAMP_CORNER"
                if self.ramp_connects_left():
                    objectid += "_LRAMP"
                else:
                    objectid += "_LEND"
                rtn.from_object(bpy.data.objects[objectid], bpy.context.scene)

                bmesh.ops.rotate(rtn, verts=rtn.verts, cent=center, matrix=self.rot_dict[rt[0][1]])

        elif len(rt) == 2:
                objectid = "RAMP_2"
                rtn.from_object(bpy.data.objects[objectid], bpy.context.scene)
                objectid += "_R"
                dleft = self.Direction(rt[0]).prev()
                dright = self.Direction(rt[1]).next()

                neighbor = self.get_tile_in_direction([dright])
                if not neighbor is None and neighbor.terrain_type() == TerrainType.WALL:
                    objectid += "WALL"
                elif not neighbor is None and neighbor.terrain_type() == TerrainType.RAMP:
                    if self.ramp_connects_right():
                        objectid += "RAMP"
                    else:
                        objectid += "END"
                else:
                    objectid += "END"
                rtn.from_object(bpy.data.objects[objectid], bpy.context.scene)

                objectid = "RAMP_2_L"
                neighbor = self.get_tile_in_direction([dleft])
                if not neighbor is None and neighbor.terrain_type() == TerrainType.WALL:
                    objectid += "WALL"
                elif not neighbor is None and neighbor.terrain_type() == TerrainType.RAMP:
                    if self.ramp_connects_left():
                        objectid += "RAMP"
                    else:
                        objectid += "END"
                else:
                    objectid += "END"

                rtn.from_object(bpy.data.objects[objectid], bpy.context.scene)

                bmesh.ops.rotate(rtn, verts=rtn.verts, cent=center, matrix=self.rot_dict[rt[1]])

        return rtn

    def ramp_connects_left(self):
        rt = self.ramp_tops
        if len(rt) == 1 and type(rt[0]) is Tile.Direction:
            neighbortile = self.get_tile_in_direction([self.Direction(rt[0]).prev()])
            if not hasattr(neighbortile, "ramp_tops"):
                neighbortile.find_ramp_tops()
            nrt = neighbortile.ramp_tops
            topdir = rt[0]
        elif len(rt) == 1:
            neighbortile = self.get_tile_in_direction([rt[0][0]])
            if not hasattr(neighbortile, "ramp_tops"):
                neighbortile.find_ramp_tops()
            nrt = neighbortile.ramp_tops
            topdir = rt[0][1]
        elif len(rt) == 2:
            neighbortile = self.get_tile_in_direction([self.Direction(rt[1]).prev()])
            if not hasattr(neighbortile, "ramp_tops"):
                neighbortile.find_ramp_tops()
            nrt = neighbortile.ramp_tops
            topdir = rt[0]

        assert not len(nrt) in [0, 3, 4], "number of ramptops not possible!"
        if len(nrt) == 2:
            if topdir == nrt[1]:
                return True
            else:
                return False
        if len(nrt) == 1:
            if type(nrt[0]) is Tile.Direction:
                if topdir == nrt[0]:
                    return True
                else:
                    return False
            else:
                if topdir == nrt[0][0]:
                    return True
                else:
                    return False

    def ramp_connects_right(self):
        rt = self.ramp_tops
        if len(rt) == 1 and isinstance(rt[0], Tile.Direction):
            neighbortile = self.get_tile_in_direction([self.Direction(rt[0]).next()])
            if not hasattr(neighbortile, "ramp_tops"):
                neighbortile.find_ramp_tops()
            nrt = neighbortile.ramp_tops
            topdir = rt[0]
        elif len(rt) == 1:
            neighbortile = self.get_tile_in_direction([rt[0][1]])
            if not hasattr(neighbortile, "ramp_tops"):
                neighbortile.find_ramp_tops()
            nrt = neighbortile.ramp_tops
            topdir = rt[0][0]
        elif len(rt) == 2:
            assert rt[0].next() == rt[1], rt
            neighbortile = self.get_tile_in_direction([self.Direction(rt[1]).next()])
            if not hasattr(neighbortile, "ramp_tops"):
                neighbortile.find_ramp_tops()
            nrt = neighbortile.ramp_tops
            topdir = rt[1]

        assert not len(neighbortile.ramp_tops) in [0, 3, 4], "number of neighbor ramp tops impossible"

        if len(nrt) == 2:
            if topdir == nrt[0]:
                return True
            else:
                return False
        if len(nrt) == 1:
            if type(nrt[0]) is Tile.Direction:
                if topdir == nrt[0]:
                    return True
                else:
                    return False
            else:
                if topdir == nrt[0][1]:
                    return True
                else:
                    return False

    def find_ramp_tops(self):
        self.add_naive_tops()

        if len(self.ramp_tops) == 1 or len(self.ramp_tops) == 4:
            return

        if len(self.ramp_tops) == 0:
            self.find_diagonal_tops()
            return

        if len(self.ramp_tops) == 2:
            self.decimate_tops_two()
            return

        if len(self.ramp_tops) == 3:
            self.decimate_tops_three()
            assert len(self.ramp_tops) != 3, "not decimated (3) properly"
            return

    def find_diagonal_tops(self):
        diags = [self.W, self.N]
        for d in self.Direction:
            diags[1] = d
            if self.is_rampable(diags):
                self.ramp_tops = [diags[:]]
            diags[0] = d

    def decimate_tops_two(self):
        rt = self.ramp_tops
        if (rt[0] + 2) % 4 == rt[1]:
            self.ramp_tops = rt[1:2]
        assert len(self.ramp_tops) == 1 or rt[0].next() == rt[1], "decimation 2 failed"

    def decimate_tops_three(self):
        rt = self.ramp_tops

        neighbor_tile = self.get_tile_in_direction([(rt[1] + 2) % 4])
        if not neighbor_tile is None and neighbor_tile.terrain_type() == TerrainType.RAMP:
            if not hasattr(neighbor_tile, "ramp_tops"):
                neighbor_tile.find_ramp_tops()
        else:
            self.ramp_tops = rt[1:2]
            return

        nrt = neighbor_tile.ramp_tops
        assert not len(nrt) in [0, 4], "neighbor of 3ramp cannot have 0 or 4 tops!"

        if len(nrt) == 1 and isinstance(nrt[0], self.Direction):
            if nrt[0] == (rt[1] + 2) % 4:
                self.ramp_tops = rt[1:2]
            elif nrt[0] == rt[0]:
                self.ramp_tops = rt[0:2]
            else:
                self.ramp_tops = rt[1:3]

        if len(nrt) == 1 and type(nrt[0]) is list:
            if nrt[0][0] == rt[0]:
                self.ramp_tops = rt[0:2]
            elif nrt[0][1] == rt[2]:
                self.ramp_tops = rt[1:3]
            else:
                self.ramp_tops = rt[1:2]

        if len(nrt) == 2:
            if rt[1] == nrt[0]:
                self.ramp_tops = rt[0:2]
            else:
                self.ramp_tops = rt[1:3]

        if len(nrt) == 3:
            # case when two 3tops are next to each other
            if rt[1] == self.N or rt[1] == self.E:
                self.ramp_tops = rt[0:2]
            else:
                self.ramp_tops = rt[1:3]

    def add_naive_tops(self):
        self.ramp_tops = []
        for d in self.Direction:
            if self.is_rampable([d]):
                self.ramp_tops.append(d)

        rt = self.ramp_tops
        if rt == [0, 1, 3]:
            self.ramp_tops = [self.W, self.N, self.E]
        elif rt == [0, 2, 3]:
            self.ramp_tops = [self.S, self.W, self.N]
        elif rt == [0, 3]:
            self.ramp_tops = [self.W, self.N]

    def is_rampable(self, d):
        neighbor_t = self.get_tile_in_direction(d)
        neighbor_t_a = self.get_tile_in_direction(d, 1)
        if neighbor_t is None or neighbor_t_a is None:
            return False
        else:
            return neighbor_t.terrain_type() == TerrainType.WALL and neighbor_t_a.terrain_type() != TerrainType.WALL

    def add_ceiling_bmesh(self, bm):
        # consider doing complex ceiling for all tiles, because walls can protrude into them
        complexceiling = False
        if self.terrain.has_ceiling:
            complexceiling = True
            tile_above = self.get_tile_in_direction([], 1)
            if tile_above is None and self.terrain_type().name != 'WALL':
                bm.from_object(bpy.data.objects['CEILING_NONE'], bpy.context.scene)
                complexceiling = False
        if complexceiling and self.terrain_type().name != 'WALL':
            bm.from_object(bpy.data.objects['CEILING_CENTER'], bpy.context.scene)

        center = (1, -1, 0)
        corner_directions = [[self.W], [self.W, self.N], [self.N]]
        for d in self.Direction:
            corner_directions[1][1] = d
            corner_directions[2][0] = d
            l = len(bm.verts)
            if complexceiling:
                ceiling_string = self.build_ceiling_id(corner_directions)
                if len(ceiling_string) > 0:
                    bm.from_object(bpy.data.objects[ceiling_string], bpy.context.scene)
                    bmesh.ops.rotate(bm, verts=bm.verts[l:len(bm.verts)], cent=center, matrix=self.rot_dict[d])
            corner_directions[0][0] = d
            corner_directions[1][0] = d

    def build_ceiling_id(self, directions):
        if self.terrain_type().name == 'WALL':
            return self.build_wall_ceiling_id(directions)
        rtn = 'CEILING_'
        for e in directions:
            neighbor_tile_a = self.get_tile_in_direction(e, 1)
            if neighbor_tile_a is None or neighbor_tile_a.terrain.has_floor:
                rtn += 'FL'
            else:
                rtn += 'EM'
        return rtn

    def build_wall_ceiling_id(self, directions):
        rtn = 'CEILING_'
        for e in directions:
            neighbor_tile_a = self.get_tile_in_direction(e, 1)
            neighbor_tile = self.get_tile_in_direction(e)
            if neighbor_tile is None:
                return ''
            elif neighbor_tile.terrain_type().name == 'WALL':
                rtn += 'WA'
            elif neighbor_tile_a is None or neighbor_tile_a.terrain.has_floor:
                rtn += 'FL'
            else:
                rtn += 'EM'
        return rtn
