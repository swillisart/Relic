from PySide2.QtCore import ( 
    QFile
)
import ctypes


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]

    def __init__(self):
        # have to initialize this to the size of MEMORYSTATUSEX
        self.dwLength = ctypes.sizeof(self)
        super(MEMORYSTATUSEX, self).__init__()


class MemoryStatus(object):
    def __init__(self):
        self._memstatus = None

    def __enter__(self):
        if not self._memstatus:
            stat = MEMORYSTATUSEX()
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            self._memstatus = stat
        return self._memstatus

    def __exit__(self, *args):
        return False

MEMORY_STATUS = MemoryStatus()

def memoryTotal(gigabytes=False):
    """Gets total size of available memory in Gigabytes (Gb's)

    Returns
    -------
    float
        gigabyte value
    """
    with MEMORY_STATUS as m:
        if gigabytes:
            result = m.ullTotalPhys / 1E+9
        else:
            result = m.ullTotalPhys

        return result

def memoryLoad():
    """Gets the current memory in-use 

    Returns
    -------
    float
        percent of memory in use
    """
    with MEMORY_STATUS as m:
        return m.dwMemoryLoad 

def fitsInMemory(bytes_load):
    memory_limit = memoryTotal()
    gigabytes_remaining = (memory_limit -  bytes_load) / 1E+9
    if gigabytes_remaining < 1:
        return False
    else:
        return True

def openResource(resource_path):
    resource_file = QFile(resource_path)
    if resource_file.open(QFile.ReadOnly):
        result = resource_file.readAll()
    return result
