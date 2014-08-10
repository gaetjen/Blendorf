__author__ = 'JoeJoe'

import proto.Tile_pb2
from Terrain import Terrain, TerrainType
import bpy
import bmesh
import math
from mathutils import Matrix

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
    """
    map_tiles = []
    mesh_dict = []

    def __init__(self, proto_tile=None, block=None, mat_library=None, map_tiles=[]):
        if map_tiles and not self.map_tiles:
            self.map_tiles = map_tiles
            obj_meshes = ['BOULDER', 'BROOK_BED', 'RAMP', 'SAPLING', 'SHRUB',
                          'STAIR_DOWN', 'STAIR_UP', 'STAIR_UPDOWN', 'TREE']

            mesh_dict = {s: bmesh.new() for s in obj_meshes}
            for k in mesh_dict:
                mesh_dict[k].from_object(bpy.data.objects[k], bpy.context.scene)

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

    def add_ceiling(self):
        self.terrain.add_ceiling()

    def add_floor(self):
        self.terrain.add_floor()

    def build_bmesh(self):
        if rtn = self.build_wall_bmesh()
            rtn = self.build_wall_bmesh()
        elif self.terrain.has_floor:
            rtn = self.build_floor_bmesh()
            # add more stuff, join, delete doubles

    def build_wall_bmesh(self):



    def build_floor_bmesh(self):
        no_extra_floors = [TerrainType.RAMP, TerrainType.STAIR_DOWN, TerrainType.STAIR_UP,
                           TerrainType.STAIR_UPDOWN, TerrainType.FORTIFICATION]
        t_type = self.terrain.terrain_type
        if t_type ==  or t_type == TerrainType.