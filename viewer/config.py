from qtshared6.utils import Preferences

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
FILE_ACTIONS = ['New', 'Exit'] # TODO: 'Open', 'Save',
ZOOM_RATIOS = ['', 25, 50, 100, 150, 200] # percent