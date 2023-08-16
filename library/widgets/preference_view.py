from relic.qt import *
from relic.qt.widgets import FilterBox

from relic.qt.role_model.views import RoleTreeView, RoleHeaderView
from relic.qt.role_model.models import GroupFilterProxyModel
from relic.qt.role_model.delegates import (AdvanceAxis, Indication, RoleItemDelegate, ItemDispalyModes,
    Title, TitleIndicator, TextIndicator, LabelDelegate)
from relic.qt.role_model.editors import (EditorRole, BaseEditor, ComboBoxEditor, SpinEditor, CheckBoxEditor,
                                        EditorDelegate, LineEditor)

from library.config import RELIC_PREFS
from library.ui.preferences_form import Ui_PreferenceForm

from extra_types.composable import Attributable, Composable, SlotsCompose, Slots
from extra_types.flag_enum import EnumAuto, Enumerant

class ViewScale(EnumAuto):
    Tree = Enumerant
    Compact = Enumerant
    Icon = Enumerant


class ViewScaleEditor(ComboBoxEditor):
    __order__ = ['Tree', 'Compact', 'Icon']
    Tree = QStandardItem('Tree')
    Compact = QStandardItem('Compact')
    Icon = QStandardItem('Icon')

GENERAL = QStandardItem('General')
INGEST = QStandardItem('Ingest')
SITE = QStandardItem('Site')
USER = QStandardItem('User')
GENERAL.appendRow(USER)

ingest_editor_map = {
    'renderer': LineEditor,
    'denoise': CheckBoxEditor,
}
general_editor_map = {
    'assets_per_page': SpinEditor,
    'edit_mode': CheckBoxEditor,
    'recurse_subcategories': CheckBoxEditor,
    'view_scale': ViewScaleEditor,
}
user_editor_map = {
    'user_id': SpinEditor,
}

cl = Qt.AlignVCenter | Qt.AlignLeft


class PreferenceItem:
    __slots__ = ['name', 'title']#, 'count']
    INDICATIONS = [
        Indication('title', TitleIndicator, cl, AdvanceAxis.NONE),
    ]

    def __init__(self, name):
        self.name = name
        self.title = Title(self.name)


class PreferencesTree(RoleTreeView):

    def __init__(self, *args, **kwargs):
        super(PreferencesTree, self).__init__(*args, **kwargs)
        self.setMouseTracking(True)
        self.setHeaderHidden(True)
        self.setWordWrap(True)
        self.setIndentation(16)

        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.setItemDelegate(EditorDelegate(self))
        title_delegate = LabelDelegate(self)
        self.setItemDelegateForColumn(0, title_delegate)


class PreferencesView(QWidget):
    def __init__(self, *args, **kwargs):
        super(PreferencesView, self).__init__(*args, **kwargs)
        self.view = PreferencesTree(self)

        layout = QFormLayout(self)
        self.setLayout(layout)

        model = QStandardItemModel()
        model.setColumnCount(2)
        model.dataChanged.connect(self.onDataChanged)
        [model.appendRow(x) for x in (GENERAL, INGEST, SITE)]
        user_settings = RELIC_PREFS.getUserSettings()

        header = RoleHeaderView()
        header.setModel(model)
        header.createAttributeLabels(['title', 'value'], visible=['title', 'value'])
        self.view.setHeader(header)

        self._createItems(ingest_editor_map, INGEST, user_settings)
        self._createItems(general_editor_map, GENERAL, user_settings)
        self._createItems(user_editor_map, USER, user_settings)
        proxy_model = GroupFilterProxyModel()
        proxy_model.setSourceModel(model)

        self.view.setModel(proxy_model)
        layout.addWidget(self.view)
        self.editor = None

    @staticmethod
    def _createItems(data, parent_item, user_settings):
        model = parent_item.model()
        for key, editor in data.items():
            value = user_settings.value(key)
            if isinstance(value, str) and value.isnumeric():
                value = int(value)
            obj = PreferenceItem(key)

            label_item = QStandardItem(obj.name)
            label_item.setData(obj, role=Qt.UserRole)
            value_item = QStandardItem()
            value_item.setData(value, role=Qt.EditRole)
            value_item.setData(editor, role=EditorRole)
            parent_item.appendRow([label_item, value_item])

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


class PreferencesDialog(Ui_PreferenceForm, QWidget):
    def __init__(self, *args, **kwargs):
        super(PreferencesDialog, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.preference_view = PreferencesView()
        self.content_frame.layout().addWidget(self.preference_view)
        self.filter_box = FilterBox(self)
        self.filter_box.button.setChecked(True)
        self.filter_box.editor.textChanged.connect(self.preference_view.view.filter)
        self.filter_layout.addWidget(self.filter_box)

    def close(self):
        self.parent().close()
