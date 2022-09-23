import ctypes
import os
from ctypes import windll, pointer, POINTER, sizeof, byref, Structure
from ctypes import c_ulong, c_int, c_void_p
import ctypes.wintypes as wintypes
from enum import Enum

from PySide6.QtCore import  QSize
from PySide6.QtGui import Qt, QPixmap, QPainter, QImage
from PySide6.QtSvgWidgets import QSvgWidget
import numpy as np
from extra_types.enums import IndexedEnum


class Cursors(IndexedEnum):
    # CursorInfo.hCursor (windows handle)
    ARROW = 65541
    UP = 65549
    CROSS = 65547
    WAIT = 65545
    IBEAM = 65543
    NS = 65557
    EW = 65555
    NESW = 65553
    NWSE = 65551
    MOVE = 65559
    LINK = 65569
    UNAVAIL = 65561
    HELPSEL = 65565
    BUSY = 65563


class POINT(Structure):
    _fields_ = [
        ("x", c_int),
        ("y", c_int),
    ]


class CursorInfo(Structure):
    _fields_ = [
        ("cbSize", wintypes.INT),
        ("flags", wintypes.INT),
        ('hCursor', c_void_p),
        ('ptScreenPos', POINT),
    ]


GetCursorInfo = windll.user32.GetCursorInfo
GetCursorInfo.argtypes = [POINTER(CursorInfo)]


CURSOR_ROOT = '{}/cursors/'.format(os.getenv('SystemRoot').replace('\\', '/'))
EXTENSION = '.svg'

def build_cursor_data(cursor_size):
    results = []
    SVG_WIDGET = QSvgWidget()
    SVG_RENDERER = SVG_WIDGET.renderer()
    for cursor in Cursors:
        SVG_WIDGET.load(CURSOR_ROOT + cursor.name.lower() + EXTENSION)
        w = cursor_size; h = cursor_size
        svg_pix = QPixmap(QSize(w, h))
        svg_pix.fill(Qt.transparent)
        painter = QPainter(svg_pix)
        SVG_RENDERER.render(painter)
        painter.end()
        img = svg_pix.toImage().mirrored(False, True)

        # Bit Mask
        mask = img.convertToFormat(QImage.Format_Alpha8)
        mask_array = np.frombuffer(mask.bits(), np.uint8)
        mask_array = mask_array.reshape((h, w, 1)).view(bool)
        mask_array = np.repeat(mask_array, 3, axis=2)

        # Color
        img = img.convertToFormat(QImage.Format_BGR888)
        color_array = np.frombuffer(img.bits(), np.uint8)
        color_array = np.clip(color_array.reshape((h, w, 3)), 1, 255)
        
        results.append([color_array, mask_array])
    return results

def get_cursor_info():
    cursor_info = CursorInfo()
    cursor_info.cbSize = sizeof(cursor_info)
    GetCursorInfo(byref(cursor_info))
    return cursor_info

def get_cursor_arrays(cursor_list):
    cursor_info = get_cursor_info() 
    try:
        index = Cursors(cursor_info.hCursor).index
    except ValueError: # Unknown cursor using default index
        index = Cursors.ARROW.index

    return cursor_info, cursor_list[index]
