import copy
import datetime
import os
import time
import json
import subprocess
from functools import partial
from sequence_path.main import SequencePath as Path
from collections import defaultdict
from qtshared6.utils import polymorphicItem
from qtshared6.delegates import BaseView, BaseItemDelegate, ColorIndicator, BaseItemModel, ItemDispalyModes

# -- Module --
import library.config as config
from library.config import Classification, Extension
from library.io.ingest import ConversionRouter, remakePreview
from library.io.util import LocalThumbnail

from library.objectmodels import allCategories, subcategory, temp_asset, getCategoryConstructor, Library, Type

# -- Third-party --
from PySide6.QtCore import (QByteArray, QItemSelectionModel, QMargins, QThreadPool,
                            QMimeData, QModelIndex, QObject, QPoint,
                            QPropertyAnimation, QRect, QSize, Signal, Slot, QEvent, QTimer, QUrl)
from PySide6.QtGui import (QAction, QIcon, QColor, QCursor, QDrag, QFont, QMovie, QPainter,
                           QPainterPath, QPen, QPixmap, QRegion,
                           QStandardItemModel, Qt, QImage, QMouseEvent)
from PySide6.QtWidgets import (QAbstractItemView, QLineEdit, QInputDialog,
                               QListView, QMenu, QStyle, QStyledItemDelegate,
                               QStyleOption, QWidget, QApplication, QCheckBox, QMessageBox)
#unimageable_types = {
#    '.r3d': QPixmap(':resources/general/RedLogo.png')
#} 
THREAD_POOL = QThreadPool.globalInstance()

class AssetItemModel(BaseItemModel):

    def mimeData(self, indices):
        # Removes unserializable data
        paths = []
        unhashable = defaultdict(list)
        objs = []

        by_category = defaultdict(list)
        unique_ids = []

        for index in indices:
            obj = index.data(polymorphicItem.Object)
            if obj:
                if isinstance(obj, temp_asset):
                    by_category['uncategorized'].append(obj.export)
                else:
                    for asset in obj.recurseDependencies(obj):
                        # Insert asset into the payload
                        if isinstance(asset, polymorphicItem):
                            asset = asset.data(polymorphicItem.Object)
                        key = allCategories.slots[asset.category]
                        by_category[key].append(asset.export)
                        
                paths.append(QUrl.fromLocalFile(str(obj.path)))
                unhashable['icon'].append(obj.icon)
                unhashable['category'].append(obj.category)
                unhashable['subcategory'].append(obj.subcategory)
                unhashable['tags'].append(obj.tags)
                unhashable['alusers'].append(obj.alusers)
                unhashable['upstream'].append(obj.upstream)
                unhashable['downstream'].append(obj.downstream)
                unhashable['video'].append(obj.video)
                objs.append(obj)
                obj.icon = None
                obj.category = None
                obj.subcategory = None
                obj.tags = None
                obj.alusers = None
                obj.upstream = None
                obj.downstream = None
                obj.video = None
                

        mime_data = super(BaseItemModel, self).mimeData(indices)

        payload = json.dumps(by_category)

        protocol = 'relic://'
        mime_data.setText(payload)

        itemData = QByteArray()
        mime_data.setData('application/x-relic', itemData)
        url = QUrl.fromLocalFile(protocol + str(payload))
        mime_data.setUrls([url])

        # Tacks back in serializable data
        for i, obj in enumerate(objs):
            obj.icon = unhashable['icon'][i]
            obj.category = unhashable['category'][i]
            obj.subcategory = unhashable['subcategory'][i]
            obj.tags = unhashable['tags'][i]
            obj.alusers = unhashable['alusers'][i]
            obj.upstream = unhashable['upstream'][i]
            obj.downstream = unhashable['downstream'][i]
            obj.video = unhashable['video'][i]

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
        self.setViewMode(QListView.IconMode)
        self.setFlow(QListView.LeftToRight)
        self.setMouseTracking(True)
        self.setUniformItemSizes(True)
        self.setAutoFillBackground(True)
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
        self.setItemDelegate(BaseItemDelegate(self))

        self.lastIndex = None
        self.drag_select = False
        # Actions

        #self.actionPreview = QAction('Peak Preview', self)
        #self.actionPreview.triggered.connect(self.assetPreview)
        self.actionExploreLocation = QAction('Browse File Location', self)
        self.actionExploreLocation.triggered.connect(self.browseLocalAsset)
        self.actionDelete = QAction('Delete', self)
        self.actionDelete.triggered.connect(self.deleteAsset)
        self.actionUnlink = QAction('Unlink', self)
        self.actionUnlink.triggered.connect(self.unlinkAsset)
        self.actionGeneratePreview =  QAction('Generate Preview', self)
        self.actionGeneratePreview.triggered.connect(self.generatePreview)
        self.additional_actions = []

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
        selection = self.selectionModel().selectedIndexes()
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
        link_mapping = []
        for item in selection:
            asset = item.data(polymorphicItem.Object)
            link_mapping.append([asset.relationMap, asset.id])

        collection.createCollection(link_mapping)

    def getSelectedAsset(self):
        selection = self.selectionModel().selectedIndexes()
        if not selection:
            return None
        return selection[-1].data(polymorphicItem.Object)

    def indexToItem(self, index):
        proxy_model = index.model()
        remapped_index = proxy_model.mapToSource(index)
        item = self.model.itemFromIndex(remapped_index)

        return item

    def mouseMoveEvent(self, event):
        super(AssetListView, self).mouseMoveEvent(event)
        mouse_pos = event.pos()
        index = self.indexAt(mouse_pos)
        if not index.isValid():
            return
        asset = index.data(polymorphicItem.Object)

        if index != self.lastIndex:
            self.lastIndex = index
            if BaseItemDelegate.VIEW_MODE == ItemDispalyModes.THUMBNAIL:
                has_movie = hasattr(asset, 'duration') and asset.duration
                if has_movie or getattr(asset, 'class') == Classification.MODEL:
                    asset.stream_video_to()
                elif asset.type == int(Type.COLLECTION):
                    asset.video = []
                    if isinstance(asset.upstream, list):
                        for num, x in enumerate(asset.upstream):
                            if num > 15:
                                break
                            linked_asset = x.data(polymorphicItem.Object)
                            #linked_asset.fetchIcon()
                            ico = linked_asset.network_path.suffixed('_icon', '.jpg')
                            worker = LocalThumbnail(ico, asset.video.append)
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

                self.dataChanged(index, index)

    def dropEvent(self, event):
        if not int(config.RELIC_PREFS.edit_mode):
            return

        index = self.indexAt(event.pos())
        if not index.isValid():
            return
        primary_asset = index.data(polymorphicItem.Object)
        
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
                if not primary_asset.dependencies:
                    primary_asset.dependencies = 1
                else:
                    primary_asset.dependencies += 1

        primary_asset.update(fields=['dependencies'])


    @Slot()
    def showContextMenus(self, val):
        """Populates a context menu based on the current application index.
        """
        sender = self.sender()
        context_menu = QMenu(self)
        context_menu.addAction(self.actionExploreLocation)
        #context_menu.addAction(self.actionPreview)
    
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
        count_data = defaultdict(int)

        for index in self.selectedIndexes():
            asset = index.data(polymorphicItem.Object)
            subcategory = asset.subcategory
            if isinstance(subcategory, list):
                subcategory = subcategory[0]

            if subcategory and asset.type != Type.COLLECTION:
                count_data[subcategory.id] -= 1

            if not isinstance(asset, temp_asset):
                asset.remove()
            self.setRowHidden(index.row(), True)
            self.onDeleted.emit(index)

        # Update the subcategories with new counts
        self.assetsDeleted.emit(count_data)

    def generatePreview(self, action):
        msg = 'Regenerate previews from source file or ues existing preview?'
        message_box = QMessageBox(QMessageBox.Question, 'Choice', msg,
                QMessageBox.Yes|QMessageBox.No|QMessageBox.Cancel, self)
        result = message_box.exec_()
        if result == QMessageBox.Cancel:
            return
        elif result == QMessageBox.No:
            for index in self.selectedIndexes():
                asset = index.data(polymorphicItem.Object)
                path = asset.network_path
                if asset.path == '' or not path.parent.exists():
                    continue
                remakePreview(path)
            return

        for index in self.selectedIndexes():
            asset = index.data(polymorphicItem.Object)
            path = asset.network_path
            if asset.path == '' or not path.parent.exists():
                continue
            path.checkSequence()
            if path.sequence_path:
                ConversionRouter.processSEQ(path, path)
            elif path.ext in Extension.LDR:
                ConversionRouter.processLDR(path, path)
            elif path.ext in Extension.HDR:
                ConversionRouter.processHDR(path, path)
            elif path.ext in Extension.MOVIE:
                ConversionRouter.processMOV(path, path)

    def browseLocalAsset(self, action):
        for index in self.selectedIndexes():
            asset = index.data(polymorphicItem.Object)
            winpath = str(asset.network_path.parent).replace('/', '\\')
            cmd = 'explorer /select, "{}"'.format(winpath)
            subprocess.Popen(cmd)
    
    def assetPreview(self, action):
        index = self.selectedIndexes()[-1]
        asset = index.data(polymorphicItem.Object)
        config.peakPreview(asset.network_path)

