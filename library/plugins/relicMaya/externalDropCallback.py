"""
To use, make sure that externalDropCallback.py is in your MAYA_PLUG_IN_PATH
then do the following:

import maya.cmds as cmds
cmds.loadPlugin("externalDropCallback.py")

Drag and drop events should appear in the script editor output.
"""

import sys
import json
import maya.OpenMaya as OpenMaya
import maya.OpenMayaUI as OpenMayaUI
from PySide2.QtCore import QDataStream, QIODevice, QByteArray

class PyExternalDropCallback(OpenMayaUI.MExternalDropCallback):
    instance = None

    def __init__(self):
        OpenMayaUI.MExternalDropCallback.__init__(self)

    def externalDropCallback(self, doDrop, controlName, data):
        retstring = "External Drop:  doDrop = %d,  controlName = %s" % (
            doDrop,
            controlName,
        )
        """
        # Mouse button
        if data.mouseButtons() & OpenMayaUI.MExternalDropData.kLeftButton:
            str += ", LMB"
        if data.mouseButtons() & OpenMayaUI.MExternalDropData.kMidButton:
            str += ", MMB"
        if data.mouseButtons() & OpenMayaUI.MExternalDropData.kRightButton:
            str += ", RMB"

        # Key modifiers
        if data.keyboardModifiers() & OpenMayaUI.MExternalDropData.kShiftModifier:
            str += ", SHIFT"
        if data.keyboardModifiers() & OpenMayaUI.MExternalDropData.kControlModifier:
            str += ", CONTROL"
        if data.keyboardModifiers() & OpenMayaUI.MExternalDropData.kAltModifier:
            str += ", ALT"
        """
        #print(data.formats())

        if data.hasFormat(b'application/x-relic') and doDrop:
            drop_script = data.urls()[0]
            """
            if drop_script.endswith('.pyw'):
                try:
                    with open(drop_script, 'rb') as fp:
                        script = fp.read()
                        exec(script, None, {'pathd': drop_script})
                except Exception as exerr:
                    print(exerr)
                return True
            """
            with open(drop_script, 'rb') as fp:
                script = fp.read()
                exec(script, None, {'assets': data.text(), 'pathd': drop_script})
            return True

        """
        if data.hasUrls():
            urls = data.urls()
            for (i,url) in enumerate(urls):
                str += (", url[%d] = %s" % (i, url))
        if data.hasHtml():
            str += (", html = %s" % data.html())
        if data.hasColor():
            color = data.color()
            str += (", color = (%d, %d, %d, %d)" % (color.r, color.g, color.b, color.a))
        if data.hasImage():
            str += (", image = true")
        str += "\n"
        """
        return OpenMayaUI.MExternalDropCallback.kMayaDefault


def initializePlugin(plugin):
    try:
        PyExternalDropCallback.instance = PyExternalDropCallback()
        OpenMayaUI.MExternalDropCallback.addCallback(PyExternalDropCallback.instance)
        sys.stdout.write("Successfully registered callback: PyExternalDropCallback\n")
    except Exception:
        sys.stderr.write("Failed to register callback: PyExternalDropCallback\n")
        raise


def uninitializePlugin(plugin):
    try:
        OpenMayaUI.MExternalDropCallback.removeCallback(PyExternalDropCallback.instance)
        sys.stdout.write("Successfully deregistered callback: PyExternalDropCallback\n")
    except Exception:
        sys.stderr.write("Failed to deregister callback: PyExternalDropCallback\n")
        raise
