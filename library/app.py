import ctypes
import math
import os
import sys

# -- Third-party --
from PySide6.QtCore import Slot, QPoint, QModelIndex
from PySide6.QtGui import QFontDatabase, QFont, QIcon, QColor, Qt
from PySide6.QtWidgets import (QApplication, QMainWindow, QSystemTrayIcon,
    QMenu, QWidget, QSizePolicy, QGraphicsDropShadowEffect)

# -- First-party --
from sequencePath import sequencePath as Path

# -- Module --
from library.ui.dialog import Ui_RelicMainWindow
from library.config import relic_preferences
from library.objectmodels import Library, db, polymorphicItem
from library.widgets.assets import assetItemModel, assetListView
from library.widgets.subcategoriesViews import ExpandableTab, CategoryManager
from library.widgets.metadataView import metadataFormView
from library.widgets.relationshipView import LinkViewWidget
from kohainetwork.client import KohaiClient

KOHAI = KohaiClient()

class RelicMainWindow(Ui_RelicMainWindow, QMainWindow):
    def __init__(self, *args, **kwargs):
        super(RelicMainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.app_icon = QIcon(':/resources/icons/app_icon.svg')
        self.tray = QSystemTrayIcon(self.app_icon, self)
        self.tray.activated.connect(self.toggleVisibility)
        self.tray.show()
        #self.tray.showMessage('Relic', 'Relic is now running...', self.app_icon, 2)
        # Assign the dock's title bar to search widget 
        # then set the dock's widget to an empty widget so separators disappear
        empty_widget = QWidget(self)
        empty_widget.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed))
        self.searchDock.setTitleBarWidget(self.searchDock.widget())
        self.searchDock.setWidget(empty_widget)
        self.resizeDocks([self.searchDock], [0], Qt.Horizontal) # (QTBUG-65592) fixes dock resize
        self.library = Library()
        self.category_manager = CategoryManager(self)
        self.category_manager.onSelection.connect(self.updateAssetView)
        self.searchBox.returnPressed.connect(self.updateAssetView)
        self.pageSpinBox.valueChanged.connect(self.updateAssetView)

        category_layout = self.categoryScrollAreaWidgetContents.layout()
        for index, category in enumerate(self.category_manager.createCategories(self.library.categories)):
            category_layout.insertWidget(index, category)
 
        self.categoryDock.setTitleBarWidget(self.dockTitleFrame)
        self.attributeDock.setTitleBarWidget(self.attributeDockTitle)
        self.linksDock.setTitleBarWidget(self.linkDockTitle)
        self.linksDock.hide()

        # Shadow graphics
        shadow = QGraphicsDropShadowEffect(self, blurRadius=6.0,
                color=QColor(31, 31, 31), offset=QPoint(0, 0))
        self.categoryDock.setGraphicsEffect(shadow)
        shadow = QGraphicsDropShadowEffect(self, blurRadius=8.0,
                color=QColor(31, 31, 31), offset=QPoint(1, 1))
        self.attributeDock.setGraphicsEffect(shadow)
        shadow = QGraphicsDropShadowEffect(self, blurRadius=8.0,
                color=QColor(31, 31, 31), offset=QPoint(0, 0))
        self.linksDock.setGraphicsEffect(shadow)
        self.attributeDock.setAutoFillBackground(True)
        self.categoryDock.setAutoFillBackground(True)
        self.linksDock.setAutoFillBackground(True)


        # Creates asset view
        self.assets_view = assetListView(self)
        self.asset_item_model = assetItemModel(self.assets_view)
        self.assets_view.setModel(self.asset_item_model)
        self.centralwidget.layout().insertWidget(2, self.assets_view)

        self.links_view = LinkViewWidget(self)
        self.metatdata_view = metadataFormView(self)
        self.attributeDock.setWidget(self.metatdata_view)
        self.linksDock.setWidget(self.links_view)

        # Signals / Slots
        self.filterBox.textChanged.connect(self.category_manager.filterAll)
        self.linkFilterBox.textChanged.connect(self.links_view.filterAll)
        self.actionPortal.toggled.connect(self.hideDocks)
        self.attrExpandButton.toggled.connect(self.attributeDock.widget().setVisible)
        self.categoryExpandButton.toggled.connect(self.categoryDock.widget().setVisible)
        self.assets_view.selmod.selectionChanged.connect(self.loadAssetData)
        self.assets_view.onLinkLoad.connect(self.loadLinkData)
        self.backButton.clicked.connect(self.assetViewing)

        db.accessor.imageStreamData.connect(self.updateIcons)
        self.actionAdministration_Mode.setChecked(int(relic_preferences.edit_mode))

    def hideDocks(self, state):
        self.categoryExpandButton.setChecked(state)
        self.attrExpandButton.setChecked(state)

    @Slot()
    def updateIcons(self, data):
        img, id = data
        models = [self.links_view.model, self.assets_view.model]
        for model in models:
            for i in range(model.rowCount()):
                index = model.index(i, 0)
                item = model.itemFromIndex(index)
                if item.id == id:
                    item.icon = img
                    item.emitDataChanged()

    def loadAssetPreview(self, asset):
        path = str(asset.local_path)
        KOHAI.requestFileLoad(path)
        if KOHAI.errored:
            #TODO: launch Kohai 
            pass

    @Slot()
    def assetViewing(self):
        self.links_view.clear()
        self.linksDock.hide()
        self.assets_view.show()

    @Slot()
    def updateAssetView(self, obj=None):
        sender = self.sender()
        if isinstance(obj, dict):
            categories = obj.copy()
        else:
            categories = self.category_manager.selected_subcategories.copy()

        # Only re-query the database if the searchbox has changed
        new_search = False
        limit = int(relic_preferences.assets_per_page)

        # Split text into list of search term keywords
        text = self.searchBox.text()
        terms = text.split(' ') if text else None
        new_search = self.library.search(terms, categories)
        asset_total = len(self.library.assets)
            
        self.assets_view.clear()

        if new_search or sender not in [self.searchBox, self.category_manager]:
            page = self.pageSpinBox.value()

            for item in self.library.load(page, limit, categories):
                self.assets_view.addItem(item)
            asset_total = len(self.library.assets_filtered)

            self.assets_view.scrollTo(self.assets_view.model.index(0, 0, QModelIndex()))
        page_count = math.ceil(asset_total / limit) or 1
        self.pageSpinBox.setSuffix('/' + str(page_count))
        self.pageSpinBox.setMaximum(page_count)
        msg = 'Search results: {} Assets...'.format(asset_total)
        self.statusbar.showMessage(msg)

    @Slot()
    def loadAssetData(self, selection):
        sender = self.sender()
        indexes = selection.indexes()

        if indexes:
            asset = indexes[0].data(polymorphicItem.Object)
            asset.related(noassets=True)
            self.metatdata_view.loadAsset(asset)
            if self.previewCheckBox.isChecked():
                self.loadAssetPreview(asset)

    @Slot()
    def loadLinkData(self, index):
        """Load related assets via links from relationships.

        Parameters
        ----------
        index : QModelIndex
            the index which this slot connects to
        """

        self.assets_view.hide()
        self.linksDock.show()

        indices = set(self.assets_view.selectedIndexes())
        indices.add(index)

        for index in indices:
            asset = index.data(polymorphicItem.Object)
            asset.related()
            self.links_view.updateGroups(asset.upstream)

    @Slot()
    def toggleVisibility(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.grab()
            self.setVisible(not self.isVisible())
            self.activateWindow()
            self.raise_()

    @Slot()
    def toggleAdminMode(self, toggle):
        #TODO: query the databse for permissions level
        print(relic_preferences.edit_mode)
        relic_preferences.edit_mode = int(toggle)


def main(args):
    app = qApp or QApplication(sys.argv)
    ctypes.windll.kernel32.SetConsoleTitleW("Relic")
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(u"resarts.relic")
    window = RelicMainWindow()
    window.resize(1500, 925)
    window.show()
    sys.exit(app.exec_())
