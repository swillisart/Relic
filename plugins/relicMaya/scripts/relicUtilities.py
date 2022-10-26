import os
import maya.cmds as cmds
import maya.mel as mel

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

def setMeshMetadata(selection, asset):
    meshes = []
    # Set the poly count
    if cmds.nodeType(selection) == "transform":
        meshes.extend(cmds.listRelatives(
            selection, allDescendents=True, type="mesh", fullPath=1))

    cmds.select(meshes, r=True)
    asset.polycount = cmds.polyEvaluate(face=True)

    # set the bounding box
    size3 = []
    for axis in cmds.polyEvaluate(boundingBox=1):
        size3.append(str(round(abs(axis[0]) + axis[1], 2)))
    asset.resolution = ' x '.join(size3)

def importAllReferences():
    # Get a list of all top-level references in the scene.
    all_ref_paths = cmds.file(q=True, reference=True) or []  

    for ref_path in all_ref_paths:
        is_loaded = cmds.referenceQuery(ref_path, isLoaded=True)
        if is_loaded: 
            cmds.file(ref_path, importReference=True)
            # If the reference had any nested references they will now become top-level references, so recollect them.
            new_ref_paths = cmds.file(q=True, reference=True) or []
            for new_ref_path in new_ref_paths:
                if new_ref_path not in all_ref_paths:
                    all_ref_paths.append(new_ref_path)

def collapseAllNamespaces(selection):
    """Clears all namespaces in the scene by iteratively collapsing
    the top level namespaces till none remain.

    Parameters
    ----------
    selection : list
        maya selection list to update.
    """
    cmds.namespace(setNamespace=':')
    namespaces = cmds.namespaceInfo(listOnlyNamespaces=True, recurse=False)
    DEFAULT_NAMESPACES = ['shared', 'UI']
    if not len(namespaces) > 2: 
        return selection # means only default namespaces remain... exit the infinite loop.
    for namespace in namespaces[:-2]:
        if namespace in DEFAULT_NAMESPACES:
            continue
        cmds.namespace(rm=namespace, mergeNamespaceWithRoot=True, force=True)
        for index, selected in enumerate(selection):
            # similar to x.replace(y+':', '') but zero chance of a non-namespace rename
            if selected.startswith(namespace):
                selection[index] = selected[len(namespace)+1:]
    return collapseAllNamespaces(selection)

def clearAllShading():
    """Removes all objects from Maya's shading groups / engines.
    """
    sel = cmds.ls(type='shadingEngine')
    DEFAULT_SHADING_ENGINES = ['initialShadingGroup', 'initialParticleSE']
    for item in sel:
        if item not in DEFAULT_SHADING_ENGINES:
            cmds.sets(e=1, clear=item)

def clearAllRenderLayers():
    """Switches the current layer to masterlayer and deletes everything in Render Setup.
    """
    from maya.app.renderSetup.model import (
        override, selector, collection, renderLayer, renderSetup)

    rs = renderSetup.instance()
    default_rl = rs.getDefaultRenderLayer()
    rs.switchToLayer(default_rl)
    rs.clearAll()

def selectedCenteroid(selection):
    one_over = 1 / len(selection)
    center = [0,0,0]
    for sel in selection:
        c = cmds.objectCenter(sel, gl=True) # gl=global but is a reserved key
        center[0] += (c[0] * one_over)
        center[1] += (c[1] * one_over)
        center[2] += (c[2] * one_over)
    return center

def generateThumbnails(selection, file_path):
    # Make turntable orbit camera
    orbitCameraShape = cmds.createNode("camera")
    cmds.setAttr(orbitCameraShape + '.focalLength', 55)
    orbitCamera = cmds.listRelatives(orbitCameraShape, p=True)[0]
    cmds.rename(orbitCamera, "orbitCam")
    mel.eval("lookThroughModelPanel orbitCam modelPanel4;")
    cmds.setAttr("hardwareRenderingGlobals.multiSampleEnable", 1)
    cmds.viewFit(selection, f=0.9)
    center = selectedCenteroid(selection)
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
    out_movie_file = mov_path.suffixed('', '.mp4')
    if out_movie_file.exists():
        os.remove(str(out_movie_file))
    os.rename(str(mov_path), str(out_movie_file))
    # Cleanup
    cmds.displayPref(wsa="full")
    cmds.delete('orbitCam')
