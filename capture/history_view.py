# -- Built-in --
from enum import Enum, IntEnum

# -- Third-party --
from PySide6.QtCore import QDir, QMargins, QPoint, QRect, QSize, Qt, QUrl, QMimeData, QSortFilterProxyModel, Slot, QItemSelection, QModelIndex
from PySide6.QtGui import (QColor, QFont, QPainter, QRegion, QPainterPath, QPixmap,
                           QStandardItemModel, QDrag, QCursor, QAction, QIcon)
from PySide6.QtWidgets import (QHBoxLayout, QListView, QStyle,
                               QStyledItemDelegate, QAbstractItemView, QTreeView, QTreeWidgetItem,
                               QWidget, QStyleOption, QMenu)
from qtshared6.delegates import (BaseItemDelegate, IconIndicator, NamedEnum, AutoEnum,
                                 Statuses)
from qtshared6.utils import polymorphicItem

def scale_icon(pix: QPixmap):
    return pix.scaled(16,16, Qt.KeepAspectRatio, Qt.SmoothTransformation)

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

    class Indicators(NamedEnum):
        TYPE =       (4, {'data': Types, 'rect': QRect(12, -22, 16, 16)})
        STATUS =     (3, {'data': Statuses, 'rect': QRect(28, -22, 16, 16)})

    class Columns(AutoEnum):
        NAME = {'data': 0}
        DATE = {'data': 6}
        COUNT = {'data': 2}

    def attrFromIndicator(self, indicator):
        return getattr(self, self.__slots__[indicator])


class CaptureItemModel(QStandardItemModel):

    def mimeData(self, indices):
        paths = []
        for index in indices:
            obj = index.data(polymorphicItem.Object)
            if isinstance(obj, polymorphicItem):
                paths.append(QUrl.fromLocalFile(str(obj.path)))

        drag = QDrag(self)
        mimeData = QMimeData()
        mimeData.setUrls(paths)
        drag.setMimeData(mimeData)

        # Capture the rendered item and set to mime data's pixmap
        size = BaseItemDelegate.VIEW_MODE.item_size
    
        pixmap = QPixmap(size)
        pixmap.fill(QColor(68,68,68))
        painter = QPainter(pixmap)
        #painter.setRenderHint(QPainter.Antialiasing, True)
        delegate = BaseItemDelegate()
        option = QStyleOption()
        option.state = QStyle.State_MouseOver
        option.rect = QRect(QPoint(0,0), size)
        delegate.paint(painter, option, indices[0])
        painter.end()
        drag.setPixmap(pixmap)
        drag.exec(Qt.CopyAction)


class HistoryTreeView(QTreeView):

    def __init__(self, *args, **kwargs):
        super(HistoryTreeView, self).__init__(*args, **kwargs)
        self.setMouseTracking(True)
        self.setIndentation(16)
        self.setDragEnabled(True)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.CopyAction)
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
