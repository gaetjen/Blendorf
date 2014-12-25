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
from helpers import BROOK_DEPTH, TILE_HEIGHT, TILE_WIDTH

# filename
f = open('../maps/ramps.dfmap', "rb")
# min and max coordinates to build
# min is inclusive, max is exclusive
# -1 for whole map
minX = 75
maxX = -1
minY = -1
maxY = 90
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

# determine min and max stuff
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
Tile.map_tiles = map_tiles
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

for x in range(minX, maxX):
    for y in range(minY, maxY):
        terrainful = False
        sky_above = True
        for z in reversed(range(minZ, maxZ_global)):
            t = map_tiles[x][y][z]
            if sky_above:
                if t is not None:
                    sky_above = False
            elif t is None:
                terrainful = True
            elif terrainful:
                t.add_ceiling()
                terrainful = False


ceilingtime = time.time() - start_time
start_time = time.time()


print(numBlocks, "building objects")

numBlocks = 0
num_col = 0
filename = bpy.data.filepath

all_v = []
all_f = []
material_face_dict = {}
for x in range(minX, maxX):
    for y in range(minY, maxY):
        numBlocks += 1
        print("doing column ", numBlocks, "of", (maxX - minX) * (maxY - minY))
        for z in range(minZ, maxZ):
            t = map_tiles[x][y][z]
            if t is not None:
                loc = Vector((t.global_x * TILE_WIDTH, t.global_y * -TILE_WIDTH, t.global_z * TILE_HEIGHT))
                add_bm = t.build_bmesh()
                bmesh.ops.translate(add_bm, vec=loc, verts=add_bm.verts)

                # create some pydata
                vertindex_offset = len(all_v)
                f_start = len(all_f)
                all_v.extend(v.co[:] for v in add_bm.verts)
                all_f.extend([[v.index + vertindex_offset for v in f.verts] for f in add_bm.faces])
                try:
                    material_face_dict[t.material].extend(i for i in range(f_start, len(all_f)))
                except KeyError:
                    material_face_dict[t.material] = []
                    material_face_dict[t.material].extend(i for i in range(f_start, len(all_f)))

me = bpy.data.meshes.new("landscape")
me.from_pydata(all_v, [], all_f)
ob = bpy.data.objects.new("Land", me)
bpy.context.scene.objects.link(ob)

bpy.context.scene.update()

terraintime = time.time()-start_time
start_time = time.time()

print("finalizing objects and cleaning up geometry")
bpy.context.scene.objects.active = bpy.data.objects["Land"]
bpy.ops.object.select_pattern(pattern="Land*")
terrain = bpy.data.objects["Land"]

# for loop where all materials are appended to the terrain
for m in bpy.data.materials:
    terrain.data.materials.append(m)

print(material_face_dict.keys())
# input("cont")
# for loop where the faces get the proper material indices (loop over object materials)
# TODO: differentiate terrain and props (wait for 0.40.xx maps?)
for i, mat in enumerate(terrain.data.materials):
    matname = mat.name
    try:
        faces = material_face_dict[matname]
        for f in faces:
            terrain.data.polygons[f].material_index = i
    except KeyError:
        print(matname, "was not found")

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles()
bpy.ops.object.mode_set(mode='OBJECT')
# bpy.ops.wm.save_mainfile(filepath=filename)


jointime = time.time()-start_time

print("copy: ", copytime, "ceilings: ", ceilingtime, "terrain: ", terraintime, "join: ", jointime)

print(numBlocks, "last call")