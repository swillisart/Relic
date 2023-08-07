from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

ICO_SIZE = 16

class Rating(QFrame):

    SPACES = [i*ICO_SIZE for i in range(5)]

    def __init__(self, parent):
        super(Rating, self).__init__(parent)
        self.rating = 0
        self.setAutoFillBackground(True)
        self.setMouseTracking(True)

    def setValue(self, value):
        self.rating = value or 0

    def getValue(self):
        return self.rating
    
    def value(self):
        return self.rating

    def mousePressEvent(self, event):
        #super(Rating, self).mousePressEvent(event)
        if event.buttons() == Qt.LeftButton:
            # Get the closest rating index by relative click position
            axis = event.x()
            previous = self.rating
            for i, x in enumerate(Rating.SPACES):
                if axis >= x:
                    self.rating = i + 1
        self.update()

    def mouseDoubleClickEvent(self, event):
        super(Rating, self).mouseDoubleClickEvent(event)
        self.rating = 0

    @classmethod
    def paint(cls, painter, rect, value):
        # Value must be a RatingField<int>
        painter.save()
        painter.translate(rect.topLeft())
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        value = value or 0
        # Draw all disabled images
        for i, x in enumerate(cls.SPACES):
            pix_rect = QRect(x, 0, ICO_SIZE, ICO_SIZE)
            # Draw Enabled images in range up the current value
            if i < value or 0:
                painter.drawPixmap(pix_rect, cls.icon)
            else:
                painter.drawPixmap(pix_rect, cls.disabled)

        painter.restore()

    def paintEvent(self, event):
        super(Rating, self).paintEvent(event)
        painter = QPainter(self)
        rect = self.rect() - QMargins(3,3,3,3)
        self.paint(painter, rect, self.rating)
        painter.end()
