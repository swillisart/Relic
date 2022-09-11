import av
import io
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import QRunnable
from sequence_path.main import SequencePath as Path

def videoToFrames(data):
    frames = []
    buffer = io.BytesIO()
    buffer.write(data.data())

    with av.open(buffer, mode='r', format='mp4') as container:
        for frame in container.decode(video=0):
            rgb = frame.to_rgb()
            array = rgb.to_ndarray()
            h, w, c = array.shape
            img = QImage(array, w, h, QImage.Format_RGB888)
            px = QPixmap.fromImageInPlace(img)
            frames.append(px)
    buffer.close()
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
