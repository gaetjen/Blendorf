__author__ = 'JoeJoe'

import proto.Block_pb2 as Block_pb2
import proto.Map_pb2 as Map_pb2
import proto.Material_pb2 as Material_pb2
import proto.Plant_pb2 as Plant_pb2
import proto.Tile_pb2 as Tile_pb2
from Tile import Tile
from Terrain import TileType
from Terrain import Terrain
import zlib
import bpy
import bmesh
from mathutils import Vector
import sys
import time
import math
from helpers import *


f = open('trainregion.dfmap', "rb")         # filename
minX = -1                                   # min and max coordinates to build
maxX = -1                                  # min is inclusive, max is exclusive
minY = -1                                   # -1 for whole map
maxY = -1
minZ = -1
maxZ = -1




start_time = time.time()
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
#print(str(mapData))
#determine min and max stuff
minX = max(1, minX)
minY = max(1, minY)
minZ = max(1, minZ)
if maxX < 0:
    maxX = mapData.x_size * 16 - 1
else:
    maxX = min(maxX, mapData.x_size * 16 - 1)
if maxY < 0:
    maxY = mapData.y_size * 16 - 1
else:
    maxY = min(maxY, mapData.y_size * 16 - 1)
if maxZ < 0:
    maxZ = mapData.z_size - 1
else:
    maxZ = min(maxZ, mapData.z_size - 1)


#print(proto.Tile_pb2.Tile.FLOOR)
#proto.Tile_pb2.Tile.STONE
print("copy tiles")
numBlocks = 0
map_tiles = [[[None for x in range(mapData.z_size)]for x in range(mapData.y_size * 16)]for x in range(mapData.x_size * 16)]
while pos < len(unzipped_data):
    lengthLength = get_length_length(unzipped_data, pos)
    msglength = get_msg_length(unzipped_data[pos:pos+lengthLength])
    pos += lengthLength
    protomessage = unzipped_data[pos:pos + msglength]
    pos += msglength
    newblock = Block_pb2.Block()
    newblock.ParseFromString(protomessage)
    if newblock.IsInitialized() and len(newblock.tile) > 0:
        bigX = newblock.x * 16
        bigY = newblock.y * 16
        bigZ = newblock.z
        for t in newblock.tile:
            map_tiles[bigX+t.x][bigY+t.y][bigZ] = Tile(t, newblock, material_lib)
            numBlocks += 1


del mapData
del protomessage
del raw_data
del unzipped_data

copytime = time.time()-start_time
start_time = time.time()
print(numBlocks, "start ceilings")
print(len(map_tiles), len(map_tiles[0]), len(map_tiles[0][0]))

makesterrainful = [1, 2, 3, 4, 5, 6, 9, 11, 13, 14, 15]
needsceiling = [0, 1, 2, 3, 6, 7, 8, 9, 10, 13, 14, 15, 16]
numBlocks = 0
for x in range(minX, maxX):
    for y in range(minY, maxY):
        terrainful = False
        for z in reversed(range(minZ, maxZ)):
            #input("add stuff?")
            t = map_tiles[x][y][z]
            if not t is None:
                numBlocks += 1
                if terrainful:
                    if t.terrain.type in needsceiling:
                        t.add_ceiling()
                        terrainful = False
                    elif t.terrain.type == TileType.WALL:
                        if map_tiles[x][y][z+1] is None:
                            t.add_ceiling()
                        elif map_tiles[x][y][z+1].terrain.type != TileType.WALL:
                            t.add_ceiling()

                if t.terrain.type in makesterrainful:
                        terrainful = True


ceilingtime = time.time() - start_time
start_time = time.time()


print(numBlocks, "building objects")
no_terrain = ['RAMP_TOP', 'BROOK_TOP', 'ENDLESS_PIT']
numBlocks = 0
num_col = 0
bm = bmesh.new()
stepsize = 100
filename = bpy.data.filepath

obj_meshes = ['BOULDER0', 'BOULDER1', 'BROOK_BED0', 'EMPTY1', 'FLOOR0', 'FLOOR1', 'RAMP0', 'RAMP1', 'SAPLING0',
              'SAPLING1', 'SHRUB0', 'SHRUB1', 'STAIR_DOWN0', 'STAIR_DOWN1', 'STAIR_UP0', 'STAIR_UP1', 'STAIR_UPDOWN0',
              'STAIR_UPDOWN1', 'TREE0', 'TREE1']

mesh_dict = {s: type('bm_ext', (object,), dict(v=Vector((0, 0, 0)), bm=bmesh.new())) for s in obj_meshes}
for k in mesh_dict:
    mesh_dict[k].bm.from_object(bpy.data.objects[k], bpy.context.scene)

for x in range(minX, maxX):
    for y in range(minY, maxY):
        print("doing column ", numBlocks, "of", maxX * maxY)
        numBlocks += 1
        num_col += 1
        for t in map_tiles[x][y]:
            if not t is None:
                identificator = t.terrain.type.name

                if identificator == "PEBBLES":
                    identificator = 'FLOOR'
                if identificator == 'FORTIFICATION':
                    identificator = 'WALL'
                if identificator in no_terrain:
                    identificator = 'EMPTY'
                if identificator != "WALL":
                    if t.terrain.has_ceiling:
                        identificator += '1'
                    else:
                        identificator += '0'
                if not identificator == "EMPTY0":
                    loc = Vector((t.global_x * 2, t.global_y * - 2, t.global_z * 3))
                    add_bm = bmesh.new()
                    if identificator == "WALL":
                        add_bm = build_wall_bm(t, map_tiles)
                        bmesh.ops.translate(add_bm, vec=loc, verts=add_bm.verts)
                    else:
                        add_bm = mesh_dict[identificator].bm
                        bmesh.ops.translate(add_bm, vec=loc-mesh_dict[identificator].v, verts=add_bm.verts)
                        mesh_dict[identificator].v = loc
                    #join the bmeshes
                    me = bpy.data.meshes.new("temp")
                    add_bm.to_mesh(me)
                    bm.from_mesh(me)

                    """
                    # 292 s in background
                    add_bm = bmesh.new()
                    add_bm.from_object(bpy.data.objects[identificator], bpy.context.scene)
                    bmesh.ops.translate(add_bm, vec=loc, verts=add_bm.verts)
                    #join the bmeshes
                    me = bpy.data.meshes.new("temp")
                    add_bm.to_mesh(me)
                    add_bm.free()
                    bm.from_mesh(me)
                    """
                    """
                    #this part is extremely slow--58 s for 500
                    start_vert = len(bm.verts)
                    bm.from_object(bpy.data.objects[identificator], bpy.context.scene)
                    bmesh.ops.translate(bm, vec=loc, verts=bm.verts[start_vert:len(bm.verts)])
                    """
                    """
                    #this is super slow 60 s for first 500
                    add_bm = bmesh.new()
                    add_bm.from_object(bpy.data.objects[identificator], bpy.context.scene)
                    bmesh.ops.translate(add_bm, vec=loc, verts=add_bm.verts)
                    vertindex_offset = len(bm.verts)
                    for v in add_bm.verts:
                        bm.verts.new(v.co)
                    for e in add_bm.edges:
                        bm.edges.new([bm.verts[v.index + vertindex_offset] for v in e.verts])
                    for f in add_bm.faces:
                        bm.faces.new([bm.verts[v.index + vertindex_offset] for v in f.verts])
                    add_bm.free()
                    """

        if num_col >= stepsize:
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
            me = bpy.data.meshes.new("landscape")
            bm.to_mesh(me)
            ob = bpy.data.objects.new("Land", me)
            bpy.context.scene.objects.link(ob)
            #bm.free()
            #del bm
            bm = bmesh.new()
            num_col = 0
            print("reloading file, time: ", time.time()-start_time)
            bpy.ops.wm.save_mainfile(filepath=filename)
            bpy.ops.wm.open_mainfile(filepath=filename)

bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
me = bpy.data.meshes.new("landscape")
bm.to_mesh(me)
bm.free()
ob = bpy.data.objects.new("Land", me)
bpy.context.scene.objects.link(ob)

bpy.context.scene.update()

terraintime = time.time()-start_time
start_time = time.time()


bpy.context.scene.objects.active = bpy.data.objects["Land"]
bpy.ops.object.select_pattern(pattern="Land*")
bpy.ops.object.join()
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles()
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_mainfile(filepath=filename)


jointime = time.time()-start_time

print("copy: ", copytime, "ceilings: ", ceilingtime, "terrain: ", terraintime, "join: ", jointime)

print(numBlocks, "last call")