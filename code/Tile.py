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

    def is_rampable(self, d):
        neighbor_t = self.get_tile_in_direction(d)
        neighbor_t_a = self.get_tile_in_direction(d, 1)
        if neighbor_t is None or neighbor_t_a is None:
            return False
        else:
            return neighbor_t.terrain_type() == TerrainType.WALL and neighbor_t_a.terrain_type() != TerrainType.WALL