__author__ = 'JoeJoe'

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

"""
def build_wall_bm(tile, map):

    x = tile.global_x
    y = tile.global_y
    z = tile.global_z
    center = (1, -1, 0)
    if not (map[x][y - 1][z] is None) and map[x][y - 1][z].terrain.type.name == 'WALL':

    else:


    l = len(rtn.verts)
    if not (map[x - 1][y][z] is None) and map[x - 1][y][z].terrain.type.name == 'WALL':
        rtn.from_object(bpy.data.objects['WALL_WALL'], bpy.context.scene)
        bmesh.ops.rotate(rtn, verts=rtn.verts[l:len(rtn.verts)], cent=center, matrix=rot_w)
    else:
        rtn.from_object(bpy.data.objects['WALL_CLEAR'], bpy.context.scene)
        bmesh.ops.rotate(rtn, verts=rtn.verts[l:len(rtn.verts)], cent=center, matrix=rot_w)

    l = len(rtn.verts)
    if not (map[x + 1][y][z] is None) and map[x + 1][y][z].terrain.type.name == 'WALL':
        rtn.from_object(bpy.data.objects['WALL_WALL'], bpy.context.scene)
        bmesh.ops.rotate(rtn, verts=rtn.verts[l:len(rtn.verts)], cent=center, matrix=rot_e)
    else:
        rtn.from_object(bpy.data.objects['WALL_CLEAR'], bpy.context.scene)
        bmesh.ops.rotate(rtn, verts=rtn.verts[l:len(rtn.verts)], cent=center, matrix=rot_e)

    l = len(rtn.verts)
    if not (map[x][y + 1][z] is None) and map[x][y + 1][z].terrain.type.name == 'WALL':
        rtn.from_object(bpy.data.objects['WALL_WALL'], bpy.context.scene)
        bmesh.ops.rotate(rtn, verts=rtn.verts[l:len(rtn.verts)], cent=center, matrix=rot_s)
    else:
        rtn.from_object(bpy.data.objects['WALL_CLEAR'], bpy.context.scene)
        bmesh.ops.rotate(rtn, verts=rtn.verts[l:len(rtn.verts)], cent=center, matrix=rot_s)

    bmesh.ops.remove_doubles(rtn, verts=rtn.verts, dist=0.0001)

    return rtn
"""