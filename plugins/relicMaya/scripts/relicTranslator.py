import re
import os
from glob import glob

import maya.cmds as cmds
import maya.api.OpenMaya as om
#maya_resources = om.MGlobal.getAbsolutePathToResources() -> <MAYA_RESOURCES>
# preserve sets om.MGlobal.getAssociatedSets()
from relic.local import INGEST_PATH, getAssetSourceLocation
from functools import partial

from sequence_path import SequencePath

REPLACE_TOKEN = partial(re.sub, SequencePath.TOKEN_REGEX)

def getFileAttributePaths(node_name, collection):
    file_attributes = cmds.listAttr(node_name, usedAsFilename=True)
    if not file_attributes:
        return
    for attribute in file_attributes + ['filePath']:
        if not cmds.attributeQuery(attribute, node=node_name, exists=1):
            continue
        attr = node_name + '.' + attribute
        path = cmds.getAttr(attr, x=1)
        if path:
            #TODO: This is for nonexistent textures and particularly the 
            # <MAYA_RESOURCES> token in defaultColorMgtGlobals.configFilePath
            # needs to handle relative paths images/sourceimages within the project too.
            if not os.path.exists(path):
                continue
            udim_path = REPLACE_TOKEN('.1001.', path)
            glob_path = REPLACE_TOKEN('.*.', path)
            for tiles in glob(glob_path):
                collection.add(tiles)
            filename = path.rsplit('/', 1)[-1]
            # Set the relative path for the library.
            subfolder = getAssetSourceLocation(path)
            changed_path = subfolder + '/' + filename
            cmds.setAttr(attr, changed_path, type='string')


def collectIfRef(dep_node, assets, files=None):
    if dep_node.isFromReferencedFile:
        try:
            try:
                node_name = dep_node.uniqueName()
            except:
                node_name = dep_node.name()
            asset_path = cmds.referenceQuery(node_name, filename=True)
            ref_node = cmds.referenceQuery(node_name, rfn=True)
        except:
            return
        #hash_attr = ref_node + '.' + 'RELIC_hash'
        id_attr = ref_node + '.' + 'RELIC_id'
        category_attr = ref_node + '.' + 'RELIC_category'
        basepath, ext = os.path.splitext(asset_path)
        if cmds.attributeQuery('RELIC_id', node=ref_node, exists=1):
            assets[asset_path] = {
                'id': cmds.getAttr(id_attr),
                #'hash': cmds.getAttr(hash_attr),
                'category': cmds.getAttr(category_attr),
            }
            try:
                cmds.parent(node_name, world=1)
            except:
                # Objects within a Reference's Hierarchy may not be reparented.
                return
            filename = os.path.basename(basepath)
            ref_edit_path = 'C:/Users/Resartist/.relic/ingest/{}.editMB'.format(filename)
            exclusion = cmds.ls('{}_mtlx::*'.format(filename))
            cmds.exportEdits(ref_edit_path, orn=ref_node, f=1, type='editMB',
                includeAnimation=1, includeShaders=1, includeSetAttrs=1,
                excludeNode=exclusion)
            files.add(ref_edit_path)

        elif not files or asset_path in files: # Skip paths already collected...
            return
        if ext not in ['.abc', '.usd']:
            return
        # Not a relic asset so add as dependent file
        files.add(asset_path)


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
                    collectIfRef(dep_node, assets)
                    continue
                #print('\t..(node)', dep_node.name(), new_node.apiTypeStr)
                try:
                    node_name = dep_node.uniqueName()
                except:
                    node_name = dep_node.name()
                #print('test', node_name)
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
    collectIfRef(dep_node, assets)

    for plug in plug_array:
        obj = plug.attribute()
        if obj.apiType() == om.MFn.kTypedAttribute:
            for src in plug.connectedTo(True, False):
                new_node = src.node()
                if new_node.apiType() != om.MFn.kMesh:
                    dep_node.setObject(new_node)
                    collectIfRef(dep_node, assets)
                    #print('node', new_node.apiTypeStr)
                    #print('\tplug', plug.name(), plug.source())
                    recurseUpstreamConnections(dep_node, visited_nodes, files, assets)


def getSelectionDependencies(selected):
    dependent_files = set()
    dependent_assets = {}
    visited_nodes = []
    selectList =  om.MSelectionList()

    selectList.add(selected)
    descendents = cmds.listRelatives(selected, allDescendents=True, fullPath=1)
    for node in descendents:
        selectList.add(node)

    iterSel = om.MItSelectionList(selectList, om.MFn.kDagNode)
    dep_node = om.MFnDependencyNode()


    while not iterSel.isDone():
        node = iterSel.getDependNode()
        dag = iterSel.getDagPath()

        dep_node.setObject(node)
        if node.apiType() == om.MFn.kMesh:
            # Iterate over dependency graph plugs
            mItDependencyGraph = om.MItDependencyGraph(
                dag.node(),
                om.MItDependencyGraph.kPlugLevel)

            while not mItDependencyGraph.isDone():
                plug_node = mItDependencyGraph.currentNode()
                dep_node.setObject(plug_node)
                collectIfRef(dep_node, dependent_assets)
                collectMaterialFiles(
                    dep_node, visited_nodes, dependent_files, dependent_assets)

                mItDependencyGraph.next()

        elif node.apiType() != om.MFn.kTransform:
            # USD Shapes don't collect unless directly accessed via filePath attribute.
            pass
            #dag_path = dag.fullPathName()
            #getFileAttributePaths(dag_path, dependent_assets) 
        elif node.apiType() == om.MFn.kTransform:
            collectIfRef(dep_node, dependent_assets, dependent_files)
    
        #print('epic',dep_node.classification(node.apiTypeStr))
        #print("Name: %s, Type: %s" % (dep_node.name(), node.apiTypeStr))
        #types = om.MGlobal.getFunctionSetList(node)
        iterSel.next()
    
    #print(dependent_files)
    #print(dependent_assets)
    return dependent_files, dependent_assets


if __name__=='__main__':
    getSelectionDependencies(cmds.ls(sl=True)[0])
