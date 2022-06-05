from extra_types.enums import DataAutoEnum

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

# Setters and getters to "_set" and "_get".
QComboBox._set = 'setCurrentIndex'; QComboBox._get = 'currentIndex'; 
QCheckBox._set = 'setChecked'; QCheckBox._get = 'isChecked'; 
QLineEdit._set = 'setText'; QLineEdit._get = 'text'; 
QDateEdit._set = 'setDate'; QDateEdit._get = 'date'; 
QSpinBox._set = 'setValue'; QSpinBox._get = 'value'; 

class TreeTableModel(QStandardItemModel):

    def __init__(self, rows, columns):
        super(TreeTableModel, self).__init__(len(rows), len(columns))
        self.rows = rows
        self.columns = columns

    def data(self, index, role):
        if index.isValid():
            field_id = self.columns[index.column()]
            value = getattr(self.rows[index.row()], field_id)
            if role == Qt.EditRole:
                return value
            elif role in (Qt.DisplayRole, Qt.ToolTipRole):
                return str(value)
            #elif (role == Qt.TextAlignmentRole):
            #    return Qt.AlignLeft

    def setData(self, index, value, role=Qt.EditRole):
        if index.isValid() and role == Qt.EditRole:
            field_id = self.columns[index.column()]
            setattr(self.rows[index.row()], field_id, value)
            self.dataChanged.emit(index, index)
            return True

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.columns[section]
        return super(TreeTableModel, self).headerData(section, orientation, role)

    def flags(self, index):
        flags = super(TreeTableModel, self).flags(index)

        if index.isValid():
            flags |= Qt.ItemIsEditable
            flags |= Qt.ItemIsDragEnabled
        else:
            flags = Qt.ItemIsDropEnabled

        return flags


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
                return str(value)

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
        my_parent = self.parent()
        model = index.model() 
        item = model.itemFromIndex(index)

        field_obj = item.data(role=VerticalTreeModel.FieldRole)
        if not field_obj:
            return
        if my_parent:
            widget = my_parent.data_mapper.mappedWidgetAt(field_obj.value)

        value = item.data(role=Qt.EditRole)
        new = value.widget(parent)
        setter = getattr(new, widget._set)
        new._type = widget._type
        return new

    def setEditorData(self, editor, index):
        if index.column() != 1:
            return
        model = index.model() 
        item = model.itemFromIndex(index)

        value = item.data(role=Qt.EditRole)
        field_obj = item.data(role=VerticalTreeModel.FieldRole)
        if value is not None:
            func = getattr(editor, editor._set)
            # Qt Needs this cause it interprests 'str' instances special.
            if field_obj.data == TextField: 
                func(str(value))
            else:
                func(value)

    def setModelData(self, editor, model, index):
        func = getattr(editor, editor._get)
        value = func()
        converted = editor._type(value)
        model.setData(index, converted, Qt.EditRole)
    
    def paint(self, painter, option, index):
        value = index.model().data(index, Qt.EditRole)
        if index.column() == 1 and value is not None:
            try:
                widget = value.widget
                value.draw(painter, option, index, value)
            except:
                super(FieldDelegate, self).paint(painter, option, index)
        else:
            super(FieldDelegate, self).paint(painter, option, index)

    #def destroyEditor(self, editor, index):
    #    pass

class ComboField(DataAutoEnum):

    @staticmethod
    def draw(painter, option, index, value):
        style_opt = QStyleOptionComboBox()
        style_opt.rect = option.rect
        style_opt.currentText = str(value.name)
        style_opt.currentIcon = value.data
        style_opt.iconSize = QSize(16, 16)
        style_opt.editable = False
        style_opt.subControls = QStyle.SC_ComboBoxArrow
        style_opt.state = option.state
        widget = option.widget
        widget_style = widget.style()
        widget_style.drawComplexControl(QStyle.CC_ComboBox, style_opt, painter)
        widget_style.drawControl(QStyle.CE_ComboBoxLabel, style_opt, painter)


class CheckField(int):
    widget = QCheckBox

    @staticmethod
    def draw(painter, option, index, value):
        style_opt = QStyleOptionButton()
        style_opt.rect = option.rect
        style_opt.state |= QStyle.State_Enabled
        if value:
            style_opt.state |= QStyle.State_On
        else:
            style_opt.state |= QStyle.State_Off

        #style_opt.setStyleSheet("background-color: red")
        widget = option.widget
        widget_style = widget.style()
        if option.state & QStyle.State_Selected:
            widget_style.drawPrimitive(QStyle.PE_Frame, style_opt, painter, widget)

        widget_style.drawControl(QStyle.CE_CheckBox, style_opt, painter, widget)


class TextField(object):
    widget = QLineEdit

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


class IntField(int):
    widget = QSpinBox
