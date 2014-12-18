__author__ = 'JoeJoe'

import proto.Tile_pb2
from Terrain import Terrain, TerrainType
import bpy
import bmesh
import math
from mathutils import Matrix
from Direction import Direction
import random
from helpers import BROOK_DEPTH, TILE_HEIGHT, TILE_WIDTH


class BmeshFactory:
    """A factory to build the final bmesh for the tiles
    """
    N = Direction.North
    E = Direction.East
    S = Direction.South
    W = Direction.West
    rot_dict = {N: Matrix.Rotation(0, 3, 'Z'), E: Matrix.Rotation(-math.pi/2, 3, 'Z'),
                S: Matrix.Rotation(math.pi, 3, 'Z'), W: Matrix.Rotation(math.pi / 2, 3, 'Z')}
    center = (TILE_WIDTH / 2, -TILE_WIDTH / 2, 0)

    @staticmethod
    def build(tile):
        """main function for building the bmesh
        """
        rtn = bmesh.new()
        if tile.terrain_type() in Terrain.floor_terrains:
            rtn = BmeshFactory.build_floor(tile)
        elif tile.terrain_type() in Terrain.empty_terrains:
            BmeshFactory.add_floor_corners(rtn, tile)
        elif tile.terrain_type() == TerrainType.WALL:
            rtn = BmeshFactory.build_wall(tile)
        elif tile.terrain_type() == TerrainType.FORTIFICATION:
            rtn = BmeshFactory.build_fortification(tile)
        elif tile.terrain_type() == TerrainType.STAIR_DOWN or tile.terrain_type() == TerrainType.STAIR_UPDOWN:
            rtn = BmeshFactory.build_stair(tile)
        elif tile.terrain_type() == TerrainType.RAMP:
            rtn = BmeshFactory.build_ramp(tile)
        elif tile.terrain_type() == TerrainType.BROOK_BED:
            rtn = BmeshFactory.build_brook(tile)

        BmeshFactory.build_ceiling(rtn, tile)

        # bmesh.ops.remove_doubles(rtn, verts=rtn.verts, dist=0.0001)
        bmesh.ops.dissolve_limit(rtn, angle_limit=math.pi/90, use_dissolve_boundaries=False,
                                 verts=rtn.verts, edges=rtn.edges)
        return rtn

    @staticmethod
    def build_floor(tile):
        """main function for building the floorlike meshes"""
        rtn = bmesh.new()
        rtn.from_object(bpy.data.objects['FLOOR_CENTER'], bpy.context.scene)
        BmeshFactory.add_floor_corners(rtn, tile)
        rtn.from_object(bpy.data.objects[tile.terrain_type().name], bpy.context.scene)
        BmeshFactory.add_ceiling_center_below(rtn, tile)
        return rtn

    @staticmethod
    def add_floor_corners(mesh, tile):
        """adds the corner parts of a floor"""
        corner_directions = [[BmeshFactory.W], [BmeshFactory.W, BmeshFactory.N], [BmeshFactory.N]]
        tile_below = tile.get_tile_in_direction([], -1)
        ceiling_below = False
        if tile_below is not None:
            ceiling_below = True
        for d in Direction:
            corner_directions[1][1] = d
            corner_directions[2][0] = d
            l = len(mesh.verts)
            add_corner = False
            try:
                if tile.terrain.extend_to:
                    for e in corner_directions:
                        neighbor_tile = tile.get_tile_in_direction(e)
                        if neighbor_tile is None or (neighbor_tile.terrain.extend_to and not tile.terrain.make_edges_to):
                            add_corner = True
                    neighbor_tile = tile.get_tile_in_direction([d])
                    if neighbor_tile is None or neighbor_tile.terrain.make_edges_to:
                        mesh.from_object(bpy.data.objects['FLOOR_Cen'], bpy.context.scene)
                # for tiles that do not get extended to but help connect diagonals
                if tile.terrain.connect_diag and tile.terrain.make_edges_to:
                    neighbor_tile1 = tile.get_tile_in_direction(corner_directions[0])
                    neighbor_tile2 = tile.get_tile_in_direction(corner_directions[2])
                    if neighbor_tile1.terrain.extend_to and neighbor_tile2.terrain.extend_to and \
                            not neighbor_tile1.terrain.make_edges_to and not neighbor_tile2.terrain.make_edges_to:
                        add_corner = True
                        mesh.from_object(bpy.data.objects['FLOOR_OD'], bpy.context.scene)
            except AttributeError:
                pass
            if add_corner:
                num_walls = 0
                for e in corner_directions:
                    neighbor_tile = tile.get_tile_in_direction(e)
                    if neighbor_tile is not None and neighbor_tile.terrain.terrain_type == TerrainType.WALL:
                        num_walls += 1
                if num_walls < 3:
                    mesh.from_object(bpy.data.objects['FLOOR_CORNER'], bpy.context.scene)
                    if ceiling_below:
                        BmeshFactory.add_ceiling_single_corner(mesh, tile_below, corner_directions, True)
                try:
                    neighbor_tile = tile.get_tile_in_direction(corner_directions[0])
                    diag_tile = tile.get_tile_in_direction(corner_directions[1])
                    if neighbor_tile is None or neighbor_tile.terrain.make_edges_to:
                        if diag_tile is None or not (diag_tile.terrain.extend_to and neighbor_tile.terrain.connect_diag):
                            mesh.from_object(bpy.data.objects['FLOOR_Cor0'], bpy.context.scene)
                    neighbor_tile = tile.get_tile_in_direction(corner_directions[2])
                    if neighbor_tile is None or neighbor_tile.terrain.make_edges_to:
                        if diag_tile is None or not (diag_tile.terrain.extend_to and neighbor_tile.terrain.connect_diag):
                            mesh.from_object(bpy.data.objects['FLOOR_Cor2'], bpy.context.scene)
                except AttributeError:
                    print("unexpected None Type Attribute Error")
            elif tile.terrain.extend_to:
                mesh.from_object(bpy.data.objects['FLOOR_ID'], bpy.context.scene)

            bmesh.ops.rotate(mesh, verts=mesh.verts[l:len(mesh.verts)], cent=BmeshFactory.center, matrix=BmeshFactory.rot_dict[d])
            corner_directions[0][0] = d
            corner_directions[1][0] = d

    # I was told in Software Engineering a function should be no longer than 7 lines,
    # so here's a function that's ten times as long
    @staticmethod
    def build_wall(tile):
        rtn = bmesh.new()
        corner_directions = [[BmeshFactory.W], [BmeshFactory.W, BmeshFactory.N], [BmeshFactory.N]]
        wall = TerrainType.WALL
        tile_below = tile.get_tile_in_direction([], -1)
        ceiling_below = False
        if tile_below is not None:
            ceiling_below = True
        for d in Direction:
            corner_directions[1][1] = d
            corner_directions[2][0] = d
            l = len(rtn.verts)
            neighbor_tiles = [None, None, None]
            neighbor_terrains = [None, None, None]
            add_corner = False
            corner_below = True
            for e in range(3):
                neighbor_tiles[e] = tile.get_tile_in_direction(corner_directions[e])
                try:
                    neighbor_terrains[e] = neighbor_tiles[e].terrain_type()
                except AttributeError:
                    neighbor_terrains[e] = TerrainType.WALL
                if neighbor_tiles[e] is not None:
                    if neighbor_tiles[e].terrain.extend_to:
                        add_corner = True
            if TerrainType.RAMP not in neighbor_terrains:
                if neighbor_terrains[0] != wall:
                    rtn.from_object(bpy.data.objects['WALL_Cen1'], bpy.context.scene)
                    if neighbor_terrains[2] != wall:
                        rtn.from_object(bpy.data.objects['WALL_ID'], bpy.context.scene)
                        rtn.from_object(bpy.data.objects['WALL_Cen2'], bpy.context.scene)
                        if neighbor_tiles[2].terrain.make_edges_to:
                            rtn.from_object(bpy.data.objects['FLOOR_Cen'], bpy.context.scene)
                        if add_corner:
                            rtn.from_object(bpy.data.objects['FLOOR_CORNER'], bpy.context.scene)
                            if neighbor_tiles[0].terrain.make_edges_to:
                                rtn.from_object(bpy.data.objects['FLOOR_Cor0'], bpy.context.scene)
                            if neighbor_tiles[2].terrain.make_edges_to:
                                rtn.from_object(bpy.data.objects['FLOOR_Cor2'], bpy.context.scene)
                        else:
                            rtn.from_object(bpy.data.objects['FLOOR_ID'], bpy.context.scene)
                            corner_below = False
                    elif neighbor_terrains[1] != wall:
                        rtn.from_object(bpy.data.objects['WALL_Cor1'], bpy.context.scene)
                        if neighbor_tiles[0].terrain.make_edges_to:
                            rtn.from_object(bpy.data.objects['FLOOR_Cor0'], bpy.context.scene)
                elif neighbor_terrains[2] != wall:
                    rtn.from_object(bpy.data.objects['WALL_Cen2'], bpy.context.scene)
                    if neighbor_tiles[2].terrain.make_edges_to:
                        rtn.from_object(bpy.data.objects['FLOOR_Cen'], bpy.context.scene)
                    if neighbor_terrains[1] != wall:
                        rtn.from_object(bpy.data.objects['WALL_Cor2'], bpy.context.scene)
                        if neighbor_tiles[2].terrain.make_edges_to:
                            rtn.from_object(bpy.data.objects['FLOOR_Cor2'], bpy.context.scene)
                elif neighbor_terrains[1] != wall:
                    rtn.from_object(bpy.data.objects['WALL_OD'], bpy.context.scene)
                    if ceiling_below:
                        BmeshFactory.add_outer_below(rtn, tile_below.get_tile_in_direction(corner_directions[1]), d)
                    if neighbor_tiles[1].terrain.make_edges_to:
                        rtn.from_object(bpy.data.objects['FLOOR_ODW'], bpy.context.scene)
            if ceiling_below and corner_below:
                BmeshFactory.add_ceiling_single_corner(rtn, tile_below, corner_directions, True)

            raise_floor = False
            for e in neighbor_terrains:
                if e == TerrainType.BROOK_BED:
                    raise_floor = True

            if raise_floor:
                BmeshFactory.raise_to_brook(rtn, l)

            bmesh.ops.rotate(rtn, verts=rtn.verts[l:len(rtn.verts)], cent=BmeshFactory.center, matrix=BmeshFactory.rot_dict[d])
            corner_directions[0][0] = d
            corner_directions[1][0] = d
        BmeshFactory.add_ceiling_center_below(rtn, tile)
        return rtn

    @staticmethod
    def build_fortification(tile):
        rtn = bmesh.new()
        rtn.from_object(bpy.data.objects['FORTIFICATION'], bpy.context.scene)
        BmeshFactory.add_floor_corners(rtn, tile)
        BmeshFactory.add_ceiling_center_below(rtn, tile)
        return rtn

    @staticmethod
    def build_stair(tile):
        rtn = bmesh.new()
        if tile.terrain_type() == TerrainType.STAIR_UPDOWN:
            rtn.from_object(bpy.data.objects['STAIR_UP'], bpy.context.scene)
        rtn.from_object(bpy.data.objects['STAIR_DOWN'], bpy.context.scene)
        BmeshFactory.add_floor_corners(rtn, tile)
        return rtn

    @staticmethod
    def build_ramp(tile):
        # TODO: implement
        rtn = bmesh.new()
        tile_below = tile.get_tile_in_direction([], -1)
        if tile_below is not None:
            BmeshFactory.build_ceiling(rtn, tile_below)
        return rtn

    @staticmethod
    def build_brook(tile):
        rtn = bmesh.new()
        rtn.from_object(bpy.data.objects['FLOOR_CENTER'], bpy.context.scene)
        BmeshFactory.add_floor_corners(rtn, tile)
        if random.randint(1, 15) == 1:
            rtn.from_object(bpy.data.objects['BROOK_BOULDER'], bpy.context.scene)
        bmesh.ops.translate(rtn, vec=(0, 0, 2.5), verts=rtn.verts)
        BmeshFactory.add_ceiling_center_below(rtn, tile)
        return rtn

    @staticmethod
    def raise_to_brook(mesh, length):
        raise_verts = []
        for i in range(length, len(mesh.verts)):
            if mesh.verts[i].co[2] < 1:
                raise_verts.append(mesh.verts[i])
        brook_height = TILE_HEIGHT - BROOK_DEPTH
        bmesh.ops.translate(mesh, vec=(0, 0, brook_height), verts=raise_verts)

    @staticmethod
    def build_ceiling(mesh, tile):
        if tile.terrain.has_ceiling:
            if tile.terrain_type() == TerrainType.FORTIFICATION:
                mesh.from_object(bpy.data.objects['CEILING_FORT'], bpy.context.scene)
            elif tile.terrain_type() != TerrainType.WALL:
                mesh.from_object(bpy.data.objects['CEILING_CENTER'], bpy.context.scene)
            BmeshFactory.add_ceiling_corners(mesh, tile)

    @staticmethod
    def add_ceiling_corners(mesh, tile):
        corner_directions = [[BmeshFactory.W], [BmeshFactory.W, BmeshFactory.N], [BmeshFactory.N]]
        for d in Direction:
            corner_directions[1][1] = d
            corner_directions[2][0] = d
            l = len(mesh.verts)
            BmeshFactory.add_ceiling_single_corner(mesh, tile, corner_directions)
            bmesh.ops.rotate(mesh, verts=mesh.verts[l:len(mesh.verts)], cent=BmeshFactory.center, matrix=BmeshFactory.rot_dict[d])
            corner_directions[0][0] = d
            corner_directions[1][0] = d

    @staticmethod
    def add_ceiling_single_corner(mesh, tile, corner_directions, below=False, outer=False):
        numwalls = 0
        wall_ceiling = False
        for e in range(3):
            neighbor_tile = tile.get_tile_in_direction(corner_directions[e])
            try:
                if neighbor_tile is None or neighbor_tile.terrain_type() == TerrainType.WALL:
                    numwalls += 1
                if e == 1 and neighbor_tile.terrain_type() == TerrainType.WALL:
                    wall_ceiling = True
            except AttributeError:
                pass

        if (numwalls < 3 and tile.terrain_type() != TerrainType.WALL) or numwalls == 0 or (numwalls == 1 and wall_ceiling):
            add_corner = True
        else:
            add_corner = False

        if add_corner:
            if below and not outer:
                mesh.from_object(bpy.data.objects['CORNER_BELOW'], bpy.context.scene)
            elif below and outer:
                mesh.from_object(bpy.data.objects['CORNER_BELOW_O'], bpy.context.scene)
            else:
                mesh.from_object(bpy.data.objects['CEILING_CORNER'], bpy.context.scene)

    @staticmethod
    def add_ceiling_center_below(mesh, tile):
        tile_below = tile.get_tile_in_direction([], -1)
        if tile_below is not None and tile_below.terrain_type() != TerrainType.WALL:
            if tile_below.terrain_type() == TerrainType.FORTIFICATION:
                mesh.from_object(bpy.data.objects['CEILING_BELOW_F'], bpy.context.scene)
            else:
                mesh.from_object(bpy.data.objects['CEILING_BELOW'], bpy.context.scene)

    @staticmethod
    def add_outer_below(mesh, tile, direction):
        if tile is not None:
            next_dir = direction.next()
            corner_directions = [[next_dir], [next_dir, next_dir.next()], [next_dir.next()]]
            BmeshFactory.add_ceiling_single_corner(mesh, tile, corner_directions, below=True, outer=True)
