import operator

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from qtshared6.widgets import HoverTintButton

class playerWidget(QFrame):
    def __init__(self, parent, **kwargs):
        super(playerWidget, self).__init__(parent, **kwargs)
        self.setLayout(QHBoxLayout(self))
        layout = self.layout()

        self.play = HoverTintButton(
            ':resources/play.png',
            ':resources/timeStop.png',
        )
        self.play.clicked.connect(parent.frame_engine.timeline_control.play)
        self.play.setStatusTip('Start / Stop Playback')
        self.jump_last = HoverTintButton(
            ':resources/timeFwd.png'
        )
        self.jump_last.clicked.connect(parent.frame_engine.timeline_control.jumpLast)
        self.jump_last.setStatusTip('To Last Frame')
        self.jump_first = HoverTintButton(
            ':resources/timeRew.png'
        )
        self.jump_first.clicked.connect(parent.frame_engine.timeline_control.jumpFirst)
        self.jump_first.setStatusTip('To First Frame')
        self.next_annotation = HoverTintButton(
            ':resources/timeNext.png'
        )
        self.next_annotation.clicked.connect(lambda x: parent.timeline._toAnnotatedFrame(operator.gt))
        self.next_annotation.setStatusTip('Jump To Next Annotation')
        self.previous_annotation = HoverTintButton(
            ':resources/timePrev.png'
        )
        self.previous_annotation.clicked.connect(lambda x: parent.timeline._toAnnotatedFrame(operator.lt))
        self.previous_annotation.setStatusTip('Jump To Previous Annotation')


        layout.addWidget(self.jump_first)
        layout.addWidget(self.previous_annotation)
        layout.addWidget(self.play)
        layout.addWidget(self.next_annotation)
        layout.addWidget(self.jump_last)
