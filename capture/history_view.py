from datetime import datetime

# -- Third-party --
from extra_types.composable import Attributable
from extra_types.flag_enum import EnumAuto, Enumerant
from extra_types.properties import slot_property

from relic.qt import *
from relic.qt.role_model.delegates import (AdvanceAxis,
                                RoleItemDelegate, CompactImageIndicator,
                                DurationIndicator, ExtentIndicator,
                                IconIndicator, ImageableMixin, Indication,
                                ItemDispalyModes, ProgressIndicator,
                                TextDecorationIndicator, TextIndicator, Title,
                                TitleIndicator, MarginIndicator)
from relic.qt.role_model.views import RoleTreeView, RoleViewDelegateMixin

import av


class CaptureType(Attributable, Enumerant):
    __slots__ = ['ext', 'actions']


class Types(EnumAuto):
    Screenshot = CaptureType(['.png'], [])
    Video = CaptureType(['.mp4'], [])   
    Animated = CaptureType(['.gif'], [])


class TypesIndicator(EnumAuto):
    Screenshot = IconIndicator(':type/screenshot.png')
    Video = IconIndicator(':type/video.png')
    Animated = IconIndicator(':type/gif.png')


TL = Qt.AlignTop | Qt.AlignLeft
TR = Qt.AlignTop | Qt.AlignRight
BL = Qt.AlignBottom | Qt.AlignLeft
BR = Qt.AlignBottom | Qt.AlignRight

class DateFormat(datetime):

    def __str__(self):
        return self.strftime('%m/%d/%y\n%H:%M')


class CaptureItem(ImageableMixin):
    __slots__ = ['path', 'type', 'progress', 'description', '_image', '_date', '_size', '_title', '_resolution', '_duration']

    INDICATIONS = [
        #Indication('progress', ProgressIndicator, BL, AdvanceAxis.Y),
        Indication('image', CompactImageIndicator, TL, AdvanceAxis.X),
        Indication(QRect(0,0,0,0), MarginIndicator, TL, AdvanceAxis.X | AdvanceAxis.Y),
        Indication('title', TitleIndicator, TL, AdvanceAxis.NONE),
        #Indication('type', TypesIndicator, BL, AdvanceAxis.NONE),
        Indication('duration', DurationIndicator, BR, AdvanceAxis.NONE),
        Indication(QRect(0,0,0,0), MarginIndicator, Qt.AlignLeft, AdvanceAxis.X),
        Indication('resolution', ExtentIndicator, BL, AdvanceAxis.X),
    ]

    def __init__(self, path):
        self.path = path
        self.type = 1
        self.progress = 0
        self._image = None
        self.description = ''

    @property
    def name(self):
        return self.path.name

    @slot_property
    def duration(self):
        if self.path.ext in ['.mp4', '.gif']:
            in_container = av.open(str(self.path))
            stream = in_container.streams.video[0]
            framerate = float(stream.rate)
            duration = stream.duration * float(stream.time_base)
            in_container.close()
            return duration
        else:
            return 0

    @slot_property
    def resolution(self):
        """Opens an image file to get its size without reading the pixels."""
        path = self.path
        if path.ext == '.mp4':
            in_container = av.open(str(path))
            in_stream = in_container.streams.video[0]
            width = in_stream.width
            height = in_stream.height
            in_container.close()
            result = '{}x{}'.format(width, height)
            return result

        # Path is an image (Screenshot).
        reader = QImageReader(str(path))
        size = reader.size()
        result = '{}x{}'.format(size.width(), size.height())
        return result

    @slot_property
    def title(self):
        return Title(self.path.name)

    @slot_property
    def date(self):
        return DateFormat.fromtimestamp(self.path.datemodified)

    @slot_property
    def size(self):
        return self.path.size


class HistoryTreeView(RoleViewDelegateMixin, RoleTreeView):

    onExecuted = Signal(QModelIndex)

    def __init__(self, *args, **kwargs):
        super(HistoryTreeView, self).__init__(*args, **kwargs)
        self.setIndentation(3) # 3
        self.setDragEnabled(True)
        self.setAcceptDrops(False)
        self.setDragDropOverwriteMode(False)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setDragDropMode(QAbstractItemView.DragOnly)
        self.setDefaultDropAction(Qt.IgnoreAction)  
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        # For performance if the widget/delegates are not animated
        #self.setAttribute(Qt.WA_StaticContents, True)
        self.customContextMenuRequested.connect(self.customContextMenu)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        #self.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.setSortingEnabled(True)
        self.setUniformRowHeights(True)

    @Slot(QPoint)
    def customContextMenu(self, pos):
        index = self.indexAt(pos)
        if not index:
            # Selection was empty.
            return super(HistoryTreeView, self).customContextMenu(pos) 
        context_menu = QMenu(self)
        obj = index.data(Qt.UserRole)
        if isinstance(obj, CaptureItem):
            obj_type = Types(obj.type)
            actions = self.actions() + obj_type.actions
        else:
            actions = self.actions()
        context_menu.addActions(actions)
        context_menu.exec(QCursor.pos())

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Space:
            self.onExecuted.emit(self.lastIndex)
