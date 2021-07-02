"""
maya.cmds.workspaceControl('relicMayaMixinWindowWorkspaceControl', e=True, visible=True)
"""
# TODO: add option to parse the output and retrieve paths. (Batch export assets)
# subprocess.call([str(LOCATION / 'mayapy.exe'), str(root / 'alMayaStandalone.py'),\
#    "--pushDependencies", metadata_fields['Path'].as_posix()])

# -- Built-in --
import sys
import os
import time
import subprocess
import logging
import re

# -- Third-party --
import pymel.core as pm
import maya.cmds as cmds
import maya.utils as utils
from Qt.QtCore import *
from Qt.QtGui import *
from Qt.QtWidgets import *

relic_location = os.environ['relic_location']
packages_location = '{}/pypackages27'.format(relic_location)
sys.path.append(relic_location)
sys.path.append(packages_location)

from OpenGL.GL import *
from parse_maya.binary import MayaBinaryParser
from sequencePath import sequencePath as Path
import numpy as np

# -- App --
import shiboken2
import maya.OpenMayaUI as omui
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
#import maya.OpenMaya as OpenMaya

# -- Module --
#import asset_library.file_io as file_io
from library.widgets.relationshipView import linkViewWidget
from library.widgets.main import searchableDock
from library.widgets.assets import assetListView
import library.config as config

from gltfExporter import GLTFExport

# -- Globals --
TOKEN_REGEX = re.compile(r'\<\S+\>')
preferences = config.Preferences()
if not 'relicMixinWindow' in globals():
    relicMixinWindow = None

# -- Logging --
FORMAT = '%(asctime)-10s %(filename)s: %(funcName)10s %(message)s'
logging.basicConfig(format=FORMAT)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class MbInfo(MayaBinaryParser):

    tags = []

    def on_requires_plugin(self, plugin, version):
        if not str(plugin) == 'stereoCamera':
            name = re.sub(config.RE_SOFTWARE, "", (str(plugin) + str(version)))
            self.tags.append({'Name': name, 'Type': 2})

    def on_file_info(self, key, value):
        if str(key) == 'product':
            name = re.sub(config.RE_SOFTWARE, "", str(value))
            self.tags.append({'Name': name, 'Type': 1})


def getMainWindows():
    mainWindow = shiboken2.wrapInstance(long(omui.MQtUtil.mainWindow()), QWidget)
    panel = shiboken2.wrapInstance(
        #long(omui.MQtUtil.findControl("modelPanel4")), QWidget
        long(omui.MQtUtil.findControl("relicMayaMixinWindow")), QWidget
    )
    return (mainWindow, panel)


def assetDropAction(asset):
    log.debug("Processing item {} in plugin".format(asset))
    filepath = asset.local_path
    class_index = getattr(asset, 'class')

    if class_index == config.AREA_LIGHT:
        light = pm.shadingNode("VRayLightRectShape", asLight=True)
        light.setAttr("useRectTex", 1)
        texture = pm.shadingNode("file", asTexture=True)
        texture.setAttr("fileTextureName", str(filepath))
        pm.connectAttr(
            texture.name() + ".outColor", light.name() + ".rectTex", force=True
        )
        light.select()

    elif class_index == config.IES:
        light = pm.shadingNode("VRayLightIESShape", asLight=True)
        light.setAttr("iesFile", str(filepath).replace("/", "\\"))
        light.select()

    elif class_index == config.IBL_PROBE:
        light = pm.shadingNode("VRayLightDomeShape", asLight=True)
        light.setAttr("useDomeTex", 1)
        texture = pm.shadingNode("file", asTexture=True)
        texture.setAttr("fileTextureName", str(filepath))
        pm.connectAttr(
            texture.name() + ".outColor", light.name() + ".domeTex", force=True
        )
        light.select()

    elif class_index == config.MODEL:
        model = pm.system.createReference(
            str(filepath),
            loadReferenceDepth="all",
            mergeNamespacesOnClash=False,
            deferReference=True,
            namespace="AL_{}_".format(asset.name),
        )
    elif class_index == config.TEXTURE:
        texture = pm.shadingNode("file", asTexture=True)
        texture.setAttr("fileTextureName", str(filepath))

    elif str(filepath).endswith('.mel'):
        pm.mel.eval('source "{}";'.format(filepath))

    elif str(filepath).endswith('.py'):
        import maya.app.general.executeDroppedPythonFile as alTempEDPF
        alTempEDPF.executeDroppedPythonFile(str(filepath), "")
        del alTempEDPF

    elif str(filepath).endswith('.ma') or \
        str(filepath).endswith('.mb'):
        model = pm.system.createReference(
            str(filepath),
            loadReferenceDepth="all",
            mergeNamespacesOnClash=False,
            deferReference=True,
            namespace="AL_{}_".format(asset.name),
        )
        
    log.debug('Finished {}'.format(asset.name))

def iterateUnresolvedAssets():
    yield None
    """
    for node in nuke.allNodes():
        if not node.knob('AssetLibrary') and node.Class() == 'Group':
            data = {
                'category': node.knob('alcategory').value(),
                'Id': node.knob('alid').value()
            }
            yield data
    """

def processUnresolvedAssets(item, link):
    pass

def export_selection(metadata_fields):
    """Exports an asset/component from maya's selection into the library

    Arguments:
        metadata_fields (dict): metadata dictionary fields to populate

    Returns:
        dict -- modified metadata_fields
    """

    original_selection = pm.ls(sl=True)
    if not original_selection:
        pm.mel.eval(
            'confirmDialog -title "Make Selection" \
            -message "Requires an object selection";'
        )
        return

    if len(original_selection) != 1:
        selection = original_selection[0]
    else:
        selection = original_selection
    class_name = config.ASSET_CLASSES[metadata_fields['Class']]
    metadata_fields['Polycount'] = getPolyCount(original_selection)
    file_path = metadata_fields['Path']
    generateThumbnails(selection, file_path)
    metadata_fields['Path'] = file_path.parents(0) / (file_path.name + '.mb')
    pm.select(original_selection, r=True)
    pm.mel.eval(
        'file -force -options "v=0;" -typ "mayaBinary" -pr -es "{}";'.format(
            metadata_fields['Path']
        )
    )

    # Get Maya version and plugins as tags from exported file.
    mb_info = MbInfo(stream=open(str(metadata_fields['Path']), "rb"), info_only=True)
    mb_info.parse()
    metadata_fields['tags'] = mb_info.tags

    # If exporting as a model generate a gltf from the proxy.
    pm.select(selection, r=True)
    if class_name == "Model":
        gltf_path = file_path.path.with_name(metadata_fields['Name'] + '_preview.gltf')
        GLTFExport(gltf_path.as_posix())
    else:
        metadata_fields.pop("Polycount")

    dependent_files = getAllPaths()
    return (metadata_fields, dependent_files)


def generateThumbnails(selection, file_path):
    # Make turntable orbit camera
    orbitCameraShape = pm.createNode("camera")
    orbitCameraShape.focalLength.set(55)
    orbitCamera = orbitCameraShape.listRelatives(p=True)[0].rename("orbitCam")
    pm.mel.eval("lookThroughModelPanel {} modelPanel4;".format(orbitCamera))
    pm.setAttr("hardwareRenderingGlobals.multiSampleEnable", 1)
    pm.viewFit(selection)
    center = pm.objectCenter(selection, gl=True)
    pm.move(
        center[0], center[1], center[2], orbitCamera + ".rotatePivot", absolute=True
    )
    pm.setKeyframe(orbitCamera, at="rotate", t=['1'], ott="linear", itt="linear")
    rotateY = orbitCamera.ry.get() + 360
    pm.setKeyframe(
        orbitCamera, at="rotateY", t=['36'], ott="linear", itt="linear", v=rotateY
    )

    # Create turntable and single thumbnail
    pm.displayPref(wsa="none")
    pm.mel.eval("lookThroughModelPanel {}  modelPanel4;".format(orbitCamera))
    icon_path = "{}_icon.jpg".format(file_path)
    captureViewport(save=icon_path)
    pm.mel.eval(
        'playblast -st 1 -et 36 -format qt -compression "H.264" \
        -quality 100 -f "{}_icon.mp4" -w 384 -h 256 -fp false \
        -viewer false -offScreen -showOrnaments 0 -forceOverwrite;'.format(
            file_path
        )
    )
    # Cleanup
    pm.displayPref(wsa="full")
    pm.delete(orbitCamera)


def getPolyCount(selection):
    selection = selection[0]
    meshes = []
    polyCount = None
    if pm.nodeType(selection) == "transform":
        meshes.append(selection.listRelatives(ad=True, type="mesh"))

    pm.select(meshes, r=True)
    polyCount = pm.polyEvaluate(face=True)

    return polyCount


def doRepath(new_root, library_storage, unresolved=False):
    pm.filePathEditor(refresh=True)
    if not unresolved:
        replaceTokens()
    # Gets all nodes with file inputs with unresolved switch.
    node_list = pm.filePathEditor(
        q=True, ao=True, listFiles="", unresolved=unresolved
    )
    repath = alPath(new_root).parent
    if node_list:
        for x in node_list:
            # if regular node path is a file attribute
            try:
                old_path = alPath(pm.getAttr(x))
            except: # Must be a reference file instead
                old_path = pm.referenceQuery(x, wcn=True, filename=True)

            # If the file is from the library storage repath.
            if str(old_path).startswith(str(library_storage)):
                pm.filePathEditor(x, repath=repath, force=True, recursive=True)
            elif unresolved: # if maya can't find it and will use the repath
                pm.filePathEditor(x, repath=repath, force=True, recursive=True)
    return True


def replaceTokens():
    # Gets all unresolved file input nodes.
    node_list = pm.filePathEditor(
        q=True, ao=True, listFiles="", unresolved=True
    )
    if node_list:
        for x in node_list:
            try:
                old_path = alPath(pm.getAttr(x), checksequence=1)
            except:
                pass

            # If the file is from the library storage repath.
            if str(old_path).startswith(str(library_storage)) and old_path.sequence_path:
                pm.setAttr(x, str(old_path.sequence_path).replace('*', '1001'))

    pm.filePathEditor(refresh=True)
    return True


def applyRepath(new_root, library_storage=None):
    log.debug('Applying Repath using root: {}, and library storage: {}'.format(new_root, library_storage))
    utils.executeInMainThreadWithResult(doRepath, new_root, library_storage, unresolved=False)
    # Loads the reference so we can apply the repath to new unresolved
    # nodes with file paths
    pm.loadReference(str(new_root))
    utils.executeInMainThreadWithResult(doRepath, new_root, library_storage, unresolved=True)


def getAllPaths(library_only=False):
    """Retrieves all paths in the current Maya Scene.

    Parameters
    ----------
    library_only : bool, optional
        Only gets the paths that are from the Relic Library Storages, by default False

    Returns
    -------
    list
        list of file paths
    """
    return_list = []
    pm.filePathEditor(refresh=True)
    node_types = pm.filePathEditor(q=True, ao=True, listFiles="")
    if node_types:
        for x in node_types:
            # Replace UDIMs with first in sequence (Must start at 1001).
            try:
                path = re.sub(TOKEN_REGEX, '1001', pm.getAttr(x))
            except Exception:
                path = pm.referenceQuery(x, wcn=True, filename=True)
            # Check if the path starts with the library storage root path.
            if library_only:
                if path.startswith(str(preferences.local_storage)):
                    return_list.append(path)
            else:
                return_list.append(path)

    return return_list


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


class RelicPanel(MayaQWidgetDockableMixin, QWidget):
    def __init__(self, parent=None):
        super(RelicPanel, self).__init__(parent=parent)
        self.setWindowTitle('Relic Assets')

        self.scene_assets_view = linkViewWidget(self)
        for x in self.scene_assets_view.findChildren(assetListView):
            x.expandable = False
        self.scene_assets_view.setObjectName('RelicSceneAssets')
        #self.assets_view.selmod.selectionChanged.connect(self.loadAssetData)
        dock = searchableDock('- LINKS - ')
        dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        dock.searchInput.connect(self.scene_assets_view.filterAll)
        dock.setWidget(self.scene_assets_view)

        layout = QVBoxLayout()
        self.scrollArea = QScrollArea(self)
        self.scrollArea.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setMinimumSize(QSize(46,46))
        self.scrollArea.setWidget(dock)
        layout.addWidget(self.scrollArea)

        self.setLayout(layout)
    
    def loadAssetData(self, selection):
        sender = self.sender()
        if selection.isEmpty():
            print('empty')

def DockableWidgetUIScript(restore=False):
    ''' When the control is restoring, the workspace control has already been created and
        all that needs to be done is restoring its UI.
    '''
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
    menu_name = "Relic"
    if pm.menu(menu_name, query=1, exists=1):
        pm.deleteUI(menu_name)

    control = 'relicMayaMixinWindowWorkspaceControl'
    if cmds.workspaceControl(control, q=True, exists=True):
        cmds.deleteUI(control, control=True)

def createRelicMenus():
    menu_name = "Relic"
    removeRelicMenus()
    relicMenu = cmds.menu(menu_name, parent='MayaWindow', tearOff=True, label=menu_name)
    pm.menuItem(parent=relicMenu, label="Relic Scene Assets", command=DockableWidgetUIScript)


class RelicDropCallback(omui.MExternalDropCallback):
    instance = None

    def __init__(self):
        omui.MExternalDropCallback.__init__(self)

    def externalDropCallback(self, doDrop, controlName, data):
        retstring = "External Drop:  doDrop = {},  controlName = {}".format(
            doDrop,
            controlName,
        )
        """
        # Mouse buttons
        data.mouseButtons() & omui.MExternalDropData.kLeftButton
        data.mouseButtons() & omui.MExternalDropData.kMidButton
        data.mouseButtons() & omui.MExternalDropData.kRightButton

        # Key modifiers
        data.keyboardModifiers() & omui.MExternalDropData.kShiftModifier
        data.keyboardModifiers() & omui.MExternalDropData.kControlModifier
        data.keyboardModifiers() & omui.MExternalDropData.kAltModifier
        """
        #print(data.formats())

        if data.hasFormat(b'application/x-relic') and doDrop and data.hasUrls():
            drop_script = data.urls()[0]
            #if drop_script.endswith('.pyw'):
            #    with open(drop_script, 'rb') as fp:
            #        script = fp.read()
            #        exec(script, None, {'pathd': drop_script})
            #    return True

            with open(drop_script, 'rb') as fp:
                script = fp.read()
                exec(script, None, {'assets': data.text(), 'pathd': drop_script})
            return True

        """
        if data.hasHtml()
        if data.hasColor()
            color = data.color()
            color = (%d, %d, %d, %d)" % (color.r, color.g, color.b, color.a)
        if data.hasImage():
            str += (", image = true")
        """
        return omui.MExternalDropCallback.kMayaDefault


def initializePlugin(plugin):
    try:
        createRelicMenus()
        RelicDropCallback.instance = RelicDropCallback()
        omui.MExternalDropCallback.addCallback(RelicDropCallback.instance)
        sys.stdout.write("Successfully registered RelicMayaPlugin\n")
    except Exception:
        relicMixinWindow = None
        sys.stderr.write("Failed to register RelicMayaPlugin\n")
        raise


def uninitializePlugin(plugin):
    try:
        removeRelicMenus()
        omui.MExternalDropCallback.removeCallback(RelicDropCallback.instance)
        sys.stdout.write("Successfully deregistered RelicMayaPlugin\n")
    except Exception:
        relicMixinWindow = None
        sys.stderr.write("Failed to deregister RelicMayaPlugin\n")
        raise
