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
from PySide2.QtOpenGL import *
from PySide2.QtWidgets import *
from OpenGL.GL import (GL_FRONT, GL_PACK_ALIGNMENT, GL_UNSIGNED_BYTE,
                       glPixelStorei, glReadBuffer, glReadPixels,
                       GL_RGB, GL_RGBA)

# -- First-party --
from sequencePath import sequencePath as Path

# -- Module --
from relic_base import asset_classes, asset_views, config
from relic_base.config import (INGEST_PATH, LOG, RELIC_CLIENT, RELIC_PREFS,
                               logFunction)

# -- Globals --
IGNORE_NODES = ['Write', 'DeepWrite', 'WriteGeo', 'LiveInput']
MENU_NAME = 'Relic'

FRAME_EXPR = 'root.proxy ? frame-({start}-1) : frame'
FIRST_EXPR = 'root.proxy ? 1 : {start}'
LAST_EXPR = 'root.proxy ? {proxy_last} : {seq_last}'

class RelicPanel(asset_views.RelicSceneForm):
    TITLE = 'Relic Scene Assets'
    ID = 'resarts.relic_assets'

    def __init__(self, *args, **kwargs):
        super(RelicPanel, self).__init__(*args, **kwargs)
        nukescripts.addDropDataCallback(self.assetDropCallback)

    def assetDropCallback(self, mime_type, payload):
        if payload.startswith('relic://'):
            self.update()
            stripped = payload.replace('\\', '').replace('relic://', '')
            for key, values in json.loads(stripped).items():
                constructor = asset_classes.getCategoryConstructor(str(key.decode()))

                for fields in values:
                    asset = constructor(**fields)
                    added = self.group_widget.addAsset(asset)
                    if added:
                        app_drop = partial(assetDropAction, asset)
                        icon_update = partial(asset_views.updateIcon, asset)
                        callbacks = [icon_update, app_drop]
                        asset.setDownloadCompletionCallbacks(callbacks)
                        asset.download()
            self.group_widget.updateGroups()
            self.update()
            return True
        return None

    @logFunction('Syncing Scene Assets')
    def refreshSceneAssets(self):
        for node in nuke.allNodes():
            if not node.knob('RELIC_id'):
                continue
            cat_id = int(node['RELIC_category'].value())
            constructor = asset_classes.getCategoryConstructor(cat_id)
            asset = constructor(category=cat_id)
            asset.name = str(node['name'].value())
            asset.id = int(node['RELIC_id'].value())
            asset.filehash = str(node['RELIC_hash'].value())
            asset.progress = [1,1]
            if not self.group_widget.assetInModel(asset):
                asset.fetch(on_complete=partial(self.group_widget.addAsset, asset))

    def showEvent(self, event):
        setNukeZeroMarginsWidget(self)
        self.refreshSceneAssets()
        return super(RelicPanel, self).showEvent(event)


@logFunction('Retrieving Important Qt Windows')
def getMainWindows():
    for widget in QApplication.topLevelWidgets():
        if (
            widget.inherits('QMainWindow')
            and widget.metaObject().className() == 'Foundry::UI::DockMainWindow'
        ):
            mainWindow = widget
            break
    panel = None
    for glwidget in mainWindow.findChildren(QGLWidget):
        parent = glwidget.parent()
        if parent.objectName() == 'DAG.1':
            panel = parent
            break
    if not panel:
        panel = parent

    return (mainWindow, panel)

@logFunction('Adding Library Tab & Attributes to Node')
def addRelicAttributes(nodes, asset):
    if not len(nodes) == 1:
        return

    for node in nodes:
        if not node.knob('Relic'):
            tab = nuke.Tab_Knob('Relic')
            node.addKnob(tab)
            catknob = nuke.String_Knob('RELIC_category')
            catknob.setValue(str(asset.category))
            node.addKnob(catknob)
            strknob = nuke.String_Knob('RELIC_hash')
            strknob.setValue(str(asset.filehash))
            node.addKnob(strknob)
            idknob = nuke.Int_Knob('RELIC_id')
            idknob.setValue(int(asset.id))
            node.addKnob(idknob)
            #check = nuke.Boolean_Knob('repathed')
            #check.setValue(False)
            #node.addKnob(check)
    return nodes

@logFunction('demo')
def processUnresolvedAssets(asset):
    already_exists = False

    for node in nuke.allNodes(recurseGroups=True):
        if node.knob('RELIC_hash') and node['RELIC_hash'].value() == asset.filehash:
            already_exists = True

            nuke.scriptSource(str(asset.local_path))
            a = nuke.selectedNode()
            b = node
            [x.setSelected(False) for x in nuke.selectedNodes()]

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

    return already_exists

def processUnresolvedFiles(asset):
    for node in nuke.allNodes(recurseGroups=True):
        if node.knob('file'):
            applyRepath(node, asset.local_path)

@logFunction('Asset Dropped')
def assetDropAction(asset):
    asset_path = asset.local_path
    # check for nodes of this type already in the scene.
    if processUnresolvedAssets(asset):
        return
    if asset_path.ext == '.nk':
        nuke.nodePaste(str(asset_path))
        selection = nuke.selectedNodes()
        nodes = selection
        processUnresolvedFiles(asset)
    elif asset_path.ext in config.GEO_EXT:
        #TODO: handle geometry assets
        #nodes = ?
        pass
    elif asset_path.ext == '.py':
        sys.path.append(str(asset_path.parent))
        __import__(asset_path.name)
        toolbar = nuke.toolbar('Nodes')
        library = toolbar.addMenu('Library')
        library.addCommand(asset_path.name, 'import {m};{m}.main()'.format(m=asset_path.name))
        return
    else:
        nodes = makeFileRead(asset_path)

    addRelicAttributes(nodes, asset)

def makeFileRead(asset_path):
    c_read = nuke.createNode('Read', inpanel=False)
    c_read['file'].fromUserText(str(asset_path))
    asset_path.checkSequence()
    if asset_path.sequence_path:
        proxy_path = asset_path.suffixed('_proxy', '.mp4')
        c_read['proxy'].fromUserText(str(proxy_path))
        proxy_last = int(c_read['last'].value())
        first, last = asset_path.getRange()
        c_read['frame_mode'].setValue('expression')
        c_read['frame'].setValue(FRAME_EXPR.format(start=first))
        c_read['first'].setExpression(FIRST_EXPR.format(start=first))
        c_read['last'].setExpression(LAST_EXPR.format(proxy_last=proxy_last, seq_last=last))
    else:
        proxy_path = asset_path.suffixed('_proxy', '.jpg')
        c_read['proxy'].fromUserText(str(proxy_path))

    # Set formats
    fmt = c_read['format'].value()
    c_read['proxy_format'].setValue(fmt)

    return [c_read]

def getSelectionDependencies(selected):
    assets = {}
    files = set()
    for node in selected:
        is_group = node.Class() == 'Group'
        if node.knob('Relic'):
            if is_group:
                for subnode in node.nodes():
                    nclass = subnode.Class()
                    if nclass != 'Output' and nclass != 'Input':
                        nuke.delete(subnode)
            else:
                collectFilePath(node)
            key = node.knob('RELIC_hash').value()
            assets[key] = {
                'category': int(node.knob('RELIC_category').value()),
                'id': int(node.knob('RELIC_id').value())
            }
        elif is_group:
            for subnode in node.nodes():
                file_path = collectFilePath(subnode)
                if file_path:
                    files.add(file_path)
        else:
            file_path = collectFilePath(node)
            if file_path:
                files.add(file_path)

    return files, assets

def collectFilePath(node):
    if not node.knob('file') or node.Class() in IGNORE_NODES:
        return None
    file_path = Path(node['file'].value())
    if not file_path.parents(0).exists:
        return None
    filename = os.path.basename(str(file_path))
    subfolder = config.getAssetSourceLocation(str(file_path))
    changed_path = subfolder + '/' + filename
    node['file'].setValue(changed_path)
    return str(file_path)

@logFunction('export')
def exportSelection(asset_type=None):
    results = []

    selection = nuke.selectedNodes()
    if not selection:
        nuke.message('Nodes must be selected to Export as Asset')
        return

    LOG.debug('Zooming (frame) selection for nodegraph image capture')
    nuke.zoomToFitSelected()
    if len(selection) == 1:
        nuke.zoom(4, [selection[0].xpos()+40, selection[0].ypos()])

    asset = asset_classes.tempasset()
    asset.name = selection[-1].name()
    asset.path = INGEST_PATH / asset.name / (asset.name + '.nk')
    asset.path.createParentFolders()
    asset.category = 7 # Nuketools
    if len(selection) >= 2:
        asset.type = 3 # Collection
    elif selection[0].Class() == 'Group':
        asset.type = 1 # Component
    elif selection[0].Class() == 'Read':
        asset.type = 5 # Variant
    if asset_type: # Overrride the type
        asset.type = asset_type
    software_tag_name = 'nuke' + re.sub(config.SOFTWARE_REGEX, '', nuke.NUKE_VERSION_STRING)
    asset.tags = [{'name': software_tag_name, 'type': 1}]

    # Process the selection
    setNodeAssetInfo(asset)
    dependent_files, dependent_assets = getSelectionDependencies(selection)
    asset.dependencies = list(dependent_files)
    asset.links = [x for x in dependent_assets.values()] # unpack our unique asset links 

    LOG.debug('Capturing snapshot of nodegraph')
    captureViewport(asset.path.suffixed('_icon', ext='.jpg'))
    # write the nodes to file
    asset.path = str(asset.path)
    nuke.nodeCopy(asset.path)
    results.append(asset.__dict__)
    try:
        r = json.dumps(results)
        RELIC_CLIENT.sendPayload(r)
    except Exception as exerr:
        nuke.message('Invalid data for export! caused this error: \n%s' % exerr)
    return results

@logFunction('Collecting Nuke Node Information')
def setNodeAssetInfo(asset):
    """Collects all the important node information and
    counts all the nodes in current graph
    """

    nuke_loc = alPath(nuke.env['ExecutablePath'])
    count = 0

    for node in nuke.allNodes(recurseGroups=True):
        count += 1
        for plug in nuke.plugins():
            if not plug.startswith(nuke_loc.parent) and plug.endswith('.dll'):
                if node.Class() == Path(plug).name:
                    asset.tags.append({'name': node.Class(), 'type': 2})

    asset.nodecount = count

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
    repath = asset_path.parents(0) / file_path

    if repath.parents(0).exists:
        node['file'].setValue(str(repath))
        if str(repath).endswith('.abc'):
            alembicPatch(node)


def captureViewport(save_path):
    mainWindow, panel = getMainWindows()
    try:
        glwidget = panel.children()[1]
    except:
        LOG.error('Cannot find nuke glwidget')
        return
    w = glwidget.width()
    h = glwidget.height()
    glPixelStorei(GL_PACK_ALIGNMENT, 1)
    glReadBuffer(GL_FRONT)
    pixel_data = glReadPixels(0, 0, w, h, GL_RGBA, GL_UNSIGNED_BYTE)

    try:
        out_img = QImage(288, 192, QImage.Format_RGBA8888)
        out_img.fill(QColor(65, 65, 65, 255))

        src_img = QImage(pixel_data, w, h, QImage.Format_RGBA8888).mirrored(vertical=1)
        alpha_img = src_img.scaled(288, 192, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

        painter = QPainter(out_img)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        painter.drawImage(0, 0, alpha_img)
        painter.end()
        out_img.save(str(save_path))
    except Exception as exerr:
        LOG.error(exerr)


def setNukeZeroMarginsWidget(widget_object):
    parentApp = QApplication.allWidgets()    
    for parent in parentApp:
        for child in parent.children():
            if widget_object.__class__ != child.__class__:
                continue
            a = parent.parentWidget()
            b = a.parentWidget()
            c = b.parentWidget()
            for sub in [a, b, c]:
                for tinychild in sub.children():
                    if not isinstance(tinychild, QLayout):
                        continue
                    tinychild.setContentsMargins(0, 0, 0, 0)



def main():
    #pane = nuke.getPaneFor('Properties.1')
    panel = nukescripts.panels.registerWidgetAsPanel(
                widget='relicNukePlugin.RelicPanel',  
                name=RelicPanel.TITLE,
                id=RelicPanel.ID,
                create=False)
    
    #panel.addToPane(pane)
    #if not panel.customKnob.getObject():
    #    panel.customKnob.makeUI()
    #relic_panel = panel.customKnob.getObject().widget
    #return relic_panel
    menu = nuke.menu('Nuke')
    relic_menu = menu.addMenu('Relic')
    relic_menu.addCommand('Export Asset', 'relicNukePlugin.exportSelection()')
    relic_menu.addCommand('Export Variation', 'relicNukePlugin.exportSelection(5)')
    relic_menu.addSeparator() 

if __name__== '__main__':
    main()