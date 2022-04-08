# -- Built-in --
from enum import Enum, IntEnum

# -- Third-party --
from PySide6.QtCore import QMargins, QPoint, QRect, Qt, QSortFilterProxyModel, Slot, QItemSelection, QModelIndex
from PySide6.QtGui import (QColor, QFont, QPainter, QRegion, QPainterPath, QPixmap,
                            QDrag, QCursor, QAction, QIcon)
from PySide6.QtWidgets import (QHBoxLayout, QListView, QStyle,
                               QStyledItemDelegate, QAbstractItemView, QTreeView, QTreeWidgetItem,
                               QWidget, QStyleOption, QMenu)
from qtshared6.delegates import (BaseItemDelegate, IconIndicator, NamedEnum, AutoEnum,
                                 Statuses, scale_icon)
from qtshared6.utils import polymorphicItem

class Types(IconIndicator):
    Screenshot = {
        'data': scale_icon(QPixmap(':type/screenshot.png')),
        'item': None,
        'ext': ['.png'],
        'actions': []}
    Video = {
        'data': scale_icon(QPixmap(':type/video.png')),
        'item': None,
        'ext': ['.mp4'],
        'actions': []}
    Animated = {
        'data': scale_icon(QPixmap(':type/gif.png')),
        'item': None,
        'ext': ['.webp', '.gif'],
        'actions': []}


class HistoryTreeFilter(QSortFilterProxyModel):

    def lessThan(self, left, right):
        leftData = self.sourceModel().data(left)
        rightData = self.sourceModel().data(right)
        return leftData > rightData

    def filterAcceptsRow(self, sourceRow, sourceParent):
        index = self.sourceModel().index(sourceRow, 0, sourceParent)

        if index.isValid():
            obj = index.data(polymorphicItem.Object)
            if not obj: # Top level items are not polymorphic so keep them
                return True
            else:
                match = self.filterRegularExpression().match(obj.name)
                if match.hasMatch():
                    return True

        return False


class CaptureItem(object):
    __slots__ = ['name', 'path', 'count', 'status', 'type', 'progress', 'date', 'thumbnail']

    def __init__(self, path):
        self.name = path.name
        self.path = path
        self.count = 1
        self.status = int(Statuses.Local)
        self.type = 1
        self.progress = 0
        self.date = None
        self.thumbnail = None

    class Indicators(AutoEnum):
        type = {'data': Types, 'rect': QRect(12, -22, 16, 16)}
        status = {'data': Statuses, 'rect': QRect(28, -22, 16, 16)}

    class Columns(AutoEnum):
        name = {'data': 0}
        date = {'data': 6}
        count = {'data': 2}

class HistoryTreeView(QTreeView):

    def __init__(self, *args, **kwargs):
        super(HistoryTreeView, self).__init__(*args, **kwargs)
        self.setMouseTracking(True)
        self.setIndentation(16)
        self.setDragEnabled(True)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setDragDropMode(QAbstractItemView.DragOnly)
        self.setDefaultDropAction(Qt.IgnoreAction)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setItemDelegate(BaseItemDelegate(self))
        self.customContextMenuRequested.connect(self.customContextMenu)
        self.clicked.connect(self.expand_index)
        self.setSortingEnabled(True)

    @property
    def index_selection(self):
        indices = self.selectedIndexes()
        if not indices:
            return
        for index in indices:
            yield index

    @Slot(QModelIndex)
    def expand_index(self, index):
        state = not self.isExpanded(index)
        self.setExpanded(index, state)

    @Slot(QPoint)
    def customContextMenu(self, pos):
        index = self.indexAt(pos)
        if not index:
            return # Selection was empty.
        context_menu = QMenu(self)
        obj = index.data(polymorphicItem.Object)
        if obj:
            obj_type = Types(obj.type)
            actions = self.actions() + obj_type.actions
        else:
            actions = self.actions()
        [context_menu.addAction(action) for action in actions]
        context_menu.exec(QCursor.pos())
