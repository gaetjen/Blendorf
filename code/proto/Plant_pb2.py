# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: Plant.proto

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
import sys
if sys.version_info >= (3,):
  #some constants that are python2 only
  unicode = str
  long = int
  range = range
  unichr = chr
  def b(s):
    return s.encode("latin-1")
  def u(s):
    return s
else:
  #some constants that are python2 only
  range = xrange
  unicode = unicode
  long = long
  unichr = unichr
  def b(s):
    return s
  # Workaround for standalone backslash
  def u(s):
    return unicode(s.replace(r'\\', r'\\\\'), "unicode_escape")

from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)




DESCRIPTOR = _descriptor.FileDescriptor(
  name='Plant.proto',
  package='dfproto',
  serialized_pb=b('\n\x0bPlant.proto\x12\x07\x64\x66proto\"A\n\x05Plant\x12\t\n\x01x\x18\x01 \x02(\r\x12\t\n\x01y\x18\x02 \x02(\r\x12\x10\n\x08is_shrub\x18\x03 \x02(\x08\x12\x10\n\x08material\x18\x04 \x01(\rB\x02H\x03'))




_PLANT = _descriptor.Descriptor(
  name='Plant',
  full_name='dfproto.Plant',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='x', full_name='dfproto.Plant.x', index=0,
      number=1, type=13, cpp_type=3, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='y', full_name='dfproto.Plant.y', index=1,
      number=2, type=13, cpp_type=3, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='is_shrub', full_name='dfproto.Plant.is_shrub', index=2,
      number=3, type=8, cpp_type=7, label=2,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='material', full_name='dfproto.Plant.material', index=3,
      number=4, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  serialized_start=24,
  serialized_end=89,
)

DESCRIPTOR.message_types_by_name['Plant'] = _PLANT

Plant = _reflection.GeneratedProtocolMessageType('Plant', (_message.Message,),
    {
      'DESCRIPTOR': _PLANT,
      # @@protoc_insertion_point(class_scope:dfproto.Plant)
    })


DESCRIPTOR.has_options = True
DESCRIPTOR._options = _descriptor._ParseOptions(descriptor_pb2.FileOptions(), b('H\003'))
# @@protoc_insertion_point(module_scope)
