import re
from functools import partial

from library.ui.list_view_filtered import Ui_ListViewFiltered
from qtshared6.utils import polymorphicItem

from PySide6.QtCore import (QEvent, QFile, QItemSelectionModel, QMargins,
                            QObject, QPoint, QRect, QRegularExpression, QSize,
                            QSortFilterProxyModel, Qt, QTextStream, Signal,
                            Slot, QPropertyAnimation, Property)
from PySide6.QtGui import (QAction, QColor, QCursor, QFont, QFontMetrics,
                           QIcon, QPainter, QPixmap, QStandardItem,
                           QRegularExpressionValidator, QStandardItemModel, Qt)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QBoxLayout,
                               QDockWidget, QFrame, QLabel, QLineEdit,
                               QListView, QMenu, QScrollArea,
                               QStyledItemDelegate, QTreeView, QVBoxLayout,
                               QWidget, QLayout, QDialog)

def rasterizeSVG(svg_file, size=QSize(28, 28)):
    svgWidget = QSvgWidget()
    svgWidget.load(svg_file)
    svgRenderer = svgWidget.renderer()
    svg_image = QPixmap(size)
    svg_image.fill(Qt.transparent)
    pixPainter = QPainter(svg_image)
    svgRenderer.render(pixPainter)
    pixPainter.end()
    del svgWidget, svgRenderer, pixPainter
    return svg_image


def modifySVG(file_path, find, replace, regex=False, size_override=False):
    """Modifies an input SVG by swapping find with replace.
    May be used with regular expression via regex parameter. 

    Parameters
    ----------
    file_path : str
    find : str
        text or regex to search for
    replace : str
        text to replace matched strings
    regex : bool, optional
        find is using regular expressions, by default False
    size_override : QSize, optional
        Resize image to fit, by default False

    Returns
    -------
    QPixmap
        Modified SVG Pixmap rendered into the size of SVG
    """

    f = QFile(file_path)
    if f.open(QFile.ReadOnly | QFile.Text):
        textStream = QTextStream(f)
        if regex:
            svgData = re.sub(find, replace, textStream.readAll())
        else:
            svgData = textStream.readAll().replace(find, replace)
        f.close()

    svg = QSvgRenderer()
    svg.load(svgData.encode('utf-8'))
    size = size_override if size_override else svg.defaultSize()
    image = QPixmap(size)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    svg.render(painter)
    painter.end()
    return image

class SimpleAsset(object):
    __slots__ = ['name', 'id']
    def __init__(self, name, id):
        self.name = name
        self.id = id

class SearchBox(QLineEdit):

    focusOut = Signal(bool)
    onReturn = Signal(bool)

    def __init__(self, *args, **kwargs):
        super(SearchBox, self).__init__(*args, **kwargs)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setPlaceholderText('Filter...')
        self.stylefont = QFont("Segoi UI", 9)
        self.stylefont.setStyleHint(QFont.TypeWriter)
        self.setFont(self.stylefont)
        self.setFrame(False)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Down or key == Qt.Key_Up:
            self.focusOut.emit(True)
        elif event.key() == Qt.Key_Return:
            self.onReturn.emit(True)
        else:
            super(SearchBox, self).keyPressEvent(event)

    def paintEvent(self, event):
        super(SearchBox, self).paintEvent(event)

        if self.hasFocus() and self.text() and not self.selectedText():
            painter = QPainter(self)
            cursor_rect = self.cursorRect()
            sub_rect = cursor_rect - QMargins(6, 0, 4, 0)
            painter.fillRect(sub_rect, QColor(31, 28, 27))
            painter.setPen(QColor(205, 205, 205))

            currentPos = int(self.cursorPosition())
            currentText = self.text()
            if not currentPos < len(currentText):
                return
            elif currentPos + 1 < len(currentText):
                nextChar = currentText[currentPos+1]
            else:
                nextChar = ' '
            currentChar = currentText[currentPos]

            metric = QFontMetrics(self.font())
            width = metric.horizontalAdvance(currentChar)
            character_rect = QRect(
                cursor_rect.x()+5,
                cursor_rect.y(),
                width+2,
                cursor_rect.height()
            ) 
            painter.drawText(
                character_rect,
                currentChar + nextChar
            )
            painter.end()


class FocusFilter(QObject):
    onFocusedIn = Signal()
    onFocusedOut = Signal()
    onTabPress = Signal()

    def eventFilter(self, widget, event):
        if event.type() == QEvent.FocusOut:
            self.onFocusedOut.emit()
            return True
        if event.type() == QEvent.FocusIn:
            self.onFocusedIn.emit()
            return True
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Tab:
                self.onTabPress.emit()
                return True
            else:
                return False
        else:
            return False


class ListViewFocus(Ui_ListViewFiltered, QWidget):

    newItem = Signal(str)
    renameItem = Signal(str)
    linkItem = Signal(SimpleAsset)

    def __init__(self, *args, **kwargs):
        super(ListViewFocus, self).__init__(*args, **kwargs)
        self.setupUi(self)
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

        self.listView = FocusListView(self)
        self.listView.setModel(self.proxyModel)
        self.listView.onReturn.connect(self.onViewReturn)
        self.listView.fill_line_text.connect(self.onViewFill)

        selmod = self.listView.selectionModel()
        selmod.selectionChanged.connect(self.onSelection)

        # Widgets
        self.searchBox = SearchBox()
        self.searchBox.installEventFilter(self.focus_filter)
        self.searchBox.textChanged.connect(self.filterRegExpChanged)
        self.searchBox.focusOut.connect(self.listView.setFocus)
        focus_first = lambda x: self.listView.setCurrentIndex(self.proxyModel.index(0, 0))
        self.searchBox.focusOut.connect(focus_first)
        self.searchBox.onReturn.connect(self.onViewReturn)
        self.listView.onBackspace.connect(self.searchBox.keyPressEvent)

        qregex = QRegularExpression(self.filter_regex)
        validator = QRegularExpressionValidator(qregex)
        self.searchBox.setValidator(validator)

        # Layouts 
        self.layout().insertWidget(1, self.listView)
        self.searchFrame.layout().insertWidget(1, self.searchBox)

    def indexToItem(self, index):
        remapped_index = self.proxyModel.mapToSource(index)
        item = self.itemModel.itemFromIndex(remapped_index)
        return item

    def addItems(self, data_model, replace=False):
        if replace:
            self.itemModel.clear()
        if isinstance(data_model, QStandardItemModel):
            for i in range(data_model.rowCount()):
                item = data_model.item(i, 0)
                if item:
                    self.recursivelyAppendItemToModel(item)

    def recursivelyAppendItemToModel(self, item):
        if item.hasChildren():
            self.itemModel.appendRow(item.clone())
            for i in range(item.rowCount()):
                child_index = item.child(i, 0)
                if child_index:
                    self.recursivelyAppendItemToModel(child_index)
        else:
            self.itemModel.appendRow(item.clone())

    @Slot()
    def onSelection(self, selection):
        indices = selection.indexes()
        if indices:
            asset = indices[0].data(polymorphicItem.Object)
            #print(asset)
            
            #self.searchBox.setText(asset.name)
            #self.searchBox.setFocus()
            # model_item_index = [self.itemModel.itemFromIndex(i).data()
            #  for i in self.listView.selectedIndexes()]
            # index = self.listView.selectedIndexes()[0]


    @Slot()
    def onViewFill(self):
        try:
            index = self.listView.selectedIndexes()[0]
        except Exception:
            index = self.proxyModel.index(0, 0)

        self.searchBox.setText(index.data())
        self.searchBox.setFocus()

    @Slot()
    def hide_filter(self):
        if (
            self.searchBox.hasFocus() is False
            and self.listView.hasFocus() is False
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
            index = self.listView.selectedIndexes()[0]
        except Exception:
            index = self.proxyModel.index(0, 0)

        if index.data():
            asset = index.data(polymorphicItem.Object)
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
        self.searchBox.setFocus()
        super(ListViewFocus, self).show()


class ListViewFiltered(ListViewFocus):

    def __init__(self, *args, **kwargs):
        super(ListViewFiltered, self).__init__(*args, **kwargs)
        self.setWindowFlags(Qt.Popup|Qt.WindowStaysOnTopHint|Qt.FramelessWindowHint)


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
            index = self.listView.selectedIndexes()[0]
        except Exception:
            index = self.proxyModel.index(0, 0)

        if index.data():
            asset = index.data(polymorphicItem.Object)
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
        self.setFocusPolicy(Qt.StrongFocus)

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
            self.parent().removeEventFilter(self)
            self.close()

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
