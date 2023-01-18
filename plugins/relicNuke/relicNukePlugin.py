import json
import os
import re
import sys
from functools import partial

# -- App --
import nuke
import nukescripts
# -- Third-party --
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from relic.local import (INGEST_PATH, Category, FileType, Nuketools,
                         Subcategory, TempAsset, getAssetSourceLocation)
from relic.plugin import networking, views
from relic.plugin.classes import getCategoryConstructor
# -- Module --
from relic.qt.delegates import Statuses
from relic.qt.util import loadStylesheet
from relic.scheme import Asset, AssetType, TagType, UserType
# -- First-party --
from sequence_path import Path

# -- Globals --
MENU_NAME = 'Relic'
IGNORE_NODES = ['Write', 'DeepWrite', 'WriteGeo', 'LiveInput']
FORMAT_NAME = 'root(asset)'

FRAME_EXPR = 'root.proxy ? frame-({start}-1) : frame'
FIRST_EXPR = 'root.proxy ? 1 : {start}'
LAST_EXPR = 'root.proxy ? {proxy_last} : {seq_last}'


class RelicPanel(views.RelicSceneForm):
    TITLE = 'Relic Scene Assets'
    ID = 'resarts.relic_assets'

    def __init__(self, *args, **kwargs):
        super(RelicPanel, self).__init__(*args, **kwargs)
        nukescripts.addDropDataCallback(self.assetDropCallback)
        loadStylesheet(self, path=':app_style.qss')

    def assetDropCallback(self, mime_type, payload):
        if not payload.startswith('relic://'):
            return None

        self.update()
        stripped = payload.replace('\\', '').replace('relic://', '')
        scene_content = self.content
        for key, values in json.loads(stripped).items():
            constructor = getCategoryConstructor(str(key.decode()))
            # json paylods are strings so sort by type from string key.
            sort_key = str(Asset.TYPE.index) # 13
            sorted_values = sorted(values, key=lambda x: x.get(sort_key), reverse=True)
            for fields in sorted_values:
                asset = constructor(**fields)
                added = scene_content.addAsset(asset)
                if asset.local_path.parent.exists():
                    # Asset already exists! Add it again..
                    if added:
                        views.updateIcon(asset)
                    app_drop = partial(assetDropAction, asset)
                    QTimer.singleShot(10, app_drop)
                else:
                    asset.status = Statuses.Syncing
                    asset.callbacks = [views.updateIcon, assetDropAction]
                    asset.download()
        scene_content.updateGroups()
        self.update()
        return True

    def refreshSceneAssets(self):
        for node in nuke.allNodes():
            if not node.knob('RELIC_id'):
                continue
            cat_id = int(node['RELIC_category'].value())
            constructor = getCategoryConstructor(cat_id)
            asset = constructor(category=cat_id)
            asset.name = str(node['name'].value())
            asset.id = int(node['RELIC_id'].value())
            asset.filehash = str(node['RELIC_hash'].value())
            asset.progress = 288
            asset.status = Statuses.Local
            if not self.content.assetInModel(asset):
                asset.callbacks = [self.content.addAsset, views.updateIcon]
                asset.fetch()

    def showEvent(self, event):
        setNukeZeroMarginsWidget(self)
        self.refreshSceneAssets()
        return super(RelicPanel, self).showEvent(event)


def getMainWindows():
    for widget in QApplication.topLevelWidgets():
        if (
            widget.inherits('QMainWindow')
            and widget.metaObject().className() == 'Foundry::UI::DockMainWindow'
        ):
            mainWindow = widget
            break
    panel = None
    from PySide2.QtOpenGL import QGLWidget
    for glwidget in mainWindow.findChildren(QGLWidget):
        parent = glwidget.parent()
        if parent.objectName() == 'DAG.1':
            panel = parent
            break
    if not panel:
        panel = parent

    return (mainWindow, panel)

def addRelicAttributes(nodes, asset):
    if not len(nodes) == 1:
        return

    for node in nodes:
        if not node.knob('Relic'):
            tab = nuke.Tab_Knob('Relic')
            cat_knob = nuke.String_Knob('RELIC_category')
            cat_knob.setValue(str(asset.category))
            hash_knob = nuke.String_Knob('RELIC_hash')
            hash_knob.setValue(str(asset.filehash))
            id_knob = nuke.Int_Knob('RELIC_id')
            id_knob.setValue(int(asset.id))
            status_knob = nuke.Int_Knob('RELIC_status')
            status_knob.setValue(int(asset.status))
            map(node.addKnob, (tab, cat_knob, hash_knob, id_knob, status_knob))
    return nodes

def replaceNodeContents(a, b):
    nukescripts.clear_selection_recursive()
    temp_path = os.getenv('userprofile') + '/temp.nk'
    a.begin()
    for subnode in a.nodes():
        subnode.setSelected(True)
    nuke.nodeCopy(temp_path)
    a.end()

    b.begin()
    for subnode in b.nodes():
        nuke.delete(subnode)
    nuke.scriptSource(temp_path)
    b.end()
    nuke.delete(a)

def getKnob(knob_name, node):
    attr = node.knob(knob_name)
    if attr:
        return attr.getValue()

def processUnresolvedAssets(asset):
    nukescripts.clear_selection_recursive()
    # pre-filter all nodes by matching hash.
    ahash = str(asset.filehash)
    get_knob = partial(getKnob, 'RELIC_hash')
    criteria = lambda x : ahash == get_knob(x)
    filtered = filter(criteria, nuke.allNodes(recurseGroups=True))
    already_exists = False
    local = Statuses.Local.value
    for existing_node in filtered:
        # Set paths upstream files.
        if existing_node.Class() != 'Group' and existing_node.knob('file'):
            existing_node['file'].setValue(str(asset.local_path))
            continue
        status = existing_node.knob('RELIC_status')
        try:
            if status.getValue() == local:
                continue
        except:
            status = nuke.Int_Knob('RELIC_status')
            existing_node.addKnob(status)
        # replaces unresolved asset groups.
        nuke.scriptSource(str(asset.local_path))
        replaceNodeContents(nuke.selectedNode(), existing_node)
        status.setValue(local)
        already_exists = True
    return already_exists

def processUnresolvedFiles(asset_path):
    for node in nuke.allNodes(recurseGroups=True):
        if node.knob('file'):
            applyRepath(node, asset_path)

def executeScript(asset):
    asset_path = asset.local_path
    sys.path.append(str(asset_path.parent))
    subcategory = Subcategory(**asset.subcategory)
    asset_name = asset_path.name
    __import__(asset_name)
    toolbar = nuke.toolbar('Nodes')
    relic_tolbar = toolbar.addMenu('Relic/{}'.format(subcategory.name))
    relic_tolbar.addCommand(asset_name, 'import {m};{m}.main()'.format(m=asset_name))

def assetDropAction(asset):
    asset_path = asset.local_path
    # replace the existing upstream nodes already in the scene.
    already_exists = processUnresolvedAssets(asset)
    asset.status = Statuses.Local
    asset.progress = 0
    if already_exists:
        return
    elif asset_path.ext == '.nk':
        nuke.nodePaste(str(asset_path))
        selection = nuke.selectedNodes()
        nodes = selection
        processUnresolvedFiles(asset_path)
    #elif asset_path.ext in GEO_EXT:
    #    #TODO: handle geometry assets
    #    #nodes = ?
    #    pass
    elif asset_path.ext == '.py':
        executeScript(asset)
        return
    else:
        nodes = makeFileRead(asset_path)
    
    addRelicAttributes(nodes, asset)

def makeFileRead(asset_path):
    c_read = nuke.createNode('Read', inpanel=False)
    c_read['file'].fromUserText(str(asset_path))
    asset_path.checkSequence()
    if asset_path.sequence_path:
        #proxy_path = asset_path.suffixed('_proxy', '.mp4')
        #c_read['proxy'].fromUserText(str(proxy_path))
        #proxy_last = int(c_read['last'].value())
        first, last = asset_path.getFrameRange()
        c_read['frame_mode'].setValue('expression')
        c_read['frame'].setValue(FRAME_EXPR.format(start=first))
        c_read['first'].setValue(first)
        c_read['last'].setValue(last)
        #c_read['first'].setExpression(FIRST_EXPR.format(start=first))
        #c_read['last'].setExpression(LAST_EXPR.format(proxy_last=proxy_last, seq_last=last))
    #else:
    #    proxy_path = asset_path.suffixed('_proxy', '.jpg')
    #    c_read['proxy'].fromUserText(str(proxy_path))

    # Set formats
    fmt = c_read['format'].value()
    c_read['proxy_format'].setValue(fmt)

    return [c_read]

def collectGroupNode(node, files, assets, selected):
    node_class = node.Class()
    is_group = node_class == 'Group'
    if node_class == 'Viewer':
        nuke.delete(node) # viewers should only be top-level
    elif node.knob('Relic'):
        collectRelicAsset(node, files, assets, is_group)
    elif is_group:
        for subnode in node.nodes():
            collectGroupNode(subnode, files, assets, selected)
    elif node_class.endswith('gizmo'):
        collectGizmo(node, files, assets, selected)
    else:
        collectFilePath(node, files)

def getSelectionDependencies(selected):
    assets = {}
    files = {}
    
    for node in selected:
        node_class = node.Class()
        is_group = node_class == 'Group'
        if node_class == 'Viewer':
            node.setSelected(False)
        elif node.knob('Relic'):
            collectRelicAsset(node, files, assets, is_group)
        elif is_group:
            collectGroupNode(node, files, assets, selected)
        elif node_class.endswith('gizmo'):
            collectGizmo(node, files, assets, selected)
        else:
            collectFilePath(node, files)

    return files, assets

def collectRelicAsset(node, files, assets, is_group):
    if is_group:
        # Remove the group contents since the asset already in Relic.
        for subnode in node.nodes():
            nclass = subnode.Class()
            if nclass != 'Output' and nclass != 'Input':
                nuke.delete(subnode)
    else:
        collectFilePath(node, files)
    key = node.knob('RELIC_hash').value()
    # Reset the local status.
    node.knob('RELIC_status').setValue(Statuses.Cloud.value)
    assets[key] = {
        'category': int(node.knob('RELIC_category').value()),
        'id': int(node.knob('RELIC_id').value())
    }

def collectFilePath(node, files):
    file_knob = node.knob('file')
    if not file_knob or node.Class() in IGNORE_NODES:
        return
    node_file = file_knob.getValue()
    if not node_file:
        return
    clean_path = Path.cleanPath(node_file)
    original_path = Path(node_file)
    if not original_path.parent.exists():
        return

    subfolder = getAssetSourceLocation(str(clean_path))
    changed_path = subfolder + '/' + clean_path.stem
    node['file'].setValue(changed_path)
    files[str(original_path)] = node

def collectGizmo(node, files, assets, selected):
    nukescripts.clear_selection_recursive()
    knob_giz = ['xpos', 'ypos', 'name']

    grp = node.makeGroup()
    collectGroupNode(grp, files, assets, selected)
    node_color = nuke.defaultNodeColor(node.Class())
    grp.knob('tile_color').setValue(node_color)
    values = [node.knob(x).getValue() for x in knob_giz]

    for i in range(node.inputs()):
        upstream_in = node.input(i)
        if upstream_in is not None:
            grp.setInput(i, upstream_in)

    for downstream in node.dependent(nuke.INPUTS):
        for i in range(downstream.inputs()):
            if downstream.input(i) is node:
                downstream.setInput(i, grp)
    # Update selection, removing gizmo and replacing with new group
    selected.append(grp)
    for x in selected:
        try:
            x.setSelected(True)
        except ValueError: pass

    nuke.delete(node)
    [grp.knob(knob_giz[i]).setValue(values[i]) for i in range(len(knob_giz))]


def exportSelection(asset_type=None):
    selection = nuke.selectedNodes()
    if not selection:
        nuke.message('Nodes must be selected to Export as Asset')
        return

    print('Zooming (frame) selection for nodegraph image capture')
    nuke.zoomToFitSelected()
    if len(selection) == 1:
        nuke.zoom(4, [selection[0].xpos()+40, selection[0].ypos()])

    asset = Nuketools(name=selection[-1].name())
    asset.path = INGEST_PATH / asset.name / (asset.name + '.nk')
    asset.path.createParentFolders()
    asset.category = Category.NUKETOOLS.index
    setattr(asset, 'class', Nuketools.classifier)
    if len(selection) >= 2:
        asset.type = AssetType.COLLECTION
    elif selection[0].Class() == 'Group':
        asset.type = AssetType.ASSET
    elif selection[0].Class() == 'Read':
        asset.type = AssetType.VARIANT
    else:
        asset.type = AssetType.COMPONENT

    if asset_type: # Overrride the type
        asset.type = asset_type

    SOFTWARE_REGEX = re.compile(r"[^A-Za-z0-9\n\.]")
    software_tag_name = 'nuke' + re.sub(SOFTWARE_REGEX, '', nuke.NUKE_VERSION_STRING)
    asset.tags = [{'name': software_tag_name, 'type': 1}]

    # Process the selection
    setNodeAssetInfo(asset)
    upstream_files, upstream_assets, = getSelectionDependencies(selection)
    asset.dependencies = list(upstream_files.keys())
    asset.links = [x for x in upstream_assets.values()] # unpack collected unique asset links

    print('Capturing snapshot of nodegraph')
    captureViewport(asset.path.suffixed('_icon', ext='.jpg'))
    # Write the nodes to the temp file for main Relic ingestion.
    asset.path = str(asset.path)
    nuke.nodeCopy(asset.path)
    results = [{attr: val for i, attr, val in asset}]
    try:
        r = json.dumps(results)
        networking.tryLaunch(r)
    except Exception as exerr:
        nuke.message('Invalid data for export! caused this error: \n%s' % exerr)
    finally:
        # revert the path changes
        [n['file'].setValue(path) for path, n in upstream_files.items()]

def setNodeAssetInfo(asset):
    """Collects all the important node information and
    counts all the nodes in current graph
    """

    nuke_location = str(Path(nuke.env['ExecutablePath']).parent)
    nuke_plugins = nuke.plugins()
    nuke_nodes = nuke.allNodes(recurseGroups=True)
    asset_format = [formatToScript(f) for f in nuke.formats() if f.name() == FORMAT_NAME] or None
    plugin_ext = nuke.PLUGIN_EXT
    for node in nuke_nodes:
        node_class = node.Class()
        asset_format = setRootFormats(node, asset_format)

        for plug in nuke_plugins:
            is_nuke = plug.startswith(nuke_location)
            if not is_nuke and plug.endswith(plugin_ext) and node_class == Path(plug).name:
                tag_data = {'name': node_class, 'type': TagType.PLUGIN} 
                asset.tags.append(tag_data)

    asset.nodecount = len(nuke_nodes)

def setRootFormats(node, asset_format):
    """Converts all root.format references to a named format
    so that any asset will function the same way in any script
    independent of whatever the current root format is.
    """
    root_format = '0'
    format_knob = node.knob('format')
    if not format_knob: # No format knob
        return asset_format
    current_format = format_knob.toScript()
    if current_format != root_format: # Not referencing a root format via expression 
        return asset_format
    if asset_format is not None: # Already created the new named format.
        script = asset_format[0]
        format_knob.fromScript(script)
        return asset_format 

    # Make the new asset format using the root format value(s)
    f = format_knob.actualValue()
    format_script = formatToScript(f)
    nuke.addFormat(format_script)
    format_knob.fromScript(format_script)
    return [format_script]

def formatToScript(f):
    attrs = [f.width(), f.height(), f.x(), f.y(), f.r(), f.t(), f.pixelAspect(), FORMAT_NAME]
    return ' '.join(map(str, attrs))

def alembicPatch(node):
    sceneView = node['scene_view']
    # get a list of all nodes stored in the abc file
    allItems = sceneView.getAllItems()
    # import all items into the ReadGeo node
    sceneView.setImportedItems(allItems)
    # set everything to selected (i.e. visible)
    sceneView.setSelectedItems(allItems)

def applyRepath(node, asset_path):
    file_path = node['file'].value()
    if not file_path.startswith('source_'):
        return

    repath = asset_path.parent / file_path

    if repath.parent.exists():
        node['file'].setValue(str(repath))
        if str(repath).endswith('.abc'):
            try:
                alembicPatch(node)
            except: pass

def captureViewport(save_path):
    mainWindow, panel = getMainWindows()
    try:
        glwidget = panel.children()[1]
    except:
        print('Cannot find nuke glwidget')
        return
    src_img = glwidget.grabFrameBuffer()
    try:
        out_img = QImage(288, 192, QImage.Format_RGBA8888)
        out_img.fill(QColor(65, 65, 65, 255))
        alpha_img = src_img.scaled(288, 192, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

        painter = QPainter(out_img)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        painter.drawImage(0, 0, alpha_img)
        painter.end()
        out_img.save(str(save_path))
    except Exception as exerr:
        print(exerr)


def setNukeZeroMarginsWidget(widget_object):
    parentApp = QApplication.allWidgets()
    for parent in parentApp:
        for child in parent.children():
            if widget_object.__class__ != child.__class__:
                continue
            a = parent.parentWidget()
            b = a.parentWidget()
            c = b.parentWidget()
            for sub in (a, b, c):
                for tinychild in sub.children():
                    if not isinstance(tinychild, QLayout):
                        continue
                    tinychild.setContentsMargins(0, 0, 0, 0)

def main():
    pane = nuke.getPaneFor('Properties.1')
    panel = nukescripts.panels.registerWidgetAsPanel(
                widget='relicNukePlugin.RelicPanel',
                name=RelicPanel.TITLE,
                id=RelicPanel.ID,
                create=True)

    panel.addToPane(pane)
    #if not panel.customKnob.getObject():
    #    panel.customKnob.makeUI()
    #relic_panel = panel.customKnob.getObject().widget
    #return relic_panel
    menu = nuke.menu('Nuke')
    relic_menu = menu.addMenu(MENU_NAME)
    relic_menu.addCommand('Export Asset', 'relicNukePlugin.exportSelection()')
    relic_menu.addCommand('Export Variation', 'relicNukePlugin.exportSelection(5)')
    relic_menu.addSeparator()

if __name__== '__main__':
    main()
