"""
-- USAGE --
import maya.cmds as cmds
cmds.loadPlugin('relicMayaPlugin')
cmds.loadPlugin('P:/Code/Relic/library/plugins/relicMaya/relicMayaPlugin.py')
cmds.relic(export=True)
"""

import sys
import subprocess
import re
import json
import os
from functools import partial
from pprint import pprint

# -- Third-party --
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

# -- App --
import shiboken2
import maya.OpenMayaUI as omui
import maya.api.OpenMaya as om
import maya.cmds as cmds
import maya.utils as utils
import maya.mel as mel
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin


# -- Globals --
MENU_NAME = "Relic"
TOKEN_REGEX = re.compile(r'\<\S+\>')
ANUM_REGEX = re.compile(r"[^A-Za-z0-9]")
IGNORE_PLUGINS = ['stereoCamera']
if not 'relicMixinWindow' in globals():
    relicMixinWindow = None

# -- Module --
sys.path.append('P:/Code/Relic/library/plugins/Lib')
from relic_base import asset_views
from relic_base import asset_classes
from relic_base.ui.qtutil import updateWidgetProperty#, polymorphicItem
from sequencePath import sequencePath as Path
from relic_base.config import RELIC_PREFS, LOG, INGEST_PATH, INGEST_CLIENT, logFunction
import relic_base.config as config
#from OpenGL.GL import *
from gltfExporterFloat import GLTFExport
from relicDrop import RelicDropCallback
from relicTranslator import getSelectionDependencies

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
    for x in sel:
        if x not in ['initialShadingGroup', 'initialParticleSE']:
            cmds.sets(e=1, clear=x)

def exportSelection():
    """Exports an asset/component from maya's selection into the library
    """
    results = []
    original_selection = cmds.ls(sl=True)
    if not original_selection:
        cmds.confirmDialog(title="Make Selection", 
            message="Requires an object selection")
        return

    for selected in original_selection:
        asset = asset_classes.tempasset()
        asset.polycount = getPolyCount(selected)
        asset.name = selected.replace('|', '')
        asset.path = INGEST_PATH / asset.name / (asset.name + '.mb')
        asset.path.createParentFolders()
        asset.type = 1 # Component
        asset.category = 1 # Modeling

        generateThumbnails(selected, asset.path)

        file_infos = cmds.fileInfo(q=1)
        file_info = dict(zip(file_infos[::2], file_infos[1::2]))
        plugin_infos = cmds.pluginInfo(q=1, pluginsInUse=1)
        plugin_info = dict(zip(plugin_infos[::2], plugin_infos[1::2]))

        asset.tags = []
        for plugin, version in plugin_info.items():
            if plugin in IGNORE_PLUGINS:
                continue
            asset.tags.append({'name': '{}v{}'.format(plugin, version), 'type': 2})

        product = re.sub(ANUM_REGEX, '', file_info.get('product'))
        asset.tags.append({'name': product, 'type': 1})

        # Export the files using relative file paths in an undo chunk.
        with UndoThis():
            files, assets, assignment_map = getSelectionDependencies(selected)
            asset.dependencies = list(files)
            #asset.upstream = list(assets)
            asset.links = [x for x in assets.values()]

            # Export MaterialX material & assignments file
            cmds.select(selected, r=True)
            materialx_path = asset.path.suffixed('', '.mtlx')
            cmds.file(str(materialx_path), exportSelected=1, type='MaterialX')

            cmds.select(clear=1)    
            clearShading()
            cmds.select(selected, r=True)
            # Export the asset file.
            cmds.file(str(asset.path), force=1, options="v=0;", type="mayaBinary",
                preserveReferences=1, exportSelected=1)
            #GLTFExport(str(asset.path.suffixed('_preview', '.gltf')))

        asset.path = str(asset.path)
        pprint(asset.__dict__)
        results.append(asset.__dict__)

    INGEST_CLIENT.requestFileLoad(json.dumps(results))

    return results


def generateThumbnails(selection, file_path):
    # Make turntable orbit camera
    orbitCameraShape = cmds.createNode("camera")
    cmds.setAttr(orbitCameraShape + '.focalLength', 55)
    orbitCamera = cmds.listRelatives(orbitCameraShape, p=True)[0]
    cmds.rename(orbitCamera, "orbitCam")
    mel.eval("lookThroughModelPanel orbitCam modelPanel4;")
    cmds.setAttr("hardwareRenderingGlobals.multiSampleEnable", 1)
    cmds.viewFit(selection)
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


def getPolyCount(selection):
    meshes = []
    polyCount = None
    if cmds.nodeType(selection) == "transform":
        meshes.extend(cmds.listRelatives(
            selection, allDescendents=True, type="mesh", fullPath=1))

    cmds.select(meshes, r=True)
    polyCount = cmds.polyEvaluate(face=True)

    return polyCount


def doRepath(new_root, library_storage, unresolved=False):
    cmds.filePathEditor(refresh=True)
    if not unresolved:
        replaceTokens()
    # Gets all nodes with file inputs with unresolved switch.
    node_list = cmds.filePathEditor(
        query=True, attributeOnly=True, listFiles="", unresolved=unresolved
    )
    repath = alPath(new_root).parent
    if node_list:
        for x in node_list:
            # if regular node path is a file attribute
            try:
                old_path = alPath(cmds.getAttr(x))
            except: # Must be a reference file instead
                old_path = cmds.referenceQuery(x, wcn=True, filename=True)

            # If the file is from the library storage repath.
            if str(old_path).startswith(str(library_storage)):
                cmds.filePathEditor(x, repath=repath, force=True, recursive=True)
            elif unresolved: # if maya can't find it and will use the repath
                cmds.filePathEditor(x, repath=repath, force=True, recursive=True)
    return True

def replaceTokens():
    # Gets all unresolved file input nodes.
    node_list = cmds.filePathEditor(
        q=True, attributeOnly=True, listFiles="", unresolved=True
    )
    if node_list:
        for x in node_list:
            try:
                old_path = alPath(cmds.getAttr(x), checksequence=1)
            except:
                pass

            # If the file is from the library storage repath.
            if str(old_path).startswith(str(library_storage)) and old_path.sequence_path:
                cmds.setAttr(x, str(old_path.sequence_path).replace('*', '1001'))

    cmds.filePathEditor(refresh=True)
    return True

def applyRepath(new_root, library_storage=None):
    log.debug('Applying Repath using root: {}, and library storage: {}'.format(new_root, library_storage))
    utils.executeInMainThreadWithResult(doRepath, new_root, library_storage, unresolved=False)
    # Loads the reference so we can apply the repath to new unresolved
    # nodes with file paths
    cmds.file(loadReference=str(new_root))
    utils.executeInMainThreadWithResult(doRepath, new_root, library_storage, unresolved=True)

@logFunction('Collecting Dependent Files')
def iterateScenePaths():
    """Iteratively Retrieves all paths in the current Maya Scene.
    """
    cmds.filePathEditor(refresh=True)
    node_types = cmds.filePathEditor(q=True, attributeOnly=True, listFiles="")
    if node_types:
        for attr in node_types:
            try:
                # Replace UDIMs with first in sequence (Must start at 1001).
                path = re.sub(TOKEN_REGEX, '1001', cmds.getAttr(attr))
            except Exception:
                # getAttr failed so it must be a reference node.
                path = cmds.referenceQuery(attr, wcn=True, filename=True)
            yield path, attr


# Check if the path starts with the library storage root path.
#if path.startswith(str(RELIC_PREFS.local_storage)):
#result.append(path)


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
    cmds.menuItem(parent=relicMenu, label="Relic Scene Assets", command=DockableWidgetUIScript)
    export_cmd = lambda x : cmds.relic(export=1)
    cmds.menuItem(parent=relicMenu, label="Export Selection As Asset", command=export_cmd)

class RelicCmd(om.MPxCommand):
    # -- Meta --
    kName = 'relic'

    # -- Flags --
    kExportShort = '-ex'
    kExportLong = '-export'
    kCollectShort = '-cp'
    kCollectLong = '-collect'

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def create():
        return RelicCmd()

    @staticmethod
    def newSyntax():
        syntax = om.MSyntax()
        syntax.addFlag(RelicCmd.kExportShort, RelicCmd.kExportLong)
        syntax.addFlag(RelicCmd.kCollectShort, RelicCmd.kCollectLong)
        return syntax

    def doIt(self, args):
        parser = om.MArgParser(self.syntax(), args)
        if parser.isFlagSet(self.kExportLong):
            exportSelection()
        elif parser.isFlagSet(self.kCollectLong):
            for path, attr in iterateScenePaths():
                print(path, attr)



def initializePlugin(obj):
    plugin = om.MFnPlugin(obj)
    try:
        plugin.registerCommand(RelicCmd.kName,
                               RelicCmd.create,
                               RelicCmd.newSyntax)
        createRelicMenus()
        relicMixinWindow = DockableWidgetUIScript()
        RelicDropCallback.INSTANCE = RelicDropCallback(relicMixinWindow)
        omui.MExternalDropCallback.addCallback(RelicDropCallback.INSTANCE)
        sys.stdout.write("Successfully registered RelicMayaPlugin\n")
    except Exception:
        relicMixinWindow = None
        sys.stderr.write("Failed to register RelicMayaPlugin\n")
        raise


def uninitializePlugin(obj):
    plugin = om.MFnPlugin(obj)
    try:
        plugin.deregisterCommand(RelicCmd.kName)
        removeRelicMenus()
        omui.MExternalDropCallback.removeCallback(RelicDropCallback.INSTANCE)
        sys.stdout.write("Successfully deregistered RelicMayaPlugin\n")
    except Exception:
        relicMixinWindow = None
        sys.stderr.write("Failed to deregister RelicMayaPlugin\n")
        raise
