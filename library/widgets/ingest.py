import os
from functools import partial

from library.ui.ingestion import Ui_IngestForm
from library.io.ingest import ConversionRouter, IngestionThread
from library.objectmodels import (polymorphicItem, db, references, modeling,
                                elements, lighting, shading, software, 
                                mayatools, nuketools, relationships)
from library.widgets.assets import assetItemModel
from library.widgets.util import ListViewFiltered
from library.config import (MOVIE_EXT, SHADER_EXT, RAW_EXT, LDR_EXT, HDR_EXT,
                            LIGHT_EXT, APP_EXT, TOOLS_EXT)

from PySide6.QtCore import (Property, QEvent, QFile, QItemSelectionModel,
                            QMargins, QObject, QPoint, QPropertyAnimation,
                            QRect, QRegularExpression, QSize,
                            QSortFilterProxyModel, Qt, QTextStream, Signal,
                            Slot, QThread)
from PySide6.QtGui import (QAction, QColor, QCursor, QFont, QFontMetrics,
                           QIcon, QPainter, QPixmap,
                           QRegularExpressionValidator, QStandardItemModel, Qt)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QBoxLayout,
                               QDialog, QDockWidget, QFrame, QLabel, QLayout,
                               QLineEdit, QListView, QMenu, QScrollArea,
                               QStyledItemDelegate, QTreeView, QVBoxLayout,
                               QWidget, QMessageBox)

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
        #self.collectedListView.actionDelete.connect()
        self.existingNamesList.newItem.connect(self.setIngestQueue)
        self.existingNamesList.linkItem.connect(self.setIngestQueue)
        self.todo = 0
        self.ingest_thread = IngestionThread(self)
        inplace_update = lambda x: x.update() 
        self.ingest_thread.itemDone.connect(inplace_update)


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
            asset.links = (subcategory.relationMap, subcategory.id)

            if num == 0 and isinstance(item, str):
                primary_asset = asset
                asset.name = item
                asset.type = 3 # Collection
                #asset.dependencies = (total - 1)
                link_primary = False
            else:
                asset.name = '{}_{}'.format(primary_asset.name, num)
                asset.type = 5 # Variant
                link_primary = True

            # store the associated temp on-disk id for copying. 
            file_id = str(asset.id)
            asset.id = None # IMPORTANT clears the id for clean asset creation
            asset.create()
            asset.fetch(id=asset.id)

            # Re-apply the GUI attributes for our item's QPainter. 
            asset.icon = temp_asset.icon
            asset.path = temp_asset.path
            asset.category = category_id
            asset.subcategory = subcategory

            if link_primary:
                primary_relation = relationships(
                    category_map=asset.relationMap,
                    category_id=asset.id,
                    link=primary_asset.links,
                )
                primary_relation.create()

            self.collectedListView.setRowHidden(index.row(), True)
            self.newAssetListView.addItem(asset)
            self.ingest_thread.load([file_id, asset])

        # Update counts on assets and subcategory
        subcategory.count += total
        if dependency := primary_asset.dependencies:
            dependency += total
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
            self.categorizeTab.setEnabled(True)
            self.next_disabled()
            self.collect()
        self.tabWidget.setCurrentIndex(stage+1)
    
    def collect(self):
        paths = self.collectPathTextEdit.toPlainText().split('\n')
        function_map = self.getConversionMap()

        self.collect_thread = QThread(self)
        self.router = ConversionRouter(function_map)
        self.router.moveToThread(self.collect_thread)
        self.router.finished.connect(self.collect_thread.quit)
        self.router.progress.connect(self.receiveAsset)
        self.router.started.connect(self.updateLabelCounts)
        self.collect_thread.started.connect(self.router.run)
        self.router.addToQueue(paths)
        self.collect_thread.start()

    @Slot()
    def receiveAsset(self, asset):
        if asset:
            asset.id = self.collect_item_model.rowCount()
            self.collectedListView.addItem(asset)

    def setCategoryView(self, dock, layout):
        self.categorizeFrame.layout().insertWidget(0, dock)
        self.category_dock = dock
        self.category_widgets = []
        for index in range(self.categoryComboBox.count()):
            self.category_widgets.append(layout.itemAt(index).widget()) 
        self.onCategoryChange(0)

    @Slot()
    def updateLabelCounts(self, value):
        done = self.new_asset_item_model.rowCount()
        collected = self.collect_item_model.rowCount()
        if isinstance(value, int):
            self.todo = (value + 1)
        collect_msg = 'Files Collected : {}/{}'.format(collected, self.todo)
        self.collectedLabel.setText(collect_msg)
        assets_msg = 'New Assets : {}/{}'.format(done, self.todo)
        self.newAssetsLabel.setText(assets_msg)

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

        if self.lightsCheckBox.checkState():
            pass

        return function_map
        # [function_map[ext] = 'processGEO' for ext in GEO_EXT]
        #TODO: add standalone conversions for these:
        #LIGHT_EXT = ['.ies']
        #SHADER_EXT = ['.mtlx', '.osl', '.sbsar']
        #APP_EXT = ['.ma', '.mb', '.max', '.hip']
        #TOOLS_EXT = ['.nk', '.mel', '.py', 'hda']

    def close(self):
        # make all category widgets visible again
        [category.show() for category in self.category_widgets]
        self.beforeClose.emit(self.category_dock)
        self.ingest_thread.stop()
        self.ingest_thread.quit()
        if hasattr(self, 'collect_thread'):
            self.collect_thread.quit()
        super(IngestForm, self).close()
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

