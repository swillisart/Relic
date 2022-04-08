import os
import logging
from extra_types.enums import AutoEnum, ListEnum
from enum import IntEnum
# -- Third-party --
from PySide6.QtCore import QCoreApplication, QSettings
from sequence_path.main import SequencePath as Path
from strand.client import StrandClient
from qtshared6.utils import Preferences

# -- Globals --

class Classification(IntEnum):
    NONE = 0
    IMAGE = 1
    MODEL = 2
    ANIMATION = 3
    SHADER = 4
    AREA_LIGHT = 5
    IBL = 6
    IES = 7
    ELEMENT_2D = 8
    ELEMENT_3D = 9
    REFERENCE = 10
    TOOL = 11
    BLENDSHAPE = 12
    SOFTWARE = 13
    PLUGIN = 14
    APPLICATION = 15


# Valid Extensions in an exclusive list
class Extension(ListEnum):
    MOVIE = ['.mov', '.mxf', '.mp4', '.mkv']
    RAW = ['.cr2', '.arw', '.dng', '.cr3', '.nef']
    FILM = ['.r3d', '.arriraw']
    HDR = ['.exr']
    LDR = ['.jpg', '.png', '.tif', '.jpeg']
    LIGHT = ['.ies']
    SHADER = ['.mtlx', '.osl', '.sbsar']
    DCC = ['.ma', '.mb', '.max', '.hip']
    TOOLS = ['.nk', '.mel', '.py', '.hda', '.exe']
    GEO = ['.abc', '.fbx', '.usd']
    TEXTURE = HDR + LDR

PEAK = StrandClient('peak')
USERPROFILE = os.getenv('userprofile')
INGEST_PATH = Path(USERPROFILE) / '.relic/ingest'

INGEST_PATH.path.mkdir(parents=True, exist_ok=True)

def getAssetSourceLocation(filepath):
    """Given a filepath this deterimines the relative subfolder location of the 
    unique dependency for this asset.

    Parameters
    ----------
    filepath : str

    Returns
    -------
    str
        one of 3 image, cache or misc depending on matching valid extension
    """
    for extension in Extension.TEXTURE:
        if str(filepath).endswith(extension):
            return 'source_images'
    for extension in Extension.GEO:
        if str(filepath).endswith(extension):
            return 'source_caches'

    return 'source_misc'

def peakLoad(path):
    PEAK.sendPayload(str(path))
    if PEAK.errored:
        cmd = f'start peak://{path}'
        os.system(cmd)

def peakPreview(path):
    path.checkSequence()
    if path.sequence_path or path.ext in Extension.MOVIE:
        path = path.suffixed('_proxy', '.mp4')
    else:
        path = path.suffixed('_proxy', '.jpg')
    if not path.exists():
        return False
    peakLoad(path)
    return True


class RelicPreferences(Preferences):

    defaults = {
        'assets_per_page': 25,
        'render_using': '',
        'edit_mode': False,
        'view_scale': 2,
        'recurse_subcategories': 1,
        'denoise' : 0,
    }

    options = {
        'host': ['ws://localhost:8000/session', 'https://yoursite.shotgunstudio.com/api/v1/'],
    }

    def __getattr__(self, name):
        result = super(RelicPreferences, self).__getattr__(name)
        if result is None:
            result = RelicPreferences.defaults.get(name)
        return result

RELIC_PREFS = RelicPreferences('Relic')

# -- Logging --
logging.basicConfig(
    filename=f'{USERPROFILE}/.relic/relic.log',
    format='%(asctime)-10s %(filename)s: %(funcName)10s %(message)s'
)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

def logFunction(message=None):
    def logExceptions(func):
        def logWrapper(*args, **kwargs):
            try:
                value = func(*args, **kwargs)
                if message:
                    msg = '{}: {} returning: {}'
                    log.debug(msg.format(func.__name__, message, value))
                return value
            except Exception as exerr:
                log.error('\n\tModule: {}\n\tFunction: {}\n\tError: {}'.format(
                    func.__module__, func.__name__, verboseException()) #exerr)
                )

        return logWrapper
    return logExceptions

def verboseException():
    import linecache
    import sys
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    exception_message = 'LINE {} "{}"): {}'.format(
        lineno, line.strip(), exc_obj
    )
    return exception_message
