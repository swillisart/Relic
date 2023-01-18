"""USAGE
import maya.cmds as cmds
cmds.loadPlugin('relicMayaPlugin')
cmds.loadPlugin('P:/Code/Relic/plugins/relicMaya/relicMayaPlugin.py')
"""

import json
import os
import re
import sys
from functools import partial

# -- App --
import maya.api.OpenMaya as om
import maya.cmds as cmds
import maya.OpenMayaUI as omui
import shiboken2
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

# -- Third-party --
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

# -- First-party --
from sequence_path import Path
from relic.local import (INGEST_PATH, Category, FileType, Nuketools, TempAsset,
                         getAssetSourceLocation)
from relic.scheme import AssetType, TagType, UserType
from relic.plugin import views, networking, classes
from relic.qt.util import loadStylesheet

# -- Module --
from relicDrop import RelicDropCallback
from relicArchive import archiveScene
from relicTranslator import getSelectionDependencies
from relicUtilities import (UndoThis, clearAllShading, generateThumbnails,
                            setMeshMetadata)

# -- Globals --
MENU_NAME = 'Relic'
ANUM_REGEX = re.compile(r"[^A-Za-z0-9]")
IGNORE_PLUGINS = ['stereoCamera']

if not 'relicMixinWindow' in globals():
    relicMixinWindow = None

#from gltfExporterFloat import GLTFExport

def maya_useNewAPI():
    # Using the Maya Python API 2.0.
    pass

def exportSelection(asset_type):
    """Exports an asset/component from maya's selection into the library
    """
    results = []
    original_selection = cmds.ls(selection=True)
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
        asset.category = Category.MODELING.index

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

            clearAllShading()
            cmds.select(selected, r=True)
            # Export the asset file.
            cmds.file(str(asset.path), force=1, options="v=0;", type="mayaBinary",
                preserveReferences=1, exportSelected=1)
            #GLTFExport(str(asset.path.suffixed('_preview', '.gltf')))

        asset.path = str(asset.path)
        results.append(asset.asDict())

    return json.dumps(results)

def captureViewport(save=False):
    cmds.getPanel(withFocus=True)
    view = omui.M3dView.active3dView()
    view.display()
    #glPixelStorei(GL_PACK_ALIGNMENT, 1) # copied recently FROM NUKE 
    #glReadBuffer(GL_FRONT)
    #w, h = view.portWidth(), view.portHeight()
    #data = glReadPixels(0, 0, w, h, GL_RGBA, GL_UNSIGNED_BYTE)
    #if save:
    #    icon_img = file_io.makeIconQt(data, w, h)
    #    icon_img.save(save)

class RelicPanel(MayaQWidgetDockableMixin, views.RelicSceneForm):
    def __init__(self, parent=None):
        super(RelicPanel, self).__init__(parent=parent)
        self.setWindowTitle('Relic Assets')
        loadStylesheet(self, path=':app_style.qss')

    def refreshSceneAssets(self):
        all_nodes_iter = om.MItDependencyNodes()
        dep_node = om.MFnDependencyNode()
        while not all_nodes_iter.isDone():
            dep_node.setObject(all_nodes_iter.thisNode())
            if dep_node.hasAttribute('RELIC_id'):
                nodename = dep_node.name()
                cat_id = cmds.getAttr(nodename + '.RELIC_category')
                constructor = classes.getCategoryConstructor(cat_id)
                asset = constructor(category=cat_id)
                asset.name = str(nodename.split('RN')[0])
                asset.id = cmds.getAttr(nodename + '.RELIC_id')
                asset.filehash = cmds.getAttr(nodename + '.RELIC_hash')
                if not self.content.assetInModel(asset):
                    asset.fetch(on_complete=partial(self.content.addAsset, asset))

            all_nodes_iter.next()

    def deleteAsset(self, asset):
        pass


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
    payback = networking.tryLaunch
    relicMenu = cmds.menu(MENU_NAME, parent='MayaWindow', tearOff=True, label=MENU_NAME)
    cmds.menuItem(parent=relicMenu, label='Scene Assets Panel', command=DockableWidgetUIScript)
    cmds.menuItem(divider=True, dividerLabel='Export')
    export_cmd = lambda x : payback(exportSelection(AssetType.ASSET))
    cmds.menuItem(parent=relicMenu, label='Export Asset', command=export_cmd)
    variation_cmd = lambda x : payback(exportSelection(AssetType.VARIANT))
    cmds.menuItem(parent=relicMenu, label='Export Variation', command=variation_cmd)
    archive_cmd = lambda x : payback(archiveScene())
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
