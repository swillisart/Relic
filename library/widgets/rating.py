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
        self.rating = value

    def getValue(self):
        return self.rating

    def mousePressEvent(self, event):
        super(Rating, self).mousePressEvent(event)
        if event.buttons() == Qt.LeftButton:
            # Get the closest rating index by relative click position
            axis = event.x()
            previous = self.rating
            for i, x in enumerate(Rating.SPACES):
                if axis >= x:
                    self.rating = self.rating.__class__(i + 1)
        self.update()

    def mouseDoubleClickEvent(self, event):
        super(Rating, self).mouseDoubleClickEvent(event)
        self.rating = self.rating.__class__(0)

    @staticmethod
    def paint(painter, rect, value):
        # Value must be a RatingField<int>
        if type(value) is int:
            return
        painter.save()
        painter.translate(rect.topLeft())
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        
        # Draw all disabled images
        for i, x in enumerate(Rating.SPACES):
            pix_rect = QRect(x, 0, ICO_SIZE, ICO_SIZE)
            # Draw Enabled images in range up the current value
            if i < value:
                painter.drawPixmap(pix_rect, value.icon)
            else:
                painter.drawPixmap(pix_rect, value.disabled)


        painter.restore()

    def paintEvent(self, event):
        super(Rating, self).paintEvent(event)
        painter = QPainter(self)
        Rating.paint(painter, self.rect(), self.rating)
