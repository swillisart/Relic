import json
import os
import sys
import math
from subprocess import PIPE, Popen
from functools import partial

# -- Third-Party --
import cv2
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Signal, Slot, QUrl, QObject, QEventLoop, QSaveFile, QIODevice, QFile
from PySide6.QtNetwork import (
    QNetworkReply,
    QNetworkRequest,
    QNetworkAccessManager,
    QTcpSocket,
)

from sequencePath import sequencePath as Path

# -- Globals --
DEVNULL = open(os.devnull, "w")


class libraryNetwork(QObject):
    
    imageStreamData = Signal(tuple)
    videoStreamData = Signal(object)

    def __init__(self, *args, **kwargs):
        super(libraryNetwork, self).__init__(*args, **kwargs)
        qApp or QApplication() # need QApplication instance for event loop.
        self.netman = QNetworkAccessManager(self)
        self.netman.connectToHost('localhost', port=8000)
        self.result = None

    def setHostName(self, hostname):
        self.hostname = hostname

    def doRequest(self, url, data=None):
        url = QUrl(self.hostname + url)
        request = QNetworkRequest(url)
        if data is not None:
            request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
            post_data = json.dumps(data).encode()
            self.response = self.netman.post(request, post_data)
        else:
            self.response = self.netman.get(request)
    
        loop = QEventLoop()
        self.response.finished.connect(self.onFinished)
        self.response.finished.connect(loop.quit)
        #self.response.readyRead.connect(self.onReady)
        self.response.errorOccurred.connect(self.onError)
        loop.exec()
        #if self.response:
        #    self.response.deleteLater()
        return self.result

    @Slot()
    def onFinished(self):
        bytes_string = self.response.readAll()
        data = bytes_string.data()
        content_type = self.response.header(QNetworkRequest.ContentTypeHeader)
        if content_type == 'application/json':
            if not data:
                self.result = None
                return
            obj = json.loads(data)
            self.result = obj
        elif content_type == 'image/jpg':
            img = QPixmap()
            img.loadFromData(data)
            id = self.response.id
            self.imageStreamData.emit((img, id))
        elif content_type == 'video/mp4':
            w, h, c = (256, 144, 3)
            local_mp4 = os.getenv('USERPROFILE').replace('\\', '/') + "/in_pipe"
            
            with open(local_mp4, "wb") as in_pipe:
                in_pipe.write(data)
 
            cap = cv2.VideoCapture(local_mp4)
            ret = True
            while ret:
                ret, frame = cap.read()
                if ret:
                    img = QImage(frame, w, h, QImage.Format_RGB888)
                    px = QPixmap.fromImageInPlace(img.rgbSwapped())
                    self.videoStreamData.emit(px)
            cap.release()

    @Slot()
    def onReadyRead(self, asset, fileobj):
        if self.response:# and self.response.bytesAvailable() > 10000:
            #size = sys.getsizeof(data)
            #print(f'zip recieved: {size}/{asset.filesize}, for file: {asset.relativePath} ')
            fileobj.write(self.response.readAll())

    @Slot()
    def downloadFinished(self, asset, fileobj):
        content_type = self.response.header(QNetworkRequest.ContentTypeHeader)
        #if content_type == 'application/x-zip-compressed':
        fileobj.commit()

    @Slot(QNetworkReply.NetworkError)
    def onError(self, code: QNetworkReply.NetworkError):
        print(self.response.errorString())

    def doStream(self, url, id):
        url = QUrl(self.hostname + url)
        request = QNetworkRequest(url)
        self.response = self.netman.get(request)
        self.response.id = id
        # DEBUG STUFF
        loop = QEventLoop()
        self.response.finished.connect(self.onFinished)
        self.response.finished.connect(loop.quit)
        #self.response.readyRead.connect(self.onReady)
        self.response.errorOccurred.connect(self.onError)
        loop.exec()
        #if self.response:
        #    self.response.deleteLater()

    def download(self, url, asset):
        url = QUrl(self.hostname + url)
        request = QNetworkRequest(url)
        self.response = self.netman.get(request)
        #fileobj = open('E:/library/test.png', 'wa')
        fileobj = QSaveFile('E:/library/test.png')
        fileobj.open(QIODevice.WriteOnly)
        write = partial(self.onReadyRead, asset, fileobj)
        finish = partial(self.downloadFinished, asset, fileobj)
        self.response.readyRead.connect(write)
        self.response.finished.connect(finish)
        self.response.errorOccurred.connect(self.onError)

    def run(self):
        pass

class AssetDatabase(object):

    def __init__(self, database):
        self.accessor = libraryNetwork()
        #thread = QThread()
        #self.accessor.moveToThread(thread)
        self.accessor.setHostName(database)
        #thread.started.connect(self.accessor.run)
        #thread.start()
