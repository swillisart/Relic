import json
import logging

# -- Third-Party --
from PySide6.QtCore import (QObject, QUrl, Signal, Slot, QThread, Qt)
from PySide6.QtWebSockets import QWebSocket
from PySide6.QtWidgets import QApplication

# -- First-Party --
from qt_logger import attachHandler

# -- Module --
import relic.config as config
LOG = logging.getLogger('RelicClientSession')
attachHandler(LOG)


class QSocket(QWebSocket):
    def sendTextMessage(self, message):
        LOG.debug('Sending command to server : %s' % message)
        super(QSocket, self).sendTextMessage(message)

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
    callback = Signal(str)

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

    URI = config.SOCKET
    IMAGE = 0
    VIDEO = 1
    onVideoReceived = Signal(str, bytes)
    onImageReceived = Signal(str, bytes)

    def __init__(self, url: str = None):
        super(RelicClientSession, self).__init__()
        qApp or QApplication() # need QApplication instance for event loop.
        self.count = 0
        self.socket = QSocket()
        self.socket.textMessageReceived.connect(self.receiveText)
        self.socket.binaryMessageReceived.connect(self.receiveBinary)#, Qt.QueuedConnection)
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
        self.videostream.callback.connect(self.prepVideo)
        #self.imagestream.callback.connect(self.prepImage)
        self.video_path = None
        self.image_path = None

    @Slot(str)
    def prepVideo(self, data):
        self.video_path = data
        self._binaryReciever = self.receiveVideo

    @Slot(str)
    def prepImage(self, data):
        self.image_path = data
        self._binaryReciever = self.receiveImage

    def bindTo(self, hostname: str):
        self.socket.close()
        self.socket.open(QUrl(hostname))

    def rebind(self):
        self.bindTo(RelicClientSession.URI)

    @Slot(str)
    def receiveText(self, text):
        LOG.debug(f'Received message: {text}')
        result = json.loads(text)
        for cmd, data in result.items():
            caller = getattr(self, cmd.lower())
            caller.callback.emit(data)

    @Slot(bytes)
    def receiveBinary(self, data):
        self._binaryReciever(data)

    def _binaryReciever(self, data):
        pass

    def receiveImage(self, data):
        self.onImageReceived.emit(self.image_path, data)

    def receiveVideo(self, data):
        if self.video_path is None:
            LOG.warning('Late video data received.')
            return # late video data received.
        path = self.video_path
        self.onVideoReceived.emit(path, data)
        self.video_path = None

if __name__ == '__main__':
    import sys
    #app = QApplication(sys.argv)
    session = RelicClientSession(RelicClientSession.URI)
    sys.exit(qApp.exec())
