import sys
import os
import json
from functools import partial
library_path = os.path.dirname(os.path.dirname(pathd))
sys.path.append(library_path)

# -- Module --
import plugins
from sequencePath import sequencePath as Path
from library.objectmodels import (
    allCategories,
    lighting,
    shading,
    mayatools,
    modeling,
    elements,
    references,
    db,
    polymorphicItem,
)

# Ids and category variables are injected into this
# function via drop handler callbacks
# EXAMPLE: exec(stringarg, None, {"ids": items[2:], "category": items[1]})
asset_list = []
for key, value in json.loads(assets).items():
    constructor = locals()[str(key)]
    for x in value:
        asset = constructor(**x)
        asset_item = polymorphicItem(fields=asset)
        asset_list.append(asset_item)


# Iterate through all the available plugins in the directory and attempt
# to fetch the host applications Qt Main window to Parent to.
# Will only succeed if the plugin is able to provide them.
app_plugin = None

all_plugins = plugins.retrievePlugins(plugins_path)

for x in all_plugins:
    try:
        mainWindow, relic_panel = x.getMainWindows()
        app_plugin = x
        print('loaded plugin: {}'.format(app_plugin))
        break
    except Exception as exerr:
        print('Failed to load plugin {} with error {}'.format(x, exerr))
if not app_plugin:
    print('Unable to load plugin make sure \
        you have the host applications plugin properly installed.')

for asset in asset_list:
    asset_data = asset.data(polymorphicItem.Object)
    # Load the icon from local path
    lp = asset_data.local_path
    icon_path = lp.parents(0) / (lp.name + '_icon.jpg')
    asset_data.icon = QPixmap(str(icon_path))
    app_plugin.assetDropAction(asset_data)

relic_assets = relic_panel.findChild(QWidget, 'RelicSceneAssets')
relic_assets.updateGroups(asset_list, clear=False)

# Resolve dependent asset links
"""
links = db.retrieveLinks(x.Links, assets_only=True)
unresolved = app_plugin.iterateUnresolvedAssets()
for x in unresolved:
    if x:
        for link in links:
            link.Path = library_storage / str(link.Path)
            app_plugin.processUnresolvedAssets(x, link)
"""

# Resolve dependent files
dependent_files = app_plugin.getAllPaths(library_only=True)
#destination = alPath(alPrefs.getPref("project_path").format(os.getenv(alPrefs.getPref("project_var"))))

# If there are no direct files add the main file to search for <ASSET>_sources

if not dependent_files:
    dependent_files.extend([x.path for x in asset_list])

print(dependent_files)
#data = db.accessor.doRequest('retrieveAssets', search_data)

#function = partial(app_plugin.applyRepath, library_storage=library_storage)
#log.debug('Building partial function for thread execution using \
#func: {} library_storage: {}'.format(app_plugin.applyRepath, library_storage))
#popup = file_io.progressNotifier(
#    mainWindow, relic_panel, dependent_files, destination, function=function
#)
#log.debug(
#    'Made progress popup using args \
#    dependent: {} destination: {}'.format(dependent_files, destination)
#)
