import json
import os
from functools import partial
from collections import defaultdict
from imagine.colorchecker_detection import detectColorChecker
from sequencePath import sequencePath as Path

from PySide6.QtCore import (Property, QEvent, QFile, QItemSelectionModel,
                            QMargins, QObject, QPoint, QPropertyAnimation,
                            QRect, QRegularExpression, QSize,
                            QSortFilterProxyModel, Qt, QTextStream, QThread,
                            Signal, Slot, QThreadPool)
from PySide6.QtGui import (QAction, QColor, QCursor, QFont, QFontMetrics,
                           QIcon, QImage, QMovie, QPainter, QPixmap,
                           QRegularExpressionValidator, QStandardItemModel, Qt)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QBoxLayout,
                               QDialog, QDockWidget, QFrame, QLabel, QLayout,
                               QLineEdit, QListView, QMenu, QMessageBox,
                               QScrollArea, QStyledItemDelegate, QTreeView,
                               QVBoxLayout, QWidget)

from library.config import (DCC_EXT, FILM_EXT, GEO_EXT, HDR_EXT, LDR_EXT,
                            LIGHT_EXT, MOVIE_EXT, RAW_EXT, RELIC_PREFS,
                            SHADER_EXT, TOOLS_EXT, INGEST_PATH)
from library.io.ingest import (TaskRunner, ConversionRouter, IngestionThread,
                               applyImageModifications, blendRawExposures)
from library.objectmodels import (alusers, RelicTypes, polymorphicItem, relationships,
                                    tags, temp_asset, getCategoryConstructor, session)
from library.ui.ingestion import Ui_IngestForm
from library.widgets.assets import assetItemModel
from library.widgets.util import ListViewFiltered, SimpleAsset

CLOSE_MSG = """
You have not completed categorizing the collected files.
The remaining unprocessed files will be lost.

Are you sure you want to cancel and close?
"""

class IngestForm(Ui_IngestForm, QDialog):

    beforeClose = Signal(QWidget)

    def __init__(self, *args, **kwargs):
        super(IngestForm, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.nextButton.clicked.connect(self.nextStage)
        self.next_enabled = partial(self.nextButton.setEnabled, True)
        self.next_disabled = partial(self.nextButton.setEnabled, False)
        self.collectedListView.compactMode()
        self.collectedListView.onDeleted.connect(self.removeIngestFiles)
        self.actionGetMatrix = QAction('Get Color Matrix', self)
        self.actionBlendExposures = QAction('Align And Blend Exposures', self)
        self.actionReprocessImage = QAction('Re-Process Image', self)
        self.actionReprocessImage.triggered.connect(self.reprocessImage)
        self.actionGetMatrix.triggered.connect(self.getColorMatrix)
        self.actionBlendExposures.triggered.connect(self.alignBlendExposures)

        self.collectedListView.additional_actions.extend(
            [self.actionGetMatrix, self.actionReprocessImage, self.actionBlendExposures])
        self.newAssetListView.compactMode()

        self.collect_item_model = assetItemModel(self.collectedListView)
        self.new_asset_item_model = assetItemModel(self.newAssetListView)

        self.collect_item_model.rowsInserted.connect(self.updateLabelCounts)
        self.new_asset_item_model.rowsInserted.connect(self.updateLabelCounts)
        self.categoryComboBox.currentIndexChanged.connect(self.onCategoryChange)
        self.collectPathTextEdit.textChanged.connect(self.next_enabled)
        self.collectedListView.assetsDeleted.connect(self.updateLabelCounts)
        self.existingNamesList.newItem.connect(self.onNewItem)
        self.existingNamesList.linkItem.connect(self.onLinkItem)
        self.ingest_thread = IngestionThread(self)
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

        self.categoryComboBox.currentIndexChanged.connect(session.retrieveassetnames.execute)

        session.retrieveassetnames.callback.connect(self.onAssetNameRetrieval)
        session.initializeprimaryasset.callback.connect(self.createVariations)
        session.createassets.callback.connect(self.ingestAssets)

    def show(self):
        super(IngestForm, self).show()
        self.todo = 0
        self.done = 0
        self.updateLabelCounts(None)
        self.completedLabel.hide()
        self.processCompleteLabel.hide()
        self.tabWidget.setCurrentIndex(0)

    @Slot()
    def removeIngestFiles(self, index):
        temp_path, temp_asset = self.getCollectedPath(index)
        preview_flavors = [
            temp_path.suffixed('_icon', ext='.jpg'),
            temp_path.suffixed('_proxy', ext='.jpg'),
            temp_path.suffixed('_icon', ext='.mp4'),
            temp_path.suffixed('_proxy', ext='.mp4'),
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

    def collectAssetsFromPlugin(self, assets):
        self.categorizeTab.setEnabled(True)
        self.tabWidget.setCurrentIndex(1)
        self.kept_original_name = True
        
        for fields in assets:
            asset = temp_asset(**fields)
            asset.path = Path(asset.path)
            icon_path = asset.path.suffixed('_icon', ext='.jpg')
            asset.icon = QPixmap.fromImage(QImage(str(icon_path)))
            self.collectedListView.addAsset(asset)
        self.updateLabelCounts(len(assets)-1)

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
        category_id = self.categoryComboBox.currentIndex()
        asset_constructor = getCategoryConstructor(category_id)
        # If a selection contains multiple switch the creation mode
        # to make a collection and link all created Assets as Variants.
        total = len(selection)
        self.increment = 0
        if total > 1:
            primary_asset = asset_constructor(
                name=name,
                path=f'{subcategory.name}/{name}',
                links=(subcategory.relationMap, subcategory.id),
                type=RelicTypes.COLLECTION,)
            primary_data = {primary_asset.categoryName: primary_asset.export}
            session.initializeprimaryasset.execute(primary_data)
        else:
            asset = asset_constructor(
                name=name,
                links=(subcategory.relationMap, subcategory.id),
                type=RelicTypes.ASSET,)
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

        category_id = self.categoryComboBox.currentIndex()
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
            increment = self.increment + num + 1
            asset = asset_constructor() # 
            asset.links = (subcategory.relationMap, subcategory.id)
            asset.name = f'{primary_asset.name}_{increment}'
            asset.type = RelicTypes.VARIANT
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
        category_id = self.categoryComboBox.currentIndex()
        subcategory = self.selectedSubcategory.data(polymorphicItem.Object)
        asset_constructor = getCategoryConstructor(category_id)
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
            self.linkIngesAssetDependencies(asset, temp_asset)

            self.collectedListView.setRowHidden(index.row(), True)
            self.newAssetListView.addAsset(asset)
            self.processLoadingLabel.show()
            extra_files = temp_asset.dependencies

            self.ingest_thread.load([temp_filename, asset, extra_files])
            # add any new (unique) asset to the existing assets list view
            if '_' not in asset.name:
                self.existingNamesList.addItem(asset.name, asset.id)

        # Update counts on assets and subcategories
        count_data = {subcategory.id: len(selection)}
        session.updatesubcategorycounts.execute(count_data)
        self.collectedListView.clearSelection()

    def linkIngesAssetDependencies(self, asset, temp_asset):
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
        tab = self.category_widgets[self.categoryComboBox.currentIndex()]
        if selection := tab.category.tree.selectedIndexes():
            return selection[-1]

    def updateSubcategoryCounts(self, index):
        tab = self.category_widgets[self.categoryComboBox.currentIndex()]
        item = tab.category.tree.indexToItem(index)
        tab.category.tree.updateSubcategoryCounts(item)

    @Slot()
    def nextStage(self):
        stage = self.tabWidget.currentIndex()
        if stage == 0:
            self.loadingLabel.show()
            self.categorizeTab.setEnabled(True)
            self.next_disabled()
            self.collect()
            self.tabWidget.setCurrentIndex(stage+1)
        else:
            self.close()

    def collect(self):
        self.kept_original_name = False 

        paths = self.collectPathTextEdit.toPlainText().split('\n')
        # sanitize the paths leaving only literal filepaths
        filepaths = [x.replace('file:///', '') for x in paths if x]
        function_map = self.getConversionMap()

        self.collect_thread = QThread(self)
        self.router = ConversionRouter(function_map)
        self.router.moveToThread(self.collect_thread)
        self.router.finished.connect(self.collectionComplete)
        self.router.progress.connect(self.receiveAsset)
        self.router.started.connect(self.updateLabelCounts)
        self.collect_thread.started.connect(self.router.run)
        self.router.addToQueue(filepaths)
        self.collect_thread.start()

    @Slot()
    def collectionComplete(self):
        self.loadingLabel.hide()
        self.completedLabel.show()
        self.collect_thread.quit()

    @Slot()
    def receiveAsset(self, asset):
        if not asset:
            return
        asset.id = self.collect_item_model.rowCount()
        self.collectedListView.addAsset(asset)

    def setCategoryView(self, dock, layout):
        self.categorizeFrame.layout().insertWidget(0, dock)
        self.category_dock = dock
        self.category_widgets = []
        for index in range(self.categoryComboBox.count()):
            self.category_widgets.append(layout.itemAt(index).widget()) 

    @Slot()
    def updateLabelCounts(self, value):
        self.done = 0
        for i in range(self.collect_item_model.rowCount()):
            if self.collectedListView.isRowHidden(i):
                self.done += 1

        collected = self.collect_item_model.rowCount()
        if isinstance(value, int):
            self.todo = (value + 1)
        collect_msg = 'Collected : {}/{}'.format(collected, self.todo)
        self.collectedLabel.setText(collect_msg)
        assets_msg = 'Processed : {}/{}'.format(self.done, self.todo)
        self.newAssetsLabel.setText(assets_msg)
        if len(self.ingest_thread.queue) == 0 and self.done == self.todo:
            self.nextButton.setText('Finish')
            self.next_enabled()

    def getConversionMap(self):
        """Setup an file-extension based conversion map
        to pass to a 'ConversionRouter()' ingestion thread.

        Returns
        -------
        dict
            the extensions as keys and functions in string form
            >>> {'.exr' : 'processHDR', '.mov' : 'processMOV'}
        """
        function_map = {}
        if self.moviesCheckBox.checkState():
            [function_map.update({ext:'processMOV'}) for ext in MOVIE_EXT]
        if self.texturesReferencesCheckBox.checkState():
            [function_map.update({ext:'processLDR'}) for ext in LDR_EXT]
            [function_map.update({ext:'processHDR'}) for ext in HDR_EXT]
        if self.rawCheckBox.checkState():
            [function_map.update({ext:'processRAW'}) for ext in RAW_EXT]
            [function_map.update({ext:'processFILM'}) for ext in FILM_EXT]
        if self.toolsCheckBox.checkState():
            [function_map.update({ext:'processTOOL'}) for ext in TOOLS_EXT]
        if self.lightsCheckBox.checkState():
            pass

        return function_map
        # [function_map[ext] = 'processGEO' for ext in GEO_EXT]
        #TODO: add standalone conversions for these:
        #LIGHT_EXT = ['.ies']
        #SHADER_EXT = ['.mtlx', '.osl', '.sbsar']
        #DCC_EXT = ['.ma', '.mb', '.max', '.hip']
        #TOOLS_EXT = ['.nk', '.mel', '.py', 'hda']

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
        # Clear the models.
        self.collect_item_model.clear()
        self.new_asset_item_model.clear()
        self.collectPathTextEdit.clear()
        #self.ingest_thread.stop()
        #self.ingest_thread.quit()
        #if hasattr(self, 'collect_thread'):
        #    self.collect_thread.stop()
        #    self.collect_thread.quit()
        self.parent().close()

    @Slot()
    def onCategoryChange(self, value):
        """Fetch Assets in active Category 
        and set the naming and categorization views"""
        category_name = self.categoryComboBox.currentText().lower()
        category_index = self.categoryComboBox.currentIndex()
        for index, category in enumerate(self.category_widgets):
            if index == category_index:
                category.expandState()
                category.show()
            else:
                category.collapseState()
                category.hide()

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
                index_number = int(index)
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

    @Slot()
    def reprocessImage(self):
        pool = QThreadPool.globalInstance()
        for index in self.collectedListView.selectedIndexes():
            temp_path, temp_asset = self.getCollectedPath(index)
            func = partial(applyImageModifications, temp_path, temp_asset)
            worker = TaskRunner(func)
            pool.start(worker)

    @Slot()
    def getColorMatrix(self):
        index = self.collectedListView.selectedIndexes()[-1]
        temp_path, temp_asset = self.getCollectedPath(index)
        if temp_asset.path.ext != '.exr' or not temp_asset.path.exists():
            msg = 'Wrong image format "{}" needs to be exr.'.format(temp_asset.path.stem)
            QMessageBox.information(self, 'Detection Failed', msg)
            return
        func = partial(detectColorChecker, str(temp_asset.path))
        worker = TaskRunner(func, signal=True)
        worker.signal.completed.connect(self.updateClipboard)
        pool = QThreadPool.globalInstance()
        pool.start(worker)

    @Slot(tuple)
    def updateClipboard(self, ccm):
        clipboard = QApplication.clipboard()
        if ccm:
            clipboard.setText(json.dumps(ccm))
        else:
            msg = 'Was unable to auto-detect a colorchecker within the selected image.'
            QMessageBox.information(self, 'Detection Failed', msg)
            clipboard.clear()

    @Slot()
    def alignBlendExposures(self):
        indices = self.collectedListView.selectedIndexes()
        if len(indices) < 2:
            msg = 'Select more than one asset.'
            QMessageBox.information(self, 'Invalid Selection', msg)
            return

        # Pack the data by path key.
        assets_by_file = {k:v for k, v in map(self.getCollectedPath, indices)}
        # Hide the extra bracketed exposure assets.
        [self.collectedListView.setRowHidden(x.row(), True) for x in indices[1:]]
        self.updateLabelCounts(None)
        worker = TaskRunner(partial(blendRawExposures, assets_by_file))
        pool = QThreadPool.globalInstance()
        pool.start(worker)