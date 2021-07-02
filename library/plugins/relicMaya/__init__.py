import os

try:
    from alMayaPlugin import (
        getAllPaths,
        export_selection,
        applyRepath,
        assetDropAction,
        getMainWindows,
        iterateUnresolvedAssets,
        processUnresolvedAssets
    )
except Exception as exerr:
    print(__name__, exerr)
    import asset_library.file_io as file_io
    # Outside of maya

LOCATION = "C:/Autodesk/Maya2018/bin"
EXT = [".mb", ".ma", ".mel"]
APP_INDEX = 1
NAME = 'Maya'

def ingestHandler(source, destination):
    old_icon_path = source.parents(0) / (source.name + "_icon.png")
    if old_icon_path.exists:
        icon_path = source.parents(0) / (source.name + "_icon.jpg")
        file_io.makeIconFile(old_icon_path, icon_path)
    try:
        swatch = source.parents(0) / '.mayaSwatches' / (source.path.name + '.swatch')
        destination = destination / (destination.name + '_icon.png')
        cmd = '{}/imgcvt.exe "{}" "{}"'.format(LOCATION, swatch, destination)
        if swatch.exists:
            os.system(cmd)
    except Exception:
        pass