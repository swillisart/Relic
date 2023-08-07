from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from relic.qt.delegates import SimpleDelegate
from relic.qt.util import _indexToItem
from relic.qt.widgets import GroupViewFilter

from extra_types.flag_enum import FlagEnumAuto, Flag

from library.widgets.util import ListViewFocus
from library.objectmodels import session
from library.config import RELIC_PREFS


class RelationEdit(FlagEnumAuto):
    NEW = Flag('Add New')
    UNLINK = Flag('Unlink')
    RENAME = Flag('Rename')
    DELETE = Flag('Delete')

re = RelationEdit
re.ALL = re.NEW | re.UNLINK | re.RENAME | re.DELETE


class RelationQueryView(ListViewFocus):
    def __init__(self, *args, **kwargs):
        super(RelationQueryView, self).__init__(*args, **kwargs)
        self.setWindowFlags(Qt.Popup | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        session.searchcategory.callback.connect(self.onFilterResults)
        self.constructor = None
        self.checked_db = False

    def setConstructor(self, constructor):
        self.constructor = constructor

    @Slot(list)
    def onFilterResults(self, results):
        if not self.constructor:
            return
        constructor = self.constructor
        item_model = self.itemModel
        item_model.clear()
        for x in results:
            relate = constructor(*x)
            item = QStandardItem(relate.name)
            item.setData(relate, role=Qt.UserRole)
            item_model.appendRow(item)

    def onFilterChanged(self):
        text = self.searchBox.text()
        if len(text) >= 3 and not self.checked_db:
            # Search the database for the text after 3 characters.
            self.checked_db = True
            session.searchcategory.execute(self.constructor.__name__, text)
        elif len(text) < 3:
            self.checked_db = False
            self.itemModel.clear()
        super(RelationQueryView, self).onFilterChanged()

    def sizeHint(self):
        return QSize(275, 250)

    def hide(self):
        # delayed close the widget after hidden.
        super(RelationQueryView, self).hide()
        QTimer.singleShot(100, self.close)


class RelationEditList(QListView):

    action_features = RelationEdit.ALL
    constructor = None # Constructor for the asset type.

    def __init__(self, *args, **kwargs):
        super(RelationEditList, self).__init__(*args, **kwargs)
        self.setItemDelegate(SimpleDelegate(self)) # BaseItemDelegate
        self.verticalScrollBar().setSingleStep(40)
        self.setDragDropMode(QAbstractItemView.NoDragDrop)
        self.setDragEnabled(False)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.setFlow(QListView.LeftToRight)
        self.setResizeMode(QListView.Adjust)
        self.setWrapping(True)
        # NEW
        self.setViewMode(QListView.IconMode)
        self.setSpacing(2)
        self.setUniformItemSizes(True)

        self.setWordWrap(False) # True
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.onContextMenuRequested)

        self.item_model = QStandardItemModel()
        self.proxy_model = GroupViewFilter()
        self.proxy_model.setSourceModel(self.item_model)
        self.setModel(self.proxy_model)
        self.setSizeAdjustPolicy(QAbstractScrollArea.AdjustIgnored)

    def sizeHint(self):
        return QSize(24, 74)

    def mouseDoubleClickEvent(self, event):
        if RELIC_PREFS.edit_mode:
            self.newAction()

    def onContextMenuRequested(self, value):
        if not RELIC_PREFS.edit_mode:
            return
        context_menu = QMenu(self)
        actions = [
            QAction(RelationEdit.NEW.value, self, triggered=self.newAction),
            QAction(RelationEdit.UNLINK.value, self, triggered=self.unlinkAction),
            QAction(RelationEdit.RENAME.value, self, triggered=self.renameAction),
            QAction(RelationEdit.DELETE.value, self, triggered=self.deleteAction),
        ]

        features = self.action_features
        for feature in RelationEdit:
            if features & feature:
                context_menu.addAction(actions[feature.index])
        context_menu.exec(QCursor.pos())

    def subView(self):
        relation_view = RelationQueryView()
        relation_view.setConstructor(self.constructor)
        relation_view.newItem.connect(self.onNew)
        relation_view.linkItem.connect(self.onLink)
        relation_view.renameItem.connect(self.onRename)
        relation_view.show()
        return relation_view

    def markAsEdited(self):
        # clear the original value so the editor detects a change.
        self.original_value = None

    def newAction(self):
        self.subView()

    def renameAction(self):
        sub_view = self.subView()
        sub_view.rename_mode = True

    def unlinkAction(self):
        self.markAsEdited()
        for index in self.selectionModel().selectedIndexes():
            asset = index.data(Qt.UserRole)
            asset.status = RelationEdit.UNLINK
            self.setRowHidden(index.row(), True)

    def deleteAction(self):
        self.markAsEdited()
        for index in self.selectionModel().selectedIndexes():
            asset = index.data(Qt.UserRole)
            asset.status = RelationEdit.DELETE
            self.setRowHidden(index.row(), True)

    @Slot(str)
    def onNew(self, name):
        self.markAsEdited()
        asset = self.constructor(name=name, status=RelationEdit.NEW)
        new_item = QStandardItem(asset.name)
        new_item.setData(asset, Qt.UserRole)
        self.item_model.appendRow(new_item)

    @Slot()
    def onLink(self, asset):
        self.markAsEdited()
        asset.status = RelationEdit.NEW
        exists = self.item_model.findItems(asset.name)
        if not exists:
            item = QStandardItem(asset.name)
            item.setData(asset, Qt.UserRole)
            self.item_model.appendRow(item)

    @Slot(str)
    def onRename(self, new_name):
        self.markAsEdited()
        dataChanged = self.item_model.dataChanged
        for index in self.selectionModel().selectedIndexes():
            item = _indexToItem(index)
            asset = item.data(role=Qt.UserRole)
            asset.name = new_name
            asset.status = RelationEdit.RENAME
            asset.title.text = new_name
            item.setData(asset, Qt.UserRole)
            dataChanged.emit(index, index, [Qt.UserRole, Qt.DisplayRole])
