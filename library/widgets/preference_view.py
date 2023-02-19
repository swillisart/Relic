from extra_types.enums import DataAutoEnum, AutoEnum
from enum import IntEnum

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from relic.qt.widgets import FilterBox

from library.config import RELIC_PREFS
from library.widgets.fields import (
    ComboField, IntField, CheckField, VerticalTreeModel, TextField,
    FieldDelegate, ObjectField)
from library.ui.preferences_form import Ui_PreferenceForm


class ViewScale(ComboField, IntEnum):
    Tree = 0
    Compact = 1
    Icon = 2

    @staticmethod
    def widget(parent):
        widget = QComboBox(parent)
        [widget.addItem(x.name, x.name) for x in ViewScale]
        return widget

    @property
    def icon(self):
        return QPixmap()


class Group(DataAutoEnum):
    GENERAL = QStandardItem('General')
    INGEST = QStandardItem('Ingest')
    SITE = QStandardItem('Site')


class Subgroup(AutoEnum):
    USER = {'data': QStandardItem('User'), 'parent': Group.GENERAL}


class UserPrefs(object):

    class Fields(AutoEnum):
        assets_per_page = {'data': IntField, 'parent': Group.GENERAL}
        renderer = {'data': TextField, 'parent': Group.INGEST}
        denoise = {'data': CheckField, 'parent': Group.INGEST}
        edit_mode = {'data': CheckField, 'parent': Group.GENERAL}
        recurse_subcategories = {'data': CheckField, 'parent': Group.GENERAL}
        user_id = {'data': IntField, 'parent': Subgroup.USER}
        view_scale = {'data': ViewScale, 'parent': Group.GENERAL}

    def __init__(self):
        user_settings = RELIC_PREFS.getUserSettings()
        user_keys = set(user_settings.childKeys())
        [user_keys.add(x.name) for x in self.Fields]
        for key in user_keys:
            value = user_settings.value(key)
            if isinstance(value, str) and value.isnumeric():
                value = int(value)
            setattr(self, key, self.getPref(key, value))

    def getPref(self, key, value):
        try:
            pref_value = UserPrefs.Fields[key].data(value)
        except:
            pref_value = UserPrefs.Fields[key].data[value]
        return pref_value


class PreferencesView(QWidget):
    def __init__(self, *args, **kwargs):
        super(PreferencesView, self).__init__(*args, **kwargs)
        self.view = QTreeView(self)
        self.view.setWordWrap(True)

        layout = QFormLayout(self)
        self.setLayout(layout)

        user_prefs = UserPrefs()

        model = VerticalTreeModel()
        model.dataChanged.connect(self.onDataChanged)

        self.data_mapper = QDataWidgetMapper(self)
        self.data_mapper.setItemDelegate(FieldDelegate(self))
        self.data_mapper.setModel(model)

        for grp in Group:
            model.appendRow(grp.data)
    
        for sub in Subgroup:
            parent_item = sub.parent.data
            parent_item.appendRow(sub.data)

        for field in user_prefs.Fields:
            widget = field.data.widget(self.view)
            widget._type = field.data
            widget.hide()
            self.data_mapper.addMapping(widget, field.value)
            parent_item = field.parent.data
            label_item = QStandardItem(field.name)
            value_item = QStandardItem()
            value_data = getattr(user_prefs, field.name)
            value_item.setData(value_data, role=Qt.EditRole)
            value_item.setData(field, role=VerticalTreeModel.FieldRole)
            parent_item.appendRow([label_item, value_item])

        self.view.setHeaderHidden(True)
        self.view.setIndentation(16)
        self.view.setModel(model)
        #self.view.setEditTriggers(QAbstractItemView.CurrentChanged | QAbstractItemView.SelectedClicked)
        self.view.setEditTriggers(QAbstractItemView.AllEditTriggers)
        self.view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.view.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.view.setItemDelegate(FieldDelegate(self))
        self.view.selectionModel().selectionChanged.connect(self.onSelection)

        layout.addWidget(self.view)
        selection_model = self.view.selectionModel()
        selection_model.currentRowChanged.connect(self.data_mapper.setCurrentModelIndex)

    @Slot()
    def onDataChanged(self, top_left, bot_right, roles):
        new_index = top_left.sibling(top_left.row(), 0)
        label = new_index.data(role=Qt.DisplayRole)
        value = top_left.data()
        setattr(RELIC_PREFS, label, value)

    def resizeEvent(self, event):
        header = self.view.header()
        column_width = (self.view.width() / 2)
        header.resizeSection(0, column_width)
        return super(PreferencesView, self).resizeEvent(event)

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
