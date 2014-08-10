__author__ = 'JoeJoe'

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


# filename
f = open('trainregion.dfmap', "rb")
# min and max coordinates to build
# min is inclusive, max is exclusive
# -1 for whole map
minX = 70
maxX = 90
minY = -1
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

#determine min and max stuff
minX = max(1, minX)
minY = max(1, minY)
minZ = max(1, minZ)
if maxX < 0:
    maxX = mapData.x_size * 16
else:
    maxX = min(maxX, mapData.x_size * 16)
if maxY < 0:
    maxY = mapData.y_size * 16
else:
    maxY = min(maxY, mapData.y_size * 16)
if maxZ < 0:
    maxZ = mapData.z_size
else:
    maxZ = min(maxZ, mapData.z_size)
maxZ_global = mapData.z_size


print("copy tiles")
numBlocks = 0

map_tiles = [[[None for x in range(maxZ_global + 1)]for x in range(maxY + 1)]for x in range(maxX + 1)]
Tile(map_tiles=map_tiles)
print("made empty")

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
        if bigX + 16 <= maxX:
            bigY = newblock.y * 16
            if bigY + 16 <= maxY:
                bigZ = newblock.z
                if bigZ >= minZ:
                    for t in newblock.tile:
                        if bigX + t.x >= minX and bigY + t.y >= minY:
                            map_tiles[bigX + t.x][bigY + t.y][bigZ] = Tile(t, newblock, material_lib)
                            numBlocks += 1

del mapData
del protomessage
del raw_data
del unzipped_data

copytime = time.time() - start_time
start_time = time.time()
print(numBlocks, "start ceilings")
print(len(map_tiles), len(map_tiles[0]), len(map_tiles[0][0]))

makesterrainful = [1, 2, 3, 4, 5, 6, 9, 11, 13, 14, 15]
needsceiling = [0, 1, 2, 3, 6, 7, 8, 9, 10, 13, 14, 15, 16]
hasfloor = [1, 2, 3, 4, 5, 6, 7, 8, 9, 13, 14, 15]          # everything where floor gets extended to
numBlocks = 0
for x in range(minX, maxX):
    for y in range(minY, maxY):
        terrainful = False
        for z in reversed(range(minZ, maxZ_global)):
            #input("add stuff?")
            t = map_tiles[x][y][z]
            if not t is None:
                numBlocks += 1
                if terrainful:
                    if t.terrain.type in needsceiling:
                        t.add_ceiling()
                        terrainful = False
                    elif t.terrain.type == TerrainType.WALL:
                        if map_tiles[x][y][z+1] is None:
                            t.add_ceiling()
                        elif map_tiles[x][y][z+1].terrain.type != TerrainType.WALL:
                            t.add_ceiling()

                if t.terrain.type in makesterrainful:
                        terrainful = True

                if t.terrain.type in hasfloor:
                    t.add_floor()


ceilingtime = time.time() - start_time
start_time = time.time()


print(numBlocks, "building objects")
no_terrain = ['RAMP_TOP', 'BROOK_TOP', 'ENDLESS_PIT']

numBlocks = 0
num_col = 0
filename = bpy.data.filepath

all_v = []
all_f = []

for x in range(minX, maxX):
    for y in range(minY, maxY):
        numBlocks += 1
        print("doing column ", numBlocks, "of", (maxX - minX) * (maxY - minY))
        for z in range(minZ, maxZ):
            t = map_tiles[x][y][z]
            if not t is None:
                identificator = t.terrain.terrain_type.name

                if identificator == 'PEBBLES':
                    identificator = 'FLOOR'
                if identificator == 'FORTIFICATION':
                    identificator = 'WALL'
                if identificator in no_terrain:
                    identificator = 'EMPTY'
                if not identificator == "EMPTY":
                    loc = Vector((t.global_x * 2, t.global_y * - 2, t.global_z * 3))
                    add_bm = t.build_bmesh()
                    bmesh.ops.translate(add_bm, vec=loc, verts=add_bm.verts)

                    #create some pydata
                    vertindex_offset = len(all_v)
                    all_v.extend(v.co[:] for v in add_bm.verts)
                    all_f.extend([[v.index + vertindex_offset for v in f.verts] for f in add_bm.faces])

me = bpy.data.meshes.new("landscape")
me.from_pydata(all_v, [], all_f)
ob = bpy.data.objects.new("Land", me)
bpy.context.scene.objects.link(ob)

bpy.context.scene.update()

terraintime = time.time()-start_time
start_time = time.time()


bpy.context.scene.objects.active = bpy.data.objects["Land"]
bpy.ops.object.select_pattern(pattern="Land*")
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles()
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_mainfile(filepath=filename)


jointime = time.time()-start_time

print("copy: ", copytime, "ceilings: ", ceilingtime, "terrain: ", terraintime, "join: ", jointime)

print(numBlocks, "last call")