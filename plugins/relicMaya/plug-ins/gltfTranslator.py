import json
import time
import struct
import os
import base64
import shutil
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import maya.api.OpenMaya as om
import maya.mel as mel
from pprint import pprint

# The bufferView target that the GPU buffer should be bound to.
ARRAY_BUFFER = 34962  # eg vertex data
ELEMENT_ARRAY_BUFFER = 34963  # eg index data
WORLDSPACE = om.MSpace.kWorld
OBJECTSPACE = om.MSpace.kObject


def removeTriangulateNodes():
    triNodes = cmds.ls(type='polyTriangulate')
    cmds.delete(triNodes)

class ResourceFormats(object):
    EMBEDDED = 'embedded'
    SOURCE = 'source'
    BIN = 'bin'

class ClassPropertyDescriptor(object):
    def __init__(self, fget):
        self.fget = fget

    def __get__(self, obj, klass=None):
        if klass is None:
            klass = type(obj)
        return self.fget.__get__(obj, klass)()

    def __set__(self, obj, value):
        raise AttributeError("can't set attribute")

def classproperty(func):
    if not isinstance(func, (classmethod, staticmethod)):
        func = classmethod(func)
    return ClassPropertyDescriptor(func)

class ExportSettings(object):
    file_format = 'gltf'
    resource_format = 'bin'
    out_file = ''
    _out_dir = ''
    _out_basename = ''

    @classmethod
    def set_defaults(cls):
        cls.file_format = 'glb'
        cls.resource_format = 'bin'
        cls.out_file = ''

    @classproperty
    def out_bin(cls):
        return cls.out_basename + '.bin'

    @classproperty
    def out_basename(cls):
        base, ext = os.path.splitext(cls.out_file)
        cls._out_basename = os.path.basename(base)
        return cls._out_basename

    @classproperty
    def out_dir(cls):
        cls._out_dir = os.path.dirname(cls.out_file)
        return cls._out_dir


class GLTFExport(object):
    def __init__(self, file_path, resource_format='bin'):
        self.output = {
            "asset": {
                "version": "2.0",
                "generator": "maya-glTFExport",
            }
        }
        ExportSettings.set_defaults()
        Scene.set_defaults()
        Node.set_defaults()
        Mesh.set_defaults()
        Buffer.set_defaults()
        BufferView.set_defaults()
        Accessor.set_defaults()

        ExportSettings.out_file = file_path
        ExportSettings.resource_format = resource_format

        basename, ext = os.path.splitext(ExportSettings.out_file)

        ExportSettings.file_format = ext[1:]

        if not os.path.exists(ExportSettings.out_dir):
            os.makedirs(ExportSettings.out_dir)

        scene = Scene()

        # we only support exporting single scenes,
        # so the first scene is the active scene
        self.output['scene'] = 0
        if Scene.instances:
            self.output['scenes'] = Scene.instances
        if Node.instances:
            self.output['nodes'] = Node.instances
        if Mesh.instances:
            self.output['meshes'] = Mesh.instances
        if Buffer.instances:
            self.output['buffers'] = Buffer.instances
        if BufferView.instances:
            self.output['bufferViews'] = BufferView.instances
        if Accessor.instances:
            self.output['accessors'] = Accessor.instances

        if not Scene.instances[0].nodes:
            raise RuntimeError('Scene is empty.  No file will be exported.')

        with open(ExportSettings.out_file, 'w') as outfile:
            json.dump(self.output, outfile, cls=GLTFEncoder)



class GLTFEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ExportItem):
            return obj.to_json()
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)

class ExportItem(object):
    def __init__(self, name=None):
        self.name = name


class Scene(ExportItem):
    '''Needs to add itself to scenes'''
    instances = []
    maya_nodes = None

    @classmethod
    def set_defaults(cls):
        cls.instances = []

    def __init__(self, name="defaultScene"):
        super(Scene, self).__init__(name=name)
        self.index = len(Scene.instances)
        Scene.instances.append(self)
        self.nodes = []
        self.maya_nodes = cmds.ls(assemblies=True, long=True, defaultNodes=False)
        for transform in self.maya_nodes:
            if transform not in ['persp', 'top', 'front', 'side']:
                self.nodes.append(Node(transform))
        #removeTriangulateNodes()

    def to_json(self):
        scene_def = {"name": self.name, "nodes":[node.index for node in self.nodes]}
        return scene_def



class Node(ExportItem):
    '''Needs to add itself to nodes list, possibly node children, and possibly scene'''
    instances = []
    maya_node = None
    matrix = None
    translation = None
    rotation = None
    scale = None
    mesh = None

    @classmethod
    def set_defaults(cls):
        cls.instances = []

    def __init__(self, maya_node):
        self.maya_node = maya_node
        name = cmds.ls(maya_node, shortNames=True)[0]
        super(Node, self).__init__(name=name)
        self.index = len(Node.instances)
        Node.instances.append(self)
        self.children = []
        self.translation = cmds.getAttr(self.maya_node + '.translate')[0]
        self.rotation = self._get_rotation_quaternion()
        self.scale = cmds.getAttr(self.maya_node + '.scale')[0]
        maya_children = cmds.listRelatives(self.maya_node, children=True, fullPath=True)
        if maya_children:
            for child in maya_children:
                childType = cmds.objectType(child)
                if childType == 'mesh' and not cmds.getAttr(child + ".intermediateObject"):
                    mesh = Mesh(child)
                    self.mesh = mesh
                elif childType == 'transform':
                    node = Node(child)
                    self.children.append(node)


    def _get_rotation_quaternion(self):
        obj=OpenMaya.MObject()
        #make a object of type MSelectionList
        sel_list=OpenMaya.MSelectionList()
        #add something to it
        #you could retrieve this from function or the user selection
        sel_list.add(self.maya_node)
        #fill in the MObject
        sel_list.getDependNode(0,obj)
        #check if its a transform
        if (obj.hasFn(OpenMaya.MFn.kTransform)):
            quat = OpenMaya.MQuaternion()
            #then we can add it to transfrom Fn
            #Fn is basically the collection of functions for given objects
            xform=OpenMaya.MFnTransform(obj)
            xform.getRotation(quat)
            # glTF requires normalize quat
            quat.normalizeIt()

        py_quat = [quat[x] for x in range(4)]
        return py_quat

    def to_json(self):
        node_def = {}
        if self.matrix:
            node_def['matrix'] = self.matrix
        if self.translation:
            node_def['translation'] = self.translation
        if self.rotation:
            node_def['rotation'] = self.rotation
        if self.scale:
            node_def['scale'] = self.scale
        if self.children:
            node_def['children'] = [child.index for child in self.children]
        if self.mesh:
            node_def['mesh'] = self.mesh.index
        return node_def


class Mesh(ExportItem):
    '''Needs to add itself to node and its accesors to meshes list'''
    instances = []
    maya_node = None
    indices_accessor = None
    position_accessor = None
    normal_accessor = None
    tangent_accessor = None
    texcoord0_accessor = None

    @classmethod
    def set_defaults(cls):
        cls.instances = []

    def __init__(self, maya_node):
        self.maya_node = maya_node
        name = cmds.ls(maya_node, shortNames=True)[0]
        super(Mesh, self).__init__(name=name)
        self.index = len(Mesh.instances)
        Mesh.instances.append(self)
        cmds.polyTriangulate(self.maya_node, ch=1)
        self._getMeshData()

    def to_json(self):
        mesh_def = {"primitives" : [ {
                        "mode": 4,
                        "attributes" : {
                          "POSITION" : self.position_accessor.index,
                          "NORMAL": self.normal_accessor.index,
                          "TANGENT": self.tangent_accessor.index,
                          "TEXCOORD_0": self.texcoord0_accessor.index
                        },
                        "indices" : self.indices_accessor.index,
                      } ]
                    }
        return mesh_def



    def _getMeshData(self):
        # Populate selection list
        selectionList = om.MSelectionList()
        selectionList.add(self.maya_node)
        om.MGlobal.setActiveSelectionList(selectionList)
        mesh = selectionList.getDagPath(0)
        try:
            # Get Bounding Data
            boundingBox = om.MFnDagNode(mesh).boundingBox
            meshFn = om.MFnMesh(mesh)

            # Get Point data
            inMeshMPointArray = meshFn.getFloatPoints(WORLDSPACE)
            vertexCountArray, vertexIndexArray = meshFn.getVertices() # MInt
            #triangleCountArray, triangleIndexArray = meshFn.getTriangles() # MInt
            # Get Normal data
            inMeshNormalArray = meshFn.getVertexNormals(False, WORLDSPACE)

            # Get UV data
            U_MFloatArray, V_MFloatArray = meshFn.getUVs() #MFloat
            uvCountArray, uvIndexArray = meshFn.getAssignedUVs() # MInt
            # Re-index the Uv's based on vertex indices.
            ct = len(V_MFloatArray)
            reordered_points = om.MPointArray().setLength(ct)
            reordered_normals = om.MFloatVectorArray().setLength(ct)
            reordered_tangents = om.MFloatVectorArray().setLength(ct)
            reordered_uvs = list(zip(U_MFloatArray, V_MFloatArray))

            for i, x in enumerate(vertexIndexArray):
                norm = inMeshNormalArray[x]
                point = inMeshMPointArray[x]
                reordered_normals[uvIndexArray[i]] = norm
                reordered_points[uvIndexArray[i]] = point

            third = 0

            for idx in uvIndexArray:
                if third == 0:
                    i0 = idx
                    third = 1
                    continue
                elif third == 1:
                    i1 = idx
                    third = 2
                    continue
                else:
                    i2 = idx 

                #print('processing triangle face indices', i0, i1, i2)
                p0 = reordered_points[i0]
                p1 = reordered_points[i1]
                p2 = reordered_points[i2]

                w0 = reordered_uvs[i0]
                w1 = reordered_uvs[i1]
                w2 = reordered_uvs[i2]

                # Edges 1 and 2 
                e1 = p1 - p0
                e2 = p2 - p0

                # U (S) or (X) Coord
                x1 = w1[0] - w0[0]
                x2 = w2[0] - w0[0]
                # V (T) or (Y) Coord
                y1 = w1[1] - w0[1]
                y2 = w2[1] - w0[1]

                denom = (x1 * y2) - (x2 * y1)
                r = denom if (1.0 / denom) else 0.0

                t = om.MFloatVector((e1 * y2 - e2 * y1) * r)

                reordered_tangents[i0] = t.normal()
                reordered_tangents[i1] = t.normal()
                reordered_tangents[i2] = t.normal()
                
                # Reset the UV-centric Face index
                third = 0

            for i in xrange(len(reordered_tangents)):
                n = reordered_normals[i]
                t = reordered_tangents[i]
                zero = om.MFloatVector(0.0, 0.0, 0.0)
                if zero != t:
                    nt_dot = n*t
                    t = (t - n * nt_dot).normalize()
                else:
                    sign = -1.0 if (n[2] < 0.0) else 1.0
                    a = -1.0 / (sign + n[2])
                    b = n[0] * n[1] * a
                    t = om.MFloatVector(
                        1.0 + sign * n[0] * n[0] * a,
                        sign * b,
                        -sign * n[0]
                    )  


            indices = uvIndexArray
            positions = reordered_points
            normals = reordered_normals
            tangents = reordered_tangents
            uvs = reordered_uvs
        except Exception as exerr:
            print('ERROR', exerr)

        # Write Data to bin file
        if not len(Buffer.instances):
            primary_buffer = Buffer('primary_buffer')
        else:
            primary_buffer = Buffer.instances[0]

        if len(positions) >= 0xffff:
            idx_component_type = ComponentTypes.UINT
            mult = 4
        else:
            mult = 2
            idx_component_type = ComponentTypes.USHORT


        self.indices_accessor = Accessor(indices, "SCALAR", idx_component_type, ELEMENT_ARRAY_BUFFER, primary_buffer, name=self.name + '_idx')
        self.position_accessor = Accessor(positions, "VEC3", ComponentTypes.FLOAT, ARRAY_BUFFER, primary_buffer, name=self.name + '_pos')
        self.normal_accessor = Accessor(normals, "VEC3", ComponentTypes.FLOAT, ARRAY_BUFFER, primary_buffer, name=self.name + '_norm')
        self.tangent_accessor = Accessor(tangents, "VEC3", ComponentTypes.FLOAT, ARRAY_BUFFER, primary_buffer, name=self.name + '_tang')
        self.texcoord0_accessor = Accessor(uvs, "VEC2", ComponentTypes.FLOAT, ARRAY_BUFFER, primary_buffer, name=self.name + '_uv')
        self.indices_accessor.min_ = [0]
        self.indices_accessor.max_ = [len(positions)]
        self.position_accessor.max_ = list(boundingBox.max)[:3]
        self.position_accessor.min_ =  list(boundingBox.min)[:3]

        integer_type = Accessor.component_type_codes[idx_component_type]*Accessor.type_codes['SCALAR']
        byteSize = 0
 
        with open(ExportSettings.out_dir + "/" + primary_buffer.uri, 'ab') as outfile:
            byte_length = (mult * len(indices))
            self._append_bytes(self.indices_accessor, primary_buffer, byte_length)
            for item in indices: # 4
                outfile.write(struct.pack('<' + integer_type, item))

            byte_length = (12 * len(positions))
            self._append_bytes(self.position_accessor, primary_buffer, byte_length)
            for item in positions: # 12
                item = list(item)[:3]
                outfile.write(struct.pack('<fff', *item))
            
            byte_length = (12 * len(normals))
            self._append_bytes(self.normal_accessor, primary_buffer, byte_length)
            for item in normals: # 12
                outfile.write(struct.pack('<fff', *item))

            byte_length = (8 * len(uvs))
            self._append_bytes(self.texcoord0_accessor, primary_buffer, byte_length)
            for item in uvs: # 8
                outfile.write(struct.pack('<ff', *item))

            byte_length = (12 * len(tangents))
            self._append_bytes(self.tangent_accessor, primary_buffer, byte_length)
            for item in tangents: # 12
                outfile.write(struct.pack('<fff', *item))

            # Optionally faster struct packing
            #newlist = list(chain.from_iterable(data))
            #byte_str += struct.pack('%sf' % len(newlist), *newlist)

            # 4-byte-aligned
            #aligned_len = (len(self.byte_str) + 3) & ~3
            #for i in range(aligned_len - len(self.byte_str)):
            #    byte_str += '0'

    @staticmethod
    def _append_bytes(accessor, buffer, byte_length):
        # update global buffer offset
        buffer.byte_length += byte_length
        # update local buffer offset
        accessor.buffer_view.byte_length = byte_length
        accessor.buffer_view.byte_offset = (buffer.byte_length - byte_length)


class Buffer(ExportItem):
    instances = []
    byte_str = b''
    uri = ''

    @classmethod
    def set_defaults(cls):
        cls.instances = []

    def __init__(self, name=None):
        super(Buffer, self).__init__(name=name)
        self.index = len(Buffer.instances)
        self.byte_length = 0
        Buffer.instances.append(self)
        if (ExportSettings.file_format == 'gltf'
                and ExportSettings.resource_format == ResourceFormats.BIN):
            self.uri = ExportSettings.out_bin

    def __len__(self):
        return len(self.byte_str)

    def to_json(self):
        #buffer_def = {"byteLength" : len(self)}
        buffer_def = {"byteLength" : self.byte_length}
        if self.uri and ExportSettings.resource_format == ResourceFormats.BIN:
            buffer_def['uri'] = self.uri
        elif ExportSettings.resource_format in [ResourceFormats.EMBEDDED, ResourceFormats.SOURCE]:
            buffer_def['uri'] = "data:application/octet-stream;base64," + base64.b64encode(self.byte_str)
        # no uri for GLB
        return buffer_def


class BufferView(ExportItem):
    instances = []
    buffer = None
    byte_offset = None
    byte_length = None
    target = None

    @classmethod
    def set_defaults(cls):
        cls.instances = []

    def __init__(self, buffer, byte_offset, target=None, name=None):
        super(BufferView, self).__init__(name=name)
        self.index = len(BufferView.instances)
        BufferView.instances.append(self)
        self.buffer = buffer
        self.byte_offset = byte_offset
        self.byte_length = len(buffer) - byte_offset
        self.target = target

    def to_json(self):
        buffer_view_def = {
          "buffer" : self.buffer.index,
          "byteOffset" : self.byte_offset,
          "byteLength" : self.byte_length,
        }
        if self.target:
            buffer_view_def['target'] = self.target

        return buffer_view_def


class ComponentTypes(object):
    USHORT = 5123
    UINT = 5125
    FLOAT = 5126


class Accessor(ExportItem):
    instances = []
    buffer_view = None
    byte_offset = 0
    component_type = None
    count = None
    type_ = None
    src_data = None
    max_  = None
    min_ = None
    type_codes = {
        "SCALAR":1,
        "VEC2":2,
        "VEC3":3,
        "VEC4":4
    }
    component_type_codes = {
        ComponentTypes.USHORT:"H", # unsigned short
        ComponentTypes.UINT:"I", # unsigned int
        ComponentTypes.FLOAT:"f"  # float
    }

    @classmethod
    def set_defaults(cls):
        cls.instances = []

    def __init__(self, data, type_, component_type, target, buffer, name=None):
        super(Accessor, self).__init__(name=name)
        self.index = len(Accessor.instances)
        Accessor.instances.append(self)
        self.src_data = data
        self.component_type = component_type
        self.type_= type_
        byte_code = self.component_type_codes[component_type]*self.type_codes[type_]

        buffer_end = len(buffer)
        self.buffer_view = BufferView(buffer, buffer_end, target)

    def to_json(self):
        accessor_def = {
          "bufferView" : self.buffer_view.index,
          "byteOffset" : self.byte_offset,
          "componentType" : self.component_type,
          "count" : len(self.src_data),
          "type" : self.type_
        }
        if self.max_:
            accessor_def['max'] = self.max_
        if self.min_:
            accessor_def['min'] = self.min_
        return accessor_def


if __name__ == "__main__":
    try:
        os.remove('P:/Projects/pbrtest/scenes/tangenttest.gltf')
        os.remove('P:/Projects/pbrtest/scenes/tangenttest.bin')
    except: pass
    GLTFExport('P:/Projects/pbrtest/scenes/tangenttest.gltf')
