__author__ = 'JoeJoe'

from enum import IntEnum


class TerrainType(IntEnum):
        EMPTY = 0
        FLOOR = 1
        BOULDER = 2
        PEBBLES = 3
        WALL = 4
        FORTIFICATION = 5
        STAIR_UP = 6
        STAIR_DOWN = 7
        STAIR_UPDOWN = 8
        RAMP = 9
        RAMP_TOP = 10
        BROOK_BED = 11
        BROOK_TOP = 12
        TREE = 13
        SAPLING = 14
        SHRUB = 15
        ENDLESS_PIT = 16


class Terrain:
    """A class containing more context information about a Tile's terrain

    Attributes:
        terrain_type            base terrain type for the Tile
        terrainful              the next tile under this one needs a ceiling
        has_ceiling             a ceiling is above the tile
        extend_to               neighboring floors connect to this tile
        connect_diag            neighboring tiles can get connected diagonally through this tile
        edge_to                 adjacent floors need edges in this direction
        rampinfo                Ramp object with more information
    """
    # list of terrains, that are just a floor, maybe with more stuff placed on it
    floor_terrains = [1, 2, 3, 6, 13, 14, 15]
    # list of terrains, that have no objects
    empty_terrains = [0, 12, 16]
    # list containing walls and stairs, because they behave the same
    wall_terrains = [4, 5, 7, 8, 11]
    has_ceiling = False

    def __init__(self, terrain_type):
        self.terrain_type = TerrainType(terrain_type)

        if terrain_type in self.floor_terrains:
            self.extend_to =        True
            self.connect_diag =     True
            self.make_edges_to =    False

        if terrain_type in self.wall_terrains:
            self.extend_to =        True
            self.connect_diag =     True
            self.make_edges_to =    False

        if terrain_type == TerrainType.RAMP:
            self.extend_to =        True
            self.connect_diag =     False
            self.make_edges_to =    False
            self.rampinfo = None

        if terrain_type == TerrainType.RAMP_TOP:
            self.extend_to =        True
            self.connect_diag =     False
            self.make_edges_to =    True

        if terrain_type in self.empty_terrains:
            self.extend_to =        False
            self.connect_diag =     True
            self.make_edges_to =    True

    def add_ceiling(self):
        self.has_ceiling = True
