from PySide6.QtGui import QImage, QPainter, QColor#, QPixmap
from PySide6.QtCore import Qt

from library.abstract_objects import ImageDimensions
from library.qt_objects import SinglePainter


def makeIconQImage(img_data):
    # source and target sizes
    size = ImageDimensions.fromArray(img_data.shape)
    target = ImageDimensions(384, 256)

    # image format based on input data channel count 
    if size.c == 3:
        img_format = QImage.Format_RGB888
    else:
        img_format = QImage.Format_RGBA8888

    if size.w <= size.h:
        aspect_mult = size.aspect - target.aspect
        w = (-aspect_mult * target.h) / 2
        mult = ImageDimensions(w, 0)
    else:
        aspect_mult = size.aspectReversed - target.aspectReversed
        h = (-aspect_mult * target.w) / 2
        mult = ImageDimensions(0, h)

    # Create our Images
    img = QImage(img_data, size.w, size.h, img_format).mirrored(vertical=1)
    img_resized = img.scaled(target.w, target.h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    comp = QImage(target.w, target.h, img_format)
    
    # compositing together with a center offset for the smaller size axis 
    comp.fill(QColor(65, 65, 65))
    with SinglePainter(comp) as p:
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)
        p.drawImage(mult.w, mult.h, img_resized)

    return comp
