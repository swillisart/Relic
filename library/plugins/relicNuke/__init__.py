try:
    from alNukePlugin import (
        getAllPaths,
        export_selection,
        assetDropAction,
        applyRepath,
        getMainWindows,
        iterateUnresolvedAssets,
        processUnresolvedAssets
    )
except Exception as exerr:
    print(__name__, exerr)
    import asset_library.file_io as file_io
    # Outside of nuke

EXT = [".nk"]
APP_INDEX = 2
NAME = 'Nuke'

def ingestHandler(source, destination):
    old_icon_path = source.parents(0) / (source.name + "_icon.png")
    if old_icon_path.exists:
        icon_path = source.parents(0) / (source.name + "_icon.jpg")
        file_io.makeIconFile(old_icon_path, icon_path)
    try:
        print('ingestHandler', source, destination)
    except Exception:
        pass