import json
import os
import sys
import math
import requests
from subprocess import PIPE, Popen
from functools import partial

# -- Third-Party --
import cv2
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import QTimer, Signal, Slot, QUrl, QObject, QEventLoop, QSaveFile, QIODevice, QFile, QRunnable
from PySide6.QtNetwork import (
    QNetworkReply,
    QNetworkRequest,
    QNetworkAccessManager,
    QTcpSocket,
)

from sequencePath import sequencePath as Path

# -- Globals --
DEVNULL = open(os.devnull, "w")
session = requests.session()

class libraryNetwork(QObject):
    
    imageStreamData = Signal(tuple)
    videoStreamData = Signal(object)

    def __init__(self, *args, **kwargs):
        super(libraryNetwork, self).__init__(*args, **kwargs)
        qApp or QApplication() # need QApplication instance for event loop.
        self.netman = QNetworkAccessManager(self)
        self.result = None
        self.response = None

    def makeConnection(self, hostname=None):
        if hostname:
            self.hostname = hostname
        self.netman.connectToHost('localhost', port=8000)

    def doRequestWithResult(self, url, data=None):
        if data:
            data = json.dumps(data)
            r = session.post(self.hostname + url, data=data)
        else:
            r = session.get(self.hostname + url)
        try:
            result = r.json()
        except:
            result = None
        return result

    def doRequest(self, url, data=None):
        self.makeConnection()
        # CRITICAL. Wait on response before attempting request
        while self.response:
            loop = QEventLoop()
            QTimer.singleShot(450, loop.quit)
            loop.exec_()
            if not self.response:
                break

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
        self.response.errorOccurred.connect(self.onError)
        loop.exec()
        self.response = None
        return self.result

    @Slot()
    def onFinished(self):
        if not self.response:
            print('finish aborted')
            return
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
            w, h, c = (288, 192, 3)
            userp = os.getenv('USERPROFILE').replace('\\', '/')
            local_mp4 = f'{userp}/.relic/pipe_mp4_preview'
            with open(local_mp4, 'wb') as in_pipe:
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
            os.remove(local_mp4)

        if self.response:
            self.response = None

    @Slot(QNetworkReply.NetworkError)
    def onError(self, code: QNetworkReply.NetworkError):
        if code == QNetworkReply.NetworkError.ProtocolInvalidOperationError:
            self.makeConnection()
        else:
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


class AssetDatabase(object):

    def __init__(self, database):
        self.accessor = libraryNetwork()
        self.accessor.makeConnection(database)


class LocalThumbnail(QRunnable):
    
    def __init__(self, img, signal):
        super(LocalThumbnail, self).__init__(signal)
        self.signal = signal
        self.img = img

    def run(self):
        if self.img.exists:
            image = QPixmap(str(self.img))
            self.signal(image)
