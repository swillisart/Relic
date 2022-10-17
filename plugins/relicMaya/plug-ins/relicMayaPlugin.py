"""USAGE
import maya.cmds as cmds
cmds.loadPlugin('relicMayaPlugin')
cmds.loadPlugin('P:/Code/Relic/plugins/relicMaya/relicMayaPlugin.py')
"""

import sys
import re
import json
import os
from functools import partial

# -- Third-party --
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

# -- App --
import shiboken2
import maya.OpenMayaUI as omui
import maya.api.OpenMaya as om
import maya.cmds as cmds
import maya.mel as mel
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

# -- First-party --
from relic_base import (asset_classes, asset_views)
from relic.local import (Nuketools, Category, FileType, TempAsset, INGEST_PATH, getAssetSourceLocation)
from relic.scheme import (AssetType, TagType, UserType)
from sequence_path import Path
from intercom import Client

# -- Module --
from relicDrop import RelicDropCallback
from relicTranslator import getSelectionDependencies

# -- Globals --
MENU_NAME = 'Relic'
ANUM_REGEX = re.compile(r"[^A-Za-z0-9]")
IGNORE_PLUGINS = ['stereoCamera']
RELIC_CLIENT = Client('relic')
if not 'relicMixinWindow' in globals():
    relicMixinWindow = None

#from OpenGL.GL import *
#from gltfExporterFloat import GLTFExport

def maya_useNewAPI():
    # Using the Maya Python API 2.0.
    pass

class UndoThis(object):
    """Convenience Undo chunk context manager
    """
    def __enter__(self):
        # Create an undo chunk.
        cmds.undoInfo(openChunk=True)

    def __exit__(self, x_type, x_value, x_tb):
        # Close the chunk and undo everything.
        cmds.undoInfo(closeChunk=True)
        cmds.undo()

def clearShading():
    """Removes all objects from Maya's shading groups / engines.
    """
    sel = cmds.ls(type='shadingEngine')
    for item in sel:
        if item not in ['initialShadingGroup', 'initialParticleSE']:
            cmds.sets(e=1, clear=item)

def exportSelection(asset_type):
    """Exports an asset/component from maya's selection into the library
    """
    results = []
    original_selection = cmds.ls(selection=1)
    if not original_selection:
        cmds.confirmDialog(title="Make Selection", 
            message="Requires an object selection")
        return

    for selected in original_selection:
        asset = TempAsset()
        asset.name = selected.replace('|', '')
        asset.path = INGEST_PATH / asset.name / (asset.name + '.mb')
        asset.path.createParentFolders()
        asset.type = asset_type
        asset.category = 1 # Modeling

        setMeshMetadata(selected, asset)
        generateThumbnails(selected, asset.path)

        file_infos = cmds.fileInfo(q=1)
        file_info = {}
        if file_infos:
            file_info = dict(zip(file_infos[::2], file_infos[1::2]))

        plugin_infos = cmds.pluginInfo(q=1, pluginsInUse=1)
        plugin_info = {}
        if plugin_infos:
            plugin_info = dict(zip(plugin_infos[::2], plugin_infos[1::2]))

        asset.tags = []
        for plugin, version in plugin_info.items():
            if plugin in IGNORE_PLUGINS:
                continue
            asset.tags.append({'name': '{}v{}'.format(plugin, version), 'type': 2})

        mayaver = file_info.get('product')
        if mayaver:
            product = re.sub(ANUM_REGEX, '', mayaver)
            asset.tags.append({'name': product, 'type': 1})

        # Export the files using relative file paths in an undo chunk.
        with UndoThis():
            # Get all dependent files and asset while assigning all other nodes
            # a parent namespace to link maya edits to.
            files, assets = getSelectionDependencies(selected)
            asset.dependencies = list(files)
            #asset.upstream = list(assets)
            asset.links = [x for x in assets.values()]

            # Export MaterialX material & assignments file
            cmds.select(selected, r=True)
            materialx_path = asset.path.suffixed('', '.mtlx')
            cmds.file(str(materialx_path), exportSelected=1, type='MaterialX')

            clearShading()
            cmds.select(selected, r=True)
            # Export the asset file.
            cmds.file(str(asset.path), force=1, options="v=0;", type="mayaBinary",
                preserveReferences=1, exportSelected=1)
            #GLTFExport(str(asset.path.suffixed('_preview', '.gltf')))

        asset.path = str(asset.path)
        results.append(asset.__dict__)

    RELIC_CLIENT.sendPayload(json.dumps(results))

    return results


def generateThumbnails(selection, file_path):
    # Make turntable orbit camera
    orbitCameraShape = cmds.createNode("camera")
    cmds.setAttr(orbitCameraShape + '.focalLength', 55)
    orbitCamera = cmds.listRelatives(orbitCameraShape, p=True)[0]
    cmds.rename(orbitCamera, "orbitCam")
    mel.eval("lookThroughModelPanel orbitCam modelPanel4;")
    cmds.setAttr("hardwareRenderingGlobals.multiSampleEnable", 1)
    cmds.viewFit(selection, f=0.9)
    center = cmds.objectCenter(selection, gl=True)
    cmds.move(
        center[0], center[1], center[2], "orbitCam.rotatePivot", absolute=True
    )
    cmds.setKeyframe('orbitCam', at="rotate", t=['1'], ott="linear", itt="linear")
    rotateY = cmds.getAttr('orbitCam.ry') + 360
    cmds.setKeyframe(
        'orbitCam', at="rotateY", t=['36'], ott="linear", itt="linear", v=rotateY
    )

    # Create turntable and single thumbnail
    cmds.displayPref(wsa="none")
    mel.eval("lookThroughModelPanel orbitCam modelPanel4;")
    #captureViewport(save=icon_path)
    mel.eval(
        'playblast -st 1 -et 1 -format image -compression jpg \
        -percent 100 -quality 100 -cf "{}" -w 288 -h 192 -fp false \
        -viewer false -offScreen -showOrnaments 0 -forceOverwrite;'.format(
            file_path.suffixed('_icon', '.jpg')
        )
    )
    mov_path = file_path.suffixed('_icon', '.mov')
    mel.eval(
        'playblast -st 1 -et 36 -format qt -compression "H.264" \
        -percent 100 -quality 100 -f "{}" -w 288 -h 192 -fp false \
        -viewer false -offScreen -showOrnaments 0 -forceOverwrite;'.format(
            mov_path
        )
    )
    os.rename(str(mov_path), str(file_path.suffixed('_icon', '.mp4')))
    # Cleanup
    cmds.displayPref(wsa="full")
    cmds.delete('orbitCam')


def setMeshMetadata(selection, asset):
    meshes = []
    # Set the poly count
    if cmds.nodeType(selection) == "transform":
        meshes.extend(cmds.listRelatives(
            selection, allDescendents=True, type="mesh", fullPath=1))

    cmds.select(meshes, r=True)
    asset.polycount = cmds.polyEvaluate(face=True)

    # set the bounding box
    size3 = []
    for axis in cmds.polyEvaluate(boundingBox=1):
        size3.append(str(round(abs(axis[0]) + axis[1], 2)))
    asset.resolution = ' x '.join(size3)


def captureViewport(save=False):
    cmds.getPanel(withFocus=True)
    view = omui.M3dView.active3dView()
    view.display()
    glReadBuffer(GL_FRONT)
    w, h = view.portWidth(), view.portHeight()
    data = glReadPixels(0, 0, w, h, GL_RGBA, GL_UNSIGNED_BYTE)
    #if save:
    #    icon_img = file_io.makeIconQt(data, w, h)
    #    icon_img.save(save)


class RelicPanel(MayaQWidgetDockableMixin, asset_views.RelicSceneForm):
    def __init__(self, parent=None):
        super(RelicPanel, self).__init__(parent=parent)
        self.setWindowTitle('Relic Assets')

    def refreshSceneAssets(self):
        all_nodes_iter = om.MItDependencyNodes()
        dep_node = om.MFnDependencyNode()
        while not all_nodes_iter.isDone():
            dep_node.setObject(all_nodes_iter.thisNode())
            if dep_node.hasAttribute('RELIC_id'):
                nodename = dep_node.name()
                cat_id = cmds.getAttr(nodename + '.RELIC_category')
                constructor = asset_classes.getCategoryConstructor(cat_id)
                asset = constructor(category=cat_id)
                asset.name = str(nodename.split('RN')[0])
                asset.id = cmds.getAttr(nodename + '.RELIC_id')
                asset.filehash = cmds.getAttr(nodename + '.RELIC_hash')
                asset.progress = [1,1]
                if not self.group_widget.assetInModel(asset):
                    asset.fetch(on_complete=partial(self.group_widget.addAsset, asset))

            all_nodes_iter.next()

    def show(self, *args, **kwargs):
        self.refreshSceneAssets()
        super(RelicPanel, self).show(*args, **kwargs)


def DockableWidgetUIScript(restore=False):
    """ When the control is restoring, the workspace control has already been created and
        all that needs to be done is restoring its UI.
    """
    global relicMixinWindow

    if restore == True:
        # Grab the created workspace control with the following.
        restoredControl = omui.MQtUtil.getCurrentParent()

    if relicMixinWindow is None:
        # Create a relic mixin widget for the first time
        relicMixinWindow = RelicPanel()     
        relicMixinWindow.setObjectName('relicMayaMixinWindow')
        
    if restore == True:
        # Add relic mixin widget to the workspace control
        mixinPtr = omui.MQtUtil.findControl(relicMixinWindow.objectName())
        omui.MQtUtil.addWidgetToMayaLayout(long(mixinPtr), long(restoredControl))
    else:
        # Create a workspace control for the mixin widget by passing all the needed parameters.
        # See workspaceControl command documentation for all available flags.
        relicMixinWindow.show(dockable=True, height=520, width=380, uiScript='DockableWidgetUIScript(restore=True)')
        
    return relicMixinWindow

def removeRelicMenus():
    if cmds.menu(MENU_NAME, query=1, exists=1):
        cmds.deleteUI(MENU_NAME)

    control = 'relicMayaMixinWindowWorkspaceControl'
    if cmds.workspaceControl(control, q=True, exists=True):
        cmds.deleteUI(control, control=True)

def createRelicMenus():
    removeRelicMenus()
    relicMenu = cmds.menu(MENU_NAME, parent='MayaWindow', tearOff=True, label=MENU_NAME)
    cmds.menuItem(parent=relicMenu, label='Scene Assets Panel', command=DockableWidgetUIScript)
    export_cmd = lambda x : exportSelection(AssetType.ASSET)
    cmds.menuItem(parent=relicMenu, label='Export Asset', command=export_cmd)
    variation_cmd = lambda x : exportSelection(AssetType.VARIANT)
    cmds.menuItem(parent=relicMenu, label='Export Variation', command=variation_cmd)
    archive_cmd = lambda x : archiveScene()
    cmds.menuItem(parent=relicMenu, label='Archive Scene', command=archive_cmd)

def initializePlugin(obj):
    plugin = om.MFnPlugin(obj)
    try:
        createRelicMenus()
        relicMixinWindow = DockableWidgetUIScript()
        RelicDropCallback.INSTANCE = RelicDropCallback(relicMixinWindow)
        omui.MExternalDropCallback.addCallback(RelicDropCallback.INSTANCE)
        sys.stdout.write("Successfully registered RelicMayaPlugin\n")
        cmds.loadPlugin('materialXTranslator')
    except Exception:
        relicMixinWindow = None
        sys.stderr.write("Failed to register RelicMayaPlugin\n")
        raise


def uninitializePlugin(obj):
    plugin = om.MFnPlugin(obj)
    try:
        removeRelicMenus()
        omui.MExternalDropCallback.removeCallback(RelicDropCallback.INSTANCE)
        sys.stdout.write("Successfully deregistered RelicMayaPlugin\n")
        cmds.unloadPlugin('materialXTranslator')
    except Exception:
        relicMixinWindow = None
        sys.stderr.write("Failed to deregister RelicMayaPlugin\n")
        raise
