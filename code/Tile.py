__author__ = 'JoeJoe'

import proto.Tile_pb2
from Terrain import Terrain, TerrainType
import bpy
import bmesh
import math
from mathutils import Matrix
from enum import Enum

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
    Attribute-like functions:
        liquid_type()   water or magma
        flow_size()     amount of liquid [1..7]
        base_mat()      base material of protobuf Tile
        terrain_type()  exposes the terrain_type attribute of the terrain attribute
    """
    map_tiles = []
    # mesh_dict = []

    class Direction(Enum):
        North = 0
        East = 1
        South = 2
        West = 3

    N = Direction.North
    E = Direction.East
    S = Direction.South
    W = Direction.West
    rot_dict = {N: Matrix.Rotation(0, 3, 'Z'), E: Matrix.Rotation(-math.pi/2, 3, 'Z'),
                S: Matrix.Rotation(math.pi, 3, 'Z'), W: Matrix.Rotation(math.pi / 2, 3, 'Z')}

    no_extra_floors = [TerrainType.RAMP, TerrainType.STAIR_DOWN, TerrainType.STAIR_UP,
                       TerrainType.STAIR_UPDOWN, TerrainType.FORTIFICATION]

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

    def add_ceiling(self):
        self.terrain.add_ceiling()

    def add_floor(self):
        self.terrain.add_floor()

    def build_bmesh(self):
        rtn = bmesh.new()
        if self.terrain_type() == TerrainType.WALL or self.terrain_type() == TerrainType.FORTIFICATION:
            return self.build_wall_bmesh()
        elif self.terrain.has_floor:
            rtn = self.build_floor_bmesh()
        if self.terrain_type() != TerrainType.FLOOR:
            rtn.from_object(bpy.data.objects[self.terrain_type().name], bpy.context.scene)
        bmesh.ops.remove_doubles(rtn, verts=rtn.verts, dist=0.0001)
        bmesh.ops.dissolve_limit(rtn, angle_limit=math.pi/90, use_dissolve_boundaries=False,
                                 verts=rtn.verts, edges=rtn.edges)
        return rtn

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

    def build_object_id(self, prefix, directions):
        rtn = prefix
        for e in directions:
            neighbor_tile = self.get_tile_in_direction(e)
            if neighbor_tile is None:
                if self.terrain_type().name == 'WALL':
                    return ''
                else:
                    rtn += 'EM'
            elif self.terrain_type().name == 'WALL' and neighbor_tile.terrain_type().name == 'WALL':
                rtn += 'WA'
            else:
                if neighbor_tile.terrain.has_floor:
                    rtn += 'FL'
                else:
                    rtn += 'EM'
        return rtn

    def build_wall_bmesh(self):

        rtn = bmesh.new()

        self.add_directional_mesh_parts('WALL_', rtn)

        bmesh.ops.remove_doubles(rtn, verts=rtn.verts, dist=0.0001)
        bmesh.ops.dissolve_limit(rtn, angle_limit=math.pi/90, use_dissolve_boundaries=False,
                                 verts=rtn.verts, edges=rtn.edges)

        return rtn

    def build_floor_bmesh(self):
        rtn = bmesh.new()
        if self.terrain.terrain_type in self.no_extra_floors:
            return rtn

        rtn.from_object(bpy.data.objects['FLOOR_CENTER'], bpy.context.scene)

        self.add_directional_mesh_parts('FLOOR_', rtn)
        bmesh.ops.remove_doubles(rtn, verts=rtn.verts, dist=0.0001)
        bmesh.ops.dissolve_limit(rtn, angle_limit=math.pi/90, use_dissolve_boundaries=False,
                                 verts=rtn.verts, edges=rtn.edges)

        return rtn

    def add_directional_mesh_parts(self, prefix, bm):
        center = (1, -1, 0)
        corner_directions = [[self.W], [self.W, self.N], [self.N]]
        for d in self.Direction:
            corner_directions[1][1] = d
            corner_directions[2][0] = d
            object_string = prefix
            object_string = self.build_object_id(object_string, corner_directions)
            if len(object_string) > 0:
                l = len(bm.verts)
                bm.from_object(bpy.data.objects[object_string], bpy.context.scene)
                bmesh.ops.rotate(bm, verts=bm.verts[l:len(bm.verts)], cent=center, matrix=self.rot_dict[d])
            corner_directions[0][0] = d
            corner_directions[1][0] = d