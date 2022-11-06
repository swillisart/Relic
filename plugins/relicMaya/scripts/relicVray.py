import maya.cmds as cmds
import vray

from relicUtilities import texturedLight

def areaLight(path):
    light = cmds.shadingNode('VrayAreaLightShape', asLight=1)
    cmds.setAttr(light + '.useRectTex', 1)
    texturedLight(light, '.rectTex', path)

def iesLight(path):
    light = cmds.shadingNode('VRayLightIESShape', asLight=1)
    plug_path = str(path).replace('/', '\\') # this specific node requires backslashes.
    cmds.setAttr(light + '.iesFile', plug_path)
    cmds.select(light, r=1)

def domeLight(path):
    light = cmds.shadingNode('VRayLightDomeShape', asLight=1)
    cmds.setAttr(light + '.useDomeTex', 1)
    texturedLight(light, '.domeTex', path)
