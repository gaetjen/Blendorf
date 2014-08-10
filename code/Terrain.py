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
        terrain_type    base terrain type for the Tile
        has_ceiling     boolean whether or not a ceiling is above the tile
        has_floor       boolean whether or not the tile has a floor, for construction purposes
    """
    has_ceiling = False
    has_floor = False

    def __init__(self, terrain_type):
        self.terrain_type = TerrainType(terrain_type)

    def add_ceiling(self):
        self.has_ceiling = True

    def add_floor(self):
        self.has_floor = True