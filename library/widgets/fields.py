import time
from functools import partial
from collections import UserList
from datetime import date, datetime
from enum import IntEnum

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from relic.scheme import Classification, AssetType, UserType, TagType
from relic.local import Category, Relational
from library.objectmodels import temp_asset, alusers, tags, getCategoryConstructor
from library.widgets.rating import Rating
from library.widgets.simple_asset_view import SimpleAssetView
from qtshared6.utils import polymorphicItem


class SpinBox(QSpinBox):
    def __init__(self, *args, **kwargs):
        super(SpinBox, self).__init__(*args, **kwargs)
        self.setMaximum(2147483647)

def scale_icon(pix: QPixmap):
    return pix.scaled(16,16, Qt.KeepAspectRatio, Qt.SmoothTransformation)

# Setters and getters to "_set" and "_get".
QDateTimeEdit._set = QDateTimeEdit.setDateTime; QDateTimeEdit._get = QDateTimeEdit.dateTime
QComboBox._set = QComboBox.setCurrentIndex; QComboBox._get = QComboBox.currentIndex
QCheckBox._set = QCheckBox.setChecked; QCheckBox._get = QCheckBox.isChecked
QLineEdit._set = QLineEdit.setText; QLineEdit._get = QLineEdit.text
QDateEdit._set = QDateEdit.setDate; QDateEdit._get = QDateEdit.date
SpinBox._set = SpinBox.setValue; SpinBox._get = SpinBox.value
Rating._set = Rating.setValue; Rating._get = Rating.getValue

class RelationDelegate(QStyledItemDelegate):

    def paint(self, painter, option, index):
        option.decorationPosition = QStyleOptionViewItem.Left
        super(RelationDelegate, self).paint(painter, option, index)

    def sizeHint(self, option, index):
        bounds = option.fontMetrics.boundingRect(
            option.rect, 0, str(index.data(Qt.DisplayRole))
        )
        return bounds.size() + QSize(option.decorationSize.width() * 2.1, 0)

class ItemState(IntEnum):
    NONE = 0
    NEW = 1
    LINK = 2
    REMOVE = 3

class ObjectMulti(QListView):

    def __init__(self, *args, **kwargs):
        super(ObjectMulti, self).__init__(*args, **kwargs)
        self.setItemDelegate(RelationDelegate(self))
        self.setFlow(QListView.LeftToRight)
        self.setWrapping(True)
        self.setIconSize(QSize(16, 16))
        self.setWordWrap(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._createContextMenus)
        self.relation_view = SimpleAssetView(self)
        self.relation_view.newItem.connect(self.createNewItem)
        self.relation_view.linkItem.connect(self.onLinkItem)
        model = QStandardItemModel()
        self.setModel(model)

    def mouseDoubleClickEvent(self, event):
        print(event)

    def _createContextMenus(self, value):
        context_menu = QMenu(self)
        new_action = context_menu.addAction("Add New")
        new_action.triggered.connect(self.onNewAction)
        remove_action = context_menu.addAction("Remove Selected")
        remove_action.triggered.connect(self.removeSelectedItems)
        context_menu.exec(QCursor.pos())

    @Slot()
    def onNewAction(self):
        field_name = self._field.name
        constructor = getCategoryConstructor(field_name.lower())

        if constructor is not temp_asset:
            self.relation_view.setConstructor(constructor)
            self.relation_view.show()

    @Slot(str)
    def createNewItem(self, name):
        relation_asset = self.relation_view.constructor(name=name)
        relation_asset.status = ItemState.NEW
        new_item = polymorphicItem(fields=relation_asset)
        self.model().appendRow(new_item)

    @Slot()
    def onLinkItem(self, relation_asset):
        relation_asset.status = ItemState.LINK
        new_item = polymorphicItem(fields=relation_asset)
        self.model().appendRow(new_item)
 
    @Slot()
    def removeSelectedItems(self):
        selection = self.selectionModel().selectedIndexes()
        for index in selection:
            self.setRowHidden(index.row(), True)
            asset = index.data(Qt.UserRole)
            asset.status = ItemState.REMOVE

    def setItems(self, values):
        model = self.model()
        for item in values:
            icon = icon_from_item(item)
            item.status = ItemState.NONE
            item.setIcon(icon)
            model.appendRow(item)

    def getItems(self):
        model = self.model()
        items = [model.takeItem(i, 0) for i in range(model.rowCount())]
        return items


ObjectMulti._set = ObjectMulti.setItems; ObjectMulti._get = ObjectMulti.getItems


class VerticalTreeModel(QStandardItemModel):

    FieldRole = Qt.UserRole + 1

    def __init__(self, *args, **kwargs):
        super(VerticalTreeModel, self).__init__(*args, **kwargs)
        self.setColumnCount(2)

    def data(self, index, role):
        if index.isValid():
            item = self.itemFromIndex(index)
            value = item.data(role=Qt.EditRole)
            if value is None:
                return
            elif role == Qt.EditRole:
                field = item.data(role=Qt.EditRole)
                return value
            elif role in (Qt.DisplayRole, Qt.ToolTipRole):
                try:
                    v = str(value)
                    return v
                except: pass
            elif (role == Qt.TextAlignmentRole) and index.column() == 1:
                return Qt.AlignLeft
            elif (role == Qt.TextAlignmentRole) and index.column() == 0:
                return Qt.AlignTop

    def flags(self, index):
        flags = super(VerticalTreeModel, self).flags(index)

        if index.isValid():
            flags |= Qt.ItemIsEditable
            flags |= Qt.ItemIsDragEnabled
        else:
            flags = Qt.ItemIsDropEnabled

        return flags


class FieldDelegate(QStyledItemDelegate):

    def __init__(self, parent=None):
        super(FieldDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        if index.column() != 1:
            return
        model = index.model() 
        item = model.itemFromIndex(index)

        field_obj = item.data(role=VerticalTreeModel.FieldRole)
        if not field_obj:
            return

        value = item.data(role=Qt.EditRole)

        editor = value.widget(parent)
        editor._field = field_obj

        # setEditorData is more convenient here.
        if value is not None:
            # Qt Needs this cause it interprets 'str' instances special.
            if field_obj.data in [TextField, LinkField]:
                editor._set(str(value))
            else:
                editor._set(value)

        return editor


    def setModelData(self, editor, model, index):
        value = editor._get()
        converted = editor._field.data(value)
        model.setData(index, converted, Qt.EditRole)
    
    def paint(self, painter, option, index):
        option.decorationPosition = QStyleOptionViewItem.Left
        value = index.model().data(index, Qt.EditRole)
        if index.column() == 1 and value is not None and value != []:
            if hasattr(value, 'draw'):
                super(FieldDelegate, self).paint(painter, option, index)
                value.draw(painter, option, index, value)
                return

        widget = option.widget
        if widget.indentation():
            return super(FieldDelegate, self).paint(painter, option, index)

        opt = QStyleOptionViewItem(option)
        is_zero_column = (index.column() == 0)
        if is_zero_column:
            opt.font.setWeight(QFont.DemiBold)
            item = index.model().itemFromIndex(index)
            if item.hasChildren():
                opt.rect.adjust(opt.rect.height(), 0, 0, 0)

        super(FieldDelegate, self).paint(painter, opt, index)

        if is_zero_column and item.hasChildren():
            branch = QStyleOptionViewItem()
            branch.rect = QRect(0, opt.rect.y(), opt.rect.height(), opt.rect.height())
            branch.state = option.state
            style = widget.style()
            style.drawPrimitive(QStyle.PE_IndicatorBranch, branch, painter, widget)

    def sizeHint(self, option, index):
        if index.column() == 1:
            item = index.model().itemFromIndex(index)
            obj = item.data(role=VerticalTreeModel.FieldRole)
            if obj and obj.data == ObjectField:
                return QSize(24, 72)
        elif index.column() == 0:
            return QSize(option.rect.width(), 22)

        return super(FieldDelegate, self).sizeHint(option, index)


class ComboField(object):
    default = 0

    def draw(self, painter, option, index, value):
        if not option.state & QStyle.State_Selected:
            painter.save()
            style_opt = QStyleOptionComboBox()
            style_opt.rect = option.rect - QMargins(2,2,2,1)#- QMargins(2,3,4,2)
            style_opt.currentText = str(value.name.capitalize())
            style_opt.currentIcon = value.icon
            style_opt.iconSize = QSize(16, 16)
            style_opt.state = option.state
            widget = option.widget
            widget_style = widget.style()
            widget_style.drawComplexControl(QStyle.CC_ComboBox, style_opt, painter, widget)
            widget_style.drawControl(QStyle.CE_ComboBoxLabel, style_opt, painter, widget)
            path = QPainterPath()
            path.addRoundedRect(style_opt.rect, 2, 2)
            painter.setPen(QPen(QColor(58,58,58), 1))
            painter.fillPath(path, QColor(250,250,250,25))
            painter.drawPath(path)
            painter.restore()


class CheckField(int):
    widget = QCheckBox
    default = 0

    @staticmethod
    def draw(painter, option, index, value):
        widget = option.widget
        widget_style = widget.style()
        bg = widget.palette().color(widget.backgroundRole())
        painter.fillRect(option.rect, bg)
        style_opt = QStyleOptionButton()
        style_opt.rect = widget_style.subElementRect(QStyle.SE_ItemViewItemText, option, widget)
        if value:
            style_opt.state |= QStyle.State_On
        else:
            style_opt.state |= QStyle.State_Off
    
        widget_style.drawControl(QStyle.CE_ItemViewItem, option, painter, widget)

        widget_style.drawControl(QStyle.CE_CheckBox, style_opt, painter, widget)
        

class RatingField(int):
    widget = Rating
    default = 0
    icon = scale_icon(QPixmap(':resources/app/heart.svg'))
    disabled = scale_icon(QPixmap(':resources/app/heart_disabled.svg'))

    def draw(self, painter, option, index, value):
        widget = option.widget 
        widget_style = widget.style()
        bg = widget.palette().color(widget.backgroundRole())

        widget.ensurePolished()
        painter.fillRect(option.rect, bg)
        sub_rect = widget_style.subElementRect(QStyle.SE_ItemViewItemText, option, widget)
        widget_style.drawControl(QStyle.CE_ItemViewItem, option, painter, widget)

        RatingField.widget.paint(painter, sub_rect, value)


class QualityField(RatingField):
    icon = scale_icon(QPixmap(':resources/app/star.svg'))
    disabled = scale_icon(QPixmap(':resources/app/star_disabled.svg'))


class ObjectField(UserList):
    widget = ObjectMulti
    default = UserList()

    def __init__(self, values):
        super(ObjectField, self).__init__(values)

    def __str__(self):
        return ','.join([x.name for x in self])

    @staticmethod
    def draw(painter, option, index, value):
        painter.save()

        items = value.data
        widget = option.widget
        bg = widget.palette().color(widget.backgroundRole())
        widget_style = widget.style()

        rect = option.rect
        inbound = rect - QMargins(3,3,3,3)
        painter.fillRect(inbound, QColor(43,43,43))
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        new_size = rect.size() - QSize(37, 0)
        x_origin = rect.x() + 9
        rect_width = new_size.width()
        painter.translate(x_origin, rect.y() + 5)
        y_offset_count = 0
        x_pos = 0
        margin = 8
        draw_expander = False
        for i, item in enumerate(items):
            icon = icon_from_item(item)
            x_offset = option.fontMetrics.horizontalAdvance(item.name) + (margin * 2) + 1
            if x_pos + x_offset >= rect_width:
                painter.translate(-x_pos, 16)
                x_pos = 0
                y_offset_count += 1
            # The vertical size can only fit 3 rows of items to display.
            if y_offset_count == 3:
                draw_expander = True
                break
            painter.drawPixmap(QRect(0, 0, 16, 16), icon)
            painter.translate(16, 0)
            x_pos += 16
            painter.drawText(QRect(margin - 2, 0, x_offset - 2, 16), item.name)
            painter.translate(x_offset, 0)
            x_pos += x_offset

        painter.restore()
        # Draw drop down indicator
        if draw_expander:
            dropdown = QStyleOptionToolButton()
            size = QSize(inbound.width(), 16)
            pos = inbound.bottomLeft() - QPoint(0, size.height()-1)
            dropdown.rect = QRect(pos, size) - QMargins(1,1,1,1)
            dropdown.state = QStyle.State_Enabled | QStyle.State_Raised
            dropdown.toolButtonStyle = Qt.ToolButtonIconOnly
            dropdown.subControls = QStyle.SC_ToolButton
            dropdown.icon = QIcon(':resources/style/stylesheet-branch-open.png')
            dropdown.iconSize = QSize(8, 8)
            widget_style.drawComplexControl(QStyle.CC_ToolButton, dropdown, painter, widget)
        # Draw counts in bottom right corner
        painter.drawText(
            inbound - QMargins(1,1,2,1),
            Qt.AlignBottom | Qt.AlignRight,
            f'({len(value)})',
        )


class TextField(object):
    widget = QLineEdit
    default = ''

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class LinkField(TextField):

    @staticmethod
    def draw(painter, option, index, value):
        painter.save()
        widget = option.widget
        roi = option.rect - QMargins(5,3,4,0)
        option.font.setUnderline(True)
        painter.setFont(option.font)
        if option.state & QStyle.State_MouseOver:
            painter.setPen(QColor(32,32,32))
            option.font.setWeight(QFont.Bold)
            if not option.state & QStyle.State_Selected:
                painter.fillRect(roi, QColor(75,75,75))
                painter.setPen(QColor(108,128,254))
        else:
            painter.setPen(QColor(32,32,32))
            if not option.state & QStyle.State_Selected:
                painter.fillRect(roi, QColor(68,68,68))
                painter.setPen(QColor(92,108,245))

        painter.drawText(roi, str(value))
        painter.restore()


class IntField(int):
    widget = SpinBox
    default = 0

class FileSizeField(IntField):
    def __str__(self):
        return "{:,} MB".format(self / 1000)

class DurationField(IntField):
    def __str__(self):
        return "{} Sec".format(int(self))

class FramerateField(IntField):
    def __str__(self):
        return "{} fps".format(int(self))

class DateField(date):
    widget = QDateEdit
    
    def __new__(cls, args):
        if isinstance(args, QDate):
            return date.__new__(cls, args.year(), args.month(), args.day())

        return date.__new__(cls, *args)


class DateTimeField(datetime):
    widget = QDateTimeEdit

    def __new__(cls, args):
        if isinstance(args, QDateTime):
            date = args.date()
            _time = args.time()
            return datetime.__new__(
                cls, date.year(), date.month(), date.day(), _time.hour(), _time.minute(), _time.second())
        elif isinstance(args, str):
            return datetime.__new__(cls, *(time.strptime(args, '%Y-%m-%d %H:%M:%S.%f')[0:6]))
            #1/12/2021 6:38 PM
        return datetime.__new__(cls, *args)

    def __str__(self):
        return self.strftime("%b %d, %Y %H:%M")


def enum_widget_creator(cls, parent):
    widget = QComboBox(parent)
    [widget.addItem(x.icon, x.name.capitalize()) for x in cls]
    return widget

def assign_enum_icons(obj):
    prefix = obj.__name__
    for x in obj:
        x.icon = QPixmap(f':{prefix}/{x.name}')

def setup_enum_ui(combo_enum):
    combo_enum.draw = ComboField.draw
    combo_enum.default = 0
    combo_enum.widget = partial(enum_widget_creator, combo_enum)
    assign_enum_icons(combo_enum)

def icon_from_item(item):
    asset = item.data(role=Qt.UserRole)
    # TODO: make this logic better.
    if hasattr(asset, 'category'):
        icon = Category(asset.category).icon
    elif isinstance(asset, alusers):
        if not asset.type:
            icon = UserType(0).icon
        else:
            icon = UserType(asset.type).icon
    elif isinstance(asset, tags):
        if not asset.type:
            icon = TagType(0).icon
        else:
            icon = TagType(asset.type).icon
    else:
        icon = QPixmap()
    return icon

# Setup asset type UI
setup_enum_ui(AssetType)
setup_enum_ui(Classification)
setup_enum_ui(Category)
setup_enum_ui(TagType)
setup_enum_ui(UserType)
