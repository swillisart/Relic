import operator

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from qtshared2.widgets import HoverTintButton

class playerWidget(QFrame):
    def __init__(self, parent, main_view, timeline_view, **kwargs):
        super(playerWidget, self).__init__(parent, **kwargs)
        self.timeline_view = timeline_view
        self.main_view = main_view
        self.setLayout(QHBoxLayout(self))
        layout = self.layout()

        self.play = HoverTintButton(
            ':resources/play.png',
            ':resources/timeStop.png',
        )
        self.play.clicked.connect(self.timeline_view.controller.play)
        self.jump_last = HoverTintButton(
            ':resources/timeFwd.png'
        )
        self.jump_last.clicked.connect(self.timeline_view.controller.jumpLast)
        self.jump_first = HoverTintButton(
            ':resources/timeRew.png'
        )
        self.jump_first.clicked.connect(self.timeline_view.controller.jumpFirst)
        self.next_annotation = HoverTintButton(
            ':resources/timeNext.png'
        )
        self.next_annotation.clicked.connect(lambda x: self.timeline_view._toAnnotatedFrame(operator.gt))
        self.previous_annotation = HoverTintButton(
            ':resources/timePrev.png'
        )
        self.previous_annotation.clicked.connect(lambda x: self.timeline_view._toAnnotatedFrame(operator.lt))


        layout.addWidget(self.jump_first)
        layout.addWidget(self.previous_annotation)
        layout.addWidget(self.play)
        layout.addWidget(self.next_annotation)
        layout.addWidget(self.jump_last)