# -- Built-in --
import re
import os
import sys
from pathlib import Path
from pprint import pprint, pformat
import logging

# -- Third-party --
from Qt.QtCore import *
from Qt.QtGui import *
from Qt.QtWidgets import *
from Qt.QtOpenGL import *
from OpenGL.GL import *
import nuke

# -- Module --
from asset_library import config
from asset_library import file_io
from asset_library import log, logFunction

from alPath import sequencePath as alPath

IGNORE_NODES = ["Write", "DeepWrite", "WriteGeo", "LiveInput"]

@logFunction('Retrieving Important Qt Windows')
def getMainWindows():
    for widget in QApplication.topLevelWidgets():
        if (
            widget.inherits("QMainWindow")
            and widget.metaObject().className() == "Foundry::UI::DockMainWindow"
        ):
            mainWindow = widget
            break
    panel = None
    for glwidget in mainWindow.findChildren(QGLWidget):
        parent = glwidget.parent()
        if parent.objectName() == "DAG.1":
            panel = parent
            break
    if not panel:
        panel = parent

    return (mainWindow, panel)

@logFunction('Adding Library Tab & Attributes to Node')
def addLibraryAttributes(nodes, item):
    if not len(nodes) == 1:
        return

    for node in nodes:
        if not node.knob('AssetLibrary'):
            tab = nuke.Tab_Knob('AssetLibrary')
            node.addKnob(tab)
            catknob = nuke.String_Knob('alcategory')
            catknob.setValue(item.category)
            node.addKnob(catknob)
            strknob = nuke.String_Knob('alfilehash')
            strknob.setValue(item.Filehash)
            node.addKnob(strknob)
            idknob = nuke.Int_Knob('alid')
            idknob.setValue(item.Id)
            node.addKnob(idknob)
            check = nuke.Boolean_Knob('repathed')
            check.setValue(False)
            node.addKnob(check)
    return nodes

@logFunction('Collecting Nuke Node Assets')
def iterateUnresolvedAssets():
    retval = []
    empty_group = set(['Input', 'Output'])
    for node in nuke.allNodes():
        if node.knob('AssetLibrary') and node.Class() == 'Group':
            node_contents = set([x.Class() for x in node.nodes()])
            if len(node_contents.difference(empty_group)) == 0:
                data = {
                    'node': node,
                    'category': node.knob('alcategory').value(),
                    'Id': int(node.knob('alid').value())
                }
                retval.append(data)
    return retval

@logFunction('demo')
def processUnresolvedAssets(item, link):
    [x.setSelected(False) for x in nuke.allNodes()]
    nuke.scriptSource(str(link.Path))
    a = nuke.selectedNode()
    b = item['node']
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

def assetDropAction(item):
    filepath = item.Path
    lock = True

    if filepath.ext == '.nk':
        nuke.scriptSource(str(filepath))
        selection = nuke.selectedNodes()
        nodes = selection
        lock = False
    elif filepath.ext == ".abc":
        pass
    elif filepath.ext == ".mov":
        cRead = nuke.createNode("Read", inpanel=False)
        cRead["file"].fromUserText(str(filepath))
        nodes = [cRead]
    elif filepath.ext == ".py":
        sys.path.append(str(filepath.parent))
        __import__(filepath.name)
        toolbar = nuke.toolbar("Nodes")
        library = toolbar.addMenu('Library')
        library.addCommand(filepath.name, 'import {m};{m}.main()'.format(m=filepath.name))
        return
    else:
        framerange = file_io.sequence_range_from_path(str(filepath))
        cRead = nuke.createNode("Read", inpanel=False)
        cRead["file"].setValue(str(filepath))
        if framerange:
            cRead["first"].setValue(int(framerange[0]))
            cRead["last"].setValue(int(framerange[1]))
        cRead["raw"].setValue(True)
        nodes = [cRead]

    addLibraryAttributes(nodes, item)

    # Lock the node
    #if lock:
    #    knobs = cRead.allKnobs()
    #    for knob in knobs:
    #        knob.setEnabled(False)

@logFunction('export')
def export_selection(metadata_fields):
    file_path = metadata_fields["Path"]
    metadata_fields["Path"] = file_path.parents(0) / (file_path.name + '.nk')
    selection = nuke.selectedNodes()
    if not selection:
        nuke.message("Nodes must be selected to Export as Asset")
        return (False, False)
    log.debug('Zooming to nodes for nodegraph image capture')
    # frame the node graph selection.
    nuke.zoomToFitSelected()
    if len(selection) == 1:
        nuke.zoom(4, [selection[0].xpos()+40, selection[0].ypos()])

    links = []
    for node in selection:
        if node.knob('AssetLibrary') and node.Class() == 'Group':
            for subnode in node.nodes():
                nclass = subnode.Class()
                if nclass != 'Output' and nclass != 'Input':
                    nuke.delete(subnode)
            link = {
                'category': node.knob('alcategory').value(),
                'Id': node.knob('alid').value()
            }
            links.append(link)
    if links:
        log.debug('Collected all AssetLibrary node groups and converted them to links {}'.format(links))
        metadata_fields['links'] = links
        metadata_fields['Dependencies'] = len(links)

    software_tag_name = 'nuke' + re.sub(config.RE_SOFTWARE, "", nuke.NUKE_VERSION_STRING)
    metadata_fields['tags'] = [{'Name': software_tag_name, 'Type': 1}]
    log.debug('Tagged software version as {}'.format(software_tag_name))


    dependent_files = getAllPaths(modify=metadata_fields)
    metadata_fields = getNodeInfo(metadata_fields)

    # capture graph as image for icon
    icon_path = "{}/{}_icon.jpg".format(file_path.parent, file_path.name)
    log.debug('capturing snapshot of nodegraph {}'.format(icon_path))
    captureViewport(save=icon_path)

    # write the nodes to file
    nuke.nodeCopy(str(metadata_fields["Path"]))

    return (metadata_fields, dependent_files)

@logFunction('Collecting Dependent Files')
def getAllPaths(returnNodes=0, modify=None):
    """Return every nodes path (that's not in IGNORE_NODES) and (uses a file input)

    Returns:
        return_list[dict] - {node "hash": path}
    """
    dependent_files = []
    for node in nuke.allNodes(recurseGroups=True):
        repathed = node.knobs().get("repathed")
        if repathed is not None:
            repathed = repathed.value()
        if node.knobs().get("file") and node.Class() not in IGNORE_NODES and not repathed:
            if returnNodes:
                dependent_files.append(node)
            else:
                f = node["file"].getValue()
                if f:
                    dependent_files.append(f)
                    if modify:
                        modpath = file_io.resolve_asset_source_destination(
                            alPath(f), modify["Path"], relative=1
                        )
                        node["file"].setValue(str(modpath))

    return dependent_files

@logFunction('Collecting Nuke Node Information')
def getNodeInfo(metadata_fields):
    """collects all the important node information and
    counts all the nodes in current graph

    Returns:
        dict: metadata fields
    """

    nuke_loc = alPath(nuke.env['ExecutablePath'])
    count = 0

    for node in nuke.allNodes(recurseGroups=True):
        count += 1
        for plug in nuke.plugins():
            if not plug.startswith(nuke_loc.parent) and plug.endswith('.dll'):
                if node.Class() == alPath(plug).name:
                    metadata_fields['tags'].append({'Name': node.Class(), 'Type': 2})

    metadata_fields['NodeCount'] = count

    return metadata_fields

def alembicPatch(node):
    sceneView = node['scene_view'] 
    # get a list of all nodes stored in the abc file
    allItems = sceneView.getAllItems()
    # import all items into the ReadGeo node
    sceneView.setImportedItems(allItems)
    # set everything to selected (i.e. visible)
    sceneView.setSelectedItems(allItems)

@logFunction('Repathed:')
def applyRepath(new_path, library_storage=None):
    nodes = getAllPaths(returnNodes=1)
    new_path = alPath(new_path)
    done = []
    for node in nodes:
        filepath = alPath(node["file"].getValue())
        repath = new_path.mergePath(filepath)

        if repath is False:
            repath = new_path.mergePath(new_path.name / filepath)

        if repath is not False:
            node['file'].setValue(str(repath))
            if str(repath).endswith('.abc'):
                alembicPatch(node)
                node['repathed'].setValue(True)
        done.append('{} >> {}'.format(filepath, repath))
    return done


def captureViewport(save=None):
    mainWindow, panel = getMainWindows()
    try:
        glwidget = panel.children()[1]
    except:
        log.error('Cannot find nuke glwidget')

    w = glwidget.width()
    h = glwidget.height()
    glPixelStorei(GL_PACK_ALIGNMENT, 1)
    glReadBuffer(GL_FRONT)
    try:
        data = glReadPixels(0, 0, w, h, GL_RGBA, GL_UNSIGNED_BYTE)
    except:
        data = glReadPixels(0, 0, w, h, GL_RGB, GL_UNSIGNED_BYTE)
    if save:
        icon_img = file_io.makeIconQt(data, w, h)
        icon_img.save(save)