import json
import re

# -- Third-Party --
from PySide6.QtCore import (QObject, QUrl, Signal, Slot)
from PySide6.QtWebSockets import QWebSocket
from PySide6.QtWidgets import QApplication

# -- Module -- 
from library.config import RELIC_PREFS

# -- Globals --
URL_REGEX = re.compile(r'(\w+):\/\/(\w+):(\d{4})')

class RelicCommand(QObject):

    callback = Signal(dict)
    socket = None
    def __init__(self):
        super(RelicCommand, self).__init__()

    def execute(self, data):
        self.socket.sendTextMessage(json.dumps({self.__class__.__name__: data}))

class SearchCategory(RelicCommand):

    callback = Signal(list)

    def execute(self, subcategory: str, text: str):
        data = (subcategory, text)
        super(SearchCategory, self).execute(data)

class RetrieveAssetNames(RelicCommand):
    callback = Signal(list)

    def execute(self, category_id: int):
        super(RetrieveAssetNames, self).execute(category_id)

class VideoStream(RelicCommand):
    callback = Signal(dict)

    def execute(self, data: str):
        self.socket.sendTextMessage(json.dumps({self.__class__.__name__: data}))

class SearchCategories(RelicCommand):
    pass

class UpdateSubcategoryCounts(RelicCommand):
    pass

class UpdateAssets(RelicCommand):
    pass

class SearchKeywords(RelicCommand):
    pass

class FetchAssets(RelicCommand):
    pass

class MoveAssets(RelicCommand):
    pass

class RetrieveAssets(RelicCommand):
    callback = Signal(list)

class RemoveRelationships(RelicCommand):
    callback = Signal(list)

class CreateRelationships(RelicCommand):
    callback = Signal(list)

class LinkSubcategories(RelicCommand):
    callback = Signal(list)

class GetCategories(RelicCommand):
    callback = Signal(list)

class DeleteAssets(RelicCommand):
    callback = Signal(list)

class CreateCollection(RelicCommand):
    callback = Signal(int)

class RetrieveLinks(RelicCommand):
    pass

class RetrieveDependencies(RelicCommand):
    pass

class CreateAssets(RelicCommand):
    pass

class CreateTag(RelicCommand):
    pass

class CreateUser(RelicCommand):
    pass

class CreateSubcategory(RelicCommand):
    pass

class RemoveAssets(RelicCommand):
    pass

class InitializePrimaryAsset(RelicCommand):
    pass

class RelicClientSession(QObject):

    URI = RELIC_PREFS.socket
    IMAGE = 0
    VIDEO = 1
    onVideoReceived = Signal(bytes)
    onImageReceived = Signal(str, bytes)

    def __init__(self, url: str = None):
        super(RelicClientSession, self).__init__()
        qApp or QApplication() # need QApplication instance for event loop.
        self.count = 0
        self.mode = self.IMAGE
        self.video_info = None
        self.image_info = None
        self.socket = QWebSocket()
        self.socket.textMessageReceived.connect(self.receiveText)
        self.socket.binaryMessageReceived.connect(self.receiveBinary)
        if url:
            self.bindTo(url)
        RelicCommand.socket = self.socket
        self.searchkeywords = SearchKeywords()
        self.searchcategories = SearchCategories()
        self.searchcategory = SearchCategory()
        self.retrieveassets = RetrieveAssets()
        self.getcategories = GetCategories()
        self.retrievedependencies = RetrieveDependencies()
        self.updatesubcategorycounts = UpdateSubcategoryCounts()
        self.updateassets = UpdateAssets()
        self.retrievelinks = RetrieveLinks()
        self.createcollection = CreateCollection()
        self.removerelationships = RemoveRelationships()
        self.createrelationships = CreateRelationships()
        self.linksubcategories = LinkSubcategories()
        self.createsubcategory = CreateSubcategory()
        self.createtag = CreateTag()
        self.createuser = CreateUser()
        self.createassets = CreateAssets()
        self.fetchassets = FetchAssets()
        self.moveassets = MoveAssets()
        self.removeassets = RemoveAssets()
        self.deleteassets = DeleteAssets()
        self.retrieveassetnames = RetrieveAssetNames()
        self.initializeprimaryasset = InitializePrimaryAsset()
        self.videostream = VideoStream()
        self.videostream.callback.connect(self.setupVideo)
        #self.imagestream.callback.connect(image_callback)

    @Slot(str)
    def setupVideo(self, data):
        self.video_info = data
        self.mode = self.VIDEO

    @Slot(str)
    def setupImage(self, data):
        self.image_info = data
        self.mode = self.IMAGE

    def bindTo(self, hostname: str):
        self.socket.close()
        self.socket.open(QUrl(hostname))

    def rebind(self):
        self.bindTo(RelicClientSession.URI)

    @Slot(str)
    def receiveText(self, text):
        result = json.loads(text)
        for cmd, data in result.items():
            caller = getattr(self, cmd.lower())
            caller.callback.emit(data)

    @Slot(bytes)
    def receiveBinary(self, data):
        self._receiver(data)

    def _receiver(self, data):
        if self.mode == self.IMAGE:
            self.onImageReceived.emit(self.image_info, data)
        elif self.mode == self.VIDEO:
            self.onVideoReceived.emit(data)


if __name__ == '__main__':
    import sys
    #app = QApplication(sys.argv)
    session = RelicClientSession(RelicClientSession.URI)
    sys.exit(qApp.exec())
