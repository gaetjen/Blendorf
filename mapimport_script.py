__author__ = 'Johannes'

import proto.Block_pb2
import proto.Map_pb2
import proto.Material_pb2
import proto.Plant_pb2
import proto.Tile_pb2
import zlib
import sys

def b2i(byteInput):
    return int.from_bytes(byteInput, byteorder='little')

def getMsgLength(byteInput):
    rtn = 0
    for i in range(len(byteInput)):
        rtn |= (byteInput[i] & 0x7F) << (i * 7)
    return rtn

def getLengthLength(unzipped_data, pos):
    rtn = 1
    while unzipped_data[pos] & 0x80 != 0:
        pos += 1
        rtn += 1
    return rtn


f = open('trainregion.dfmap', "rb")
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

lengthLength = getLengthLength(unzipped_data, pos)

msglength = getMsgLength(unzipped_data[pos:pos+lengthLength])
pos += lengthLength
protomessage = unzipped_data[pos:pos + msglength]
pos += msglength

mapData = proto.Map_pb2.Map()
mapData.ParseFromString(protomessage)

#print(str(mapData))

blocks = []
verts = []
faces = []
numverts = 0
while pos < len(unzipped_data):
    lengthLength = getLengthLength(unzipped_data, pos)
    msglength = getMsgLength(unzipped_data[pos:pos+lengthLength])
    pos += lengthLength
    protomessage = unzipped_data[pos:pos + msglength]
    pos += msglength
    newblock = proto.Block_pb2.Block()
    newblock.ParseFromString(protomessage)
    if newblock.IsInitialized() and len(newblock.tile) > 0:
        bigX = newblock.x * 16
        bigY = newblock.y * 16
        bigZ = newblock.z
        for t in newblock.tile:
            if t.type == proto.Tile_pb2.Tile.WALL or t.type == proto.Tile_pb2.Tile.FLOOR:
                locx = bigX + t.x
                locy = bigY + t.y
                if t.type == proto.Tile_pb2.Tile.WALL:
                    newverts = [(locx * 2 - 1, locy * 2 - 1, bigZ*2 - 1), (locx * 2-1, locy * 2+1, bigZ*2 - 1), (locx * 2+1, locy * 2-1, bigZ*2-1), (locx * 2+1, locy * 2+1, bigZ*2-1), (locx * 2-1, locy * 2-1, bigZ*2+1), (locx * 2-1, locy * 2+1, bigZ*2+1), (locx * 2+1, locy * 2-1, bigZ*2+1), (locx * 2+1, locy * 2+1, bigZ*2+1)]
                    verts.extend(newverts)
                    newfaces=[(numverts, numverts+1, numverts+3, numverts+2), (numverts+4, numverts+5, numverts+7, numverts+6), (numverts, numverts+1, numverts+5, numverts+4), (numverts, numverts+2, numverts+6, numverts+4), (numverts+2, numverts+3, numverts+7, numverts+6), (numverts+1, numverts+3, numverts+7, numverts+5)]
                    faces.extend(newfaces)
                    numverts += 8
                else:
                    newverts = [(locx * 2-1, locy * 2-1, bigZ*2 - 1), (locx * 2-1, locy * 2+1, bigZ*2 - 1), (locx * 2+1, locy * 2-1, bigZ*2 - 1), (locx * 2+1, locy * 2+1, bigZ*2 - 1)]
                    verts.extend(newverts)
                    newface = (numverts, numverts+1, numverts+3, numverts+2)
                    faces.append(newface)                        
                    numverts += 4
                


#create mesh and object
mesh = bpy.data.meshes.new("land")
object = bpy.data.objects.new("land",mesh)

#set mesh location
object.location =  bpy.context.scene.cursor_location
bpy.context.scene.objects.link(object)
 
#create mesh from python data
mesh.from_pydata(verts,[],faces)
mesh.update(calc_edges=True)
#print(verts)
#print(faces)    
print("last call")
