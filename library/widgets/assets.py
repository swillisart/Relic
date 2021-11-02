import copy
import datetime
import os
import time
import json
import subprocess
from functools import partial
from sequencePath import sequencePath as Path

# -- Module --
import library.config as config
from library.io.ingest import ConversionRouter
from library.objectmodels import allCategories, polymorphicItem, subcategory, temp_asset, getCategoryConstructor, Library
from library.ui.asset_delegate import Ui_AssetDelegate
from library.qt_objects import AbstractDoubleClick
from library.ui.compact_delegate import Ui_CompactDelegate
from library.widgets.util import updateWidgetProperty
from library.widgets.metadataView import (categoryWidget, classWidget,
                                          qualityWidget, subcategoryWidget,
                                          typeWidget)
# -- Third-party --
from PySide6.QtCore import (QByteArray, QItemSelectionModel, QMargins,
                            QMimeData, QModelIndex, QObject, QPoint,
                            QPropertyAnimation, QRect, QSize, Signal, Slot, QEvent, QTimer, QUrl)
from PySide6.QtGui import (QAction, QIcon, QColor, QCursor, QDrag, QFont, QMovie, QPainter,
                           QPainterPath, QPen, QPixmap, QRegion,
                           QStandardItemModel, Qt, QImage, QMouseEvent)
from PySide6.QtWidgets import (QAbstractItemView, QLineEdit, QInputDialog,
                               QListView, QMenu, QStyle, QStyledItemDelegate,
                               QStyleOption, QWidget, QApplication, QCheckBox, QMessageBox)

ICON_SIZE = QSize(296, 239)

def generateBlankImage():
    blank = QPixmap(':resources/app/checker.png').scaled(
        288, 192, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

    return blank

NO_IMAGE = generateBlankImage()

unimageable_types = {
    '.r3d': QPixmap(':resources/general/RedLogo.png')
} 

class assetItemModel(QStandardItemModel):

    def __init__(self, parent):
        super(assetItemModel, self).__init__(parent)
        proto_item = polymorphicItem(fields=subcategory(name='', count=0))
        self.setItemPrototype(proto_item)
        try: parent.setModel(self)
        except: pass

    def unpackAssetsDependencies(self, asset, unique_ids):
        """Pre-processes with relative paths for upstream dependencies.

        Parameters
        ----------
        asset : QModelIndex

        Returns
        -------
        relic_asset
        """
        
        # Get the assets upstream dependencies.
        asset.related()
        if asset.upstream:
            # Yield the upstream dependencies.
            for i, item in enumerate(asset.upstream):
                upstream_asset = item.data(polymorphicItem.Object)
                if upstream_asset.id not in unique_ids and upstream_asset.type != 5:
                    unique_ids.append(upstream_asset.id)
                    yield from self.unpackAssetsDependencies(upstream_asset, unique_ids)
            asset.upstream = None
        yield asset

    def mimeData(self, indexes):
        by_category = {}
        unique_ids = []

        for index in indexes:
            primary_asset = copy.copy(index.data(polymorphicItem.Object))
            #if primary_asset.busy():
            #    return
            unique_ids.append(primary_asset.id)
            for asset in self.unpackAssetsDependencies(primary_asset, unique_ids):
                # Insert asset into the payload
                key = allCategories.__slots__[asset.category]
                if by_category.get(key):
                    by_category[key].append(asset.export)
                else:
                    by_category[key] = [asset.export]

        payload = json.dumps(by_category)

        mimeText = 'relic://'
        mimeData = QMimeData()
        mimeData.setText(payload)

        itemData = QByteArray()
        mimeData.setData('application/x-relic', itemData)
        url = QUrl.fromLocalFile(mimeText + str(payload))
        mimeData.setUrls([url])
        drag = QDrag(self)
        drag.setMimeData(mimeData)

        # Capture the rendered item and set to mime data's pixmap
        size = ICON_SIZE
        pixmap = QPixmap(size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        delegate = AssetEditor(self.parent(), index)
        delegate.render(painter, QPoint(), QRegion(), QWidget.DrawChildren)
        painter.end()
        drag.setPixmap(pixmap)
        drag.exec_(Qt.MoveAction)


class assetListView(QListView):

    onSelection = Signal(QModelIndex)
    onLinkLoad = Signal(QModelIndex)
    onLinkRemove = Signal(QModelIndex)
    onDeleted = Signal(QModelIndex)

    def __init__(self, *args, **kwargs):
        super(assetListView, self).__init__(*args, **kwargs)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setAutoFillBackground(True)
        self.setFocusPolicy(Qt.StrongFocus)
        scroller = self.verticalScrollBar()
        scroller.setSingleStep(40)
        self.setResizeMode(QListView.Adjust)
        self.iconMode()
        self.setMouseTracking(True)
        self.setUniformItemSizes(True)
        # Drag & Drop
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDragDropOverwriteMode(False)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenus)

        self.lastIndex = None
        self.editor = None
        self.drag_select = False
        # Actions
        self.actionPreview = QAction('Peak Preview', self)
        self.actionPreview.triggered.connect(self.assetPreview)
        self.actionExploreLocation = QAction('Browse File Location', self)
        self.actionExploreLocation.triggered.connect(self.browseLocalAsset)
        self.actionDelete = QAction('Delete', self)
        self.actionDelete.triggered.connect(self.deleteAsset)
        self.actionUnlink = QAction('Unlink', self)
        self.actionUnlink.triggered.connect(self.unlinkAsset)
        self.actionGeneratePreview =  QAction('Generate Preview', self)
        self.actionGeneratePreview.triggered.connect(self.generatePreview)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.additional_actions = []

    def iconMode(self):
        self.compact_mode = False
        self.setFlow(QListView.LeftToRight)
        self.setViewMode(QListView.IconMode)
        self.setGridSize(ICON_SIZE + QSize(12, 12))
        self.setItemDelegate(AssetStyleDelegate(self))

    def compactMode(self):
        self.compact_mode = True
        self.setFlow(QListView.LeftToRight)
        self.setViewMode(QListView.IconMode)
        self.setGridSize(QSize(267, 58) + QSize(8, 6)) # pad by 1 pixel margins
        self.setItemDelegate(AssetCompactDelegate(self))

    def setModel(self, model):
        super(assetListView, self).setModel(model)
        self.model = model
        self.selmod = self.selectionModel()

    def addAsset(self, item):
        asset_item = polymorphicItem(fields=item)
        asset_item.setCheckable(True)
        self.model.appendRow(asset_item)

    def wheelEvent(self, event):
        if self.editor:
            self.setFocus()

        pos = self.mapFromGlobal(QCursor.pos())
        index = self.indexAt(pos)
        if not index.isValid() and self.editor:
            self.editor.close()
        super(assetListView, self).wheelEvent(event)
        _event = QMouseEvent(QEvent.MouseMove, pos, event.button(),
            event.buttons(), event.modifiers())
        self.mouseMoveEvent(_event)

    def clear(self):
        self.model.clear()

    def keyPressEvent(self, event):
        key = event.key()
        mods = event.modifiers()
        super(assetListView, self).keyPressEvent(event)
        # Populate the clipboard with our copy/paste functionality
        if mods == Qt.ControlModifier and key == Qt.Key_C:
            self.clipboardCopy()
        elif mods == Qt.ControlModifier and key == Qt.Key_V:
            self.clipboardPaste()
        elif mods == Qt.ControlModifier and key == Qt.Key_G:
            self.groupSelectedItems()

    def clipboardCopy(self):
        clipboard = QApplication.clipboard()
        if asset := self.getSelectedAsset():
            id = asset.id
            category = asset.category
            name = asset.path
            clipboard.setText(f'relic://{category}/{id}/{name}')
        else:
            clipboard.clear()

    def clipboardPaste(self):
        clipboard = QApplication.clipboard()
        clip_img = clipboard.image()
        if not int(config.RELIC_PREFS.edit_mode) or not clip_img:
            return
        if asset := self.getSelectedAsset():
            out_path = asset.network_path.suffixed('_icon', ext='.jpg')
            resize_img = clip_img.scaled(288, 192, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            out_img = resize_img.scaled(288, 192, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            out_path.path.parent.mkdir(parents=True, exist_ok=True)
            out_img.save(str(out_path))
            #asset.fetchIcon()

    def groupSelectedItems(self):
        """Creates a new collection asset and links all the selected
        assets to it.
        """
        selection = self.selmod.selectedIndexes()
        count = len(selection)
        if not selection or count <= 1:
            return
        collection_name, ok = QInputDialog.getText(self, 'New Collection',
                "Collection name:", QLineEdit.Normal)#, default_name)
        if not ok:
            return
    
        primary = selection[-1].data(polymorphicItem.Object)
        constructor = getCategoryConstructor(primary.category)
        subcategory = primary.subcategory.data(polymorphicItem.Object)
        collection = constructor(
            name=collection_name,
            dependencies=count,
            path='{}/{}'.format(subcategory.name, collection_name),
            links=(subcategory.relationMap, subcategory.id),
            type=3, # collection
            )
        collection.create()
        collection.fetch(id=collection.id)
        for item in selection:
            asset = item.data(polymorphicItem.Object)
            asset.linkTo(collection)

    def getSelectedAsset(self):
        selection = self.selmod.selectedIndexes()
        if not selection:
            return None
        return selection[-1].data(polymorphicItem.Object)

    def indexToItem(self, index, asset=False):
        proxy_model = index.model()
        remapped_index = proxy_model.mapToSource(index)
        item = self.model.itemFromIndex(remapped_index)
        if asset:
            asset = index.data(polymorphicItem.Object)
        return item

    def mouseMoveEvent(self, event):
        super(assetListView, self).mouseMoveEvent(event)
        index = self.indexAt(event.pos())
        if event.buttons() == Qt.LeftButton:
            self.drag_select = True
        if self.drag_select:
            return
        elif index.isValid() and index != self.lastIndex:
            if self.editor:
                self.editor.close()
                self.setFocus()
            self.lastIndex = index
            if self.compact_mode:
                self.editor = CompactAssetEditor(self, index)
            else:
                asset = index.data(polymorphicItem.Object)
                self.editor = AssetEditor(self, index)
                has_movie = hasattr(asset, 'duration') and asset.duration
                if has_movie or getattr(asset, 'class') == config.MODEL:
                    asset.stream_video_to(self.editor.updateSequence)
    
            self.editor.dragIt.connect(self.enterDrag)
            self.editor.loadLinks.connect(self.onLinkLoad.emit)
            self.editor.snapToSize()
            self.editor.show()
            self.editor.setFocus()
        else:
            self.lastIndex = index

    def mousePressEvent(self, event):
        index = self.indexAt(event.pos())
        pop = index in self.selectedIndexes()
        super(assetListView, self).mousePressEvent(event)
        if pop and event.buttons() == Qt.LeftButton:
            self.selmod.select(index, QItemSelectionModel.Deselect)

    def mouseReleaseEvent(self, event):
        self.drag_select = False
        super(assetListView, self).mouseReleaseEvent(event)

    @Slot()
    def enterDrag(self, parent):
        # Dragging an item not the selection rect
        self.drag_select = False
        sender = self.sender()
        #self.selmod.select(sender.index, QItemSelectionModel.Select)
        self.model.mimeData([sender.index])

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            return super(assetListView, self).dragEnterEvent(event)

    def dragMoveEvent(self, event):
        super(assetListView, self).dragMoveEvent(event)
        index = self.indexAt(event.pos())
        if event.mimeData().hasUrls() and index.isValid():
            self.setFocus()
            self.update()
            event.acceptProposedAction()

    def dropEvent(self, event):
        if not int(config.RELIC_PREFS.edit_mode):
            return

        index = self.indexAt(event.pos())
        primary_asset = index.data(polymorphicItem.Object)

        event.accept()
        dst_name = primary_asset.name
        msg = f'Link selected assets to <b>{dst_name}</b>?\n'
        message_box = QMessageBox(QMessageBox.Information, 'Are you sure?', msg,
                QMessageBox.Yes|QMessageBox.No, self)
        link_ico = QPixmap(':/resources/general/folder_link.svg')
        message_box.setIconPixmap(link_ico.scaled(64, 64, mode=Qt.SmoothTransformation))

        if QMessageBox.No == message_box.exec_():
            return

        mime = event.mimeData()
        payload = json.loads(mime.text())
        for key, values in payload.items():
            constructor = getCategoryConstructor(str(key))
            for fields in values:
                asset = constructor(**fields)
                asset.linkTo(primary_asset)
                primary_asset.dependencies += 1
        primary_asset.update(fields=['dependencies'])

    @Slot()
    def showContextMenus(self, val):
        """Populates a context menu based on the current application index.
        """
        sender = self.sender()
        context_menu = QMenu(self)
        context_menu.addAction(self.actionExploreLocation)
        context_menu.addAction(self.actionPreview)
    
        if int(config.RELIC_PREFS.edit_mode):
            context_menu.addAction(self.actionDelete)
            context_menu.addAction(self.actionGeneratePreview)
            context_menu.addAction(self.actionUnlink)

        for action in self.additional_actions:
            context_menu.addAction(action)

        context_menu.exec(QCursor.pos())

    @Slot()
    def unlinkAsset(self, action):
        for index in self.selectedIndexes():
            self.onLinkRemove.emit(index)

    @Slot()
    def deleteAsset(self, action):
        """Asset deletion. Iterates selected items to delete,
        and updates the items parent subcategory counts.
        """
        update_list = []
        for index in self.selectedIndexes():
            asset = index.data(polymorphicItem.Object)
            subcategory = asset.subcategory
            if isinstance(subcategory, list):
                subcategory = subcategory[0]
            elif subcategory:
                subcategory.count = (subcategory.count - 1)
                update_list.append(subcategory.data())
                category = Library.categories.get(asset.category)
                item = category.tree.findInTree(subcategory.id, variable='id')
                category.tree.updateSubcategoryCounts(item, offset=-1)

            if not isinstance(asset, temp_asset):
                asset.remove()
            self.setRowHidden(index.row(), True)
            self.onDeleted.emit(index)

        # Update the subcategories with new counts
        [x.update(fields=['count']) for x in update_list]

    def generatePreview(self, action):
        for index in self.selectedIndexes():
            asset = index.data(polymorphicItem.Object)
            path = asset.network_path
            if asset.path == '' or not path.parents(0).exists:
                continue
            path.checkSequence()
            if path.sequence_path:
                ConversionRouter.processSEQ(path, path)
            elif path.ext in config.LDR_EXT:
                ConversionRouter.processLDR(path, path)
            elif path.ext in config.HDR_EXT:
                ConversionRouter.processHDR(path, path)
            elif path.ext in config.MOVIE_EXT:
                ConversionRouter.processMOV(path, path)

    def browseLocalAsset(self, action):
        for index in self.selectedIndexes():
            asset = index.data(polymorphicItem.Object)
            winpath = asset.network_path.parent.replace('/', '\\')
            cmd = 'explorer /select, "{}"'.format(winpath)
            subprocess.Popen(cmd)
    
    def assetPreview(self, action):
        index = self.selectedIndexes()[-1]
        asset = index.data(polymorphicItem.Object)
        config.peakPreview(asset.network_path)


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
        
        self.iconButton.setIcon(typeWidget.ICONS[asset.type-1])
        self.categoryIcon.setIcon(categoryWidget.ICONS[asset.category])
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
        if preview_img:
            preview_img = preview_img.scaledToWidth(self.label.width(), Qt.SmoothTransformation)
        else:
            suffix = asset.network_path.ext.lower()
            preview_img = unimageable_types.get(suffix, NO_IMAGE)

        img_rect = self.label.rect()
        b = self.label.mapTo(self, img_rect.topLeft())
        painter.translate(b)
        if img_rect.width() > 128:
            img_rect = img_rect + QMargins(0,1,0,1)
        painter.drawPixmap(img_rect, preview_img)
        painter.restore()

        # Paint Category Color Id
        painter.save()
        painter.translate(rect.topLeft())
        line_rect = self.styledLine.rect() - QMargins(0,1,0,-1)
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
        self.checkBox.hide()
        self.styledLine.setStyleSheet('border: none')


class CompactDelegateWidget(AssetItemPaint, Ui_CompactDelegate, QWidget):
    def __init__(self, *args, **kwargs):
        super(CompactDelegateWidget, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.checkBox = QCheckBox(self)
        self.checkBox.hide()
        self.styledLine.setStyleSheet('border: none')


class AssetStyleDelegate(QStyledItemDelegate):
    def __init__(self, *args, **kwargs):
        super(AssetStyleDelegate, self).__init__(*args, **kwargs)
        self.asset_widget = AssetDelegateWidget(self.parent())
        self.asset_widget.hide()

    def paint(self, painter, option, index):
        rect = option.rect
        asset = index.data(polymorphicItem.Object)
        widget = self.asset_widget

        #painter.setRenderHints(QPainter.SmoothPixmapTransform)
        #painter.setRenderHint(QPainter.Antialiasing, True)
        # Paint Item State's
        widget.checkBox.setChecked(index.data(Qt.CheckStateRole))
        select_state = bool(option.state & QStyle.State_Selected)
        updateWidgetProperty(widget.HeaderFrame, "selected", select_state)
        updateWidgetProperty(widget.frame, "selected", select_state)
    
        widget.paint(painter, rect, asset)
        self.paintOverlays(painter, asset, rect)

    def paintOverlays(self, painter, asset, rect):
        # Paint HUD Overlays
        overlays = []
        if hasattr(asset, 'resolution'):
            overlays.append(asset.resolution)
        if hasattr(asset, 'duration'):
            if timecode := asset.duration:
                overlays.append(datetime.timedelta(seconds=timecode))

        if overlays:
            over_rect = rect - QMargins(4, rect.height() - 24, 4, 6)
            painter.fillRect(over_rect, QColor(0, 0, 0, 100))
            areas = [Qt.AlignLeft, Qt.AlignRight]
            for index, overlay in enumerate(overlays):
                painter.drawText(   
                    over_rect - QMargins(5, 0, 10, 0),
                    areas[index],
                    str(overlay)
                )

    def sizeHint(self, option, index):
        return ICON_SIZE


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

    def createEditor(self, parent, option, index):
        self.editor = CompactAssetEditor(self.parent(), index)
        return self.editor 

    def setEditorData(self, editor, index):
        r = self.parent().visualRect(index)
        point = r.topLeft()
        img_s1 = QRect(point, QSize(r.width(), r.height()))
        self.editor.dragIt.connect(self.parent().enterDrag)
        self.editor.loadLinks.connect(self.parent().onLinkLoad.emit)
        self.editor.setGeometry(img_s1)

    def setModelData(self, widget, model, index):
        pass


class BaseAssetEditor(AbstractDoubleClick):

    dragIt = Signal(object)
    loadLinks = Signal(QModelIndex)

    def __init__(self, parent, index):
        super(BaseAssetEditor, self).__init__(parent)
        self.index = index
        self.setMouseTracking(True)
        self._click_startpos = None

        self.asset = self.index.data(polymorphicItem.Object)
        tip = '<h4>Name</h4>{}'.format(self.asset.name)
        self.nameLabel.setStatusTip(self.asset.name)
        self.nameLabel.setToolTip(tip)

        if link_count := self.asset.dependencies:
            self.linksButton.setText(str(link_count))
        else:
            self.linksButton.hide()
        self.nameLabel.setText(self.asset.name)
        self.iconButton.setIcon(typeWidget.ICONS[self.asset.type-1])
        self.categoryIcon.setIcon(categoryWidget.ICONS[self.asset.category])
        color = self.colors[self.asset.category].getRgb()
        self.styledLine.setStyleSheet('background-color: rgb{};border: none'.format(color[:3]))
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
        self.linksButton.clicked.connect(self.onLoadLinks)
        self.aDoubleClicked.connect(self.onDoubleClick)

    @Slot()
    def onLoadLinks(self):
        indices = self.view.selectedIndexes()
        if self.index not in indices:
            self.view.selmod.select(self.index, QItemSelectionModel.ClearAndSelect)
        else:
            self.view.selmod.select(self.index, QItemSelectionModel.Select)
        self.loadLinks.emit(self.index)

    @Slot()
    def onDoubleClick(self):
        asset = self.index.data(polymorphicItem.Object)
        filepath = asset.network_path
        row = self.index.row()
        ext = filepath.ext.lower()
        if ext == '.exe':
            # Launch software executable
            with open(str(filepath), 'r') as fp:
                subprocess.Popen('"{}"'.format(fp.read()))
            return
        ingest_filename = f'unsorted{row}{ext}'
        preview_path = config.INGEST_PATH / ingest_filename

        if not config.peakPreview(preview_path):
            config.peakPreview(filepath)
        

    def snapToSize(self):
        r = self.parent().visualRect(self.index)
        edit_rect = QRect(r.topLeft(), QSize(r.width(), r.height()))
        self.setGeometry(edit_rect)

    def mousePressEvent(self, event):
        self.snapToSize()
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
            timediff = -(self.last_clicked - time.time())
            if float(timediff) > float(0.25):
                _event = QMouseEvent(QEvent.MouseButtonPress, pos, event.button(),
                    event.buttons(), event.modifiers())
                self.parent().mousePressEvent(_event)
        super(BaseAssetEditor, self).mousePressEvent(event)

    def leaveEvent(self, event):
        super(BaseAssetEditor, self).leaveEvent(event)
        self.view.setFocus()
        self.close()

    def wheelEvent(self, event):
        self.parent().wheelEvent(event)
        self.snapToSize()
        self.deferred_snap = QTimer.singleShot(100, self.snapToSize)


class AssetEditor(BaseAssetEditor, AssetDelegateWidget):

    def __init__(self, parent, index):
        super(AssetEditor, self).__init__(parent, index)
        self.sequence = []
        self.xpos = 0
        self.image = None
        if self.asset.icon:
            self.label.setPixmap(self.asset.icon)
        else:
            suffix = self.asset.network_path.ext.lower()
            icon = unimageable_types.get(suffix, NO_IMAGE)
            self.label.setPixmap(icon)

        if isinstance(self.view, assetListView):
            self.selected = bool(index in self.view.selmod.selectedIndexes())
        else:
            self.selected = True

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
    def updateSequence(self, frames):
        self.sequence = frames

    def mousePressEvent(self, event):
        super(AssetEditor, self).mousePressEvent(event)
        self.selected = not self.selected

    def mouseMoveEvent(self, event):
        self.snapToSize()
        if event.buttons() in [Qt.LeftButton, Qt.MiddleButton]:
            x = abs(self._click_startpos.x() - event.pos().x())
            y = abs(self._click_startpos.y() - event.pos().y())
            if (x + y) > 5:
                self.dragIt.emit(self.parent())
                self._click_startpos = event.pos()
        if self.sequence:
            self.xpos = event.pos().x()
            duration = len(self.sequence)
            w = self.width() or 1
            pos_idx = int(self.xpos * duration / w) + 1
            if 0 <= pos_idx < duration:
                self.label.setPixmap(self.sequence[pos_idx])
            else:
                self.label.setPixmap(self.sequence[0])
            self.progressBar.setMaximum(duration)
            self.progressBar.setValue(pos_idx)

        super(AssetEditor, self).mouseMoveEvent(event)


class CompactAssetEditor(BaseAssetEditor, CompactDelegateWidget):

    def __init__(self, parent, index):
        super(CompactAssetEditor, self).__init__(parent, index)
        if self.asset.icon:
            icon = self.asset.icon
        else:
            suffix = self.asset.network_path.ext.lower()
            icon = unimageable_types.get(suffix, NO_IMAGE)

        self.label.setPixmap(icon.scaledToWidth(72, Qt.SmoothTransformation))
        updateWidgetProperty(self.HeaderFrame, "selected", True)
        updateWidgetProperty(self.frame, "selected", True)


    def mouseMoveEvent(self, event):
        if event.buttons() in [Qt.LeftButton, Qt.MiddleButton]:
            x = abs(self._click_startpos.x() - event.pos().x())
            y = abs(self._click_startpos.y() - event.pos().y())
            if (x + y) > 5:
                self.dragIt.emit(self.parent())
                self._click_startpos = event.pos()
                self.close()

        super(CompactAssetEditor, self).mouseMoveEvent(event)
