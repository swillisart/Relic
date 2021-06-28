import copy
import datetime
import os
import time
import json
import subprocess
from functools import partial
from sequencePath import sequencePath as Path

# -- Module --
from library.config import relic_preferences, kohaiPreview
from library.objectmodels import allCategories, polymorphicItem, subcategory, temp_asset
from library.ui.asset_delegate import Ui_AssetDelegate
from library.ui.compact_delegate import Ui_CompactDelegate
from library.widgets.util import updateWidgetProperty
from library.widgets.metadataView import (categoryWidget, classWidget,
                                          qualityWidget, subcategoryWidget,
                                          typeWidget)
# -- Third-party --
from PySide6.QtCore import (QByteArray, QItemSelectionModel, QMargins,
                            QMimeData, QModelIndex, QObject, QPoint,
                            QPropertyAnimation, QRect, QSize, Signal, Slot, QEvent, QTimer)
from PySide6.QtGui import (QAction, QIcon, QColor, QCursor, QDrag, QFont, QMovie, QPainter,
                           QPainterPath, QPen, QPixmap, QRegion,
                           QStandardItemModel, Qt, QImage, QMouseEvent)
from PySide6.QtWidgets import (QAbstractItemView, QGraphicsDropShadowEffect,
                               QListView, QMenu, QStyle, QStyledItemDelegate,
                               QStyleOption, QWidget, QApplication, QCheckBox)

INGEST_PATH = Path(os.getenv('userprofile')) / '.relic/ingest'

class assetItemModel(QStandardItemModel):

    def __init__(self, parent):
        super(assetItemModel, self).__init__(parent)
        proto_item = polymorphicItem(fields=subcategory(name='', count=0))
        self.setItemPrototype(proto_item)
        try: parent.setModel(self)
        except: pass

    def mimeData(self, indexes):
        by_category = {}

        for index in indexes:
            asset = copy.copy(index.data(polymorphicItem.Object))
            if asset.upstream:
                asset.upstream = tuple((x.id, str(x.path)) for x in asset.upstream)
            key = allCategories.__slots__[asset.category]
            existing = by_category.get(key)
            if existing:
                by_category[key].append(asset.export)
            else:
                by_category[key] = [asset.export]


        payload = json.dumps(by_category)
        plugin_path = relic_preferences.relic_plugins_path
        mimeText = "{}/asset_drop.pyw".format(
            plugin_path, 
        )
        mimeData = QMimeData()
        mimeData.setText(payload)

        itemData = QByteArray()
        mimeData.setData('application/x-relic', itemData)
        mimeData.setUrls([mimeText])
        drag = QDrag(self)
        drag.setMimeData(mimeData)

        # Capture the rendered item and set to mime data's pixmap
        w, h = (296-12, 233-12)
        pixmap = QPixmap(w, h)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        delegate = self.parent().itemDelegate(index)
        options = QStyleOption()
        options.rect = QRect(0, 0, w, h)
        options.state |= QStyle.State_Selected
        delegate.paint(painter, options, index)
        painter.end()
        drag.setPixmap(pixmap)
        drag.exec_(Qt.MoveAction)


class assetListView(QListView):

    onSelection = Signal(QModelIndex)
    ondoubleClick = Signal(QModelIndex)
    onLinkLoad = Signal(QModelIndex)

    def __init__(self, *args, **kwargs):
        super(assetListView, self).__init__(*args, **kwargs)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setAutoFillBackground(True)
        self.setFocusPolicy(Qt.StrongFocus)
        scroller = self.verticalScrollBar()
        scroller.setSingleStep(50)
        self.setResizeMode(QListView.Adjust)
        self.iconMode()
        #self.setMouseTracking(True)
        self.setUniformItemSizes(True)
        # Drag & Drop
        self.setDropIndicatorShown(True)
        self.setDragDropOverwriteMode(False)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenus)

        self.lastIndex = None
        self.editor = None

        # Actions
        self.actionExploreLocation = QAction('Browse File Location', self)
        self.actionExploreLocation.triggered.connect(self.browseLocalAsset)
        self.actionDelete = QAction('Delete', self)
        self.actionDelete.triggered.connect(self.deleteAsset)
        """
        self.actionScreenshotIcon = context_menu.addAction('Upload Thumbnail')
        self.actionScreenshotIcon.triggered.connect(self.uploadThumbnail)
        self.actionRegeneratePreview = context_menu.addAction('Regenerate Preview')
        self.actionRegeneratePreview.triggered.connect(self.regenPreview)
        """


    def iconMode(self):
        self.setFlow(QListView.LeftToRight)
        self.setViewMode(QListView.IconMode)
        self.setGridSize(QSize(296, 233))
        self.setItemDelegate(AssetStyleDelegate(self))

    def compactMode(self):
        self.setFlow(QListView.TopToBottom)
        self.setViewMode(QListView.ListMode)
        self.setGridSize(QSize(267+1, 58+1))
        self.setItemDelegate(AssetCompactDelegate(self))

    def setModel(self, model):
        super(assetListView, self).setModel(model)
        self.model = model
        self.selmod = self.selectionModel()

    def addItem(self, item):
        asset_item = polymorphicItem(fields=item)
        asset_item.setCheckable(True)
        self.model.appendRow(asset_item)

    def wheelEvent(self, event):
        if self.editor:
            self.editor.close()
            self.setFocus()
        super(assetListView, self).wheelEvent(event)

    def clear(self):
        self.model.clear()

    def mouseMoveEvent(self, event):
        super(assetListView, self).mouseMoveEvent(event)

        index = self.indexAt(event.pos())
        if index.isValid() and index != self.lastIndex:
            self.lastIndex = index
            if self.editor:
                self.editor.close()
                self.setFocus()
            if self.viewMode() == QListView.IconMode:
                self.editor = AssetEditor(self, index)
                r = self.visualRect(index)
                point = r.topLeft()#self.mapToGlobal(r.topLeft())
                img_s1 = QRect(point, QSize(r.width(), r.height()))
                asset = index.data(polymorphicItem.Object)
                if hasattr(asset, 'duration'):
                    asset.stream_video_to(self.editor.updateSequence)
                self.editor.dragIt.connect(self.enterDrag)
                self.editor.loadLinks.connect(self.onLinkLoad.emit)
                self.editor.setGeometry(img_s1)
                self.editor.show()
                self.editor.setFocus()
        else:
            self.lastIndex = index

    def mouseDoubleClickEvent(self, event):
        super(assetListView, self).mousePressEvent(event)
        selection = [x for x in self.selectedIndexes()]

        for index in selection:
            preview = INGEST_PATH / 'unsorted{}_proxy.jpg'.format(index.row())
            #asset = index.data(polymorphicItem.Object)
            kohaiPreview(preview)
            break

    def mousePressEvent(self, event):
        index = self.indexAt(event.pos())
        pop = index in self.selectedIndexes()
        super(assetListView, self).mousePressEvent(event)
        if pop and event.buttons() == Qt.LeftButton:
            self.selmod.select(index, QItemSelectionModel.Deselect)

    @Slot()
    def enterDrag(self, parent):
        sender = self.sender()
        self.selmod.select(sender.index, QItemSelectionModel.Select)
        self.model.mimeData([sender.index])
        self.editor.close()

    @Slot()
    def showContextMenus(self, val):
        """Populates a context menu based on the current application index.
        """
        sender = self.sender()
        context_menu = QMenu(self)
        self.openlocation = context_menu.addAction(self.actionExploreLocation)

        if bool(int(relic_preferences.edit_mode)):
            self.delete_item = context_menu.addAction(self.actionDelete)

        context_menu.exec(QCursor.pos())

    def deleteAsset(self, action):
        """Item deletion into the trash.
        """
        update_list = []
        for index in self.selectedIndexes():
            asset = index.data(polymorphicItem.Object)
            subcategory = asset.subcategory
            if isinstance(subcategory, list):
                subcategory = subcategory[0]
    
            subcategory.count = (subcategory.count - 1)
            update_list.append(subcategory.data())

            if not isinstance(asset, temp_asset):
                asset.remove()
                #TODO: remove from disk
        # Update the subcategories with new counts
        [x.update(fields=['count']) for x in update_list]

    def browseLocalAsset(self, action):
        for index in self.selectedIndexes():
            asset = index.data(polymorphicItem.Object)
            winpath = asset.local_path.parent.replace('/', '\\')
            cmd = 'explorer /select, "{}"'.format(winpath)
            subprocess.Popen(cmd)

    def leaveEvent(self, event):
        self.lastIndex = None
        if self.editor:
            self.editor.close()
            self.setFocus()
        super(assetListView, self).leaveEvent(event)

class AssetItemPaint:

    def __init__(self, *args, **kwargs):
        super(AssetItemPaint, self).__init__(*args, **kwargs)
        self.colors = [
            QColor(168, 58, 58),
            QColor(156, 156, 156),
            QColor(198, 178, 148),
            QColor(188, 178, 98),
            QColor(168, 58, 198),
            QColor(168, 168, 198),
            QColor(66, 118, 150),
            QColor(168, 168, 198),
        ]

    def paint(self, painter, rect, asset):
        painter.save()
        painter.translate(rect.topLeft())
        link_count = asset.dependencies
        if link_count:
            self.linksButton.show()
            self.linksButton.setText(str(link_count))
        else:
            self.linksButton.hide()
        
        self.iconButton.setIcon(typeWidget.icons[asset.type-1])
        self.nameLabel.setText(asset.name)
        self.render(painter, QPoint(), QRegion(), QWidget.DrawChildren)
        # Draw interactive widgets
        icon = asset.icon
        if isinstance(icon, QPixmap):
            preview_img = icon
        elif isinstance(icon, QMovie):
            preview_img = icon.currentImage()
        else:
            preview_img = self.label.pixmap()

        img_rect = self.label.rect()
        b = self.label.mapTo(self, img_rect.topLeft())
        painter.translate(b)
        painter.drawPixmap(img_rect, preview_img)
        painter.restore()

        # Paint Category Color Id
        painter.save()
        painter.translate(rect.topLeft())
        line_rect = self.styledLine.rect()
        b = self.styledLine.mapTo(self, img_rect.topLeft())
        painter.translate(b)

        painter.fillRect(line_rect, self.colors[asset.category])
        painter.restore()



class AssetDelegateWidget(AssetItemPaint, Ui_AssetDelegate, QWidget):
    def __init__(self, *args, **kwargs):
        super(AssetDelegateWidget, self).__init__(*args, **kwargs)
        self.setupUi(self)
        #self.progressBar.setProperty("complete", True)
        #self.progressBar.setStyle(self.progressBar.style())


class CompactDelegateWidget(AssetItemPaint, Ui_CompactDelegate, QWidget):
    def __init__(self, *args, **kwargs):
        super(CompactDelegateWidget, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.checkBox = QCheckBox(self)
        self.checkBox.hide()


class AssetStyleDelegate(QStyledItemDelegate):
    def __init__(self, *args, **kwargs):
        super(AssetStyleDelegate, self).__init__(*args, **kwargs)
        self.asset_widget = AssetDelegateWidget(self.parent())
        self.asset_widget.hide()

    def paint(self, painter, option, index):
        rect = option.rect
        asset = index.data(polymorphicItem.Object)
        widget = self.asset_widget

        painter.setRenderHints(QPainter.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.Antialiasing, True)
        # Paint Item State's
        widget.checkBox.setChecked(index.data(Qt.CheckStateRole))
        select_state = bool(option.state & QStyle.State_Selected)
        updateWidgetProperty(widget.HeaderFrame, "selected", select_state)
        updateWidgetProperty(widget.frame, "selected", select_state)
    
        widget.paint(painter, rect, asset)
        self.paintOverlays(painter, asset, rect)

    def paintOverlays(self, painter, asset, rect):
        # Paint HUD Overlays
        overlay = None
        if hasattr(asset, 'duration'):
            if timecode := asset.duration:
                overlay = datetime.timedelta(seconds=timecode)
 
        if hasattr(asset, 'resolution'):
            overlay = str(asset.resolution)
        if overlay:
            over_rect = rect - QMargins(5, rect.height() - 25,5,8)
            painter.fillRect(over_rect, QColor(0, 0, 0, 100))
            painter.drawText(   
                over_rect - QMargins(5, 0, 10, 0),
                Qt.AlignLeft,
                overlay
            )

    def sizeHint(self, option, index):
        #width = relic_preferences.asset_preview_size
        return QSize(296-12, 233-12)


class AssetCompactDelegate(AssetStyleDelegate):
    def __init__(self, *args, **kwargs):
        super(AssetCompactDelegate, self).__init__(*args, **kwargs)
        self.asset_widget = CompactDelegateWidget(self.parent())
        self.asset_widget.hide()

    def paintOverlays(self, painter, asset, rect):
        # Don't Paint HUD Overlays
        return

    def sizeHint(self, option, index):
        return QSize(267, 58)


class AssetEditor(AssetDelegateWidget):

    dragIt = Signal(object)
    loadLinks = Signal(QModelIndex)
    #opened = Signal()

    def __init__(self, parent, index):
        super(AssetEditor, self).__init__(parent)
        self.setMouseTracking(True)
        #self.setAutoFillBackground(True)
        self.sequence = []
        self.index = index
        self._click_startpos = None
        self.xpos = 0
        self.image = None
        self.asset = self.index.data(polymorphicItem.Object)
        if link_count := self.asset.dependencies:
            self.linksButton.setText(str(link_count))
        else:
            self.linksButton.hide()
        self.nameLabel.setText(self.asset.name)
        self.iconButton.setIcon(typeWidget.icons[self.asset.type-1])
        color = self.colors[self.asset.category].getRgb()
        self.styledLine.setStyleSheet('background-color: rgb{};border: none'.format(color[:3]))
        self.label.setPixmap(self.asset.icon)
        self.view = self.parent()
        try:
            item = index.model().itemFromIndex(index)
        except:
            model = index.model()
            source_model = model.sourceModel()
            item = source_model.itemFromIndex(model.mapToSource(index))

        state = item.checkState()
        self.checkBox.setCheckState(state)
        check = partial(item.setCheckState, Qt.Checked)
        unchk = partial(item.setCheckState, Qt.Unchecked)
        setit = lambda x : check() if x == 2 else unchk()
        self.checkBox.stateChanged.connect(setit)
        self.selected = bool(index in self.view.selmod.selectedIndexes())
        self.linksButton.clicked.connect(partial(self.loadLinks.emit, self.index))

    @property
    def selected(self):
        return self._selected

    @selected.setter
    def selected(self, state):
        if not state:
            self.view.selmod.select(self.index, QItemSelectionModel.Deselect)
        updateWidgetProperty(self.HeaderFrame, "selected", state)
        updateWidgetProperty(self.frame, "selected", state)
        self._selected = state

    @Slot()
    def updateSequence(self, img):
        self.sequence.append(img)

    def mousePressEvent(self, event):
        self._click_startpos = event.pos()
        # close & open context menu
        pos = self.mapTo(self.parent(), event.pos())
        if Qt.RightButton == event.buttons():
            self.view.selmod.select(self.index, QItemSelectionModel.Select)
            self.view.showContextMenus(None)
            self.view.update()
            self.close()
            return
        elif Qt.LeftButton == event.buttons():
            _event = QMouseEvent(QEvent.MouseButtonPress, pos, event.button(),
                event.buttons(), event.modifiers())
            self.parent().mousePressEvent(_event)

        self.selected = not self.selected
        super(AssetEditor, self).mousePressEvent(event)


    def mouseMoveEvent(self, event):
        if event.buttons() in [Qt.LeftButton, Qt.MiddleButton]:
            x = abs(self._click_startpos.x() - event.pos().x())
            y = abs(self._click_startpos.y() - event.pos().y())
            if (x + y) > 10:
                self.dragIt.emit(self.parent())
                self._click_startpos = event.pos()
        if self.sequence:
            self.xpos = event.pos().x()
            duration = len(self.sequence)
            pos_idx = int(self.xpos * duration / self.width()) + 1
            if 0 <= pos_idx < duration:
                self.label.setPixmap(self.sequence[pos_idx])
                self.update()
            else:
                self.label.setPixmap(self.sequence[0])
            self.progressBar.setMaximum(duration)
            self.progressBar.setValue(pos_idx)

        super(AssetEditor, self).mouseMoveEvent(event)

    def wheelEvent(self, event):
        self.close()

    def leaveEvent(self, event):
        super(AssetEditor, self).leaveEvent(event)
        self.view.setFocus()
        self.close()