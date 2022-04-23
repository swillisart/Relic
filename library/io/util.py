import os
import tempfile
from PySide6.QtGui import QImage, QPainter, QColor, QPixmap
from PySide6.QtCore import QSaveFile, QIODevice, QRunnable
import cv2

from sequence_path.main import SequencePath as Path

from library.config import USERPROFILE

video_cache = f'{USERPROFILE}/.relic/'

def videoToFrames(data):
    w = 288
    h = 192
    temp_file_path = tempfile.NamedTemporaryFile(
        suffix='.bin', dir=video_cache, delete=False)
    temp_file_path.close()
    in_dat = QSaveFile(temp_file_path.name)
    in_dat.open(QIODevice.WriteOnly)
    in_dat.write(data)
    in_dat.commit()
    cap = cv2.VideoCapture(temp_file_path.name)
    ret = True
    frames = []
    while ret:
        ret, frame = cap.read()
        if ret:
            img = QImage(frame, w, h, QImage.Format_RGB888)
            px = QPixmap.fromImageInPlace(img.rgbSwapped())
            frames.append(px)
    cap.release()
    os.unlink(temp_file_path.name)
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
