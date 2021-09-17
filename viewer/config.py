from qtshared2.utils import AppPreferences

class Preferences(AppPreferences):
    DEFAULTS = {
        'exposure': 0.0,
        'gamma': 1.0,
        'source_view': '',
        'color_view': '',
    }
    OPTIONS = {
        'source_view': ['Proxy', 'Main'],
    }

PEAK_PREFS = Preferences('peak')
