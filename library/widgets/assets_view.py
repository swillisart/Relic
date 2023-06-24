import json
import subprocess
from functools import partial
from sequence_path import Path
from collections import defaultdict
from relic.qt.delegates import BaseDelegateMixin, BaseItemDelegate, BaseItemModel, ItemDispalyModes, PreviewImageIndicator

# -- Module --
import library.config as config
from relic.qt.util import _indexToItem
from relic.local import Category, TempAsset, FileType, AssetType, EXTENSION_MAP
from relic.scheme import Classification as Class
from library.io import ingest
from library.io.util import loadIcon

from library.objectmodels import subcategory, getCategoryConstructor

# -- Third-party --
from PySide6.QtCore import (QByteArray, QItemSelectionModel, QMargins, QThreadPool,
                            QMimeData, QModelIndex, QObject, QPoint,
                            QPropertyAnimation, QRect, QSize, Signal, Slot, QEvent, QTimer, QUrl)
from PySide6.QtGui import (QAction, QIcon, QColor, QCursor, QDrag, QFont, QMovie, QPainter,
                           QPainterPath, QPen, QPixmap, QRegion,
                           QStandardItemModel, Qt, QImage, QMouseEvent, QStandardItem)
from PySide6.QtWidgets import (QAbstractItemView, QLineEdit, QInputDialog, QLabel,
                               QListView, QTreeView, QMenu, QStyle, QStyledItemDelegate, QWidgetAction,
                               QStyleOption, QStyleOptionViewItem, QWidget, QApplication, QCheckBox, QMessageBox)

# -- Globals --
PREVIEWABLE = [Class.MODEL, Class.TOOL, Class.ANIMATION, Class.MOVIE, Class.PLATE]


def iterateUpstreamForPreview(asset):
    """Yields only the first 15 upstream assets for previewing.

    Parameters
    ----------
    asset : object
        input asset to iterate over

    Yields
    ------
    QStandardItem
    """
    if isinstance(asset.upstream, list):
        for num, x in enumerate(asset.upstream):
            if num > 15:
                break
            yield x


def loadHoverImage(asset):
    has_duration = hasattr(asset, 'duration') and asset.duration
    if has_duration or getattr(asset, 'class') in PREVIEWABLE:
        if asset.video is None:
            asset.stream_video_to()
    elif asset.type == int(AssetType.COLLECTION):
        for x in iterateUpstreamForPreview(asset):
            loadIcon(x)


class AssetItemModel(BaseItemModel):

    def __init__(self, *args, **kwargs):
        super(AssetItemModel, self).__init__(*args, **kwargs)

    def mimeData(self, indices):
        # TODO: this is completely stupid. 
        # Item data should not contain unserializable data that has to be removed.
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


class DraggableView(BaseDelegateMixin):
    def __init__(self, *args, **kwargs):
        super(DraggableView, self).__init__(*args, **kwargs)
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


class AssetTreeView(DraggableView, QTreeView):
    def __init__(self, *args, **kwargs):
        super(AssetTreeView, self).__init__(*args, **kwargs)


class AssetListView(DraggableView, QListView):
    onLinkRemove = Signal(QModelIndex)
    assetsDeleted = Signal(defaultdict)
    onExecuted = Signal(QModelIndex)

    def __init__(self, parent=None):
        super(AssetListView, self).__init__(parent)
        self.verticalScrollBar().setSingleStep(40)
        self.setViewMode(QListView.IconMode)
        self.setFlow(QListView.LeftToRight)
        self.setResizeMode(QListView.Adjust)
        self.setUniformItemSizes(True)

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
        self.entered.connect(self.onEnter)
        self.current_asset = None
        self.customContextMenuRequested.connect(self.showContextMenus)

    def dragMoveEvent(self, event):
        super(AssetListView, self).dragMoveEvent(event)
        index = self.indexAt(event.pos())
        if not index.isValid() or index in self.selectedIndexes():
            event.ignore()
        elif event.mimeData().hasUrls():
            self.setFocus()
            event.acceptProposedAction()

    def clear(self):
        self.current_asset = None
        self.model().clear()

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
            sel_mod = self.selectionModel()
            if sel_mod.hasSelection():
                selection = sel_mod.selectedIndexes()
                self.onExecuted.emit(selection[-1])

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
            asset.icon = out_img
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

    @Slot(QModelIndex)
    def onEnter(self, index):
        self.invalidateCurrentAsset()
        self.current_asset = index.data(Qt.UserRole)
        if self.itemDelegate().VIEW_MODE == ItemDispalyModes.THUMBNAIL:
            loadHoverImage(self.current_asset)

    def invalidateCurrentAsset(self):
        asset = self.current_asset
        if asset is not None and not isinstance(asset, TempAsset):
            asset.progress = 0
            video = asset.video
            if video is not None:
                asset.icon = video[(len(video) // 2)]
        self.current_asset = None

    def mouseMoveEvent(self, event):
        mouse_pos = event.pos()
        index = self.indexAt(mouse_pos)
        if not index.isValid():
            self.invalidateCurrentAsset()
            return super(AssetListView, self).mouseMoveEvent(event)

        delegate = self.itemDelegate()
        if isinstance(delegate.active_indicator, PreviewImageIndicator):
            asset = index.data(Qt.UserRole)
            if asset.type == AssetType.COLLECTION and asset.video is None:
                previews = [x.data(Qt.UserRole).icon for x in iterateUpstreamForPreview(asset)]
                if all(previews):
                    asset.video = previews
            self.updateHoverImage(index, mouse_pos, delegate)

        super(AssetListView, self).mouseMoveEvent(event)

    def updateHoverImage(self, index, mouse_pos, delegate):
        rect = self.visualRect(index)
        relative_pos = mouse_pos.x() - rect.topLeft().x()
        image_width = delegate.VIEW_MODE.item_size.width()
        if relative_pos > 0 and relative_pos < image_width:
            asset = index.data(Qt.UserRole)
            if asset.video is not None and len(asset.video) > 0:
                duration = len(asset.video)
                pos_idx = int(relative_pos * duration / rect.width())
                try:
                    asset.icon = asset.video[pos_idx]
                except IndexError:
                    print(duration, pos_idx)
                asset.progress = ((pos_idx+1) * 100) / duration
            self.model().dataChanged.emit(index, index, [Qt.UserRole])

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
            self.itemDeleted.emit(index)

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
