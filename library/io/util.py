import os
import tempfile
from PySide6.QtGui import QImage, QPainter, QColor, QPixmap
from PySide6.QtCore import QSaveFile, QIODevice, QRunnable
import cv2

from sequencePath import sequencePath as Path

from library.abstract_objects import ImageDimensions
from library.qt_objects import SinglePainter
from library.config import USERPROFILE

video_cache = f'{USERPROFILE}/.relic/'
icon_target = ImageDimensions(384, 256)
video_target = ImageDimensions(288, 192)

def makeIconQImage(img_data):
    # source and icon_target sizes
    size = ImageDimensions.fromArray(img_data.shape)
    icon_target = ImageDimensions(384, 256)

    # image format based on input data channel count 
    if size.c == 3:
        img_format = QImage.Format_RGB888
    else:
        img_format = QImage.Format_RGBA8888

    if size.w <= size.h:
        aspect_mult = size.aspect - icon_target.aspect
        w = (-aspect_mult * icon_target.h) / 2
        mult = ImageDimensions(w, 0)
    else:
        aspect_mult = size.aspectReversed - icon_target.aspectReversed
        h = (-aspect_mult * icon_target.w) / 2
        mult = ImageDimensions(0, h)

    # Create our Images
    img = QImage(img_data, size.w, size.h, img_format).mirrored(vertical=1)
    img_resized = img.scaled(icon_target.w, icon_target.h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    comp = QImage(icon_target.w, icon_target.h, img_format)
    
    # compositing together with a center offset for the smaller size axis 
    comp.fill(QColor(65, 65, 65))
    with SinglePainter(comp) as p:
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)
        p.drawImage(mult.w, mult.h, img_resized)

    return comp

def videoToFrames(data):
    w = 288; h = 192; c = 3
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

    def __init__(self, data, signal):
        super(LocalThumbnail, self).__init__(signal)
        self.signal = signal
        self.data = data

    def run(self):
        if isinstance(self.data, Path):
            if not self.data.exists():
                return
            image = QPixmap(str(self.data))
            self.signal(image)
        else:
            frames = videoToFrames(self.data)
            self.signal(frames)
