import os
import logging

# -- Third-party --
from sequence_path.main import SequencePath as Path
from qt_settings import Preferences

from relic.local import Extension
from intercom import Client

PEAK = Client('peak')
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

    DEFAULTS = {
        'assets_per_page': 25,
        'renderer': '',
        'edit_mode': False,
        'view_scale': 'Icon',
        'recurse_subcategories': 1,
        'denoise' : 0,
    }


RELIC_PREFS = RelicPreferences('Relic')

# -- Logging --
logging.basicConfig(
    filename=f'{USERPROFILE}/.relic/relic.log',
    format='%(asctime)-10s %(filename)s: %(funcName)10s %(message)s'
)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
