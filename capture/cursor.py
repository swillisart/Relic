from ctypes import windll, pointer, POINTER, sizeof, byref, Structure
from ctypes import c_ulong, c_int, c_void_p
import ctypes.wintypes as wintypes

from PySide6.QtGui import QPixmap, QImage, QIcon
import numpy as np

# CursorInfo.hCursor (windows handle)
CURSOR_MAP = {
    'arrow': 65541,
    'up': 65549,
    'cross': 65547,
    'wait': 65545,
    'ibeam': 65543,
    'nwse': 65551,
    'nesw': 65553,
    'ew': 65555,
    'ns': 65557,
    'move': 65559,
    'link': 65569,
    'unavail': 65561,
    'busy': 65563,
    'helpsel': 65565,
}


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

def build_cursor_data(cursor_size, extension=''):
    CURSOR_LOCATION = ':cursors/{}.svg'
    bitmaps_by_hcursor = {}

    for name, hcursor in CURSOR_MAP.items():
        path = CURSOR_LOCATION.format(name)
        cursor = QIcon(path)
        w = cursor_size; h = cursor_size
        svg_pix = cursor.pixmap(w, h)
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
        
        bitmaps_by_hcursor[hcursor] = (color_array, mask_array)

    return bitmaps_by_hcursor


def create_cursor_info():
    cursor_info = CursorInfo()
    cursor_info.cbSize = sizeof(cursor_info)
    GetCursorInfo(byref(cursor_info))
    return cursor_info


def get_cursor_arrays(bitmaps_by_hcursor, default=CURSOR_MAP['arrow']):
    cursor_info = create_cursor_info()
    try:
        bitmaps = bitmaps_by_hcursor[cursor_info.hCursor]
    except KeyError:
        #print('Unknown cursor: %d', cursor_info.hCursor)
        bitmaps = bitmaps_by_hcursor[default]

    return cursor_info, bitmaps
