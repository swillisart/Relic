from extra_types.enums import DataAutoEnum, AutoEnum
from enum import IntEnum

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from relic.qt.widgets import FilterBox

from library.config import RELIC_PREFS
from relic.qt.role_model.editors import (BaseEditor, ComboBoxEditor, SpinEditor, CheckBoxEditor,
                                        VerticalTreeModel, EditorDelegate, LineEditor)

from library.ui.preferences_form import Ui_PreferenceForm

from extra_types.composable import Attributable, Composable, SlotsCompose, Slots
from extra_types.flag_enum import EnumAuto, Enumerant

class ViewScale(EnumAuto):
    Tree = Enumerant
    Compact = Enumerant
    Icon = Enumerant


class ViewScaleEditor(ComboBoxEditor):
    __order__ = ['Tree', 'Compact', 'Icon']
    Tree = QStandardItem(QIcon(':status/local.png'), 'Tree')
    Compact = QStandardItem( QIcon(':status/syncing.png'), 'Compact')
    Icon = QStandardItem(QIcon(':status/cloud.png'), 'Icon')


class Group(DataAutoEnum):
    GENERAL = QStandardItem('General')
    INGEST = QStandardItem('Ingest')
    SITE = QStandardItem('Site')


class Subgroup(AutoEnum):
    USER = {'data': QStandardItem('User'), 'parent': Group.GENERAL}


class UserPrefs(object):

    class Fields(AutoEnum):
        assets_per_page = {'data': SpinEditor, 'parent': Group.GENERAL}
        renderer = {'data': LineEditor, 'parent': Group.INGEST}
        denoise = {'data': CheckBoxEditor, 'parent': Group.INGEST}
        edit_mode = {'data': CheckBoxEditor, 'parent': Group.GENERAL}
        recurse_subcategories = {'data': CheckBoxEditor, 'parent': Group.GENERAL}
        user_id = {'data': SpinEditor, 'parent': Subgroup.USER}
        view_scale = {'data': ViewScaleEditor, 'parent': Group.GENERAL}
        #view_scale = {'data': SpinEditor, 'parent': Group.GENERAL}

    def __init__(self):
        user_settings = RELIC_PREFS.getUserSettings()
        user_keys = set(user_settings.childKeys())
        [user_keys.add(x.name) for x in self.Fields]
        for key in user_keys:
            value = user_settings.value(key)
            if isinstance(value, str) and value.isnumeric():
                value = int(value)
            setattr(self, key, value)


class PreferencesTree(QTreeView):

    def __init__(self, *args, **kwargs):
        super(PreferencesTree, self).__init__(*args, **kwargs)
        self.setMouseTracking(True)
        #self.view.entered.connect(self.interactive_edit)
        self.setHeaderHidden(True)
        self.setWordWrap(True)
        self.setIndentation(16)

        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.setItemDelegate(EditorDelegate(self))

    def mousePressEvent(self, event):
        super(PreferencesTree, self).mousePressEvent(event)
        index = self.indexAt(event.pos())
        if not index.isValid() or index.column() == 0:
            return
        if self.state() != QAbstractItemView.EditingState:
            self.edit(index)

    @Slot(QItemSelection)
    def onSelection(self, item):
        selection_model = self.selectionModel()
        for index in item.indexes():
            model = index.model()
            new_index = index.sibling(index.row(), 0)
            item = model.itemFromIndex(new_index)
            if item.hasChildren():
                expand_state = self.isExpanded(new_index)
                self.setExpanded(new_index, not expand_state)
                selection_model.select(new_index, QItemSelectionModel.Clear)

    def interactive_edit(self, index):
        if not index.isValid():
            return
        self.edit(index)


class PreferencesView(QWidget):
    def __init__(self, *args, **kwargs):
        super(PreferencesView, self).__init__(*args, **kwargs)
        self.view = PreferencesTree(self)

        layout = QFormLayout(self)
        self.setLayout(layout)

        user_prefs = UserPrefs()

        model = VerticalTreeModel()
        model.dataChanged.connect(self.onDataChanged)

        for grp in Group:
            model.appendRow(grp.data)
    
        for sub in Subgroup:
            parent_item = sub.parent.data
            parent_item.appendRow(sub.data)

        for field in user_prefs.Fields:
            widget = field.data
            parent_item = field.parent.data
            label_item = QStandardItem(field.name)
            value_item = QStandardItem()
            value_data = getattr(user_prefs, field.name)
            value_item.setData(value_data, role=Qt.EditRole)
            value_item.setData(widget, role=VerticalTreeModel.EditorRole)
            parent_item.appendRow([label_item, value_item])

        self.view.setModel(model)
        self.view.selectionModel().selectionChanged.connect(self.view.onSelection)
        layout.addWidget(self.view)
        self.editor = None

    @Slot()
    def onDataChanged(self, top_left, bot_right, roles):
        if Qt.EditRole not in roles:
            return
        new_index = top_left.sibling(top_left.row(), 0)
        label = new_index.data(role=Qt.DisplayRole)
        value = top_left.data(role=Qt.EditRole)
        setattr(RELIC_PREFS, label, str(value))

    def resizeEvent(self, event):
        header = self.view.header()
        column_width = (self.view.width() / 2)
        header.resizeSection(0, column_width)
        return super(PreferencesView, self).resizeEvent(event)

    @Slot(QEvent)
    def leaveEvent(self, event):
        selection_model = self.view.selectionModel()
        with QSignalBlocker(selection_model):
            selection_model.clear()
    
        super(PreferencesView, self).leaveEvent(event)


class PreferencesDialog(Ui_PreferenceForm, QWidget):
    def __init__(self, *args, **kwargs):
        super(PreferencesDialog, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.preference_view = PreferencesView()
        self.content_frame.layout().addWidget(self.preference_view)
        self.filter_box = FilterBox(self)
        self.filter_box.button.setChecked(True)
        self.filter_layout.addWidget(self.filter_box)

    def close(self):
        self.parent().close()
