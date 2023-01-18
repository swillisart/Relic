from functools import partial

from relic.qt.util import polymorphicItem, indexToItem
from relic.qt.widgets import FilterBox, FilterBoxLine

from PySide6.QtCore import (QEvent, QFile, QItemSelectionModel, QMargins,
                            QObject, QPoint, QRect, QRegularExpression, QSize,
                            QSortFilterProxyModel, Qt, QTextStream, Signal,
                            Slot, QPropertyAnimation, Property)
from PySide6.QtGui import (QAction, QColor, QCursor, QFont, QFontMetrics,
                           QIcon, QPainter, QPixmap, QStandardItem,
                           QRegularExpressionValidator, QStandardItemModel, Qt)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QBoxLayout,
                               QDockWidget, QFrame, QLabel, QLineEdit,
                               QListView, QMenu, QScrollArea,
                               QStyledItemDelegate, QTreeView, QVBoxLayout,
                               QWidget, QLayout, QDialog)


class SimpleAsset(object):
    __slots__ = ['name', 'id']
    def __init__(self, name, id):
        self.name = name
        self.id = id

class FocusedSearchBox(FilterBoxLine):

    focusOut = Signal(bool)
    onReturn = Signal(bool)

    def __init__(self, *args, **kwargs):
        super(FocusedSearchBox, self).__init__(*args, **kwargs)
        self.setFocusPolicy(Qt.StrongFocus)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Down or key == Qt.Key_Up:
            self.focusOut.emit(True)
        elif event.key() == Qt.Key_Return:
            self.onReturn.emit(True)
        else:
            super(FocusedSearchBox, self).keyPressEvent(event)


class FocusFilter(QObject):
    onFocusedIn = Signal()
    onFocusedOut = Signal()
    onTabPress = Signal()

    def eventFilter(self, widget, event):
        event_type = event.type()
        if event_type == QEvent.FocusOut:
            self.onFocusedOut.emit()
        elif event_type == QEvent.FocusIn:
            self.onFocusedIn.emit()
        elif event_type == QEvent.KeyPress:
            if event.key() == Qt.Key_Tab:
                self.onTabPress.emit()
        return super(FocusFilter, self).eventFilter(widget, event)


class ListViewFocus(QFrame):

    newItem = Signal(str)
    renameItem = Signal(str)
    linkItem = Signal(SimpleAsset)

    def __init__(self, *args, **kwargs):
        super(ListViewFocus, self).__init__(*args, **kwargs)
        self.rename_mode = False
        self.filter_regex = r"[A-Za-z0-9]+"

        self.focus_filter = FocusFilter()
        self.focus_filter.onFocusedOut.connect(self.hide_filter)
        self.focus_filter.onTabPress.connect(self.onViewReturn)

        # Models
        self.proxyModel = QSortFilterProxyModel()
        self.proxyModel.setDynamicSortFilter(True)
        self.itemModel = QStandardItemModel(self)
        self.proxyModel.setSourceModel(self.itemModel)

        self.list_view = FocusListView(self)
        self.list_view.setModel(self.proxyModel)
        self.list_view.onReturn.connect(self.onViewReturn)
        self.list_view.fill_line_text.connect(self.onViewFill)

        selmod = self.list_view.selectionModel()
        selmod.selectionChanged.connect(self.onSelection)

        # Widgets
        self.filter_box = FilterBox(self, editor=False)
        self.searchBox = FocusedSearchBox()
        self.filter_box.editor = self.searchBox
        self.filter_box.layout().addWidget(self.searchBox)
        self.searchBox.installEventFilter(self.focus_filter)
        self.searchBox.textChanged.connect(self.filterRegExpChanged)
        self.searchBox.focusOut.connect(self.list_view.setFocus)
        focus_first = lambda x: self.list_view.setCurrentIndex(self.proxyModel.index(0, 0))
        self.searchBox.focusOut.connect(focus_first)
        self.searchBox.onReturn.connect(self.onViewReturn)
        self.list_view.onBackspace.connect(self.searchBox.keyPressEvent)

        qregex = QRegularExpression(self.filter_regex)
        validator = QRegularExpressionValidator(qregex)
        self.searchBox.setValidator(validator)

        # Layouts
        layout = QVBoxLayout()
        layout.setContentsMargins(2,2,2,2)
        layout.setSpacing(1)
        layout.addWidget(self.filter_box)
        layout.addWidget(self.list_view)
        self.setLayout(layout)  

    def addItems(self, data_model, replace=False):
        if replace:
            self.itemModel.clear()
        item_model = self.itemModel
        recurse = self.recursivelyAppendItemToModel
        if isinstance(data_model, QStandardItemModel):
            for i in range(data_model.rowCount()):
                item = data_model.item(i, 0)
                if item:
                    recurse(item_model, recurse, item)

        print(self.proxyModel.rowCount())
        print(self.itemModel.rowCount())

    @staticmethod
    def recursivelyAppendItemToModel(item_model, recurse, item):
        obj = item.data(Qt.UserRole)
        simple = SimpleAsset(obj.name, obj.id)
        clone = polymorphicItem(fields=simple)
        item_model.appendRow(clone)
        if item.hasChildren():
            for i in range(item.rowCount()):
                child_index = item.child(i, 0)
                if child_index:
                    recurse(item_model, recurse, child_index)

    @Slot()
    def onSelection(self, selection):
        indices = selection.indexes()
        if indices:
            asset = indices[0].data(Qt.UserRole)
            #print(asset)
            
            #self.searchBox.setText(asset.name)
            #self.searchBox.setFocus()
            # model_item_index = [self.itemModel.itemFromIndex(i).data()
            #  for i in self.list_view.selectedIndexes()]
            # index = self.list_view.selectedIndexes()[0]

    @Slot()
    def onViewFill(self):
        try:
            index = self.list_view.selectedIndexes()[0]
        except Exception:
            index = self.proxyModel.index(0, 0)

        self.searchBox.setText(index.data())
        self.searchBox.setFocus()

    @Slot()
    def hide_filter(self):
        if (
            self.searchBox.hasFocus() is False
            and self.list_view.hasFocus() is False
        ):
            self.hide()

    @Slot()
    def filterRegExpChanged(self):
        text = self.searchBox.text()
        regex = QRegularExpression(
            text, QRegularExpression.CaseInsensitiveOption)
        self.proxyModel.setFilterRegularExpression(regex)

    def addItem(self, name, id):
        asset_obj = SimpleAsset(name=name, id=id)
        item = polymorphicItem(fields=asset_obj)
        self.itemModel.appendRow(item)
        return item

    @Slot()
    def onViewReturn(self):
        try:
            index = self.list_view.selectedIndexes()[0]
        except Exception:
            index = self.proxyModel.index(0, 0)
        if index.data():
            asset = index.data(Qt.UserRole)
            if not asset.id:
                print('HEY HEY HAY REMOVE ME!!!!!')
                asset = asset.name
            self.linkItem.emit(asset)
        else:
            if self.rename_mode:
                self.renameItem.emit(str(self.searchBox.text()))
            else:
                item = self.addItem(str(self.searchBox.text()), None)
                self.newItem.emit(item.name)

        self.searchBox.setFocus()
        self.hide()

    def sizeHint(self):
        return QSize(275, 250)

    def show(self):
        self.itemModel.clear()
        self.searchBox.clear()
        pos = QCursor.pos()
        x = pos.x() - (self.sizeHint().width() / 2)
        y = pos.y()
        self.move(x + 75, y - 5)
        super(ListViewFocus, self).show()
        self.searchBox.setFocus()
        self.searchBox.setCursorPosition(0)

class AssetNameListView(ListViewFocus):


    def __init__(self, *args, **kwargs):
        super(AssetNameListView, self).__init__(*args, **kwargs)
        self.searchBox.removeEventFilter(self.focus_filter)

    def show(self):
        super(AssetNameListView, self).show()

    @Slot()
    def hide_filter(self):
        return

    @Slot()
    def onViewReturn(self):
        try:
            index = self.list_view.selectedIndexes()[0]
        except Exception:
            index = self.proxyModel.index(0, 0)

        if index.data():
            asset = index.data(Qt.UserRole)
            self.linkItem.emit(asset)
        else:
            self.newItem.emit(str(self.searchBox.text()))
        self.searchBox.clear()


class FocusListView(QListView):

    onReturn = Signal(bool)
    onBackspace = Signal(QEvent)
    fill_line_text = Signal(bool)

    def __init__(self, *args, **kwargs):
        super(FocusListView, self).__init__(*args, **kwargs)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.onReturn.emit(True)

        if event.key() == Qt.Key_Space:
            self.fill_line_text.emit(True)

        if event.key() == Qt.Key_Backspace:
            self.onBackspace.emit(event)

        super(FocusListView, self).keyPressEvent(event)


class DialogOverlay(QDialog):

    def read_opaque(self):                                                                                   
        return self._opaque                                                               
                                                                                                    
    def set_opaque(self, val):                                                                                
        self._opaque = val 

    p_opaque = Property(int, read_opaque, set_opaque)

    def __init__(self, parent, widget, modal=True):
        super(DialogOverlay, self).__init__(parent)
        # Experimental
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        # Essentials
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAutoFillBackground(True)
        self.setMouseTracking(True)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(128, 32, 128, 32)
        self.layout.setAlignment(Qt.AlignCenter)
        self.widget = widget
        #self.layout.addWidget(widget)
        self._opaque = 0
        self.setModal(modal)
        parent.installEventFilter(self)

        # Optional Animation
        self.anim = QPropertyAnimation(self, b"p_opaque")
        self.anim.setDuration(175)
        self.anim.setStartValue(0)
        self.anim.setEndValue(150)
        self.anim1 = QPropertyAnimation(self, b"geometry")
        self.anim1.setDuration(175)
        self.anim1.setStartValue(self.parent().rect() - QMargins(10, 10, 10, 10))
        self.anim1.setEndValue(self.parent().rect())
        self.show()
        self.anim.start(QPropertyAnimation.DeleteWhenStopped)
        self.anim1.start(QPropertyAnimation.DeleteWhenStopped)
        
        self.anim.finished.connect(partial(self.layout.addWidget, widget))
        self.anim.finished.connect(widget.show)

    def eventFilter(self, widget, event):
        parent = self.parent()
        if widget is parent and event.type() == QEvent.Resize:
                self.setGeometry(parent.rect())
                return True
        else:
            return False

    def mousePressEvent(self, event):
        if self.isModal() and not self.widget.underMouse():
            self.close()

    def closeEvent(self, event):
        self.parent().removeEventFilter(self)
        super(DialogOverlay, self).closeEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        #painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        painter.setBrush(QColor(10, 10, 10, self._opaque))
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.geometry())

    def show(self):
        parent = self.parent()
        self.setGeometry(parent.rect())
        super(DialogOverlay, self).show()
