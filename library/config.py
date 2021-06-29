import os
import logging

# -- Third-party --
from PySide6.QtCore import QCoreApplication, QSettings
from sequencePath import sequencePath as Path
from kohainetwork.client import KohaiClient

# -- Globals --
NONE, TEXTURE, MODEL, ANIMATION, SHADER, AREA_LIGHT, IBL_PROBE, IES, _2D_ELEMENT, _3D_ELEMENT, REFERENCE, TOOL = range(12)
# Valid Extensions
MOVIE_EXT = ['.mov', '.mxf', '.mp4', '.mkv']
SHADER_EXT = ['.mtlx', '.osl', '.sbsar']
RAW_EXT = ['.cr2', '.arw', '.dng', '.cr3']
HDR_EXT = ['.exr', '.hdr']
LDR_EXT = ['.jpg', '.png', '.tif', '.tga', '.jpeg']
LIGHT_EXT = ['.ies']
DCC_EXT = ['.ma', '.mb', '.max', '.hip']
TOOLS_EXT = ['.nk', '.mel', '.py', '.hda', '.exe']
GEO_EXT = ['.abc', '.fbx']

KOHAI = KohaiClient()

INGEST_PATH = Path(os.getenv('userprofile')) / '.relic/ingest'


def kohaiPreview(path):
    KOHAI.requestFileLoad(str(path))
    if KOHAI.errored:
        #TODO: launch Kohai 
        pass

class pref(object):
    def __init__(self, value, default, options):
        self.value = value
        self.default = default
        self.options = options

class Preferences(object):

    defaults = {
        'asset_preview_size': 288,
        'asset_preview_expand': True,
        'assets_per_page': 45,
        'local_storage': '',
        'fast_storage': '',
        'project_variable': 'show',
        'render_using': '',
        'relic_plugins_path': '',
        'edit_mode': True,
        'edit_mode': True,
        'references_color': '168, 58, 58',
        'modeling_color': '156, 156, 156',
        'elements_color': '198, 178, 148',
        'lighting_color': '188, 178, 98',
        'shading_color': '168, 58, 198',
        'software_color': '168, 168, 198',
        'mayatools_color': '66, 118, 150',
        'nuketools_color': '168, 168, 198',
    }

    options = {
        'asset_preview_size': [192, 288, 384],
    }

    def __init__(self):
        """Entry point to QSettings for all of the Applications preferences.
        when getting or setting attributes they are automatically saved on change
        to an .INI file in the USERPROFILE location.
        """

        QCoreApplication.setApplicationName('Relic')
        QSettings.setDefaultFormat(QSettings.IniFormat)
        self.user_settings()

    def __setattr__(self, name, value):
        QSettings().setValue(name, value)

    def __getattr__(self, name):
        pref = Preferences.defaults.get(name)
        return QSettings().value(name, pref)

    def user_settings(self):
        QCoreApplication.setOrganizationName(os.getenv('username'))
        path = Path(os.getenv('userprofile')) / '.relic/settings/'
        QSettings.setPath(QSettings.IniFormat, QSettings.UserScope, str(path))
        return QSettings()

    def shared_settings(self):
        QCoreApplication.setOrganizationName('ResArts')
        path = Path(os.getenv('userprofile')) / '.relic/shared_settings/'
        QSettings.setPath(QSettings.IniFormat, QSettings.SystemScope, str(path))
        return QSettings()

RELIC_PREFS = Preferences()

TRASH = Path(RELIC_PREFS.local_storage) / 'trash'

# -- Logging --
logging.basicConfig(
    filename='relic.log',
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
