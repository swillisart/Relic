import json
import os
import sys
import re
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
URL_REGEX = re.compile(r'(\w+):\/\/(\w+):(\d{4})')

def videoToFrames(data, id):
    w, h, c = (288, 192, 3)
    userp = os.getenv('USERPROFILE').replace('\\', '/')
    local_mp4 = f'{userp}/.relic/{id}'
    with open(local_mp4, 'wb') as in_pipe:
        in_pipe.write(data)

    cap = cv2.VideoCapture(local_mp4)
    ret = True
    frames = []
    while ret:
        ret, frame = cap.read()
        if ret:
            img = QImage(frame, w, h, QImage.Format_RGB888)
            px = QPixmap.fromImageInPlace(img.rgbSwapped())
            frames.append(px)
    cap.release()
    os.remove(local_mp4)
    return frames

class libraryNetwork(QObject):
    
    imageStreamData = Signal(tuple)
    videoStreamData = Signal(list)

    def __init__(self, *args, **kwargs):
        super(libraryNetwork, self).__init__(*args, **kwargs)
        qApp or QApplication() # need QApplication instance for event loop.
        self.netman = QNetworkAccessManager(self)
        self.result = None
        self.errored = False

    def makeConnection(self, hostname=None):
        if hostname:
            self.hostname = hostname
        matches = re.match(URL_REGEX, self.hostname)

        if matches:
            protocol, domain, port = matches.groups()
            self.netman.connectToHost(domain, port=int(port))

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
        request = QNetworkRequest(QUrl(self.hostname + url))
        if data is not None:
            request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
            post_data = json.dumps(data).encode()
            response = self.netman.post(request, post_data)
        else:
            response = self.netman.get(request)

        loop = QEventLoop()
        response.finished.connect(self.requestFinished)
        response.finished.connect(loop.quit)
        response.errorOccurred.connect(self.onError)
        response.errorOccurred.connect(loop.quit)
        loop.exec_()
        if self.errored:
            self.errored = False
            return self.doRequest(url, data)
        return self.result

    @Slot(QNetworkReply)
    def requestFinished(self):
        response = self.sender()
        bytes_string = response.readAll()
        data = bytes_string.data()
        content_type = response.header(QNetworkRequest.ContentTypeHeader)
        if content_type == 'application/json':
            if not data:
                self.result = None
                return
            obj = json.loads(data)
            self.result = obj
        elif content_type == 'image/jpg':
            img = QPixmap()
            img.loadFromData(data)
            id = response.id
            self.imageStreamData.emit((img, id))
        elif content_type == 'video/mp4':
            id = response.id
            frames = videoToFrames(data, id)
            self.videoStreamData.emit(frames)

        if response:
            response.deleteLater()

    @Slot(QNetworkReply)
    def onError(self):
        self.errored = True
        response = self.sender()
        if response.NetworkError == QNetworkReply.NetworkError.ProtocolInvalidOperationError:
            self.makeConnection()
        else:
            print(response.errorString())

    def doStream(self, url, id):
        url = QUrl(self.hostname + url)
        request = QNetworkRequest(url)
        response = self.netman.get(request)
        response.id = id
        #loop = QEventLoop()
        response.finished.connect(self.requestFinished)
        #response.finished.connect(loop.quit)
        response.errorOccurred.connect(self.onError)
        #loop.exec_()


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
