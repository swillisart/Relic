import os
import logging
from extra_types.enums import AutoEnum, ListEnum
from enum import IntEnum

# -- Third-party --
from PySide6.QtCore import QCoreApplication, QSettings
from sequence_path.main import SequencePath as Path
from strand.client import StrandClient
from qtshared6.settings import Preferences

from relic.scheme import Classification
from relic.local import Extension, INGEST_PATH, getAssetSourceLocation

PEAK = StrandClient('peak')
USERPROFILE = os.getenv('userprofile')

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
