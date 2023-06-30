from datetime import datetime

# -- Third-party --
from relic.qt import *
from relic.qt.delegates import (ImageableMixin, BaseDelegateMixin, CompactImageIndicator, Title, BaseItemDelegate, IconIndicator, TextDecorationIndicator, ProgressIndicator,
                                TitleIndicator, TextIndicator, Statuses, Indication, ItemDispalyModes, AdvanceAxis)
from relic.qt.widgets import BaseTreeView

from extra_types.flag_enum import EnumAuto, Enumerant
from extra_types.composable import Attributable
from extra_types.properties import slot_property


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

#Types.Screenshot.bro = 'noway'
#TypesIndicator.Screenshot.bro = 'nope'

tl = Qt.AlignTop | Qt.AlignLeft
tr = Qt.AlignTop | Qt.AlignRight
bl = Qt.AlignBottom | Qt.AlignLeft
br = Qt.AlignBottom | Qt.AlignRight


class DateFormat(datetime):

    def __str__(self):
        return self.strftime('%m/%d/%y\n%H:%M')


class CaptureItem(ImageableMixin):
    __slots__ = ['path', 'status', 'type', 'progress', 'description', '_image', '_date', '_size', '_title']

    INDICATIONS = [
        Indication('progress', ProgressIndicator, bl, AdvanceAxis.Y),
        Indication('image', CompactImageIndicator, tl, AdvanceAxis.X),
        Indication('type', TypesIndicator, bl, AdvanceAxis.NONE),
        Indication('status', Statuses, bl, AdvanceAxis.NONE),
        Indication('title', TitleIndicator, tl, AdvanceAxis.NONE),
        #Indication('resolution', TextIndicator, tr, AdvanceAxis.NONE),
        #Indication('count', TextDecorationIndicator, br, AdvanceAxis.NONE),
    ]

    def __init__(self, path):
        self.path = path
        self.status = int(Statuses.Local)
        self.type = 1
        self.progress = 0
        self._image = None
        self.description = ''

    @property
    def name(self):
        return self.path.name

    @slot_property
    def title(self):
        return Title(self.path.name)

    @slot_property
    def date(self):
        return DateFormat.fromtimestamp(self.path.datemodified)

    @slot_property
    def size(self):
        return self.path.size


class HistoryTreeView(BaseDelegateMixin, BaseTreeView):

    onExecuted = Signal(QModelIndex)

    def __init__(self, *args, **kwargs):
        super(HistoryTreeView, self).__init__(*args, **kwargs)
        self.setIndentation(3) # 3
        self.setDragEnabled(True)
        self.setAcceptDrops(False)
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
