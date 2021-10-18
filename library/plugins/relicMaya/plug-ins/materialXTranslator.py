import os
import re
import sys

# -- Application -- 
import maya.cmds as cmds
import maya.mel as mel
import maya.api.OpenMaya as om
import maya.OpenMayaMPx as OpenMayaMPx

# -- Third-Party --
import MaterialX as mx


# -- Globals --
class Remap(object):
    __slots__ = ['positions', 'values', 'interpolations', 'colors']
    kPosition = 0
    def __init__(self):
        self.positions = []
        self.values = []
        self.colors = []
        self.interpolations = []

class Namespace(str):
    """Convenience Namespace context manager
    """
    def __init__(self, namespace):
        self._namespace = namespace
    
    def __str__(self):
        return self._namespace

    def __enter__(self):
        # Set Maya's active namespace to relative asset 
        cmds.namespace(relativeNames=1)
        try:
            cmds.namespace(set=self._namespace)
        except:pass

    def __exit__(self, x_type, x_value, x_tb):
        # Set Maya's namespace back to aboslute root 
        try:
            cmds.namespace(set=':')
        except:pass
        cmds.namespace(relativeNames=0)

kPluginTranslatorTypeName = 'MaterialX'

class MaterialXTranslator(OpenMayaMPx.MPxFileTranslator):

    def __init__(self):
        OpenMayaMPx.MPxFileTranslator.__init__(self)
        self.kwargs = {}

    def haveWriteMethod(self):
        return True

    def haveReadMethod(self):
        return True

    def haveNamespaceSupport(self):
        return False

    def haveReferenceMethod(self):
        return False

    def filter(self):
        return '*.mtlx'

    def defaultExtension(self):
        return 'mtlx'

    def writer(self, fileObject, optionString, accessMode):
        fullName = fileObject.resolvedFullName()
        try:
            if accessMode == OpenMayaMPx.MPxFileTranslator.kExportAccessMode:
                exportMaterialX(cmds.ls(type='mesh'), fullName)
            elif accessMode == OpenMayaMPx.MPxFileTranslator.kExportActiveAccessMode:
                exportMaterialX(cmds.ls(sl=True), fullName)

        except:
            sys.stderr.write("Failed to write file information\n")
            raise


    def reader(self, fileObject, optionString, accessMode):
        fullName = fileObject.resolvedFullName()
        try:
            loadMaterialX(fullName)
        except:
            sys.stderr.write("Failed to read file information\n")
            raise

    def identifyFile(self, fileObject, buffer, size):
        basename, ext = os.path.splitext(fileObject.fullName())
        if ext == '.mtlx':
            return OpenMayaMPx.MPxFileTranslator.kIsMyFileType
        else:
            return OpenMayaMPx.MPxFileTranslator.kNotMyFileType

def translatorCreator():
    return OpenMayaMPx.asMPxPtr(MaterialXTranslator())

def initializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)#, "Res-Arts", "1.0", "Any")
    try:
        mplugin.registerFileTranslator(
            kPluginTranslatorTypeName, None, translatorCreator,   
            )
    except:
        sys.stderr.write("Failed to register translator: %s" % kPluginTranslatorTypeName)
        raise

def uninitializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterFileTranslator(kPluginTranslatorTypeName)
    except:
        sys.stderr.write("Failed to deregister translator: %s" % kPluginTranslatorTypeName)
        raise


def createMaterialWithAssignments(look, shader, geo_assginments, xdoc):
    collection_name = 'c_'+ shader
    collection_a = xdoc.addCollection(collection_name)
    collection_a.setIncludeGeom(','.join(geo_assginments))

    # Create a material that instantiates the shader.
    #material = xdoc.addMaterialNode(shader)
    #refStandardSrf = material.addShaderRef('SR_standardSrf', 'standard_surface')
    #assign = look.addMaterialAssign('', material.getName())
    assign = look.addMaterialAssign('', shader)
    assign.setCollection(collection_a)
    #return refStandardSrf

def recurseUpstreamConnections(dep_node, visited, upstream, mx_graph):
    absnode = dep_node.absoluteName()
    if absnode == ':defaultColorMgtGlobals':
        return
    xnode = mx_graph.getNode(dep_node.absoluteName())

    if not xnode:
        xnode = mx_graph.addNode(dep_node.typeName, absnode, "mayaNode")

    upstream_node = mx_graph.getNode(upstream)

    for index in range(dep_node.attributeCount()):
        attr_obj = dep_node.attribute(index)
        attr = om.MFnAttribute(attr_obj)
        if attr_obj.apiType() == om.MFn.kMessageAttribute:
            continue

        mplug = dep_node.findPlug(attr.name, False)
        # Maya crashes on explicit attributes. DEFECT
        if attr.name.startswith('explicit') or absnode == ':defaultColorMgtGlobals':
            continue

        if mplug.isSource:
            #upstream = ':' + mplug.source().name().split('.')[0]
            attr_str = '{}.{}'.format(absnode, attr.name)
            attr_type = cmds.getAttr(attr_str, type=1)
            value = cmds.getAttr(attr_str)
            #print('source', mplug.name())
            try:
                output = xnode.addOutput(attr.name, attr_type)
            except:
                output = xnode.addOutput(attr.name+'_out', attr_type)

            for dplug in mplug.destinations():
                _node, _attr = str(dplug.name()).split('.')
                destination_plug_name = ':' + _node
                #print('dest', destination_plug_name)
                destination_node = mx_graph.getNode(destination_plug_name)
                if not destination_node:
                    new_node = om.MFnDependencyNode(dplug.node())
                    destination_node = mx_graph.addNode(new_node.typeName, destination_plug_name, "mayaNode")
                destination_node.setConnectedNode(_attr, xnode)
                destination_node.setConnectedOutput(_attr, output)

                    
            continue
        elif attr.readable and attr.storable:
            pass
        else:
            continue

        if mplug.isNull:#not mplug.isFreeToChange():
            continue
            
        try:
            plug_parent = mplug.parent()
            if plug_parent.isConnected or plug_parent.isChild:
                continue
        except: # Plug is not a child of a compound parent.
            pass

        changed = mplug.getSetAttrCmds(valueSelector=om.MPlug.kNonDefault, useLongNames=1)#om.MPlug.kChanged)

        if not changed and not mplug.isConnected:
            continue

        #print('gah', absnode,mplug.name())
        if mplug.isDestination:
            pass
            #print('destination', mplug.source().name(), '>>', mplug.name())
           
            #print(_node, _attr)
            #if not mplug.node() in visited:
            #    _node, _attr = mplug.source().name().split('.')

            #    attr_str = '{}.{}'.format(absnode, attr.name)
            #    attr_type = cmds.getAttr(attr_str, type=1)
            #    value = cmds.getAttr(attr_str)
            #    print('visited!', _node, _attr)
            #continue

        if mplug.isArray:
            #print('arrays', mplug.name())

            remap = Remap()
            for el_index in range(mplug.numElements()):
                knot = mplug.elementByLogicalIndex(el_index)
                if knot.isCompound and knot.isElement:
                    # Assume array is of position, float, and interpolation.
                    # used by maya's "remap" nodes.
                    for ch_index in range(knot.numChildren()):
                        child_plug = knot.child(ch_index)
                        plug_data = child_plug.asMDataHandle()
                        plug_data_type = plug_data.numericType()

                        if ch_index == remap.kPosition: # Positions always first
                            remap.positions.append(child_plug.asFloat())
                        elif plug_data_type == om.MFnData.kVectorArray: # 11
                                val = plug_data.asFloat()
                                remap.values.append(val)
                        elif plug_data_type == om.MFnData.kComponentList: # 13
                                val = plug_data.asFloat3()
                                remap.colors.extend(val)
                        elif plug_data_type == om.MFnData.kInvalid: # 0
                            remap.interpolations.append(child_plug.asInt())
                        #print('\t', child_plug.name(), plug_data_type)

            attr_name = mplug.name().split('.')[1]
            curve_node = mx_graph.addNode('curve', absnode+'.'+attr_name, "curve")
            curve_node.setInputValue('position'.format(attr_name), remap.positions, 'floatarray')
            if remap.colors:
                curve_node.setInputValue('color'.format(attr_name), remap.colors, 'floatarray')
            else:
                curve_node.setInputValue('value'.format(attr_name), remap.values, 'floatarray')
                curve_node.setInputValue('interpolation'.format(attr_name), remap.interpolations, 'integerarray')
            continue
        elif mplug.isCompound:
            #print('compounds', mplug.name())
            attr_str = '{}.{}'.format(absnode, attr.name)
            try:
                value = cmds.getAttr(attr_str)
                xnode.setInputValue(attr.name, str(value[0])[1:-1], 'float3') #'color3')
            except Exception as exerr:
                print(exerr)
            #for plug_child_indice in range(mplug.numChildren()):
            #    child_plug = mplug.child(plug_child_indice)
            #    print('\tchild:', child_plug)
            continue
        elif mplug.isElement:
            #print('elements', mplug.name())
            continue
        elif mplug.isChild:
            #print('parent', mplug.name())
            continue
        
        #print('constantAttr:', absnode, attr.name)
        attr_str = '{}.{}'.format(absnode, attr.name)
        attr_type = cmds.getAttr(attr_str, type=1)
        value = cmds.getAttr(attr_str)
        xnode.setInputValue(attr.name, str(value),  attr_type)

        #print(absnode, attr.name, changed)
        #print(mplug.isDefaultValue()) #crashes maya

    # Get Connection Of Shape Node
    for plug in dep_node.getConnections():
        obj = plug.attribute()

        # Ignoring connected message MPlug types
        if obj.apiType() != om.MFn.kMessageAttribute:
            # Get source plugs
            for dst in plug.connectedTo(True, False):
                # If our node is already accounted for in the visited [list] we can skip this
                new_node = dst.node()
                if new_node in visited:
                    continue
                
                visited.append(new_node)

                dep_node.setObject(new_node)
                if dep_node.isFromReferencedFile:
                    continue
                #print('/t..(node)', dep_node.name(), new_node.apiTypeStr)
                recurseUpstreamConnections(dep_node, visited, absnode, mx_graph)


def collectMaterialFiles(dep_node, visited_nodes, upstream, mx_graph):
    """Collects the files of the dependency node's files by
    recursively iterating the node connections (MPlugs)

    Parameters
    ----------
    dep_node : om.MFnDependencyNode

    visited_nodes : list
        list of visited nodes so it avoids a circular dependency loop
    """
    plug_array = dep_node.getConnections()
    for plug in plug_array:
        obj = plug.attribute()
        if obj.apiType() == om.MFn.kTypedAttribute:
            for src in plug.connectedTo(True, False):
                new_node = src.node()
                if new_node.apiType() != om.MFn.kMesh:
                    dep_node.setObject(new_node)
                    #print('node', new_node.apiTypeStr)
                    #print('/tplug', plug.name(), plug.source())
                    recurseUpstreamConnections(dep_node, visited_nodes, upstream, mx_graph)

def exportMaterialX(selected, file_path):
    """Stores shading networks and material assignments from a 
    maya mesh selection to a file.

    Parameters
    ----------
    selected : list
        maya selection list
    file_path : sequencePath
        the '.mtlx' MaterialX output file path for storing shaders and assignments 

    """
    xdoc = mx.createDocument()
    mx_graph = xdoc.addNodeGraph()

    assignment_map = {}
    visited_nodes = []
    selectList =  om.MSelectionList()

    descendents = cmds.listRelatives(selected, allDescendents=True, fullPath=1) or []
    for node in descendents:
        selectList.add(node)

    iterSel = om.MItSelectionList(selectList, om.MFn.kDagNode)
    dep_node = om.MFnDependencyNode()


    while not iterSel.isDone():
        material_name = None
        node = iterSel.getDependNode()
        dag = iterSel.getDagPath()

        dep_node.setObject(node)

        if node.apiType() == om.MFn.kMesh:
            # Iterate over dependency graph plugs
            mItDependencyGraph = om.MItDependencyGraph(
                dag.node(),
                om.MItDependencyGraph.kPlugLevel,
                )

            while not mItDependencyGraph.isDone():
                plug_node = mItDependencyGraph.currentNode()

                # It has a ShadingGroup.
                if plug_node.hasFn(om.MFn.kShadingEngine):
                    dep_node.setObject(plug_node)
                    collectMaterialFiles(
                        dep_node, visited_nodes, dep_node.absoluteName(), mx_graph)
                    dep_node.setObject(plug_node)
                    if not dep_node.isFromReferencedFile:
                        material_name = dep_node.absoluteName()


                mItDependencyGraph.next()
            if material_name:
                meshes = assignment_map.get(material_name)
                mesh_name = dag.fullPathName()
                if meshes:
                    meshes.append(mesh_name)
                else:
                    assignment_map[material_name] = [mesh_name]

        #print(dep_node.classification(node.apiTypeStr))
        #print("Name: %s, Type: %s" % (dep_node.absoluteName(), node.apiTypeStr))
        #types = om.MGlobal.getFunctionSetList(node)
        iterSel.next()

    cmds.select(clear=1)
    
    standard_look = xdoc.addLook('standard')
    #standardSrf = xdoc.addNodeDef('ND_standardSrf', 'surfaceshader', 'standard_surface')

    for material, assigned_meshes in assignment_map.items():
        createMaterialWithAssignments(
            standard_look, material, assigned_meshes, xdoc)
        cmds.select(material, add=1)

    # Write MaterialX document with node graph and assignments.
    mx.writeToXmlFile(xdoc, file_path)

def setColorCurveAttributes(elem, current_node):
    positions = elem.getInput('position').getValue()
    colors = elem.getInput('color').getValue()
    remainder = int(len(colors) / len(positions))
    check = '{node}[0].color_Position'.format(node=elem.getName())
    try:
        cmds.getAttr(check)
        pos_attr = '.color_Position'
        color_attr = '.color_Color'
    except:
        pos_attr = '.position'
        color_attr = '.color'

    for index in range(len(positions)):
        source_attr = '{node}[{i}]'.format(node=elem.getName(), i=index)
        cmds.setAttr(
            source_attr + pos_attr,
            positions[index],
        )
        indice = index*remainder
        cmds.setAttr(
            source_attr + color_attr,
            colors[indice],
            colors[indice+1],
            colors[indice+2],
            type="double3",
        )

def assignMaterials(xdoc, filename):
    look = xdoc.getLook('standard')
    mat_namespace = ':' + filename + '_mtlx'
    with Namespace(filename):
        for assignment in look.getMaterialAssigns():
            material_name = assignment.getMaterial()
            mx_geo = assignment.getCollection().getIncludeGeom().split(',')
            try:
                cmds.sets(mx_geo, e=1, fe=mat_namespace + material_name)
            except Exception as exerr:
                print('shader assignment error:', exerr)


def loadMaterialX(file_path):
    basepath, ext = os.path.splitext(file_path)
    filename = os.path.basename(basepath)
    xdoc = mx.createDocument()
    mx.readFromXmlFile(xdoc, file_path)
    mat_namespace = filename + '_mtlx:'
    all_nodes = []
    for elem in xdoc.traverseTree():
        if elem.isA(mx.Node) and elem.getType() == 'mayaNode':
            category = elem.getCategory()
            name = elem.getName()
            if category == 'shadingEngine':
                cmds.sets(name=name, empty=True, renderable=True, noSurfaceShader=True)
            else:
                cmds.shadingNode(category, name=name, asShader=1)
            all_nodes.append(name)
            # Maya does not automatically create these color management connections
            if category == 'file': 
                cmds.connectAttr(":defaultColorMgtGlobals.cme", "{}.cme".format(name))
                cmds.connectAttr(":defaultColorMgtGlobals.cfe", "{}.cmcf".format(name))
                cmds.connectAttr(":defaultColorMgtGlobals.cfp", "{}.cmcp".format(name))
                cmds.connectAttr(":defaultColorMgtGlobals.wsn", "{}.ws".format(name))

    current_node = None
    for elem in xdoc.traverseTree():
        if elem.isA(mx.Node) and elem.getType() == 'mayaNode':
            current_node = elem
        elif elem.isA(mx.Node) and elem.getType() == 'curve':
            colors = elem.getInput('color')
            if colors:
                setColorCurveAttributes(elem, current_node)
                continue
            
            values = elem.getInput('value').getValue()
            interpolations = elem.getInput('interpolation').getValue()
            positions = elem.getInput('position').getValue()
            for index in range(len(positions)):
                source_attr = '{node}[{i}]'.format(node=elem.getName(), i=index)
                cmds.setAttr(
                    source_attr,
                    positions[index],
                    values[index],
                    interpolations[index],
                    type="double3",
                )
        elif elem.isA(mx.Input) and elem.getType().endswith('array'):
            # Skip all array types
            continue
        elif current_node and elem.getCategory() == 'input':
            upstream_node = elem.getConnectedNode()
            output_name = elem.getOutputString().replace('_out', '')
            source_attr = '{node}.{attr}'.format(
                node=current_node.getName(), attr=elem.getName())
            if upstream_node:
                destination_attr = '{node}.{attr}'.format(
                    node=upstream_node.getName(), attr=output_name)
                cmds.connectAttr(destination_attr, source_attr)
            else:
                m_type = elem.getType()
                m_value = elem.getValue()
                cmd = 'setAttr "{attr}" -type "{type}" {val};'
                if m_type == 'float3':
                    m_value = m_value.replace(',', '')
                if m_type in ['short', 'float', 'enum']:
                    cmd = 'setAttr "{attr}" {val};'.format(
                            attr=source_attr,
                            val=m_value,
                            )
                elif m_type == 'string':
                    cmd = cmd.format(attr=source_attr, type=m_type, val='"{}"'.format(m_value))
                elif m_type == 'bool':
                    cmd = 'setAttr "{}" {};'.format(source_attr, int(bool(m_value)))
                else:
                    cmd = cmd.format(attr=source_attr, type=m_type, val=m_value)
                mel.eval(cmd)
    for x in all_nodes:
        try:
            cmds.rename(x, mat_namespace+x)
        except:pass
    assignMaterials(xdoc, filename)

if __name__ == '__main__':
    exportMaterialX(cmds.ls(sl=1), 'P:/Projects/USD_Materialx_Scratchpad/materialx_test/compound_test.mtlx')
    #loadMaterialX('P:/Projects/USD_Materialx_Scratchpad/materialx_test/compound_test.mtlx')