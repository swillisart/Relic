import json
import re
import os

# -- App --
import maya.cmds as cmds
# -- First-party --
from relic.local import (INGEST_PATH, Category, FileType, Nuketools, TempAsset,
                         getAssetSourceLocation)
from relic.scheme import AssetType, TagType, UserType, Class
from relic.config import PROJECT_VARIABLE
from sequence_path import Path

# -- Module --
from relicTranslator import getSelectionDependencies
from relicUtilities import (UndoThis, collapseAllNamespaces,
                            generateThumbnails, importAllReferences, clearAllRenderLayers)


def archiveScene(path=None):
    """Exports a scene from maya's selection into the library as an archive.
    """
    selection = cmds.ls(selection=True)
    if not selection:
        cmds.confirmDialog(title='Make Selection',
            message='Requires an object selection')
        return
    # These must be run without any errors in order to continue.
    try:
        clearAllRenderLayers()
        importAllReferences()
        selection = collapseAllNamespaces(selection)
    except Exception as exerr:
        cmds.confirmDialog(title='Archive error', icon='critical', button='Ok', message=exerr)
    asset = TempAsset()
    asset.name = selection[0].replace('|', '')
    asset.path = INGEST_PATH / asset.name / (asset.name + '.ma')
    asset.path.createParentFolders()
    asset.category = Category.MODELING.index
    asset.classification = Class.MODEL.flag
    asset.type = AssetType.ASSET.index
    asset.duration = 0
    asset.resolution = ''
    asset.tags = [{'name': 'archive', 'type': 0}, {'name': os.getenv(PROJECT_VARIABLE, 'noshow'), 'type': 0}]
    generateThumbnails(selection, asset.path)

    file_info = {}
    file_infos = cmds.fileInfo(q=1)

    if file_infos:
        file_info = dict(zip(file_infos[::2], file_infos[1::2]))
        mayaver = file_info.get('product')
        if mayaver:
            product = re.sub(re.compile(r"[^A-Za-z0-9]"), '', mayaver)
            asset.tags.append({'name': product, 'type': 1})

    plugin_info = {}
    plugin_infos = cmds.pluginInfo(q=1, pluginsInUse=1)
    if plugin_infos:
        plugin_info = dict(zip(plugin_infos[::2], plugin_infos[1::2]))

    for plugin, version in plugin_info.items():
        asset.tags.append({'name': '{}v{}'.format(plugin, version), 'type': 2})

    with UndoThis():
        # Get all dependent files and asset while assigning all other nodes
        # a parent namespace to link maya edits to.
        files_assets = [getSelectionDependencies(x) for x in selection]
        all_files = set()
        [all_files.update(files) for files, assets in files_assets]

        asset.dependencies = list(all_files)
        cmds.select(selection, r=True)
        asset.path = str(asset.path)
        cmds.file(asset.path, force=1, shader=True, options="v=0;", type="mayaAscii", exportSelected=1)

    return json.dumps([asset.asDict()])
