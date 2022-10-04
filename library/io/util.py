import av
import io
import glm
from oiio.OpenImageIO import ImageSpec

from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import QRunnable
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
            rgb = frame.to_rgb()
            array = rgb.to_ndarray()
            h, w, c = array.shape
            img = QImage(array, w, h, QImage.Format_RGB888)
            px = QPixmap.fromImageInPlace(img)
            frames.append(px)
    return frames

class LocalThumbnail(QRunnable):

    def __init__(self, data, callback, item=False):
        super(LocalThumbnail, self).__init__()
        self.callback = callback
        self.item = item
        self.data = data

    def run(self):
        if isinstance(self.data, Path):
            if not self.data.exists():
                return
            image = QPixmap(str(self.data))
            self.callback(image)
        else:
            frames = videoToFrames(self.data)
            self.callback(frames)
        if self.item:
            self.item.emitDataChanged()


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

    def makeDivisble(self):
        self.x = self.divisible_width

    @property
    def divisible_width(self):
        return self.x - (self.x % 16)

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
