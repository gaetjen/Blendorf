__author__ = 'JoeJoe'

import proto.Tile_pb2
from Terrain import Terrain, TerrainType
import bpy
import bmesh
import math
from mathutils import Matrix
from enum import IntEnum

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

    class Direction(IntEnum):
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
            rtn = self.build_wall_bmesh()
        elif self.terrain_type() == TerrainType.RAMP:
            rtn = self.build_ramp_bmesh()
        elif self.terrain.has_floor:
            rtn = self.build_floor_bmesh()
        elif self.terrain_type() == TerrainType.BROOK_BED:
            rtn = self.build_brook_bmesh()
        rtn.from_object(bpy.data.objects[self.terrain_type().name], bpy.context.scene)
        self.add_ceiling_bmesh(rtn)
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
            elif self.terrain_type().name == 'WALL' and \
                    (neighbor_tile.terrain_type().name == 'WALL' or neighbor_tile.terrain_type() == TerrainType.RAMP):
                rtn += 'WA'
            elif self.terrain_type().name == 'WALL' and neighbor_tile.terrain_type() == TerrainType.BROOK_BED:
                return ''
            else:
                if neighbor_tile.terrain.has_floor or (neighbor_tile.terrain_type() == TerrainType.RAMP_TOP and
                                           self.get_tile_in_direction([], -1).terrain_type() == TerrainType.WALL) or \
                                           neighbor_tile.terrain_type() == TerrainType.BROOK_TOP:
                    rtn += 'FL'
                else:
                    rtn += 'EM'
        return rtn

    def build_wall_bmesh(self):
        rtn = bmesh.new()
        self.add_directional_mesh_parts('WALL_', rtn)
        return rtn

    def build_floor_bmesh(self):
        rtn = bmesh.new()
        if self.terrain.terrain_type in self.no_extra_floors:
            return rtn

        rtn.from_object(bpy.data.objects['FLOOR_CENTER'], bpy.context.scene)

        self.add_directional_mesh_parts('FLOOR_', rtn)

        return rtn

    def build_ramp_bmesh(self):
        rtn = bmesh.new()
        center = (1, -1, 0)
        # determine number and direction of ramp tops
        ramp_tops = []
        for d in self.Direction:
            if self.is_rampable([d]):
                ramp_tops.append(d)

        if len(ramp_tops) == 4:
            rtn.from_object(bpy.data.objects['RAMP_4'], bpy.context.scene)

        elif len(ramp_tops) == 1:
            rtn.from_object(bpy.data.objects['RAMP_1'], bpy.context.scene)
            bmesh.ops.rotate(rtn, verts=rtn.verts, cent=center, matrix=self.rot_dict[ramp_tops[0]])

        elif len(ramp_tops) == 3:
            soloramp = False
            if ramp_tops == [0, 1, 3]:
                ramp_tops = [3, 0, 1]
            if ramp_tops == [0, 2, 3]:
                ramp_tops = [2, 3, 0]
            neighbor_tile = self.get_tile_in_direction([(ramp_tops[1] + 2) % 4])
            neighbor_tile_tops = []
            for d in self.Direction:
                if neighbor_tile.is_rampable([d]):
                    neighbor_tile_tops.append(d)
            if len(neighbor_tile_tops) == 1 and neighbor_tile_tops[0] == (ramp_tops[1] + 2) % 4:
                    soloramp = True
            for d in self.Direction:
                if d not in ramp_tops:
                    if self.get_tile_in_direction([d]).terrain_type() != TerrainType.RAMP:
                        soloramp = True
            if soloramp:
                rtn.from_object(bpy.data.objects['RAMP_1'], bpy.context.scene)
                bmesh.ops.rotate(rtn, verts=rtn.verts, cent=center, matrix=self.rot_dict[ramp_tops[1]])
                ramp_tops = ramp_tops[1:2]
            else:
                rtn.from_object(bpy.data.objects['RAMP_2'], bpy.context.scene)
                if len(neighbor_tile_tops) == 0:
                    bmesh.ops.rotate(rtn, verts=rtn.verts, cent=center, matrix=self.rot_dict[ramp_tops[2]])
                    ramp_tops = ramp_tops[1:3]
                elif len(neighbor_tile_tops) == 1 or \
                        (len(neighbor_tile_tops) == 2 and (neighbor_tile_tops[0] + 1) % 4 == neighbor_tile_tops[1]):
                    if (ramp_tops[1] - 1) % 4 in neighbor_tile_tops:
                        bmesh.ops.rotate(rtn, verts=rtn.verts, cent=center, matrix=self.rot_dict[ramp_tops[1]])
                        ramp_tops = ramp_tops[0:2]
                    else:
                        bmesh.ops.rotate(rtn, verts=rtn.verts, cent=center, matrix=self.rot_dict[ramp_tops[2]])
                        ramp_tops = ramp_tops[1:3]
                else:
                    if ramp_tops[1] == self.N or ramp_tops[1] == self.E:
                        bmesh.ops.rotate(rtn, verts=rtn.verts, cent=center, matrix=self.rot_dict[ramp_tops[1]])
                        ramp_tops = ramp_tops[0:2]
                    else:
                        bmesh.ops.rotate(rtn, verts=rtn.verts, cent=center, matrix=self.rot_dict[ramp_tops[2]])
                        ramp_tops = ramp_tops[1:3]

        elif len(ramp_tops) == 0:
            diagramp = False
            diags = [self.W, self.N]
            for d in self.Direction:
                diags[1] = d
                if self.is_rampable(diags):
                    diagramp = True
                    rotate_dir = d
                diags[0] = d
            if diagramp:
                rtn.from_object(bpy.data.objects['RAMP_CORNER'], bpy.context.scene)
                bmesh.ops.rotate(rtn, verts=rtn.verts, cent=center, matrix=self.rot_dict[rotate_dir])
            else:
                rtn.from_object(bpy.data.objects['RAMP_0'], bpy.context.scene)

        else:
            if ramp_tops == [0, 3]:
                ramp_tops = [3, 0]
            if (ramp_tops[0] + 2) % 4 == ramp_tops[1]:
                rtn.from_object(bpy.data.objects['RAMP_1'], bpy.context.scene)
                bmesh.ops.rotate(rtn, verts=rtn.verts, cent=center, matrix=self.rot_dict[ramp_tops[1]])
            else:
                rtn.from_object(bpy.data.objects['RAMP_2'], bpy.context.scene)
                bmesh.ops.rotate(rtn, verts=rtn.verts, cent=center, matrix=self.rot_dict[ramp_tops[1]])
        # TODO:determine open sides and extra walls

        return rtn

    def build_brook_bmesh(self):
        rtn = bmesh.new()
        rtn.from_object(bpy.data.objects['BROOK_CENTER'], bpy.context.scene)
        self.add_brook_directions(rtn)
        self.add_brook_corners(rtn)
        return rtn

    def add_brook_directions(self, bm):
        identificator = 'BROOK_'
        for d in self.Direction:
            identificator += d.name + '_'
            tile_dir = self.get_tile_in_direction([d])
            if tile_dir is None or tile_dir.terrain_type() == TerrainType.BROOK_BED:
                identificator += 'B'
            else:
                identificator += 'F'
            bm.from_object(bpy.data.objects[identificator], bpy.context.scene)
            identificator = 'BROOK_'

    def add_brook_corners(self, bm):
        identificator = 'BROOK_'
        directions = [self.W, self.N]
        for d in self.Direction:
            directions[1] = d
            identificator += d.name + '_'
            for e in directions:
                tile_dir = self.get_tile_in_direction([e])
                if tile_dir is None or tile_dir.terrain_type() == TerrainType.BROOK_BED:
                    identificator += 'B'
                else:
                    identificator += 'F'

            bm.from_object(bpy.data.objects[identificator], bpy.context.scene)
            identificator = 'BROOK_'
            directions[0] = d

    def is_rampable(self, d):
        neighbor_t = self.get_tile_in_direction(d)
        neighbor_t_a = self.get_tile_in_direction(d, 1)
        if neighbor_t is None or neighbor_t_a is None:
            return False
        else:
            return neighbor_t.terrain_type() == TerrainType.WALL and neighbor_t_a.terrain_type() != TerrainType.WALL

    def add_directional_mesh_parts(self, prefix, bm):

        center = (1, -1, 0)
        corner_directions = [[self.W], [self.W, self.N], [self.N]]
        for d in self.Direction:
            corner_directions[1][1] = d
            corner_directions[2][0] = d
            l = len(bm.verts)

            object_string = self.build_object_id(prefix, corner_directions)
            if len(object_string) > 0:
                bm.from_object(bpy.data.objects[object_string], bpy.context.scene)
                bmesh.ops.rotate(bm, verts=bm.verts[l:len(bm.verts)], cent=center, matrix=self.rot_dict[d])
            corner_directions[0][0] = d
            corner_directions[1][0] = d

    def add_ceiling_bmesh(self, bm):
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
