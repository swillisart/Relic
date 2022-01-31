import os
import logging

# -- Third-party --
from PySide6.QtCore import QCoreApplication, QSettings
from sequencePath import sequencePath as Path
from strand.client import StrandClient
from qtshared6.utils import Preferences

# -- Globals --
NONE, TEXTURE, MODEL, ANIMATION, SHADER, AREA_LIGHT, IBL, IES, _2D_ELEMENT, _3D_ELEMENT, REFERENCE, TOOL = range(12)

# Valid Extensions in an exclusive list
MOVIE_EXT = ['.mov', '.mxf', '.mp4', '.mkv']
SHADER_EXT = ['.mtlx', '.osl', '.sbsar']
RAW_EXT = ['.cr2', '.arw', '.dng', '.cr3', '.nef']
FILM_EXT = ['.r3d', '.arriraw']
HDR_EXT = ['.exr', '.hdr']
LDR_EXT = ['.jpg', '.png', '.tif', '.tga', '.jpeg']
LIGHT_EXT = ['.ies']
DCC_EXT = ['.ma', '.mb', '.max', '.hip', '.usd']
TOOLS_EXT = ['.nk', '.mel', '.py', '.hda', '.exe']
GEO_EXT = ['.abc', '.fbx']
TEXTURE_EXT = HDR_EXT + LDR_EXT

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
    for extension in TEXTURE_EXT:
        if str(filepath).endswith(extension):
            return 'source_images'
    for extension in GEO_EXT:
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
    if path.sequence_path or path.ext in MOVIE_EXT:
        path = path.suffixed('_proxy', '.mp4')
    else:
        path = path.suffixed('_proxy', '.jpg')

    if not path.exists:
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
        'host': ['http://localhost:8000/', 'https://yoursite.shotgunstudio.com/api/v1/'],
    }

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
