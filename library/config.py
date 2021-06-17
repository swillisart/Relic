import os

# -- Third-party --
from PySide6.QtCore import QCoreApplication, QSettings
from sequencePath import sequencePath as Path

# -- Globals --
NONE, TEXTURE, MODEL, ANIMATION, SHADER, AREA_LIGHT, IBL_PROBE, IES, _2D_ELEMENT, _3D_ELEMENT, REFERENCE, TOOL = range(12)


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

relic_preferences = Preferences()
