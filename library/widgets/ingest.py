import json
from functools import partial

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
                            SHADER_EXT, TOOLS_EXT)
from library.io.ingest import (INGEST_PATH, TaskRunner, ConversionRouter, IngestionThread,
                               applyImageModifications, blendRawExposures)
from library.objectmodels import (alusers, db, elements, lighting, mayatools,
                                  modeling, nuketools, polymorphicItem,
                                  references, relationships, shading, software,
                                  tags, temp_asset)
from library.ui.ingestion import Ui_IngestForm
from library.widgets.assets import assetItemModel
from library.widgets.util import ListViewFiltered, SimpleAsset

CLOSE_MSG = """
You have not completed categorizing the collected files.
The remaining unprocessed files will be lost.

Are you sure you want to cancel and close?
"""

def uniqueNameIncrement(asset):
    """Increments name value until it reaches a unique name.

    Parameters
    ----------
    asset : BaseFields 
        asset object

    Returns
    -------
    BaseFields
        asset object result with incremented unique name.
    """
    exists = asset.nameExists()
    if exists:
        if '_' in asset.name:
            base, num = asset.name.split('_')
            upnumber = int(num) + 1
            asset.name =  f'{base}_{upnumber}'
        else:
            base = asset.name
            asset.name = f'{base}_1'

        return uniqueNameIncrement(asset)
    else:
        return asset

class IngestForm(Ui_IngestForm, QDialog):

    beforeClose = Signal(QWidget)

    def __init__(self, *args, **kwargs):
        super(IngestForm, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.nextButton.clicked.connect(self.nextStage)
        self.next_enabled = partial(self.nextButton.setEnabled, True)
        self.next_disabled = partial(self.nextButton.setEnabled, False)
        self.collectedListView.compactMode()
        self.actionGetMatrix = QAction('Get Color Matrix', self)
        #self.actionDenoise = QAction('Denoise', self)
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
        self.collectedListView.onDeleted.connect(self.updateLabelCounts)
        self.existingNamesList.newItem.connect(self.setIngestQueue)
        self.existingNamesList.linkItem.connect(self.setIngestQueue)
        self.todo = 0
        self.done = 0
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
        self.keep_original_name = False 

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

    def collectAssets(self, assets):
        self.categorizeTab.setEnabled(True)
        self.tabWidget.setCurrentIndex(1)
        self.keep_original_name = True
        
        for fields in assets:
            asset = temp_asset(**fields)
            asset.path = Path(asset.path)
            icon_path = asset.path.suffixed('_icon', ext='.jpg')
            asset.icon = QPixmap.fromImage(QImage(str(icon_path)))
            self.collectedListView.addAsset(asset)
        self.updateLabelCounts(len(assets)-1)

    @Slot()
    def setIngestQueue(self, item):
        subcategory_index = self.selectedSubcategory
        collected_indices = self.collectedListView.selectedIndexes()
        if not subcategory_index or not collected_indices:
            msg = 'Selection of a Subcategory & collected Asset is requried.'
            QMessageBox.information(self, 'Empty Selection', msg)
            return
        subcategory = subcategory_index.data(polymorphicItem.Object)
        self.collectedListView.clearSelection()

        category_name = self.categoryComboBox.currentText().lower()
        category_id = self.categoryComboBox.currentIndex()
        asset_constructor = globals()[category_name]
        total = len(collected_indices)
        if isinstance(item, SimpleAsset): # Linking to an existing item
            primary_asset = asset_constructor(name=item.name) 
            primary_asset_id = item.id
            if not primary_asset_id:
                primary_asset_id = primary_asset.nameExists()
            primary_asset.fetch(id=primary_asset_id)
            link_primary = True
        for num, index in enumerate(collected_indices):
            temp_asset = index.data(polymorphicItem.Object)
            asset = asset_constructor(*temp_asset.values)
            for attr in temp_asset.attrs:
                if hasattr(asset, attr):
                    setattr(asset, attr, getattr(temp_asset, attr))

            asset.links = (subcategory.relationMap, subcategory.id)

            if num == 0 and isinstance(item, str):
                asset.name = item
                exists = asset.nameExists()
                if exists:
                    asset.name = item
                    asset = uniqueNameIncrement(asset)
                    self.existingNamesList.addItem(asset.name, exists)
                    asset.type = 5 # Variant
                    primary_asset = asset_constructor(name=item, id=exists)
                    primary_asset.fetch(id=exists)
                    link_primary = True
                    reverse_link = False
                elif total > 1:
                    asset.name = item
                    asset = uniqueNameIncrement(asset)
                    primary_asset = asset_constructor(
                        name=item,
                        category=category_id,
                        subcategory=subcategory,
                        type=3,
                        path='{}/{}'.format(subcategory.name, item),
                        links=(subcategory.relationMap, subcategory.id),
                    )
                    primary_asset.create()
                    primary_asset.fetch(id=primary_asset.id)
                    asset.type = 5 # Variant
                    link_primary = True
                    reverse_link = False
                else:
                    primary_asset = None
                    asset.type = 2 # Asset
                    link_primary = False
                    reverse_link = False
            else:
                if not asset.type == 5:
                    asset.name = '{}_{}'.format(primary_asset.name, num + 1)
                    asset.type = 5 # Variant
                    link_primary = True
                    reverse_link = False
                else:
                    reverse_link = True

            # store the associated temp on-disk location for copying.
            if not self.keep_original_name:
                temp_filename = 'unsorted' + str(asset.id)
            else:
                temp_filename = asset.name

            asset = uniqueNameIncrement(asset)

            asset.dependencies = 0
            asset.id = None # IMPORTANT clears the id for clean asset creation
            asset.create()
            asset.fetch(id=asset.id)

            # Re-apply the GUI attributes for our item's QPainter. 
            asset.icon = temp_asset.icon
            asset.path = temp_asset.path
            asset.category = category_id
            asset.subcategory = subcategory

            if link_primary:
                asset.linkTo(primary_asset)
            if reverse_link:
                primary_asset.linkTo(asset)

            if temp_asset.links:
                for link in temp_asset.links:
                    link_relation = relationships(
                        category_map=int(link['category'])+4,
                        category_id=int(link['id']),
                        link=int(asset.links),
                    )
                    link_relation.create()
                asset.dependencies = len(temp_asset.links)
            if temp_asset.tags:
                for tag_data in temp_asset.tags:
                    tag = tags(**tag_data)
                    tag.id = tag.nameExists()
                    if not tag.id:
                        tag.create()
                    tag.linkTo(asset)

            user = alusers(id=int(RELIC_PREFS.user_id))
            user.linkTo(asset)

            self.collectedListView.setRowHidden(index.row(), True)
            self.newAssetListView.addAsset(asset)
            self.processLoadingLabel.show()
            extra_files = temp_asset.dependencies
            self.ingest_thread.load([temp_filename, asset, extra_files])

        # Update counts on assets and subcategories
        subcategory.count += total
        self.updateSubcategoryCounts(subcategory_index)
        subcategory.update(fields=['count'])
        if primary_asset:
            if primary_asset.dependencies or reverse_link:
                primary_asset.dependencies += total
            else:
                primary_asset.dependencies = total or 1
            primary_asset.update()

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
        self.keep_original_name = False 

        paths = self.collectPathTextEdit.toPlainText().split('\n')
        function_map = self.getConversionMap()

        self.collect_thread = QThread(self)
        self.router = ConversionRouter(function_map)
        self.router.moveToThread(self.collect_thread)
        self.router.finished.connect(self.collect_thread.quit)
        self.router.finished.connect(self.collectionComplete)
        self.router.progress.connect(self.receiveAsset)
        self.router.started.connect(self.updateLabelCounts)
        self.collect_thread.started.connect(self.router.run)
        self.router.addToQueue(paths)
        self.collect_thread.start()

    @Slot()
    def collectionComplete(self):
        self.loadingLabel.hide()
        self.completedLabel.show()

    @Slot()
    def receiveAsset(self, asset):
        if asset:
            asset.id = self.collect_item_model.rowCount()
            self.collectedListView.addAsset(asset)

    def setCategoryView(self, dock, layout):
        self.categorizeFrame.layout().insertWidget(0, dock)
        self.category_dock = dock
        self.category_widgets = []
        for index in range(self.categoryComboBox.count()):
            self.category_widgets.append(layout.itemAt(index).widget()) 
        #self.onCategoryChange(0)

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
        self.ingest_thread.stop()
        self.ingest_thread.quit()
        if hasattr(self, 'collect_thread'):
            self.collect_thread.quit()
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
        assets = db.accessor.doRequest('retrieveData/{}'.format(category_name))
        self.existingNamesList.itemModel.clear()
        if assets:
            for asset in assets:
                self.existingNamesList.addItem(*asset)

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
        if temp_asset.path.ext != '.exr' or not temp_asset.path.exists:
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