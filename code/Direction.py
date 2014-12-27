__author__ = 'JoeJoe'

from enum import IntEnum


class Direction(IntEnum):
    North = 0
    East = 1
    South = 2
    West = 3

    def next(self):
        return Direction((self + 1) % 4)

    def prev(self):
        return Direction((self - 1) % 4)

    def oppos(self):
        return Direction(self.next().next())

    def is_neighbor(self, direction):
        if self + 1 == direction or self - 1 == direction:
            return True
        else:
            return False
