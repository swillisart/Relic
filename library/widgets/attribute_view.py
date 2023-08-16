
# -- Third-party --
from PySide6.QtCore import (QRegularExpression, QSignalBlocker, QItemSelection, QItemSelectionModel, QObject, QModelIndex,
                            QRect, QSignalBlocker, QSize, Signal, Slot, QEvent, QMargins)
from PySide6.QtGui import (QCursor, QFont, QIcon, QPainter, QStandardItem,
                           QStandardItemModel, Qt, QTextDocument, QPixmap, QColor, QAction)
from PySide6.QtWidgets import (QAbstractItemView, QStyle, QComboBox, QStyleOptionComboBox,
                               QFrame, QGridLayout, QLabel, QListView, QMenu,
                               QSizePolicy, QSpacerItem, QSpinBox,
                               QStyledItemDelegate, QStyleOptionViewItem, QStyleOptionButton, QStyleOptionSpinBox,
                               QTextBrowser, QTreeView, QVBoxLayout, QWidget, QPushButton, QHBoxLayout)

# -- first-party --
from extra_types import Duration
from sequence_path.main import FileSize

from relic.scheme_new import Class, AssetType, Category
#from relic.local import Category

from relic.qt.widgets import FilterBox
from relic.qt.role_model.views import RoleTreeView, RoleHeaderView
from relic.qt.role_model.models import GroupFilterProxyModel, KeyValueOp
from relic.qt.role_model.delegates import (AdvanceAxis, Indication, LabelDelegate, ItemDispalyModes,
                                Title, TitleIndicator, TextIndicator)
from relic.qt.role_model.editors import (BaseEditor, ComboBoxEditor, SpinEditor, CheckBoxEditor,
                                        EditorDelegate, LineEditor, EditorRole,
                                        LabelEditor, IntComboBoxEditor, DateTimeEditor, drawFramedItem)
from relic.qt.util import _indexToItem

# -- Module --
from library.config import RELIC_PREFS
from library.objectmodels import (alusers, relationships, session, subcategory, tags)
from library.widgets.rating import Rating
from library.widgets.relations import RelationEditList, RelationEdit
# -- Globals --
open_document = QAction()
edit_document = QAction()


def scale_icon(pix):
    return pix.scaled(16,16, Qt.KeepAspectRatio, Qt.SmoothTransformation)


class FramerateEditor(SpinEditor):
    def __init__(self, value, *args, **kwargs):
        super(SpinEditor, self).__init__(value, *args, **kwargs)
        self.setSuffix(' FPS')

    @classmethod
    def draw(cls, painter, option, index, value):
        rect = drawFramedItem(painter, option)
        painter.drawText(rect, '{} FPS'.format(value or 0))


class LinkLabel(QLabel):
    def __init__(self, parent=None):
        super(LinkLabel, self).__init__(parent)
        self.setTextFormat(Qt.RichText)
        font = self.font()
        font.setUnderline(True)
        self.setFont(font)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMargin(3)
        self._text = ''

    def setText(self, text):
        content = '<a href="."><span style="color:#9a9ef9;">{}</span>'
        self._text = text or ''
        if text is None or text == '':
            new_text = content.format('None.')
        else:
            new_text = content.format(text)

        super(LinkLabel, self).setText(new_text)

    def text(self):
        return self._text


class LinkMixin:

    getter_method_name = 'text'
    default_value = ''
    trigger_on_enter = True

    @classmethod
    def draw(cls, painter, option, index, value):
        og_pen = painter.pen()
        rect = drawFramedItem(painter, option)
        painter.setPen(QColor('#9a9ef9'))
        painter.drawText(rect, str(value))
        painter.setPen(og_pen) # restore the original pen.


class DescriptionEditor(LinkMixin, BaseEditor, QFrame):
    default_value = 'No Description...'

    def __init__(self, *args, **kwargs):
        self.label = LinkLabel()
        self.label.linkActivated.connect(lambda x: open_document.triggered.emit())
        self.label.setFocusPolicy(Qt.NoFocus)
        self.setText = self.label.setText
        self.text = self.label.text
        # Initialize after wrapping the label.
        super(DescriptionEditor, self).__init__(*args, **kwargs)

        self.button = QPushButton('Modify', self)
        self.button.clicked.connect(lambda x: edit_document.triggered.emit())
        self.button.setFocusPolicy(Qt.NoFocus)
        self.button.setVisible(bool(RELIC_PREFS.edit_mode))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(self.label)
        layout.addWidget(self.button)


class LinkEditor(LinkMixin, BaseEditor, LinkLabel):

    @classmethod
    def draw(cls, painter, option, index, value):
        og_pen = painter.pen()
        rect = drawFramedItem(painter, option)
        painter.setPen(QColor('#9a9ef9'))
        painter.drawText(rect, str(value))
        painter.setPen(og_pen) # restore the original pen.

    def setText(self, text):
        new_text = text.name
        super(LinkLabel, self).setText(new_text)


class DurationEditor(LabelEditor):

    @staticmethod
    def formatText(value):
        return str(Duration(value or 0))


class FileSizeEditor(LabelEditor):

    @staticmethod
    def formatText(value):
        return str(FileSize((value or 0) << 10)) # usually in kilobytes not bytes


class RatingEditor(BaseEditor, Rating):
    icon = scale_icon(QPixmap(':app/heart.svg'))
    disabled = scale_icon(QPixmap(':app/heart_disabled.svg'))

    @classmethod
    def draw(cls, painter, option, index, value):
        rect = drawFramedItem(painter, option)
        cls.paint(painter, rect, value)


class QualityEditor(RatingEditor):
    icon = scale_icon(QPixmap(':app/star.svg'))
    disabled = scale_icon(QPixmap(':app/star_disabled.svg'))


class ItemEditor(BaseEditor, RelationEditList):
    
    getter_method_name = 'items'
    default_value = [] # default value for the editor
    trigger_on_enter = False # when entered by mouse, trigger edit.

    def items(self):
        # return all item data from the model.
        results = []
        for row in range(self.item_model.rowCount()):
            obj = self.item_model.item(row, 0).data(Qt.UserRole)
            results.append(obj)
        return results

    def convertToItem(self, obj): # TEMPORARY. remove the polyMorhpicItem class.
        item = QStandardItem(obj.name)
        item.setData(obj, Qt.UserRole)
        self.item_model.appendRow(item)

    def setItems(self, objects):
        self.item_model.clear()
        if objects is not None and len(objects) > 0:
            if isinstance(objects[0], QStandardItem):
                objects = [x.data(Qt.UserRole) for x in objects]
            self.original_value = objects
            list(map(self.convertToItem, objects))

    @classmethod
    def draw(cls, painter, option, index, value):
        rect = drawFramedItem(painter, option)
        # the editor is persistent, so no need to draw the sub-items here.



TITLE = 'Title'
DETAIL = 'Details'
SYSTEM = 'System'
RELATIONS = 'Relations'
#'upstream', # or 'links' instead?
#'downstream',  

TypeEditor = ComboBoxEditor.fromEnum('TypeEditor', AssetType, QStandardItem)
ClassEditor = ComboBoxEditor.fromEnum('ClassEditor', Class, QStandardItem)
CategoryEditor = ComboBoxEditor.fromEnum('CategoryEditor', Category, QStandardItem)


class UserEditor(ItemEditor):
    action_features = RelationEdit.NEW | RelationEdit.UNLINK
    constructor = alusers

    def sizeHint(self):
        return QSize(16, 31)


class TagEditor(ItemEditor):
    action_features = RelationEdit.NEW | RelationEdit.UNLINK
    constructor = tags


class SubcategoryEditor(BaseEditor, RelationEditList):
    getter_method_name = 'item'
    default_value = None # default value for the editor
    trigger_on_enter = False # when entered by mouse, trigger edit.
    constructor = subcategory
    action_features = RelationEdit.NEW | RelationEdit.UNLINK

    def item(self):
        # return all item data from the model.
        for row in range(self.item_model.rowCount()):
            obj = self.item_model.item(row, 0).data(Qt.UserRole)
            return obj

    def setItem(self, subcategory):
        self.item_model.clear()
        if subcategory is None:
            return
        self.original_value = subcategory
        item = QStandardItem(subcategory.name)
        item.setData(subcategory, Qt.UserRole)
        self.item_model.appendRow(item)

    @classmethod
    def draw(cls, painter, option, index, value):
        rect = drawFramedItem(painter, option)
        # the editor is persistent, so no need to draw the sub-items here.

    def sizeHint(self):
        return QSize(16, 31)

PERSISTENT_ATTRIBUTES = ('tags', 'alusers', 'subcategory')

ATTRS_ON_NEW = ('name', ) 

ATTRIBUTE_MAP = {
    # "EDITOR", "PARENT NAME", "MODIFIABLE" 
    'name': [LineEditor, TITLE, True],
    'description': [DescriptionEditor, TITLE, True],
    'path': [LineEditor, TITLE, False],
    'category': [CategoryEditor, DETAIL, False],
    'type': [TypeEditor, DETAIL, True],
    'class': [ClassEditor, DETAIL, True],
    'filesize': [FileSizeEditor, DETAIL, False],
    'resolution': [LineEditor, DETAIL, False],
    'quality': [QualityEditor, DETAIL, True],
    #'rating': [RatingEditor, DETAIL, True], TODO: weighted rating.
    'duration': [DurationEditor, DETAIL, False],
    'framerate': [FramerateEditor, DETAIL, False],
    'polycount': [LineEditor, DETAIL, False],
    'nodecount': [SpinEditor, DETAIL, False],
    'dependencies': [SpinEditor, RELATIONS, False],
    'subcategory': [SubcategoryEditor, RELATIONS, False],
    'alusers': [UserEditor, RELATIONS, True],
    'tags': [TagEditor, RELATIONS, True],
    #'upstream': [ObjectField, RELATIONS, True],
    'proxy': [CheckBoxEditor, SYSTEM, True], # this will likely be removed OR changed to a multi.
    'status': [SpinEditor, SYSTEM, True],
    'id': [SpinEditor, SYSTEM, False],
    'links': [SpinEditor, SYSTEM, False],
    'datecreated': [DateTimeEditor, SYSTEM, False],
    'datemodified': [DateTimeEditor, SYSTEM, False],
    'filehash': [LineEditor, SYSTEM, False],
    'hasnodes': [SpinEditor, SYSTEM, False],
}

LC = Qt.AlignLeft | Qt.AlignVCenter

class AttributeItem:
    __slots__ = ['name', 'title']#, 'count']
    INDICATIONS = [
        Indication('title', TitleIndicator, LC, AdvanceAxis.NONE),
    ]

    def __init__(self, name):
        self.name = name
        self.title = Title(self.name.capitalize())


class AttributeDelegate(LabelDelegate):

    VIEW_MODE = ItemDispalyModes.TREE

    def paint(self, painter, option, index):
        widget = option.widget
        is_zero_column = (index.column() == 0)
        has_children = index.model().hasChildren(index)
        
        if is_zero_column:
            # Change title font text to bold.
            opt = QStyleOptionViewItem(option)
            opt.font.setWeight(QFont.DemiBold)

            if has_children:
                # Draw the branch expansion arrow indicator.
                branch = QStyleOptionViewItem(option)
                h = branch.rect.height()
                y = branch.rect.y()
                branch.rect = QRect(0, y, h, h)
                style = widget.style()
                style.drawPrimitive(QStyle.PE_IndicatorBranch, branch, painter, widget)

                # Offset the text rect to the right of the branch indicator.
                opt.rect.adjust(opt.rect.height(), 0, 0, 0)

        # Paint the title using the adjusted options.
        super(AttributeDelegate, self).paint(painter, opt, index)


class AttributeTree(RoleTreeView):

    def __init__(self, parent):
        super(AttributeTree, self).__init__(parent)
        self.setHeaderHidden(True)
        self.setWordWrap(True)
        self.setIndentation(0)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.setItemDelegate(EditorDelegate(self))
        title_delegate = AttributeDelegate(self)

        self.setItemDelegateForColumn(0, title_delegate)
        self._label_width = 0

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
        header.resizeSection(0, self.label_width + 32) # column_width
        return super(AttributeTree, self).resizeEvent(event)


class AttributeFilter(GroupFilterProxyModel):

    def filterData(self, data):
        # dont filter out the persistent attributes that have always 
        # open editors. These have their own sub-filters.
        if data.name in PERSISTENT_ATTRIBUTES:
            return True
        else:
            return super(AttributeFilter, self).filterData(data)


class AttributesView(QFrame):

    attributeChanged = Signal(str, object, list)

    def __init__(self, *args, **kwargs):
        super(AttributesView, self).__init__(*args, **kwargs)
        self.view = AttributeTree(self)
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        self.setLayout(layout)
        layout.addWidget(self.view)
        self._block_update = True
        model = QStandardItemModel()
        model.setColumnCount(2)
        model.dataChanged.connect(self.onDataChanged)
        proxy_model = AttributeFilter()
        proxy_model.setSourceModel(model)
        self.view.setModel(proxy_model)

        # Top level groups are the parent items.
        last_parent = ''

        attr_to_item = {}

        for attr, data in ATTRIBUTE_MAP.items():
            # Unpack the structured data.
            editor, parent_name, modifiable = data

            # Create the parent item if it doesn't exist.
            if parent_name != last_parent:
                last_parent = parent_name
                parent_item = QStandardItem(parent_name)
                model.appendRow(parent_item)
            # Create the attribute item and supply an editor in a custom Role.
            self.view.label_width = attr

            item = AttributeItem(attr)
            label_item = QStandardItem(item.name)
            label_item.setData(item, role=Qt.UserRole)
            value_item = QStandardItem()
            #value_item.setData(value, role=Qt.EditRole)
            value_item.setData(editor, role=EditorRole)

            parent_item.appendRow([label_item, value_item])
            attr_to_item[attr] = value_item


        for attr in PERSISTENT_ATTRIBUTES:
            attr_index = attr_to_item[attr].index()
            proxy_index = proxy_model.mapFromSource(attr_index)
            self.view.openPersistentEditor(proxy_index)
        
        # Iterate through root/top level rows and set expansion.
        pre_collapse = ['System']
        for row in range(proxy_model.rowCount()):
            index = proxy_model.index(row, 0)
            parent_name = index.data(Qt.DisplayRole)
            expand_state = False if parent_name in pre_collapse else True
            self.view.setExpanded(index, expand_state, user=True)

        self.attr_to_item = attr_to_item
        self.assets = []
        self.adjustSize()
        self.filter_text = ''

    def filterAll(self, text):
        self.filter_text = text
        self.view.filter(text)
        # get the current open persistent editors in the view by index.
        attr_map = self.attr_to_item
        delegate = self.view.itemDelegate()
        for editor_ref in delegate.active_editors.values():
            editor_instance = editor_ref()
            if isinstance(editor_instance, ItemEditor):
                regex = QRegularExpression(text, QRegularExpression.CaseInsensitiveOption)
                editor_instance.proxy_model.setFilterRegularExpression(regex)

    def setAssets(self, assets):
        self.view.clearSelection() # Deselect all items.
        if not assets:
            return
        self.assets = assets
        asset = assets[-1]
        self._block_update = True
        #TODO: Dont block the update, Instead prompt the user to commit changes if 
        # the editor is active and contents were modified.
        for attr, value_item in self.attr_to_item.items():
            if hasattr(asset, attr):
                value = getattr(asset, attr)
                if value is None:
                    editor = value_item.data(role=EditorRole)
                    value = editor.default_value

                value_item.setData(value, role=Qt.EditRole)
        proxy_model = self.view.model()
        # Close existing persistent editors and open new ones.
        for attr in PERSISTENT_ATTRIBUTES:
            attr_index = self.attr_to_item[attr].index()
            index = proxy_model.mapFromSource(attr_index)
            self.view.closePersistentEditor(index)
            self.view.openPersistentEditor(index)

        self._block_update = False
        self.filterAll(self.filter_text)

    @Slot()
    def onDataChanged(self, top_left, bot_right, roles):
        edit_change = Qt.EditRole in roles

        if self._block_update or not edit_change:
            return

        item = _indexToItem(top_left)
        editor = item.data(role=EditorRole)
        value = top_left.data(role=Qt.EditRole)

        # retrieve the key from the sibling label item.
        label_index = top_left.sibling(top_left.row(), 0)
        label_item = label_index.data(role=Qt.UserRole)

        # Only change if the field is editable and the app is in edit mode.
        EDITABLE = 2
        key = label_item.name
        if ATTRIBUTE_MAP[key][EDITABLE] and RELIC_PREFS.edit_mode:
            self.attributeChanged.emit(key, value, self.assets)
