from functools import partial
import av
import io
import glm
from oiio.OpenImageIO import ImageSpec

from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import QRunnable, QObject, Signal, Qt, QThreadPool
from sequence_path.main import SequencePath as Path


def videoToFrames(data):
    buffer = io.BytesIO()
    buffer.write(data.data())
    frames = readMovieFrames(buffer)
    buffer.close()
    return frames

def readMovieFrames(file_obj):
    frames = []
    with av.open(file_obj, mode='r', format='mp4') as container:
        for frame in container.decode(video=0):
            array = frame.to_ndarray(format='rgb24')
            h, w, c = array.shape
            img = QImage(array, w, h, QImage.Format_RGB888)
            frames.append(img)
    return frames

def loadPreviewImage(asset, slot=None, index=None):
    if index:
        on_complete = partial(slot or onIconLoad, index)
    else:
        on_complete = partial(setattr, asset, 'icon')
    icon_path = asset.network_path.suffixed('_icon', '.jpg')
    worker = LocalThumbnail(icon_path)
    worker.signals.finished.connect(on_complete)
    QThreadPool.globalInstance().start(worker)

def loadIcon(index, slot=None):
    on_complete = partial(slot or onIconLoad, index)
    asset = index.data(Qt.UserRole)
    icon_path = asset.network_path.suffixed('_icon', '.jpg')
    worker = LocalThumbnail(icon_path)
    worker.signals.finished.connect(on_complete)
    QThreadPool.globalInstance().start(worker)

def onIconLoad(index, image):
    asset = index.data(Qt.UserRole)
    asset.icon = image
    index.emitDataChanged()

class ImageSignals(QObject):
    finished = Signal(QImage)

class VideoSignals(QObject):
    finished = Signal(list)

class LocalVideo(QRunnable):

    def __init__(self, data):
        super(LocalVideo, self).__init__()
        self.signals = VideoSignals()
        self.data = data

    def run(self):
        frames = videoToFrames(self.data)
        self.signals.finished.emit(frames)

class LocalThumbnail(QRunnable):

    def __init__(self, path):
        super(LocalThumbnail, self).__init__()
        self.signals = ImageSignals()
        self.path = path

    def run(self):
        if not self.path.exists():
            return
        image = QImage()
        image.load((str(self.path)))
        self.signals.finished.emit(image)


class ImageDimensions(glm.vec2):
    def __init__(self, width, height, channels=3):
        super(ImageDimensions, self).__init__(width, height)
        self.channels = channels

    def __str__(self):
        return f'{self.w}x{self.h}x{self.channels}'    

    @classmethod
    def fromArray(cls, array):
        h, w, c = array.shape
        obj = cls(w, h, channels=c)
        return obj

    @classmethod
    def fromSpec(cls, spec):
        obj = cls(spec.full_width, spec.full_height, spec.nchannels)
        return obj

    @classmethod
    def fromQImage(cls, qimage):
        w, h = qimage.size().toTuple()
        channels = 3
        if qimage.isGrayscale():
            channels = 1
        elif qimage.hasAlphaChannel():
            channels = 4
        obj = cls(w, h, channels)
        return obj

    @classmethod
    def fromQSize(cls, size, channels=3):
        obj = cls(size.width(), size.height(), channels)
        return obj

    def makeDivisble(self, height=False):
        self.x = self.divisible_width
        if height:
            self.y = self.divisible_height

    @property
    def divisible_width(self, height=False):
        return int(self.x) - (int(self.x) % 16)

    @property
    def divisible_height(self, height=False):
        return int(self.y) - (int(self.y) % 16)

    @property
    def aspect(self):
        return self.w / self.h

    @property
    def aspectReversed(self):
        return self.h / self.w

    @property
    def w(self):
        return int(self.x)

    @w.setter
    def w(self, value):
        self.x = value

    @property
    def h(self):
        return int(self.y)

    @h.setter
    def h(self, value):
        self.y = value

    def asSpec(self, ptype):
        return ImageSpec(self.w, self.h, self.channels, ptype)
