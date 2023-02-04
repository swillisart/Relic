
from ctypes import *
from ctypes.wintypes import *
from comtypes import *

from functools import partial
from PySide6.QtCore import QRect


IsWindowVisible = cdll.user32.IsWindowVisible
GetWindowRect = cdll.user32.GetWindowRect
EnumWindows = cdll.user32.EnumWindows
EnumWindowsProc = CFUNCTYPE(c_bool, c_int, POINTER(c_int))
RECT = c_long * 4

GetWindowText = cdll.user32.GetWindowTextW
GetWindowTextLength = cdll.user32.GetWindowTextLengthW

# Reference: https://learn.microsoft.com/en-us/windows/win32/api/shobjidl_core/nn-shobjidl_core-ivirtualdesktopmanager


def _check(hresult: HRESULT):
    if hresult:
        raise Exception(f"HRESULT: {hresult}")

class IVirtualDesktopManager(IUnknown):
    _iid_ = GUID("{A5CD92FF-29BE-454C-8D04-D82879FB3F1B}")

    _methods_ = [
        COMMETHOD(
            [],
            HRESULT,
            "IsWindowOnCurrentVirtualDesktop",
            (["in"], HWND, "topLevelWindow"),
            (["out"], LPBOOL, "onCurrentDesktop"),
        ),
        COMMETHOD(
            [],
            HRESULT,
            "GetWindowDesktopId",
            (["in"], HWND, "topLevelWindow"),
            (["out"], POINTER(GUID), "desktopId"),
        ),
        COMMETHOD(
            [],
            HRESULT,
            "MoveWindowToDesktop",
            (["in"], HWND, "topLevelWindow"),
            (["in"], POINTER(GUID), "desktopId"),
        ),
    ]

    def GetWindowDesktopId(self, hwnd: HWND) -> GUID:
        desktop_id = GUID()
        _check(self.__com_GetWindowDesktopId(hwnd, pointer(desktop_id)))
        return desktop_id

    def IsWindowOnCurrentVirtualDesktop(self, hwnd: HWND) -> bool:
        value = BOOL()
        _check(self.__com_IsWindowOnCurrentVirtualDesktop(hwnd, pointer(value)))
        return value.value

    def MoveWindowToDesktop(self, hwnd: HWND, desktop_id: GUID):
        _check(self.__com_MoveWindowToDesktop(hwnd, pointer(desktop_id)))


virtual_desktop_manager: IVirtualDesktopManager = CoCreateInstance(
    GUID("{AA509086-5CA9-4C25-8F95-589D3C07B48A}"), interface=IVirtualDesktopManager
)


# High level functions
 
def getForegroundWindow():
    return windll.user32.GetForegroundWindow()

def getRectangle(hwnd):
    rect = RECT()
    GetWindowRect(hwnd, byref(rect))
    rectangle = QRect()
    rectangle.setLeft(rect[0])
    rectangle.setTop(rect[1])
    rectangle.setRight(rect[2])
    rectangle.setBottom(rect[3])
    return rectangle

def isWindowOccluded(hwnd):
    main_rectangle = getRectangle(hwnd)
    result = []
    f = partial(_iterateWindowHandles, result, main_rectangle)
    print('') # CRITICAL. Not sure why this only works if there is a print here.
    EnumWindows(EnumWindowsProc(f), 0)
    if len(result) > 0 and result[0] != hwnd:
        return True
    else:
        return False

def _iterateWindowHandles(result, main_rectangle, hwnd, lParam):
    if IsWindowVisible(hwnd) and virtual_desktop_manager.IsWindowOnCurrentVirtualDesktop(hwnd):
        rectangle = getRectangle(hwnd)
        if rectangle.intersects(main_rectangle):
            result.append(hwnd)


if __name__ == "__main__":
    virtual_desktop_manager.GetWindowDesktopId(getForegroundWindow())
