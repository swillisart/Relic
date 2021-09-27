import sys
import json
import re
from functools import partial

import maya.OpenMayaUI as omui
import maya.api.OpenMaya as om
import maya.cmds as cmds
import shiboken2

from relic_base import asset_classes, asset_views
from relic_base import config
from relic_base.config import LOG, logFunction

from sequencePath import sequencePath as Path

#REF_ID_REGEX = re.compile(r'\{[0-9]\}')
EDIT_EXT = 'editMB'

# Using the Maya Python API 2.0.
def maya_useNewAPI():
    pass

def addRelicAttributes(asset):
    maya_ref = '{}RN'.format(asset.name)
    cmds.lockNode(maya_ref, lock=False)

    attr = 'RELIC_hash'
    cmds.addAttr(maya_ref, longName=attr, dataType='string')
    cmds.setAttr(maya_ref + '.' + attr, asset.filehash, edit=1, type='string')

    attr = 'RELIC_category'
    cmds.addAttr(maya_ref, longName=attr, attributeType='long')
    cmds.setAttr(maya_ref + '.' + attr, asset.category, edit=1)

    attr = 'RELIC_id'
    cmds.addAttr(maya_ref, longName=attr, attributeType='long')
    cmds.setAttr(maya_ref + '.' + attr, asset.id, edit=1)

    attr = 'RELIC_type'
    cmds.addAttr(maya_ref, longName=attr, attributeType='long')
    cmds.setAttr(maya_ref + '.' + attr, asset.type, edit=1)


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
            for key, values in json.loads(assets).items():
                constructor = asset_classes.getCategoryConstructor(key)
                for fields in values:
                    asset = constructor(**fields)
                    added = self.relicPanel.group_widget.addAsset(asset)
                    if added:
                        maya_drop = partial(self.assetDropAction, asset)
                        icon_update = partial(asset_views.updateIcon, asset)
                        callbacks = [icon_update, maya_drop, applyLinkedEdits]
                        asset.setDownloadCompletionCallbacks(callbacks)
                        asset.download()
            self.relicPanel.group_widget.updateGroups()
            return True

        elif data.hasFormat(b'application/x-relic') and data.hasUrls() and doDrop:
        #    for key, values in json.loads(assets).items():
        #        constructor = getattr(asset_classes, str(key))
        #        for fields in values:
        #            asset = constructor(**fields)
        #            print('dropped: ', asset)
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

    @staticmethod
    @logFunction('Asset Dropped')
    def assetDropAction(asset):
        #LOG.debug("Processing item {} in plugin".format(asset))
        class_index = getattr(asset, 'class')
        asset_path = asset.local_path
        active_renderer = cmds.getAttr('defaultRenderGlobals.currentRenderer')

        if class_index == config.AREA_LIGHT:
            if active_renderer == 'vray':
                vrayRectLight(asset_path)
        elif class_index == config.IES:
            if renderer == 'vray':
                vrayIESLight(asset_path)
        elif class_index == config.IBL:
            if renderer == 'vray':
                vrayDomeLight(asset_path)
    
        if class_index == config.MODEL:
            createMayaReference(asset, asset_path)

        elif class_index == config.TEXTURE or asset_path.ext in config.TEXTURE_EXT:
            texture = cmds.shadingNode('file', asTexture=1)
            cmds.setAttr(texture + '.fileTextureName', str(asset_path), type='string')

        elif asset.path.endswith('.mel'):
            mel.eval('source "{}";'.format(filepath))

        elif asset.path.endswith('.py'):
            import maya.app.general.executeDroppedPythonFile as TempEDPF
            TempEDPF.executeDroppedPythonFile(asset.path, "")
            del TempEDPF

        elif asset.path.endswith('.ma') or asset.path.endswith('.mb'):
            createMayaReference(asset, asset_path)

        LOG.debug('Finished {}'.format(asset.name))


def createMayaReference(asset, asset_path):
    mref = cmds.file(
        asset_path,
        reference=True,
        loadReferenceDepth="all",
        mergeNamespacesOnClash=False,
        namespace='{}'.format(asset_path.name),
    )
    materialx_path = asset_path.suffixed('', '.mtlx')
    cmds.namespace(add=asset_path.name+'_mtlx')
    mxref = cmds.file(
        str(materialx_path),
        i=True,
        loadReferenceDepth="all",
        mergeNamespacesOnClash=False,
        #namespace='{}'.format(asset_path.name+'_mtlx'),
    )
    addRelicAttributes(asset)


def iterateReferencePaths(all_references):
    for ref_node in all_references:
        ref_path = cmds.referenceQuery(ref_node, filename=1)
        
        if not ref_path.endswith('.mtlx') and not ref_path.endswith('.editMB'):
            yield ref_node, Path(ref_path)

def applyLinkedEdits():
    all_references = cmds.ls(exactType='reference')
    edited_attr = 'RELIC_edited'

    for source_ref, src_path in iterateReferencePaths(all_references):
        edits_relative_path = 'source_misc/' + src_path.name + '.' + EDIT_EXT
        
        for destination_ref, dst_path in iterateReferencePaths(all_references):
            maya_edits_path = dst_path.parents(0) / edits_relative_path
            edit_attr_exists = cmds.attributeQuery(edited_attr, node=source_ref, exists=1)
            dst_relic_attr = cmds.attributeQuery('RELIC_type', node=destination_ref, exists=1)
            if edit_attr_exists:
                if dst_relic_attr:
                    src_type = cmds.getAttr(source_ref + '.' + 'RELIC_type')
                    dst_type = cmds.getAttr(destination_ref + '.' + 'RELIC_type')
                    if src_type > dst_type:
                        continue
                else:
                    continue
            elif src_path.ext in ['.mb', '.ma']:
                try:
                    cmds.addAttr(source_ref, longName=edited_attr, attributeType='bool')
                    cmds.setAttr(source_ref + '.' + edited_attr, True, edit=1)
                except:pass

            if maya_edits_path.exists:
                LOG.debug('Maya Reference Offline Edits : {}\n\t\
                    applyTo: {} using PlaceHolder: {}'.format(
                   maya_edits_path, source_ref, destination_ref))
                cmds.file(
                    str(maya_edits_path),
                    i=1, #Import
                    #reference=1,
                    type=EDIT_EXT,
                    applyTo=source_ref,
                    mapPlaceHolderNamespace=['<root>', destination_ref]
                )
            #file -r -type "editMA" -mapPlaceHolderNamespace "<root>" "PoleLanternBasicRN" -applyTo "LanternBasicRN" "C:/Users/Resartist/.relic/ingest/LanternBasic.editMA";

def vrayTexturedLight(light, attr, path):
    texture = cmds.shadingNode('file', asTexture=1)
    cmds.setAttr(texture + '.fileTextureName', str(path), type='string')
    cmds.connectAttr(
        texture.name() + '.outColor',
        light + attr,
        force=1
    )
    cmds.select(light, r=1)

def vrayDomeLight(path):
    light = cmds.shadingNode('VRayLightDomeShape', asLight=1)
    cmds.setAttr(light + '.useDomeTex', 1)
    vrayTexturedLight(light, '.domeTex', path)

def vrayRectLight(path):
    light = cmds.shadingNode(light_type, asLight=1)
    cmds.setAttr(light + '.useRectTex', 1)
    vrayTexturedLight(light, '.rectTex', path)

def vrayIESLight(path):
    light = cmds.shadingNode('VRayLightIESShape', asLight=1)
    cmds.setAttr(light + '.iesFile', str(path).replace('/', '\\'))
    cmds.select(light, r=1)
