__author__ = 'JoeJoe'
#small script to automatically generate all the materials

import zlib
import time

import proto.Block_pb2 as Block_pb2
import proto.Map_pb2 as Map_pb2
from Tile import Tile
from Terrain import TerrainType
import bpy
import bmesh
from mathutils import Vector
from helpers import b2i, get_msg_length, get_length_length
from helpers import BROOK_DEPTH, TILE_HEIGHT, TILE_WIDTH
from proto.Tile_pb2 import _TILE_TILEMATERIALTYPE


# filename
f = open('../maps/ramps.dfmap', "rb")

raw_data = f.read()
f.close()
unzipped_data = zlib.decompress(raw_data, 16+zlib.MAX_WBITS)
header = unzipped_data[0:4]


header_check = 0x50414DDF
if b2i(header) == header_check:
    print("header is okay")
else:
    print("header is wrong")

pos = 4
lengthLength = get_length_length(unzipped_data, pos)
msglength = get_msg_length(unzipped_data[pos:pos+lengthLength])
pos += lengthLength
protomessage = unzipped_data[pos:pos + msglength]
pos += msglength

mapData = Map_pb2.Map()
mapData.ParseFromString(protomessage)

print("build MATLIB")
material_lib = [[] for x in range(2)]
for m in mapData.inorganic_material:
    material_lib[0].append(m.name)
for m in mapData.organic_material:
    material_lib[1].append(m.name)

print(material_lib)
ob = bpy.data.objects['MATERIALS']
m_names = [n.name for n in ob.material_slots]
print(m_names)
tmt = [t.name for t in _TILE_TILEMATERIALTYPE.values]
print(tmt)
for d in material_lib:
    for m in d:
        if m not in m_names:
            newmat = bpy.data.materials.new(m)
            ob.data.materials.append(newmat)

for m in tmt:
    if m not in m_names:
        newmat = bpy.data.materials.new(m)
        ob.data.materials.append(newmat)
