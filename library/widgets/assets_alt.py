import copy
import datetime
import os
import time
import json
import subprocess
from functools import partial
from sequence_path import Path
from collections import defaultdict
from relic.qt.util import polymorphicItem
from relic.qt.delegates import BaseView, BaseItemDelegate, ColorIndicator, BaseItemModel, ItemDispalyModes

# -- Module --
import library.config as config
from relic.local import Category, TempAsset, FileType, AssetType, EXTENSION_MAP
from relic.scheme import Classification as Class
from library.io import ingest
from library.io.util import LocalThumbnail

from library.objectmodels import subcategory, getCategoryConstructor, Library

# -- Third-party --
from PySide6.QtCore import (QByteArray, QItemSelectionModel, QMargins, QThreadPool,
                            QMimeData, QModelIndex, QObject, QPoint,
                            QPropertyAnimation, QRect, QSize, Signal, Slot, QEvent, QTimer, QUrl)
from PySide6.QtGui import (QAction, QIcon, QColor, QCursor, QDrag, QFont, QMovie, QPainter,
                           QPainterPath, QPen, QPixmap, QRegion,
                           QStandardItemModel, Qt, QImage, QMouseEvent, QStandardItem)
from PySide6.QtWidgets import (QAbstractItemView, QLineEdit, QInputDialog, QLabel,
                               QListView, QMenu, QStyle, QStyledItemDelegate, QWidgetAction,
                               QStyleOption, QStyleOptionViewItem, QWidget, QApplication, QCheckBox, QMessageBox)

# -- Globals --
THREAD_POOL = QThreadPool.globalInstance()
PREVIEWABLE = [Class.MODEL, Class.TOOL, Class.ANIMATION, Class.MOVIE, Class.PLATE]


class AssetItemModel(BaseItemModel):

    def mimeData(self, indices):
        # Removes unserializable data
        paths = []
        assets = {}

        by_category = defaultdict(list)
        item_getter = self.itemFromIndex
        for index in indices:
            asset = index.data(Qt.UserRole)
            if asset:
                assets[index] = asset
                export_data = asset.export
                if isinstance(asset, TempAsset):
                    by_category['uncategorized'].append(export_data)
                else:
                    for upstream in asset.recurseDependencies(asset):
                        if isinstance(upstream, QStandardItem):
                            upstream = upstream.data(Qt.UserRole)
                        # Insert upstream assets into the payload
                        key = Category(upstream.category).name.lower()
                        by_category[key].append(upstream.export)

                item = item_getter(index)
                export_data['count'] = asset.count
                item.setData(export_data, role=Qt.UserRole)
                paths.append(QUrl.fromLocalFile(str(asset.path)))

        #self.endResetModel() <- Why was this here?
        mime_data = super(QStandardItemModel, self).mimeData(indices)
        payload = json.dumps(by_category)
        protocol = 'relic://'
        mime_data.setText(payload)

        itemData = QByteArray()
        mime_data.setData('application/x-relic', itemData)
        url = QUrl.fromLocalFile(protocol + str(payload))
        mime_data.setUrls([url])

        # Tacks back in un-serializable data.
        for index, asset in assets.items():
            item = item_getter(index)
            item.setData(asset, role=Qt.UserRole)

        return mime_data


class AssetListView(BaseView):

    onSelection = Signal(QModelIndex)
    onLinkLoad = Signal(QModelIndex)
    onLinkRemove = Signal(QModelIndex)
    onDeleted = Signal(QModelIndex)
    assetsDeleted = Signal(defaultdict)
    onExecuted = Signal(QModelIndex)

    def __init__(self, *args, **kwargs):
        super(AssetListView, self).__init__(*args, **kwargs)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        scroller = self.verticalScrollBar()
        scroller.setSingleStep(40)
        self.setResizeMode(QListView.Adjust)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # Drag & Drop
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDragDropOverwriteMode(False)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.LinkAction)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenus)
        self.setSpacing(4)

        self.lastIndex = None
        self.drag_select = False
        # Actions
        self.main_actions = [
            QAction(QIcon(':app/folder.svg'), 'Open File Location', self, triggered=self.browseLocalAsset),
        ]
        self.edit_actions = [
            QAction('Generate Preview', self, triggered=self.generatePreview),
            QAction('Remove', self, triggered=self.deleteAsset),
        ]
        self.unlink_action = QAction('Unlink', self, triggered=self.unlinkAsset)

        self.advanced_label = QLabel(' Advanced')
        self.advanced_label.setStyleSheet('background-color: rgb(68,68,68); color: rgb(150, 150, 150);')
        self.additional_actions = []
        self.drop_index = None

    def dragMoveEvent(self, event):
        super(AssetListView, self).dragMoveEvent(event)
        index = self.indexAt(event.pos())
        if not index.isValid() or index in self.selectedIndexes():
            event.ignore()
            self.drop_index = None
        elif event.mimeData().hasUrls():
            self.setFocus()
            event.acceptProposedAction()
            self.drop_index = index

    def paintEvent(self, event):
        super(AssetListView, self).paintEvent(event)
        if self.drop_index:
            r = self.visualRect(self.drop_index)
            r = r - QMargins(1,1,1,1)
            painter = QPainter(self.viewport())
            painter.drawRect(r)
            self.update(self.drop_index)

    def leaveEvent(self, event):
        super(AssetListView, self).leaveEvent(event)
        self.lastIndex = None # Essential! last index will be deleted by Qt

    def enterEvent(self, event):
        super(AssetListView, self).enterEvent(event)
        self.lastIndex = None # Essential! last index will be deleted by Qt

    def setModel(self, model):
        super(AssetListView, self).setModel(model)
        self.model = model

    def clear(self):
        self.model.clear()

    def keyPressEvent(self, event):
        key = event.key()
        mods = event.modifiers()
        super(AssetListView, self).keyPressEvent(event)
        # Populate the clipboard with our copy/paste functionality
        if mods == Qt.ControlModifier and key == Qt.Key_C:
            self.clipboardCopy()
        elif mods == Qt.ControlModifier and key == Qt.Key_V:
            self.clipboardPaste()
        elif mods == Qt.ControlModifier and key == Qt.Key_G:
            self.groupSelectedItems()
        elif key == Qt.Key_Space:
            if self.lastIndex and self.lastIndex.isValid():
                self.onExecuted.emit(self.lastIndex)

    def clipboardCopy(self, description=None):
        clipboard = QApplication.clipboard()
        if asset := self.getSelectedAsset():
            id = asset.id
            category = asset.category
            name = asset.path
            if description:
                clipboard.setText(f'relic://{category}/{id}/{name}#{description}')
            else:
                clipboard.setText(f'relic://{category}/{id}/{name}')
        else:
            clipboard.clear()

    def clipboardPaste(self):
        clipboard = QApplication.clipboard()
        clip_img = clipboard.image()
        if not int(config.RELIC_PREFS.edit_mode):
            return
        mime_data = clipboard.mimeData()
        asset = self.getSelectedAsset()
        if not asset:
            return

        if mime_data.hasImage():
            out_img = ingest.makeImagePreview(clip_img)
            out_path = asset.network_path.suffixed('_icon', ext='.jpg')
            out_path.path.parent.mkdir(parents=True, exist_ok=True)
            out_img.save(str(out_path))
            asset.icon = QPixmap.fromImage(out_img) # fromImageInPlace
        elif mime_data.hasUrls():
            for url in mime_data.urls():
                if not url.isLocalFile():
                    continue
                path = Path(url.toLocalFile())
                file_type = EXTENSION_MAP[path.ext.lower()] 
                if path.is_file() and file_type == Class.MOVIE:
                    ingest.generateProxy(path, asset.network_path)

    def groupSelectedItems(self):
        """Creates a new collection asset and links all the selected
        assets to it.
        """
        selection = self.selectionModel().selectedIndexes()
        count = len(selection)
        if not selection or count <= 1:
            return
        collection_name, ok = QInputDialog.getText(self, 'New Collection',
                "Collection name:", QLineEdit.Normal)#, default_name)
        if not ok:
            return
    
        primary = selection[-1].data(Qt.UserRole)
        constructor = getCategoryConstructor(primary.category)
        subcategory = primary.subcategory.data(Qt.UserRole)

        collection = constructor(
            name=collection_name,
            dependencies=count,
            path='{}/{}'.format(subcategory.name, collection_name),
            links=(subcategory.relationMap, subcategory.id),
            type=int(AssetType.COLLECTION),
        )
        link_mapping = []
        for item in selection:
            asset = item.data(Qt.UserRole)
            link_mapping.append([asset.relationMap, asset.id])

        collection.createCollection(link_mapping)

    def getSelectedAsset(self):
        selection = self.selectionModel().selectedIndexes()
        if not selection:
            return None
        return selection[-1].data(Qt.UserRole)

    def indexToItem(self, index):
        proxy_model = index.model()
        remapped_index = proxy_model.mapToSource(index)
        item = self.model.itemFromIndex(remapped_index)

        return item

    def resetLastIndex(self):
        index = self.lastIndex
        asset = index.data(Qt.UserRole)
        asset.progress = 0
        on_complete = partial(setattr, asset, 'icon')
        worker = LocalThumbnail(asset.icon_path, on_complete)
        THREAD_POOL.start(worker)
        self.model.dataChanged.emit(index, index, [Qt.UserRole])
        self.lastIndex = None

    def mouseMoveEvent(self, event):
        super(AssetListView, self).mouseMoveEvent(event)
        mouse_pos = event.pos()
        index = self.indexAt(mouse_pos)
        if not index.isValid():
            if self.lastIndex is not None:
                self.resetLastIndex()
            return
        asset = index.data(Qt.UserRole)
        if index != self.lastIndex:
            if self.lastIndex is not None:
                self.resetLastIndex()
            self.lastIndex = index
            THREAD_POOL.clear()
            THREAD_POOL.waitForDone()
            if BaseItemDelegate.VIEW_MODE == ItemDispalyModes.THUMBNAIL:
                has_duration = hasattr(asset, 'duration') and asset.duration
                if has_duration or getattr(asset, 'class') in PREVIEWABLE:
                    asset.stream_video_to()
                elif asset.type == int(AssetType.COLLECTION):
                    asset.video = []
                    if isinstance(asset.upstream, list):
                        for num, x in enumerate(asset.upstream):
                            if num > 15:
                                break
                            linked_asset = x.data(Qt.UserRole)
                            # TODO: this is a temporary local implementation.
                            worker = LocalThumbnail(linked_asset.icon_path, asset.video.append)
                            THREAD_POOL.start(worker)

        if BaseItemDelegate.VIEW_MODE == ItemDispalyModes.THUMBNAIL:
            rect = self.visualRect(index)
            a = rect.bottomLeft()
            relative_pos = mouse_pos.x() - a.x()
            if relative_pos > 0 and relative_pos < 292:
                if asset.video:
                    duration = len(asset.video)
                    pos_idx = int(relative_pos * duration / rect.width())
                    asset.icon = asset.video[pos_idx]
                    asset.progress = relative_pos

                self.model.dataChanged.emit(index, index, [Qt.UserRole])

    def dropEvent(self, event):
        if not int(config.RELIC_PREFS.edit_mode):
            return

        index = self.indexAt(event.pos())
        if not index.isValid():
            return
        primary_asset = index.data(Qt.UserRole)
        
        dst_name = primary_asset.name
        msg = f'Link selected assets to <b>{dst_name}</b>?\n'
        message_box = QMessageBox(QMessageBox.Information, 'Are you sure?', msg,
                QMessageBox.Yes|QMessageBox.No, self)
        link_ico = QPixmap(':app/folder_link.svg')
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
                if not primary_asset.dependencies:
                    primary_asset.dependencies = 1
                else:
                    primary_asset.dependencies += 1

        primary_asset.update(fields=['dependencies'])

    @Slot(QPoint)
    def showContextMenus(self, point: QPoint):
        """Populates a context menu based on the current application index.
        """
        context_menu = QMenu(self)
        context_menu.addActions(self.main_actions)

        is_temp = [isinstance(x, TempAsset) for x in self.selectedAssets()]

        if int(config.RELIC_PREFS.edit_mode):
            context_menu.addActions(self.edit_actions)
            if not any(is_temp):
                context_menu.addAction(self.unlink_action)

        if self.additional_actions:
            advanced_action = QWidgetAction(self)
            advanced_action.setDefaultWidget(self.advanced_label)
            context_menu.addAction(advanced_action)
            context_menu.addSeparator()
            context_menu.addActions(self.additional_actions)

        context_menu.exec(QCursor.pos())

    def selectedAssets(self):
        for i in self.selectedIndexes():
            yield i.data(Qt.UserRole)

    @Slot()
    def unlinkAsset(self):
        for index in self.selectedIndexes():
            self.onLinkRemove.emit(index)

    @Slot()
    def deleteAsset(self):
        """Asset deletion. Iterates selected items to delete,
        and updates the items parent subcategory counts.
        """
        update_list = []
        count_data = defaultdict(int)

        for index in self.selectedIndexes():
            asset = index.data(Qt.UserRole)
            subcategory = asset.subcategory
            if isinstance(subcategory, list):
                subcategory = subcategory[0]

            if subcategory and asset.type != AssetType.COLLECTION:
                count_data[subcategory.id] -= 1

            if not isinstance(asset, TempAsset):
                asset.remove()
            self.setRowHidden(index.row(), True)
            self.onDeleted.emit(index)

        # Update the subcategories with new counts
        self.assetsDeleted.emit(count_data)

    def generatePreview(self):
        msg = 'Regenerate previews from source file? \nThis will remake proxies and previews.'
        message_box = QMessageBox(QMessageBox.Question, 'Choice', msg,
                QMessageBox.Yes|QMessageBox.No, self)
        result = message_box.exec_()
        if result == QMessageBox.No:
            return

        for index in self.selectedIndexes():
            asset = index.data(Qt.UserRole)
            path = asset.network_path
            if asset.path == '' or not path.parent.exists():
                continue
            # Reuse the ingest methods to make preview media.
            found_type = FileTypes[asset.path.ext]
            classifiy = found_type.value
            is_image = classifiy & Class.IMAGE
            if path.isSequence() and is_image:
                new = ingest.processSEQ(path, path)
            elif found_type & FileTypes.exr:
                new = ingest.processHDR(path, path)
            elif is_image:
                new = ingest.processLDR(path, path)
            elif classifiy in Class.MOVIE:
                new = ingest.processMOV(path, path)

            asset.icon = new.icon

    def browseLocalAsset(self):
        for index in self.selectedIndexes():
            asset = index.data(Qt.UserRole)
            if isinstance(asset, TempAsset):
                winpath = str(asset.path).replace('/', '\\')
            else:
                winpath = str(asset.network_path.parent).replace('/', '\\')
            cmd = 'explorer /select, "{}"'.format(winpath)
            subprocess.Popen(cmd)
    
    def assetPreview(self):
        index = self.selectedIndexes()[-1]
        asset = index.data(Qt.UserRole)
        config.peakPreview(asset.network_path)
