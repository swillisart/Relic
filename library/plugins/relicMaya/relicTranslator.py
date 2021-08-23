import re
import sys
import os
from pprint import pprint

import maya.cmds as cmds
import maya.api.OpenMaya as om

import MaterialX as mx

from relic_base import config

TOKEN_REGEX = re.compile(r'\<\S+\>')
 
def createMaterialWithAssignments(matxdoc, look, shader, geo_assginments):
    collection_name = 'c_'+ shader
    collection_a = matxdoc.addCollection(collection_name)
    collection_a.setIncludeGeom(','.join(geo_assginments))

    # Create a material that instantiates the shader.
    material = matxdoc.addMaterialNode(shader)
    assign = look.addMaterialAssign('', material.getName())
    assign.setCollection(collection_a)

def getFileAttributePaths(node_name, collection):
    file_attributes = cmds.listAttr(node_name, usedAsFilename=True)
    if file_attributes:
        for attribute in file_attributes + ['filePath']:
            if cmds.attributeQuery(attribute, node=node_name, exists=1):
                attr = node_name + '.' + attribute
                path = cmds.getAttr(attr, x=1)
                if path:
                    if not os.path.exists(path):
                        continue
                    new_path = re.sub(TOKEN_REGEX, '1001', path)
                    collection.add(new_path)
                    filename = os.path.basename(path)
                    # Set the relative path for the library.
                    subfolder = config.getAssetSourceLocation(path)
                    changed_path = subfolder + '/' + filename
                    cmds.setAttr(attr, changed_path, type='string')

def collectAssetIfRef(dep_node, assets):
    if dep_node.isFromReferencedFile:
        try:
            asset_path = cmds.referenceQuery(dep_node.name(), filename=True)
            ref_node = cmds.referenceQuery(dep_node.name(), rfn=True)
        except:
            return
        #hash_attr = ref_node + '.' + 'RELIC_hash'
        id_attr = ref_node + '.' + 'RELIC_id'
        category_attr = ref_node + '.' + 'RELIC_category'
        if cmds.attributeQuery('RELIC_id', node=ref_node, exists=1):
            assets[asset_path] = {
                'id': cmds.getAttr(id_attr),
                #'hash': cmds.getAttr(hash_attr),
                'category': cmds.getAttr(category_attr),
            }

def recurseUpstreamConnections(dep_node, visited, files, assets):
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
                    collectAssetIfRef(dep_node, assets)
                    continue
                #print('\t..(node)', dep_node.name(), new_node.apiTypeStr)
                node_name = dep_node.uniqueName()
                print('test', node_name)
                getFileAttributePaths(node_name, files)
                recurseUpstreamConnections(dep_node, visited, files, assets)

def collectMaterialFiles(dep_node, visited_nodes, files, assets):
    """Collects the files of the dependency node's files by
    recursively iterating the node connections (MPlugs)

    Parameters
    ----------
    dep_node : om.MFnDependencyNode

    visited_nodes : list
        list of visited nodes so it avoids a circular dependency loop
    files : set
        the resulting collection of file paths as a unique set of valaues
    """
    plug_array = dep_node.getConnections()
    collectAssetIfRef(dep_node, assets)

    for plug in plug_array:
        obj = plug.attribute()
        if obj.apiType() == om.MFn.kTypedAttribute:
            for src in plug.connectedTo(True, False):
                new_node = src.node()
                if new_node.apiType() != om.MFn.kMesh:
                    dep_node.setObject(new_node)
                    collectAssetIfRef(dep_node, assets)
                    #print('node', new_node.apiTypeStr)
                    #print('\tplug', plug.name(), plug.source())
                    recurseUpstreamConnections(dep_node, visited_nodes, files, assets)

def getSelectionDependencies(selected):
    assignment_map = {}
    dependent_files = set()
    dependent_assets = {}
    visited_nodes = []
    selectList =  om.MSelectionList()

    descendents = cmds.listRelatives(selected, allDescendents=True, fullPath=1)
    for node in descendents:
        selectList.add(node)

    iterSel = om.MItSelectionList(selectList, om.MFn.kDagNode)
    dep_node = om.MFnDependencyNode()


    while not iterSel.isDone():
        material_name = None
        node = iterSel.getDependNode()
        dag = iterSel.getDagPath()

        dep_node.setObject(node)
        collectAssetIfRef(dep_node, dependent_assets)

        if node.apiType() == om.MFn.kMesh:
            # Iterate over dependency graph plugs
            mItDependencyGraph = om.MItDependencyGraph(
                dag.node(),
                om.MItDependencyGraph.kPlugLevel)

            while not mItDependencyGraph.isDone():
                plug_node = mItDependencyGraph.currentNode()
                dep_node.setObject(plug_node)
                collectAssetIfRef(dep_node, dependent_assets)
                collectMaterialFiles(
                    dep_node, visited_nodes, dependent_files, dependent_assets)

                # It has a ShadingGroup.
                if plug_node.hasFn(om.MFn.kShadingEngine):
                    dep_node.setObject(plug_node)
                    if not dep_node.isFromReferencedFile:
                        material_name = dep_node.name()
                    #if dep_node.isFromReferencedFile:
                    #    print('REF Query', cmds.referenceQuery(dep_node.name(), filename=True))

                mItDependencyGraph.next()
            if material_name:
                meshes = assignment_map.get(material_name)
                if meshes:
                    meshes.append(dag.fullPathName())
                else:
                    assignment_map[material_name] = [dag.fullPathName()]

        elif node.apiType() != om.MFn.kTransform:
            # USD Shapes don't collect unless directly accessed via filePath attribute.
            dag_path = dag.fullPathName()
            #getFileAttributePaths(dag_path, dependent_assets) 

        #print(dep_node.classification(node.apiTypeStr))
        #print("Name: %s, Type: %s" % (dep_node.name(), node.apiTypeStr))
        #types = om.MGlobal.getFunctionSetList(node)
        iterSel.next()

    #pprint(assignment_map)
    #print(dependent_files)
    #print(dependent_assets)
    return dependent_files, dependent_assets, assignment_map

if __name__=='__main__':
    getSelectionDependencies(cmds.ls(sl=True))
