import maya.cmds as cmds
import mtoa

from relicUtilities import texturedLight

def areaLight(path):
    light = mtoa.utils.createLocator('aiAreaLight', asLight=True)
    texturedLight(light[0], '.color', path)

def iesLight(path):
    light = mtoa.utils.createLocator('aiPhotometricLight', asLight=True)
    cmds.setAttr(light[0] + '.aiFilename', plug_path)
    cmds.select(light[0], r=1)

def domeLight(path):
    light = mtoa.utils.createLocator('aiSkyDomeLight', asLight=1)
    texturedLight(light[0], '.color', path)
