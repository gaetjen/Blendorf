__author__ = 'JoeJoe'

import proto.Tile_pb2
from Terrain import Terrain

class Tile:

    def __init__(self, proto_tile, block, mat_library):
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