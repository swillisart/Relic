import sys
import json

import maya.OpenMayaUI as omui
import maya.api.OpenMaya as om
import maya.cmds as cmds
import shiboken2

from relic_base import asset_classes, asset_views
from relic_base import config
from relic_base.config import LOG, logFunction

from sequencePath import sequencePath as Path

import MaterialX as mx

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
        cmds.namespace(set=self._namespace)

    def __exit__(self, x_type, x_value, x_tb):
        # Set Maya's namespace back to aboslute root 
        cmds.namespace(set=':')
        cmds.namespace(relativeNames=0)

# Using the Maya Python API 2.0.
def maya_useNewAPI():
    pass

def addRelicAttributes(asset):
    maya_ref = '{}RN'.format(asset.name)
    cmds.lockNode(maya_ref , lock=0)

    attr = 'RELIC_hash'
    cmds.addAttr(maya_ref, longName=attr, dataType='string')
    cmds.setAttr(maya_ref + '.' + attr, asset.filehash, edit=1, type='string')

    attr = 'RELIC_category'
    cmds.addAttr(maya_ref, longName=attr, attributeType='long')
    cmds.setAttr(maya_ref + '.' + attr, asset.category, edit=1)

    attr = 'RELIC_id'
    cmds.addAttr(maya_ref, longName=attr, attributeType='long')
    cmds.setAttr(maya_ref + '.' + attr, asset.id, edit=1)

class RelicDropCallback(omui.MExternalDropCallback):
    INSTANCE = None

    def __init__(self, relicMixinWindow):
        omui.MExternalDropCallback.__init__(self)
        self.relicPanel = relicMixinWindow

    def externalDropCallback(self, doDrop, controlName, data):
        retstring = "External Drop:  doDrop = {},  controlName = {}".format(
            doDrop,
            controlName,
        )
        """
        data.mouseButtons() & omui.MExternalDropData.kLeftButton
        data.mouseButtons() & omui.MExternalDropData.kMidButton
        data.mouseButtons() & omui.MExternalDropData.kRightButton
        data.keyboardModifiers() & omui.MExternalDropData.kShiftModifier
        data.keyboardModifiers() & omui.MExternalDropData.kControlModifier
        data.keyboardModifiers() & omui.MExternalDropData.kAltModifier
        """
        drop_script = data.urls()[0]
        assets = data.text()
        if data.hasFormat(b'application/x-relic') and data.hasUrls() and not doDrop:# and data.hasUrls():
            #files = []
            for key, values in json.loads(assets).items():
                constructor = getattr(asset_classes, str(key))
                for fields in values:
                    asset = constructor(**fields)
                    added = self.relicPanel.group_widget.addAsset(asset)
                    if added:
                        print(asset.upstream)
                        self.assetDropAction(asset)
                        #files.append(asset.path)
            self.relicPanel.group_widget.updateGroups()
            # Check the scene for unresolved library-dependent files.
            #dependent_files = getAllPaths(library_only=True)
            # If there are no direct files add the main file to search for <ASSET>_sources
            #if not dependent_files:
            #    dependent_files.extend(files)

            #LOG.debug('dependent files: {}'.format(dependent_files))
            return True

        #elif data.hasFormat(b'application/x-relic') and data.hasUrls() and doDrop:
        #    for key, values in json.loads(assets).items():
        #        constructor = getattr(asset_classes, str(key))
        #        for fields in values:
        #            asset = constructor(**fields)
        #            print('dropped: ', asset)
        #    return True
        """
        if data.hasHtml()
        if data.hasColor()
            color = data.color()
            color = (%d, %d, %d, %d)" % (color.r, color.g, color.b, color.a)
        if data.hasImage():
            str += (", image = true")
        """
        return omui.MExternalDropCallback.kMayaDefault

    @logFunction('Asset Dropped')
    def assetDropAction(self, asset):
        #LOG.debug("Processing item {} in plugin".format(asset))
        class_index = getattr(asset, 'class')
        fpath = Path(asset.path)
        '''
        if class_index == config.AREA_LIGHT:
            light = cmds.shadingNode("VRayLightRectShape", asLight=True)
            light.setAttr("useRectTex", 1)
            texture = cmds.shadingNode("file", asTexture=True)
            texture.setAttr("fileTextureName", asset.path)
            cmds.connectAttr(
                texture.name() + ".outColor", light.name() + ".rectTex", force=True
            )
            #light.select()

        elif class_index == config.IES:
            light = cmds.shadingNode("VRayLightIESShape", asLight=True)
            light.setAttr("iesFile", asset.path.replace("/", "\\"))
            #light.select()

        elif class_index == config.IBL_PROBE:
            light = cmds.shadingNode("VRayLightDomeShape", asLight=True)
            light.setAttr("useDomeTex", 1)
            texture = cmds.shadingNode("file", asTexture=True)
            texture.setAttr("fileTextureName", asset.path)
            cmds.connectAttr(
                texture.name() + ".outColor", light.name() + ".domeTex", force=True
            )
            light.select()
        '''
        if class_index == config.MODEL:
            model = cmds.file(
                asset.path,
                reference=True,
                loadReferenceDepth="all",
                mergeNamespacesOnClash=False,
                deferReference=True,
                namespace='{}'.format(asset.name),
            )
            addRelicAttributes(asset)

        elif class_index == config.TEXTURE:
            texture = cmds.shadingNode("file", asTexture=True)
            texture.setAttr("fileTextureName", asset.path)

        elif asset.path.endswith('.mel'):
            mel.eval('source "{}";'.format(filepath))

        elif asset.path.endswith('.py'):
            import maya.app.general.executeDroppedPythonFile as TempEDPF
            TempEDPF.executeDroppedPythonFile(asset.path, "")
            del TempEDPF

        elif asset.path.endswith('.ma') or asset.path.endswith('.mb'):
            materialx_path = fpath.suffixed('', '.mtlx')
            cmds.file(
                asset.path,
                reference=True,
                loadReferenceDepth="all",
                mergeNamespacesOnClash=True,
                #deferReference=True,
                namespace='{}'.format(asset.name),
            )
            cmds.file(
                str(materialx_path),
                reference=True,
                loadReferenceDepth="all",
                mergeNamespacesOnClash=True,
                #deferReference=True,
                namespace='{}'.format(asset.name),
            )
            # Perform material assignments
            xdoc = mx.createDocument()
            mx.readFromXmlFile(xdoc, str(materialx_path))
            look = xdoc.getLook('standard')
            with Namespace(asset.name):
                for assignment in look.getMaterialAssigns():
                    material_name = assignment.getMaterial()
                    for geo in assignment.getCollection().getIncludeGeom().split(','):
                        cmds.sets(geo, e=1, fe=material_name)

            addRelicAttributes(asset)

        LOG.debug('Finished {}'.format(asset.name))
