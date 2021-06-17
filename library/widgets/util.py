import re

from library.ui.list_view_filtered import Ui_ListViewFiltered
from PySide6.QtCore import (QEvent, QFile, QItemSelectionModel, QMargins,
                            QObject, QPoint, QRect, QRegularExpression, QSize,
                            QSortFilterProxyModel, Qt, QTextStream, Signal,
                            Slot)
from PySide6.QtGui import (QAction, QColor, QCursor, QFont, QFontMetrics,
                           QIcon, QPainter, QPixmap,
                           QRegularExpressionValidator, QStandardItemModel, Qt)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QBoxLayout,
                               QDockWidget, QFrame, QLabel, QLineEdit,
                               QListView, QMenu, QScrollArea,
                               QStyledItemDelegate, QTreeView, QWidget)

def updateWidgetProperty(widget, attribute, value):
    widget.setProperty(attribute, value)
    widget.setStyle(widget.style())

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


class compactLayout(QBoxLayout):

    horizontal = QBoxLayout.LeftToRight
    vertical = QBoxLayout.TopToBottom

    def __init__(self, *args, **kwargs):
        super(compactLayout, self).__init__(*args, **kwargs)
        self.setSpacing(0)
        self.setContentsMargins(0, 0, 0, 0)


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


class ListViewFiltered(Ui_ListViewFiltered, QMenu):

    newItem = Signal(str)
    renameItem = Signal(str)
    linkItem = Signal(list)

    def __init__(self, *args, **kwargs):
        super(ListViewFiltered, self).__init__(*args, **kwargs)
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
        self.searchBox.onReturn.connect(self.onViewReturn)

        qregex = QRegularExpression(self.filter_regex)
        validator = QRegularExpressionValidator(qregex)
        self.searchBox.setValidator(validator)

        # Layouts 
        self.layout().insertWidget(1, self.listView)
        self.searchFrame.layout().insertWidget(1, self.searchBox)


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
    def onSelection(self, index):
        print(item.indexes()[0].data())
        print(index.data())
        self.searchBox.setText(index.data())
        self.searchBox.setFocus()
        # model_item_index = [self.itemModel.itemFromIndex(i).data()
        #  for i in self.listView.selectedIndexes()]
        # index = self.listView.selectedIndexes()[0]
        # cmds.createNode(index.data())

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

    @Slot()
    def onViewReturn(self):
        try:
            index = self.listView.selectedIndexes()[0]
        except Exception:
            index = self.proxyModel.index(0, 0)

        if index.data():
            self.linkItem.emit(index.data(polymorphicItem.Object))
        else:
            if self.rename_mode:
                self.renameItem.emit(str(self.searchBox.text()))
            else:
                self.newItem.emit(str(self.searchBox.text()))

        self.searchBox.setFocus()
        self.hide()

    def sizeHint(self):
        return QSize(275, 250)

    def show(self):
        pos = QCursor.pos()
        x = pos.x() - (self.sizeHint().width() / 2)
        y = pos.y()
        self.move(x + 75, y - 5)
        self.searchBox.setFocus()
        super(ListViewFiltered, self).show()


class FocusListView(QListView):

    onReturn = Signal(bool)
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

        super(FocusListView, self).keyPressEvent(event)


class contextPainter(QPainter):
    def __init__(self, *args, **kwargs):
        super(contextPainter, self).__init__(*args, **kwargs)

    def __enter__(self):
        self.save()
        return self

    def __exit__(self, *exc):
        self.restore()
        return False
