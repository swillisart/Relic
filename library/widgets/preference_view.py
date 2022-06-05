from extra_types.enums import DataAutoEnum, AutoEnum
#import resources
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from library.config import RELIC_PREFS
from library.widgets.fields import (
    ComboField, IntField, CheckField, VerticalTreeModel, TextField,
    FieldDelegate)
from library.ui.preferences_form import Ui_PreferenceForm


class ViewScale(ComboField):
    #TREE_TABLE = 0
    COMPACT = 0
    ICON = 1
    NONE = 2

    @staticmethod
    def widget(parent):
        widget = QComboBox(parent)
        [widget.addItem(x.name) for x in ViewScale]
        return widget

class Group(DataAutoEnum):
    GENERAL = QStandardItem('General')
    INGEST = QStandardItem('Ingest')
    SITE = QStandardItem('Site')

class Subgroup(AutoEnum):
    USER = {'data': QStandardItem('User'), 'parent': Group.GENERAL}


class UserPrefs(object):

    class Fields(AutoEnum):
        assets_per_page = {'data': IntField, 'parent': Group.GENERAL}
        denoise = {'data': CheckField, 'parent': Group.INGEST}
        edit_mode = {'data': CheckField, 'parent': Group.GENERAL}
        recurse_subcategories = {'data': CheckField, 'parent': Group.GENERAL}
        user_id = {'data': IntField, 'parent': Subgroup.USER}
        view_scale = {'data': ViewScale, 'parent': Group.GENERAL}

        host = {'data': TextField, 'parent': Group.SITE}
        socket = {'data': TextField, 'parent': Group.SITE}
        local_storage = {'data': TextField, 'parent': Group.SITE}
        network_storage = {'data': TextField, 'parent': Group.SITE}
        project_variable = {'data': TextField, 'parent': Group.SITE}

    def __init__(self):
        user_settings = RELIC_PREFS.getUserSettings()
        user_keys = user_settings.childKeys()

        for key in user_keys:
            value = user_settings.value(key)
            if isinstance(value, str) and value.isnumeric():
                value = int(value)
            pref_value = UserPrefs.Fields[key].data(value)

            setattr(self, key, pref_value)

        site_settings = RELIC_PREFS.getSiteSettings()
        site_keys = site_settings.childKeys()

        for key in site_keys:
            value = site_settings.value(key)
            if isinstance(value, str) and value.isnumeric():
                value = int(value)
            pref_value = UserPrefs.Fields[key].data(value)

            setattr(self, key, pref_value)


class PreferencesView(QWidget):
    def __init__(self, *args, **kwargs):
        super(PreferencesView, self).__init__(*args, **kwargs)
        self.view = QTreeView(self)

        layout = QFormLayout(self)
        self.setLayout(layout)

        user_prefs = UserPrefs()

        model = VerticalTreeModel()

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
        self.view.setEditTriggers(QAbstractItemView.CurrentChanged | QAbstractItemView.SelectedClicked)
        self.view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.view.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.view.setItemDelegate(FieldDelegate(self))
        self.view.selectionModel().selectionChanged.connect(self.onSelection)

        #self.view.verticalHeader().show()

        layout.addWidget(self.view)
        selection_model = self.view.selectionModel()
        selection_model.currentRowChanged.connect(self.data_mapper.setCurrentModelIndex)

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

    def close(self):
        self.parent().close()
