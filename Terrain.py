__author__ = 'JoeJoe'

from enum import IntEnum

class TileType(IntEnum):
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
    has_ceiling = False

    def __init__(self, type):
        self.type = TileType(type)

    """
    def identificator(self):
        """
    """
        if self.type is None:
            print("NONE TYPE")
            return "none"
        else:
        """
    """
        name_id = self.type.name
        if self.has_ceiling:
            name_id += '1'
        else:
            name_id += '0'
        return name_id
    """

    def add_ceiling(self):
        self.has_ceiling = True