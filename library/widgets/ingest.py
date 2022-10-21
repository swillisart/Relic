import json
import os
from collections import defaultdict
from functools import partial

from imagine.colorchecker_detection import detectColorChecker
from library.config import RELIC_PREFS, peakPreview
from library.io import ingest 
from library.objectmodels import (Type, alusers, getCategoryConstructor,
                                  relationships, session, tags)
from library.ui.ingestion import Ui_IngestForm
from library.widgets.assets_alt import AssetItemModel
from library.widgets.util import SimpleAsset
from PySide6.QtCore import (Property, QEvent, QFile, QItemSelectionModel,
                            QMargins, QObject, QPoint, QPropertyAnimation,
                            QRect, QRegularExpression, QSize,
                            QSortFilterProxyModel, Qt, QTextStream, QThread,
                            QThreadPool, Signal, Slot, QModelIndex)
from PySide6.QtGui import (QAction, QColor, QCursor, QFont, QFontMetrics,
                           QIcon, QImage, QMovie, QPainter, QPixmap,
                           QRegularExpressionValidator, QStandardItemModel, Qt)
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox, QWidget
from qtshared6.utils import polymorphicItem
from relic.local import (INGEST_PATH, Category, ClassGroup, Extension,
                         FileType, TempAsset, getAssetSourceLocation)
from relic.qt.delegates import Statuses
from relic.scheme import Class
from sequence_path.main import SequencePath as Path

CLOSE_MSG = """
You have not completed categorizing the collected files.
The remaining unprocessed files will be lost.

Are you sure you want to cancel and close?
"""
def working_task(func):
    def wrapp(self, *args, **kwargs):
        if self.working:
            msg = 'Can only have one active asset pre-process.'
            QMessageBox.information(self, 'Already Processing', msg)
            return
        else:
            self.working = True
            self.loadingLabel.show()
            self.completedLabel.hide()
        return func(self, *args, **kwargs)
    return wrapp

class IngestForm(Ui_IngestForm, QDialog):

    beforeClose = Signal(QWidget)
    finishedCollection = Signal(bool)
    finishedProcessing = Signal(bool)

    def __init__(self, *args, **kwargs):
        super(IngestForm, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.nextButton.clicked.connect(self.nextStage)
        self.next_enabled = partial(self.nextButton.setEnabled, True)
        self.next_disabled = partial(self.nextButton.setEnabled, False)
        self.collectedListView.onDeleted.connect(self.removeIngestFiles)
        self.collectedListView.additional_actions.extend([
            QAction('Detect Color Matrix', self, triggered=self.getColorMatrix),
            QAction('Align & Blend Exposures', self, triggered=self.alignBlendExposures),
            QAction('Process Image', self, triggered=self.reprocessImage),
            ])

        self.collect_item_model = AssetItemModel()
        self.new_asset_item_model = AssetItemModel()
        self.collectedListView.setModel(self.collect_item_model)
        self.collectedListView.selectionModel().selectionChanged.connect(self.filterCategories)

        self.newAssetListView.setModel(self.new_asset_item_model)

        self.collect_item_model.rowsInserted.connect(self.updateLabelCounts)
        self.new_asset_item_model.rowsInserted.connect(self.updateLabelCounts)
        self.collectPathTextEdit.textChanged.connect(self.next_enabled)
        self.collectedListView.assetsDeleted.connect(self.updateLabelCounts)
        self.existingNamesList.newItem.connect(self.onNewItem)
        self.existingNamesList.linkItem.connect(self.onLinkItem)
        self.ingest_thread = ingest.IngestionThread(self)
        self.ingest_thread.itemDone.connect(self.assetIngested)
        self.loadingLabel.setAttribute(Qt.WA_TranslucentBackground, True)
        self.loading_movie = QMovie(':resources/general/load_wheel_24.webp')
        self.loading_movie.setCacheMode(QMovie.CacheAll)
        self.loading_movie.start()
        self.loadingLabel.setMovie(self.loading_movie)
        self.loadingLabel.hide()
        self.completedLabel.hide()
        self.processLoadingLabel.setMovie(self.loading_movie)
        self.processLoadingLabel.hide()
        self.processCompleteLabel.hide()
        self.kept_original_name = False
        self.pool = QThreadPool.globalInstance()

        session.retrieveassetnames.callback.connect(self.onAssetNameRetrieval)
        session.initializeprimaryasset.callback.connect(self.createVariations)
        session.createassets.callback.connect(self.ingestAssets)
        self.collectedListView.onExecuted.connect(self.previewLocal)
        self.collectedListView.doubleClicked.connect(self.previewLocal)
        self.working = False
        self.current_category_id = None

    @Slot()
    def filterCategories(self, index):
        selection = self.sender().selectedIndexes()
        category_widgets = self.category_widgets

        if not selection: # show all possible categories
            for x in Category:
                category_expander = category_widgets[int(x)]
                category_expander.show()
            return

        classification = 0
        category_filter = set()
        for index in selection:
            asset = index.data(Qt.UserRole)
            classifier = Class(getattr(asset, 'class'))
            classification |= classifier
            # If the category is provided use that as a secondary filter
            if asset.category is not None:
                category_filter.add(Category(int(asset.category)))
        
        # Consider all categories if none are provided by the selection
        if not category_filter:
            [category_filter.add(x) for x in Category]
        # Filter by categories and classification
        for x in Category:
            category_expander = category_widgets[int(x)]
            if x.data.classifier & classification and x in category_filter:
                category_expander.show()
                category_expander.expandState()
            else:
                category_expander.collapseState()
                category_expander.hide()

    def previewLocal(self, index):
        temp_path, temp_asset = self.getCollectedPath(index)
        peakPreview(temp_path)

    def show(self):
        super(IngestForm, self).show()
        self.todo = 0
        self.done = 0
        self.updateLabelCounts(None)
        self.completedLabel.hide()
        self.processCompleteLabel.hide()
        self.ingestTabWidget.setCurrentIndex(0)

    @Slot()
    def removeIngestFiles(self, index):
        temp_path, temp_asset = self.getCollectedPath(index)
        preview_flavors = [
            temp_path.suffixed('_icon', ext='.jpg'),
            temp_path.suffixed('_proxy', ext='.jpg'),
            temp_path.suffixed('_icon', ext='.mp4'),
            temp_path.suffixed('_proxy', ext='.mp4'),
            temp_path.suffixed(''),
        ]
        for preview_file in preview_flavors:
            if preview_file.exists():
                os.remove(str(preview_file))


    def keyPressEvent(self, event):
        key = event.key()
        mods = event.modifiers()
        if mods == Qt.ControlModifier and key == Qt.Key_V:
            self.setColorMatrix()
        return super(IngestForm, self).keyPressEvent(event)

    @Slot()
    def assetIngested(self, asset):
        # Update the asset's fields in the database 
        asset.update()
        self.updateLabelCounts(None)

        # Check if all the other background copy operations have completed.
        if len(self.ingest_thread.queue) == 0:
            # Allow the user to finish.
            self.processLoadingLabel.hide()
            self.processCompleteLabel.show()
            if self.done == self.todo:
                self.nextButton.setText('Finish')
                self.next_enabled()
        else:
            # Still processing
            self.processLoadingLabel.show()
            self.processCompleteLabel.hide()

    def collectAssetsFromPlugin(self, assets):
        self.categorizeTab.setEnabled(True)
        self.ingestTabWidget.setCurrentIndex(1)
        self.kept_original_name = True
        self.updateLabelCounts(len(assets))
        # always copy and never move any plugin data.
        self.copyCheckBox.setChecked(True)
        item_model = self.collect_item_model
        for fields in assets:
            asset = TempAsset(**fields)
            asset.path = Path(asset.path)
            icon_path = asset.path.suffixed('_icon', ext='.jpg')
            asset.icon = QPixmap.fromImage(QImage(str(icon_path)))
            item = polymorphicItem(fields=asset)
            item_model.appendRow(item)

    def getSelection(self):
        selection = self.collectedListView.selectedIndexes()
        if not self.selectedSubcategory or not selection:
            msg = 'Selection of a Subcategory & Collected Asset is requried.'
            QMessageBox.information(self, 'Empty Selection', msg)
            return False
        else:
            return selection

    @Slot(str)
    def onNewItem(self, name):
        selection = self.getSelection()
        if not selection:
            return
        subcategory = self.selectedSubcategory.data(polymorphicItem.Object)
        category_id = self.current_category_id
        asset_constructor = getCategoryConstructor(category_id)

        # If a selection contains multiple switch the creation mode
        # to make a collection and link all created Assets as Variants.
        total = len(selection)
        self.increment = 0
        asset = asset_constructor(
            name=name,
            path=f'{subcategory.name}/{name}',
            links=(subcategory.relationMap, subcategory.id)
        )
        if total > 1:
            asset.type = int(Type.COLLECTION)
            primary_data = {asset.categoryName: asset.export}
            session.initializeprimaryasset.execute(primary_data)
        else:
            asset.type = int(Type.ASSET)
            asset_data = {asset.categoryName: [asset.export]}
            session.createassets.execute(asset_data)

    @Slot(SimpleAsset)
    def onLinkItem(self, simple_asset):
        """Handles linking of a new asset (as a Variant) to a primary asset or collection.

        Parameters
        ----------
        simple_asset : SimpleAsset
            The existing asset name, id handling object.
        """
        selection = self.getSelection()
        if not selection:
            return

        name = simple_asset.name
        # Split the increment and add 1 to give unique, associative subasset name.
        if ' ' in name:
            base, num = name.split(' ')
            self.increment = int(num)
        else: # Starting the at 1 to for uniqeness.
            base = name
            self.increment = 0

        # upate the group item with new count.
        total = self.increment + len(selection)
        index = self.existingNamesList.listView.selectedIndexes()[0]
        qitem = self.existingNamesList.indexToItem(index)
        simple_asset.name = f'{base} {total}'
        qitem.setData(simple_asset.name, Qt.DisplayRole)

        category_id = self.current_category_id
        asset_constructor = getCategoryConstructor(category_id)

        primary_asset = asset_constructor(name=base, id=simple_asset.id)
        primary_data = {primary_asset.categoryName: primary_asset.export}
        session.initializeprimaryasset.execute(primary_data)

    @Slot(dict)
    def createVariations(self, primary_data):
        for category_name, fields in primary_data.items():
            asset_constructor = getCategoryConstructor(category_name)
            primary_asset = asset_constructor(*fields)
        
        selection = self.collectedListView.selectedIndexes()
        subcategory = self.selectedSubcategory.data(polymorphicItem.Object)
        if primary_asset.dependencies:
            upstream_count = len(selection) + primary_asset.dependencies
        else:
            upstream_count = len(selection)

        primary_asset.dependencies = upstream_count
        primary_asset.update(fields=['dependencies'])
        assets = []
        for num, index in enumerate(selection):
            increment = self.increment + num
            asset = asset_constructor() # 
            asset.links = (subcategory.relationMap, subcategory.id)
            asset.name = f'{primary_asset.name}_{increment}'
            asset.type = int(Type.VARIANT)
            asset.dependencies = 0
            assets.append(asset.export)
        asset_data = {
            category_name: assets,
            'id_map': [[primary_asset.relationMap, primary_asset.links]],
            }
        session.createassets.execute(asset_data)

    @Slot(dict)
    def ingestAssets(self, new_assets_data):
        new_asset_fields = new_assets_data.popitem()[-1]

        selection = self.collectedListView.selectedIndexes()
        category_id = self.current_category_id
        subcategory = self.selectedSubcategory.data(polymorphicItem.Object)
        asset_constructor = getCategoryConstructor(category_id)
        ingester = self.ingest_thread
        if self.copyCheckBox.checkState():
            ingester.file_op = ingest.IngestionThread.copyOp
        else:
            ingester.file_op = ingest.IngestionThread.moveOp

        item_model = self.new_asset_item_model
        for num, index in enumerate(selection):
            temp_asset = index.data(polymorphicItem.Object)

            # temp on-disk local asset location for copying to the network.
            if self.kept_original_name:
                temp_filename = temp_asset.name
            else:
                temp_filename = 'unsorted' + str(temp_asset.id)

            # Construct asset from database-created fields
            asset = asset_constructor(**new_asset_fields[num])

            # Re-apply the GUI attributes for our item's QPainter. 
            asset.icon = temp_asset.icon
            asset.path = temp_asset.path
            asset.resolution = temp_asset.resolution
            asset.category = category_id
            asset.subcategory = subcategory
            self.linkIngestAssetDependencies(asset, temp_asset)

            self.collectedListView.setRowHidden(index.row(), True)
            item = polymorphicItem(fields=asset)
            item_model.appendRow(item)
            self.processLoadingLabel.show()
            extra_files = temp_asset.dependencies

            ingester.load([temp_filename, asset, extra_files])
            # add any new (unique) asset to the existing assets list view
            if '_' not in asset.name:
                self.existingNamesList.addItem(asset.name, asset.id)

        # Update counts on assets and subcategories
        count_data = {subcategory.id: len(selection)}
        session.updatesubcategorycounts.execute(count_data)
        self.collectedListView.clearSelection()

    def linkIngestAssetDependencies(self, asset, temp_asset):
        # Create asset relationships.
        relations = []
        if temp_asset.links:
            asset.dependencies += len(temp_asset.links)
            for link in temp_asset.links:
                link_constructor = getCategoryConstructor(link['category'])
                polymorphic = link_constructor()
                relations.append([
                    polymorphic.relationMap,
                    int(link['id']),
                    asset.links,
                ])
        if temp_asset.tags:
            for tag_data in temp_asset.tags:
                tag = tags(**tag_data)
                tag.createNew( [[tag.relationMap, asset.links]])
        user = alusers(name=os.getenv('username'), id=int(RELIC_PREFS.user_id))
        user.createNew([[user.relationMap, asset.links]])
        session.createrelationships.execute(relations)

    @property
    def selectedSubcategory(self):
        tab = self.category_widgets[self.current_category_id]
        if selection := tab.category.tree.selectedIndexes():
            return selection[-1]

    def updateSubcategoryCounts(self, index):
        tab = self.category_widgets[self.current_category_id]
        item = tab.category.tree.indexToItem(index)
        tab.category.tree.updateSubcategoryCounts(item)

    @Slot()
    def nextStage(self):
        stage = self.ingestTabWidget.currentIndex()
        if stage == 0:
            self.loadingLabel.show()
            self.categorizeTab.setEnabled(True)
            self.next_disabled()
            self.collect()
            self.ingestTabWidget.setCurrentIndex(stage+1)
        else:
            self.close()

    def collect(self):
        self.kept_original_name = False 

        paths = self.collectPathTextEdit.toPlainText().split('\n')
        # sanitize the paths leaving only literal filepaths
        filepaths = [x.replace('file:///', '') for x in paths if x]
        ingest_map = self.getIngestionMap()

        self.collect_thread = QThread(self)
        self.router = ingest.ConversionRouter(ingest_map)
        self.router.moveToThread(self.collect_thread)
        self.router.finished.connect(self.collectionComplete)
        self.router.progress.connect(self.receiveAsset)
        self.router.started.connect(self.updateLabelCounts)
        self.router.error.connect(self.updateLabelCounts)
        self.collect_thread.started.connect(self.router.run)
        self.router.addToQueue(filepaths)
        self.collect_thread.start()

    @Slot()
    def collectionComplete(self):
        self.loadingLabel.hide()
        self.completedLabel.show()
        self.collect_thread.quit()
        self.finishedCollection.emit(True)

    @Slot()
    def receiveAsset(self, asset):
        if not asset:
            return
        asset.id = self.collect_item_model.rowCount() + 1
        asset.type = int(Type.ASSET)
        asset.status = int(Statuses.Local)
        item = polymorphicItem(fields=asset)
        self.collect_item_model.appendRow(item)

    def setCategoryView(self, dock, layout):
        self.categorizeFrame.layout().insertWidget(0, dock)
        self.category_dock = dock
        self.category_widgets = []
        for x in Category:
            category_widget = layout.itemAt(int(x)).widget()
            category_widget.collapseExpand.connect(self.onCategoryChanged)
            self.category_widgets.append(category_widget)

    @Slot()
    def updateLabelCounts(self, value):
        self.done = 0
        for i in range(self.collect_item_model.rowCount()):
            if self.collectedListView.isRowHidden(i):
                self.done += 1

        collected = self.collect_item_model.rowCount()
        if isinstance(value, int):
            self.todo = value
        collect_msg = 'Collected : {}/{}'.format(collected, self.todo)
        self.collectedLabel.setText(collect_msg)
        assets_msg = 'Processed : {}/{}'.format(self.done, self.todo)
        self.newAssetsLabel.setText(assets_msg)
        if collected == 0 and self.todo == 0:
            self.nextButton.setText('Collect')
        elif len(self.ingest_thread.queue) == 0 and self.done == self.todo:
            self.finishedProcessing.emit(True)
            self.nextButton.setText('Finish')
            self.next_enabled()

    def _filterFlag(self, func, _flag, flags):
        f = filter(lambda i: i.value & _flag, FileType)
        result = {f'.{x.name.lower()}': (func, x) for x in f}
        flags |= _flag # Join the temp flag with the other flags
        return result

    def getIngestionMap(self):
        """Setup an file-extension based conversion map
        to pass to a 'ingest.ConversionRouter()' ingestion thread.

        Returns
        -------
        dict
            the extensions as keys and functions in string form
            >>> {'.exr' : ingest.processIMAGE, '.mov' : 'ingest.processMOV'}
        """
        ingest_map = {}
        flags = 0
        if self.moviesCheckBox.checkState():
            _flag = Class.MOVIE
            ingest_map.update(self._filterFlag(ingest.processMOV, _flag, flags))
        if self.texturesReferencesCheckBox.checkState():
            _flag = Class.IMAGE | Class.ELEMENT
            ingest_map.update(self._filterFlag(ingest.processIMAGE, _flag, flags))
        if self.rawCheckBox.checkState():
            _flag = Class.PHOTO | Class.PLATE
            ingest_map.update(self._filterFlag(ingest.processRAW, _flag, flags))
        if self.toolsCheckBox.checkState():
            _flag = ClassGroup.SOFTWARE
            ingest_map.update(self._filterFlag(ingest.processTOOL, _flag, flags))
        if self.lightsCheckBox.checkState():
            _flag = ClassGroup.EMISSIVE
            ingest_map.update(self._filterFlag(ingest.processLIGHT, _flag, flags))

        return ingest_map
        #TODO: add standalone conversions for these:
        #Extension.SHADER = ['.mtlx', '.osl', '.sbsar']
        #Extension.DCC = ['.ma', '.mb', '.max', '.hip']
        #Extension.TOOLS = ['.nk', '.mel', '.py', 'hda']

    def close(self):
        if self.done != self.todo:
            message = QMessageBox(QMessageBox.Warning, 'Are you sure?', CLOSE_MSG,
                    QMessageBox.NoButton, self)
            message.addButton('Yes', QMessageBox.AcceptRole)
            message.addButton('No', QMessageBox.RejectRole)
            if message.exec_() == QMessageBox.RejectRole:
                return

        # make all category widgets visible again
        [category.show() for category in self.category_widgets]
        self.beforeClose.emit(self.category_dock)

        # remove any leftover / abandoned temp ingest files 
        collect_model = self.collect_item_model
        for i in range(collect_model.rowCount()):
            self.removeIngestFiles(collect_model.index(i, 0))

        # Clear the models.
        collect_model.clear()
        self.new_asset_item_model.clear()
        self.collectPathTextEdit.clear()
        # Close all the thread resources
        #self.ingest_thread.stop()
        #self.ingest_thread.quit()
        #if hasattr(self, 'collect_thread'):
        #    self.collect_thread.stop()
        #    self.collect_thread.quit()
        self.parent().close()

    @Slot()
    def onCategoryChanged(self, state):
        """Fetch Assets in active Category 
        and set the naming and categorization views"""
        self.existingNamesList.itemModel.clear()
        sender = self.sender()
        if not sender.state:
            return
        for i, expander_widget in enumerate(self.category_widgets):
            if expander_widget is sender:
                session.retrieveassetnames.execute(i)
                self.current_category_id = i
            else:
                expander_widget.collapseState()

    @Slot(list)
    def onAssetNameRetrieval(self, asset_data):
        item_model = self.existingNamesList.itemModel
        item_model.clear()
        adder = self.existingNamesList.addItem
        groups = defaultdict(int)
        separator = '_'
        splitter = partial(str.rsplit, sep=separator, maxsplit=1)
        for asset in asset_data:
            name, _id = asset
            if separator in name:
                name, index = splitter(name)
                # Needed to check if we have a index greater than count.
                try:
                    index_number = int(index)
                except ValueError: # asset is not part of a set
                    adder(name, _id)
                    continue
                if index_number > groups[name]:
                    groups[name] = index_number + 1
            else:
                adder(name, _id)

        for key, value in groups.items():
            items = item_model.match(
                item_model.index(0, 0), Qt.DisplayRole, key, -1, Qt.MatchRecursive)
            if items:
                index = items[0]
                item = index.model().itemFromIndex(index)
                item.setData(f'{key} {value}', Qt.DisplayRole)

    @Slot()
    def onTaskCompleted(self, asset):
        asset.status = int(Statuses.Local)
        self.working = False
        collected = self.collect_item_model.rowCount()
        if collected == self.todo:
            self.loadingLabel.hide()
            self.completedLabel.show()
        index = self.collect_item_model.index(asset.id, 0)
        self.collect_item_model.dataChanged.emit(index, index, [Qt.UserRole])
        self.collectedListView.update()

    def getCollectedPath(self, index):
        temp_asset = index.data(polymorphicItem.Object)
        temp_path = INGEST_PATH / 'unsorted{}{}'.format(
            temp_asset.id, temp_asset.path.ext)
        return temp_path, temp_asset

    def setColorMatrix(self): 
        clipboard = QApplication.clipboard()
        for index in self.collectedListView.selectedIndexes():
            temp_path, temp_asset = self.getCollectedPath(index)
            ccm = json.loads(clipboard.text())
            if ccm:
                temp_asset.colormatrix = ccm

    def setupTask(self, asset, func):
        asset.status = int(Statuses.Syncing)
        worker = ingest.TaskRunner(func)
        worker.signals.completed.connect(self.onTaskCompleted)
        return worker

    @working_task
    @Slot()
    def reprocessImage(self):
        for index in self.collectedListView.selectedIndexes():
            temp_path, temp_asset = self.getCollectedPath(index)
            func = partial(ingest.applyImageModifications, temp_path, temp_asset)
            worker = self.setupTask(temp_asset, func)
            self.pool.start(worker)

    @staticmethod
    def colorMatrixFromAsset(asset):
        asset.colormatrix = detectColorChecker(str(asset.path))
        return asset
    
    @working_task
    @Slot()
    def getColorMatrix(self):
        index = self.collectedListView.selectedIndexes()[-1]
        temp_path, temp_asset = self.getCollectedPath(index)
        if getattr(temp_asset, 'class') ^ FileType.EXR or not temp_asset.path.exists():
            msg = f'Wrong image type "{temp_asset.path.stem}" must be an exr.'
            self.failTask(temp_asset, msg)
            return
        func = partial(self.colorMatrixFromAsset, temp_asset)
        worker = self.setupTask(temp_asset, func)
        worker.signals.completed.connect(self.updateClipboard)
        self.pool.start(worker)

    def failTask(self, asset, message):
        QMessageBox.information(self, 'Failed', message)
        self.onTaskCompleted(asset)

    @Slot()
    def updateClipboard(self, asset):
        clipboard = QApplication.clipboard()
        if asset.colormatrix:
            clipboard.setText(json.dumps(asset.colormatrix))
        else:
            msg = 'Was unable to auto-detect a colorchecker within the selected image.'
            self.failTask(asset, msg)
            clipboard.clear()
    
    @working_task
    @Slot()
    def alignBlendExposures(self):
        indices = self.collectedListView.selectedIndexes()
        if len(indices) < 2:
            msg = 'Select more than one asset.'
            QMessageBox.information(self, 'Invalid Selection', msg)
            return

        # Pack the data by path key.
        assets_by_file = {k:v for k, v in map(self.getCollectedPath, indices)}
        # remove the temp previews 
        [self.removeIngestFiles(x) for x in indices]
        # Hide the extra bracketed exposure assets.
        [self.collectedListView.setRowHidden(x.row(), True) for x in indices[1:]]
        self.updateLabelCounts(None)
        primary_asset = indices[0].data(polymorphicItem.Object)
        func = partial(ingest.blendRawExposures, assets_by_file)
        worker = self.setupTask(primary_asset, func)
        self.pool.start(worker)
