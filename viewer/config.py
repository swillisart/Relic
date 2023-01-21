from qtshared6.utils import Preferences
import os
import logging

class PeakPreferences(Preferences):
    DEFAULTS = {
        'exposure': 0.0,
        'gamma': 1.0,
        'source_view': '',
        'color_view': '',
    }
    OPTIONS = {
        'source_view': ['Preview', 'Proxy', 'Main'],
    }

PEAK_PREFS = PeakPreferences('Peak')
FILE_ACTIONS = ['New', 'Export', 'Exit'] # TODO: 'Open', 'Save',
ZOOM_RATIOS = ['', 25, 50, 100, 150, 200] # percent
VIEW_MODES = ['Single', 'Stack',]# 'Split/Wipe']
USERPROFILE = os.getenv('userprofile')

# -- Logging --
logging.basicConfig(
    #filename='./peak.log',
    format='%(filename)s, %(funcName)10s, %(message)s (%(asctime)s%(msecs)04d))',
    datefmt='%H:%M:%S',
)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
