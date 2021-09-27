from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QPainter, Qt
from PySide6.QtWidgets import QWidget
import time

class ContextPainter(QPainter):
    def __init__(self, *args, **kwargs):
        super(ContextPainter, self).__init__(*args, **kwargs)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

    def __enter__(self):
        self.save()
        return self

    def __exit__(self, *exc):
        self.restore()
        return False


class SinglePainter(QPainter):
    def __init__(self, *args, **kwargs):
        super(SinglePainter, self).__init__(*args, **kwargs)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.end()
        return False


class AbstractDoubleClick(QWidget):

    aDoubleClicked = Signal(bool)

    def __init__(self, *args, **kwargs):
        super(AbstractDoubleClick, self).__init__(*args, **kwargs)
        self.last_clicked = time.time() - 1

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            timediff = -(self.last_clicked - time.time())
            if float(timediff) < float(0.25):
                self.aDoubleClicked.emit(True)
            self.last_clicked = time.time()
        return super(AbstractDoubleClick, self).mousePressEvent(event)
        