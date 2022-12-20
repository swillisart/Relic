import json

import maya.OpenMayaUI as omui
import maya.api.OpenMaya as om
import maya.cmds as cmds
import shiboken2

from relic.qt.delegates import Statuses
from relic.plugin.views import updateIcon
from relic.plugin.classes import getCategoryConstructor
from relic.scheme import Class
from relic.local import Category, ClassGroup

from sequence_path.main import SequencePath as Path

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

    long_attrs = ['category', 'id', 'type']
    for attr in long_attrs:
        attr_name = 'RELIC_'+attr
        cmds.addAttr(maya_ref, longName=attr_name, attributeType='long')
        cmds.setAttr(maya_ref + '.' + attr_name, getattr(asset, attr), edit=1)


class RelicDropCallback(omui.MExternalDropCallback):
    INSTANCE = None

    def __init__(self, relicMixinWindow):
        omui.MExternalDropCallback.__init__(self)
        self.relicPanel = relicMixinWindow

    def externalDropCallback(self, doDrop, controlName, data):
        retstring = "External Drop: doDrop = {}, controlName = {}".format(
            doDrop, controlName)

        m_drop = omui.MExternalDropData
        mouse_button = data.mouseButtons()
        key_mod = data.keyboardModifiers()
        """
        mouse_button & m_drop.kLeftButton
        mouse_button & m_drop.kMidButton
        mouse_button & m_drop.kRightButton
        key_mod & m_drop.kShiftModifier
        key_mod & m_drop.kControlModifier
        key_mod & m_drop.kAltModifier
        """
        drop_script = data.urls()[0]
        assets = data.text()
        
        is_from_relic = data.hasFormat(b'application/x-relic') and data.hasUrls()
        scene_content = self.relicPanel.content
        if is_from_relic and not doDrop:
            for key, values in json.loads(assets).items():
                constructor = getCategoryConstructor(key)
                for fields in values:
                    asset = constructor(**fields)
                    added = scene_content.addAsset(asset)
                    if not added:
                        continue
                    if asset.local_path.parent.exists():
                        # asset exists; update progress and callback
                        asset.progress = 288
                        asset.status = Statuses.Local
                        self.assetDropAction(asset)
                        updateIcon(asset)
                        scene_content.updateProgress(asset)
                    else:
                        asset.status = Statuses.Syncing
                        asset.callbacks = [updateIcon, self.assetDropAction, applyLinkedEdits]
                        asset.download()
            scene_content.updateGroups()
            return True

        elif is_from_relic and doDrop:
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
        """
        return omui.MExternalDropCallback.kMayaDefault

    @staticmethod
    def assetDropAction(asset):
        category = asset.category
        classify = Class(asset.classification)
        if category == Category.LIGHTING.index:
            createLighting(asset)
        elif classify & ClassGroup.SOFTWARE: # category == Category.MAYATOOLS.index
            if asset.path.endswith('.py'):
                import maya.app.general.executeDroppedPythonFile as TempEDPF
                TempEDPF.executeDroppedPythonFile(asset.local_path, "")
                del TempEDPF
            #if asset.path.endswith('.mel'):
            #    mel.eval('source "{}";'.format(filepath))
            #cmds.loadModule(scan=True) 
            else: # zipped plugin with module
                paths = cmds.loadModule(scan=True)
                plugins = cmds.loadModule(allModules=True)
                cmds.loadPlugin(asset.name, quiet=True)

        elif asset.local_path.ext in ['.mb', '.ma']: # gracefully handle unclassified scenes.
            createMayaReference(asset, asset.local_path)
        """
        if class_index == Class.MODEL:
            createMayaReference(asset, asset.local_path)
        elif class_index == config.TEXTURE or asset.local_path.ext in config.TEXTURE_EXT:
            texture = cmds.shadingNode('file', asTexture=1)
            cmds.setAttr(texture + '.fileTextureName', str(asset.local_path), type='string')
        """
        asset.status = Statuses.Local
        asset.progress = 0

def createLighting(asset):
    class_index = asset.classification
    active_renderer = cmds.getAttr('defaultRenderGlobals.currentRenderer')
    if active_renderer == 'arnold':
        import relicArnold as renderer
    elif active_renderer == 'vray':
        import relicVray as renderer
    else:
        return

    if class_index == Class.IBL.index:
        renderer.domeLight(asset.local_path)
    elif class_index == Class.IES.index:
        renderer.iesLight(asset.local_path)
    elif class_index == Class.IMAGE.index:
        renderer.areaLight(asset.local_path)


def createMayaReference(asset, asset_path):
    mref = cmds.file(
        asset_path,
        reference=True,
        loadReferenceDepth="all",
        mergeNamespacesOnClash=False,
        namespace='{}'.format(asset_path.name),
    )
    addRelicAttributes(asset)
    materialx_path = asset_path.suffixed('', '.mtlx')
    if not materialx_path.exists():
        return
    cmds.namespace(add=str(asset_path.name)+'_mtlx')
    mxref = cmds.file(
        str(materialx_path),
        i=True,
        loadReferenceDepth="all",
        mergeNamespacesOnClash=False,
        #namespace='{}'.format(asset_path.name+'_mtlx'),
    )

def iterateReferencePaths(all_references):
    for ref_node in all_references:
        ref_path = cmds.referenceQuery(ref_node, filename=1)
        
        if not ref_path.endswith('.mtlx') and not ref_path.endswith('.editMB'):
            yield ref_node, Path(ref_path)

def applyLinkedEdits(asset):
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

            if maya_edits_path.exists():
                print('Maya Reference Offline Edits : {}\n\t\
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
