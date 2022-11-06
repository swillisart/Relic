# -- Third-party --
from relic.qt import *
from relic.qt.delegates import (BaseItemDelegate, IconIndicator,
                                Statuses, Indication)

TREE_GROUP_STYLE = """
QTreeView {
    border: none;
	alternate-background-color: rgb(75,75,75);
    background-color: rgb(48, 48, 48);
    padding-top: 0px;
}
QTreeView::item {
    border-top: none;
    padding-right: 8px;
    padding-left: 3px;
    margin-top: 1px;
    margin-bottom: 1px;
}
QTreeView::item:has-children {
    background-color: rgb(93, 93, 93);
}
QTreeView::branch {
    padding: 4px;
    margin-top: 1px;
    margin-bottom: 1px;
    margin-left: 1px;
    margin-right: -3px;
    border-left: 2px solid rgb(43,43,43);
	border-radius: 3px 3px 0px 0px;
}
QTreeView::branch:has-siblings:!adjoins-item {
    border-image: none;
}
QTreeView::branch:has-siblings:adjoins-item {
    border-image: none;
}
QTreeView::branch:!has-children:!has-siblings:adjoins-item {
    border-image: none;
}
QTreeView::branch:has-children:!has-siblings:closed,
QTreeView::branch:closed:has-children:has-siblings {
    background-color: rgb(93, 93, 93);
    border-left: 3px solid rgb(93, 93, 93);
    border-radius: 0px 0px 3px 0px;
}
QTreeView::branch:open:has-children:!has-siblings,
QTreeView::branch:open:has-children:has-siblings  {
    background-color: rgb(93, 93, 93);
    border-left: 2px solid rgb(93, 93, 93);
    border-radius: 0px 0px 3px 0px;
}
"""

class TypesIndicator(IconIndicator):
    Screenshot = ':type/screenshot.png'
    Video = ':type/video.png'
    Animated = ':type/gif.png'


class HistoryTreeFilter(QSortFilterProxyModel):
    def __init__(self, filter_id):
        super(HistoryTreeFilter, self).__init__()
        self.filter_id = filter_id

    def lessThan(self, left, right):
        leftData = self.sourceModel().data(left)
        rightData = self.sourceModel().data(right)
        return leftData > rightData

    def filterAcceptsRow(self, sourceRow, sourceParent):
        index = self.sourceModel().index(sourceRow, 0, sourceParent)

        if index.isValid():
            obj = index.data(Qt.UserRole)
            if not obj: # Top level items are not filterable so keep them
                return True
            else:
                if obj.type == self.filter_id:
                    match = self.filterRegularExpression().match(obj.name)
                    if match.hasMatch():
                        return True
        return False


class CaptureItem(object):
    __slots__ = ['name', 'path', 'count', 'status', 'type', 'progress', 'date', 'icon']

    INDICATIONS = [
        Indication('type', TypesIndicator, QRect(12, -22, 16, 16)),
        Indication('status', Statuses,  QRect(28, -22, 16, 16))
    ]

    def __init__(self, path):
        self.name = path.name
        self.path = path
        self.count = 1
        self.status = int(Statuses.Local)
        self.type = 1
        self.progress = 0
        self.date = None
        self.icon = None


class HistoryTreeView(QTreeView):

    onExecuted = Signal(QModelIndex)

    def __init__(self, *args, **kwargs):
        super(HistoryTreeView, self).__init__(*args, **kwargs)
        self.setMouseTracking(True)
        self.setIndentation(3)
        self.setDragEnabled(True)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setDragDropMode(QAbstractItemView.DragOnly)
        self.setDefaultDropAction(Qt.IgnoreAction)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        #self.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setItemDelegate(BaseItemDelegate(self))
        self.customContextMenuRequested.connect(self.customContextMenu)
        self.clicked.connect(self.expand_index)
        self.setSortingEnabled(True)
        self.setStyleSheet(TREE_GROUP_STYLE)
        TypesIndicator.cache() # cache icon indicators

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
        obj = index.data(Qt.UserRole)
        if isinstance(obj, CaptureItem):
            obj_type = obj.type
            actions = self.actions() + obj_type.actions
        else:
            actions = self.actions()
        [context_menu.addAction(action) for action in actions]
        context_menu.exec(QCursor.pos())

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Space:
            self.onExecuted.emit(self.lastIndex)
