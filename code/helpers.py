__author__ = 'JoeJoe'

import bpy
import bmesh
import math
from mathutils import Matrix


TILE_HEIGHT = 3
TILE_WIDTH = 2
BROOK_DEPTH = 0.5

def b2i(byte_input):
    return int.from_bytes(byte_input, byteorder='little')


def get_msg_length(byte_input):
    rtn = 0
    for i in range(len(byte_input)):
        rtn |= (byte_input[i] & 0x7F) << (i * 7)
    return rtn


def get_length_length(unzipped_data, pos):
    rtn = 1
    while unzipped_data[pos] & 0x80 != 0:
        pos += 1
        rtn += 1
    return rtn
