import datetime

import numpy as np
from extra_types.enums import AutoEnum, DataAutoEnum
from library.config import RELIC_PREFS
from library.objectmodels import (allCategories, alusers, attachLinkToAsset,
                                  relationships, session, subcategory, tags)
#from library.widgets.util import ListViewFiltered
from library.widgets.fields import (CheckField, DateTimeField, LinkField,
                                    FieldDelegate, IntField, ObjectField, QualityField,
                                    TextField, VerticalTreeModel, FileSizeField, RatingField, FramerateField, DurationField)
from PySide6.QtCore import (QSignalBlocker, QItemSelection, QItemSelectionModel, QObject, QModelIndex,
                            QRect, QSignalBlocker, QSize, Signal, Slot, QEvent)
from PySide6.QtGui import (QCursor, QFont, QIcon, QPainter, QStandardItem,
                           QStandardItemModel, Qt, QTextDocument, QPixmap)
from PySide6.QtWidgets import (QAbstractItemView, QComboBox,
                               QFrame, QGridLayout, QLabel, QListView, QMenu,
                               QSizePolicy, QSpacerItem, QSpinBox,
                               QStyledItemDelegate, QStyleOptionViewItem,
                               QTextBrowser, QTreeView, QVBoxLayout, QWidget)


from relic.scheme import Classification, AssetType
from relic.local import Category

class Group(DataAutoEnum):
    TITLE = QStandardItem('Title')
    DETAIL = QStandardItem('Details')
    STRUCTURE = QStandardItem('Structure')
    SYSTEM = QStandardItem('System')

class Fields(AutoEnum):
    NAME = {'data': TextField, 'parent': Group.TITLE}
    CATEGORY = {'data': Category, 'parent': Group.TITLE}
    SUBCATEGORY = {'data': LinkField, 'parent': Group.TITLE}
    PATH = {'data': TextField, 'parent': Group.TITLE}

    DESCRIPTION = {'data': LinkField, 'parent': Group.TITLE}
    TYPE = {'data': AssetType, 'parent': Group.DETAIL}
    CLASS = {'data': Classification, 'parent': Group.DETAIL}
    FILESIZE = {'data': FileSizeField, 'parent': Group.DETAIL}
    RESOLUTION = {'data': TextField, 'parent': Group.DETAIL}
    QUALITY = {'data': QualityField, 'parent': Group.DETAIL}
    RATING = {'data': RatingField, 'parent': Group.DETAIL}
    DURATION = {'data': DurationField, 'parent': Group.DETAIL}
    FRAMERATE = {'data': FramerateField, 'parent': Group.DETAIL}
    POLYCOUNT = {'data': IntField, 'parent': Group.DETAIL}
    PROXY = {'data': CheckField, 'parent': Group.DETAIL}
    NODECOUNT = {'data': IntField, 'parent': Group.DETAIL}

    STATUS = {'data': IntField, 'parent': Group.STRUCTURE}
    DEPENDENCIES = {'data': IntField, 'parent': Group.STRUCTURE}
    TAGS = {'data': ObjectField, 'parent': Group.STRUCTURE}
    ALUSERS = {'data': ObjectField, 'parent': Group.STRUCTURE}
    UPSTREAM = {'data': ObjectField, 'parent': Group.STRUCTURE}

    ID = {'data': IntField, 'parent': Group.SYSTEM}
    LINKS = {'data': IntField, 'parent': Group.SYSTEM}
    DATECREATED = {'data': DateTimeField, 'parent': Group.SYSTEM}
    DATEMODIFIED = {'data': DateTimeField, 'parent': Group.SYSTEM}
    FILEHASH = {'data': TextField, 'parent': Group.SYSTEM}
    HASNODES = {'data': IntField, 'parent': Group.SYSTEM}

    #'upstream', # or 'links' instead?
    #'downstream',

EDITABLE_FIELDS = [
    Fields.NAME,
    #Fields.SUBCATEGORY,
    Fields.DESCRIPTION,
    Fields.TYPE,
    Fields.CLASS,
    Fields.RESOLUTION,
    Fields.QUALITY,
    Fields.RATING,
    Fields.DURATION,
    Fields.FRAMERATE,
    Fields.POLYCOUNT,
    Fields.PROXY,
    Fields.NODECOUNT,
    Fields.STATUS,
    Fields.TAGS,
    Fields.ALUSERS,
    Fields.UPSTREAM,
]

class MetadataTree(QTreeView):

    def __init__(self, parent):
        super(MetadataTree, self).__init__(parent)
        self.setHeaderHidden(True)
        self.setWordWrap(True)
        self.setIndentation(0)
        self.setEditTriggers(QAbstractItemView.AllEditTriggers)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.setItemDelegate(FieldDelegate(parent))
        self._label_width = 0

    def mouseMoveEvent(self, event):
        super(MetadataTree, self).mouseMoveEvent(event)
        mouse_pos = event.pos()
        index = self.indexAt(mouse_pos)
        if not index.isValid():
            return
        model = index.model()
        item = model.itemFromIndex(index)
        field = item.data(role=VerticalTreeModel.FieldRole)
        if field and field.data is LinkField:
            self.setCursor(Qt.PointingHandCursor)
        else:    
            self.setCursor(Qt.ArrowCursor)

    @property
    def label_width(self):
        return self._label_width
    
    @label_width.setter
    def label_width(self, value):
        width = self.fontMetrics().horizontalAdvance(value)
        if width > self._label_width:
            self._label_width = width

    def resizeEvent(self, event):
        header = self.header()
        column_width = (self.width() / 2) # center
        header.resizeSection(0, self.label_width + 32)
        return super(MetadataTree, self).resizeEvent(event)


class MetadataView(QFrame):

    openDescription = Signal()
    fieldChanged = Signal(str, object)

    def __init__(self, *args, **kwargs):
        super(MetadataView, self).__init__(*args, **kwargs)
        self.view = MetadataTree(self)
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        layout.addWidget(self.view)

        model = VerticalTreeModel()
        self.view.setModel(model)

        for grp in Group:
            model.appendRow(grp.data)
            if grp != Group.SYSTEM:
                self.view.setExpanded(grp.data.index(), True)

        for field in Fields:
            self.view.label_width = field.name
            widget = field.data.widget(self.view)
            widget.hide()
            parent_item = field.parent.data
            label_item = QStandardItem(field.name.capitalize())
            value_item = QStandardItem()
            field.item = value_item
            value_item.setData(field, role=VerticalTreeModel.FieldRole)
            parent_item.appendRow([label_item, value_item])

        layout.addWidget(self.view)
        selection_model = self.view.selectionModel()
        self.view.selectionModel().selectionChanged.connect(self.onSelection)
        model.dataChanged.connect(self.onDataChanged)
        self._block_update = True

    def setAssets(self, assets):
        asset = assets[-1]
        self._block_update = True
        for field in Fields:
            attr_name = field.name.lower()
            if hasattr(asset, attr_name):
                value = getattr(asset, attr_name)

                if value is not None:
                    field_data = field.data(value)
                else:
                    field_data = field.data(field.data.default)
            else:
                field_data = field.data(field.data.default)

            field.item.setData(field_data, role=Qt.EditRole)

        self._block_update = False

    @Slot()
    def onDataChanged(self, top_left, bot_right, roles):
        if self._block_update:
            return
        model = top_left.model()
        item = model.itemFromIndex(top_left)
        field = item.data(role=VerticalTreeModel.FieldRole)
        value = top_left.data(role=Qt.EditRole)
        # Only change if the field is editable and the app is in edit mode.
        if field in EDITABLE_FIELDS and int(RELIC_PREFS.edit_mode):
            self.fieldChanged.emit(field.name, value)

    @Slot(QItemSelection)
    def onSelection(self, item):
        selection_model = self.view.selectionModel()
        for index in item.indexes():
            model = index.model()
            new_index = index.sibling(index.row(), 0)
            item = model.itemFromIndex(new_index)
            if item.hasChildren():
                expand_state = self.view.isExpanded(new_index)
                self.view.setExpanded(new_index, not expand_state)
                selection_model.select(new_index, QItemSelectionModel.Clear)
            elif index.column() == 1:
                this_item = model.itemFromIndex(index)
                field = this_item.data(role=VerticalTreeModel.FieldRole)
                if field == Fields.DESCRIPTION:
                    self.openDescription.emit()

    @Slot(QEvent)
    def leaveEvent(self, event):
        selection_model = self.view.selectionModel()
        with QSignalBlocker(selection_model):
            selection_model.clear()
    
        super(MetadataView, self).leaveEvent(event)
