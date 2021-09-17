import os
from functools import partial

from sequencePath import sequencePath as Path

from library.ui.ingestion import Ui_IngestForm
from library.io.ingest import ConversionRouter, IngestionThread
from library.objectmodels import (polymorphicItem, db, references, modeling,
                                elements, lighting, shading, software, alusers,
                                mayatools, nuketools, relationships, temp_asset, tags)
from library.widgets.assets import assetItemModel
from library.widgets.util import ListViewFiltered

from library.config import (MOVIE_EXT, SHADER_EXT, RAW_EXT, LDR_EXT, HDR_EXT,
                            LIGHT_EXT, DCC_EXT, TOOLS_EXT, GEO_EXT, RELIC_PREFS)

from PySide6.QtCore import (Property, QEvent, QFile, QItemSelectionModel,
                            QMargins, QObject, QPoint, QPropertyAnimation,
                            QRect, QRegularExpression, QSize,
                            QSortFilterProxyModel, Qt, QTextStream, Signal,
                            Slot, QThread)
from PySide6.QtGui import (QAction, QColor, QCursor, QFont, QFontMetrics,
                           QIcon, QPainter, QPixmap, QMovie, QImage,
                           QRegularExpressionValidator, QStandardItemModel, Qt)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QBoxLayout,
                               QDialog, QDockWidget, QFrame, QLabel, QLayout,
                               QLineEdit, QListView, QMenu, QScrollArea,
                               QStyledItemDelegate, QTreeView, QVBoxLayout,
                               QWidget, QMessageBox)

CLOSE_MSG = """
You have not completed categorizing the collected files.
The remaining unprocessed files will be lost.

Are you sure you want to cancel and close?
"""

class SimpleAsset(object):
    __slots__ = ['name', 'id']
    def __init__(self, name, id):
        self.name = name
        self.id = id


class IngestForm(Ui_IngestForm, QDialog):

    beforeClose = Signal(QWidget)

    def __init__(self, *args, **kwargs):
        super(IngestForm, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.nextButton.clicked.connect(self.nextStage)
        self.next_enabled = partial(self.nextButton.setEnabled, True)
        self.next_disabled = partial(self.nextButton.setEnabled, False)
        self.collectedListView.compactMode()
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
        inplace_update = lambda x: x.update() 
        self.ingest_thread.itemDone.connect(inplace_update)
        self.loadingLabel.setAttribute(Qt.WA_TranslucentBackground, True)
        self.loading_movie = QMovie(':resources/general/load_wheel_24.webp')
        self.loading_movie.setCacheMode(QMovie.CacheAll)
        self.loading_movie.start()
        self.loadingLabel.setMovie(self.loading_movie)
        self.loadingLabel.hide()
        self.completedLabel.hide()
        self.keep_original_name = False 

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
        subcategory = self.selectedSubcategory
        collected_indices = self.collectedListView.selectedIndexes()
        if not subcategory or not collected_indices:
            msg = 'Selection of a Subcategory & collected Asset is requried.'
            QMessageBox.information(self, 'Empty Selection', msg)
            return

        self.collectedListView.clearSelection()

        category_name = self.categoryComboBox.currentText().lower()
        category_id = self.categoryComboBox.currentIndex()
        asset_constructor = globals()[category_name]
        total = len(collected_indices)
        if isinstance(item, SimpleAsset): # Linking to an existing item
            primary_asset = asset_constructor(name=item.name, id=item.id)
            primary_asset.fetch()
            link_primary = True
        for num, index in enumerate(collected_indices):
            temp_asset = index.data(polymorphicItem.Object)
            asset = asset_constructor(*temp_asset.values)
            for attr in temp_asset.attrs:
                if hasattr(asset, attr):
                    setattr(asset, attr, getattr(temp_asset, attr))

            asset.links = (subcategory.relationMap, subcategory.id)

            if num == 0 and isinstance(item, str):
                primary_asset = asset
                asset.name = item
                asset.type = 3 # Collection
                #asset.dependencies = (total - 1)
                link_primary = False
                reverse_link = False
            else:
                if not asset.type == 5:
                    asset.name = '{}_{}'.format(primary_asset.name, num)
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
            extra_files = temp_asset.dependencies
            self.ingest_thread.load([temp_filename, asset, extra_files])

        # Update counts on assets and subcategory
        subcategory.count += total
        if dependency := primary_asset.dependencies:
            dependency += total
        elif reverse_link:
            primary_asset.dependencies += total
        else:
            primary_asset.dependencies = (total - 1)

        primary_asset.update()
        subcategory.update(fields=['count'])

    @property
    def selectedSubcategory(self):
        tab = self.category_widgets[self.categoryComboBox.currentIndex()]
        if selection := tab.category.tree.selectedIndexes():
            #item = tab.category.tree.indexToItem(selection[0])
            return selection[0].data(polymorphicItem.Object)

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
        if self.done == self.todo:
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
                asset_obj = SimpleAsset(*asset)
                asset_item = polymorphicItem(fields=asset_obj)
                self.existingNamesList.itemModel.appendRow(asset_item)

