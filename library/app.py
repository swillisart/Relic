import ctypes
import math
import os
import sys
from functools import partial
import webbrowser

# -- Third-party --
from PySide6.QtCore import Slot, QPoint, QModelIndex, QThreadPool
from PySide6.QtGui import QPixmap, QImage, QFontDatabase, QFont, QIcon, QColor, Qt, QTextDocument, QTextCursor
from PySide6.QtWidgets import (QApplication, QMainWindow, QSystemTrayIcon,
    QMenu, QWidget, QSizePolicy,QFrame, QGraphicsDropShadowEffect, QLabel, QTextBrowser)

# -- First-party --
from sequencePath import sequencePath as Path
from strand import server

# -- Module --
from library.ui.dialog import Ui_RelicMainWindow
from library.config import RELIC_PREFS, peakPreview
from library.objectmodels import Library, db, polymorphicItem, getCategoryConstructor, alusers
from library.widgets.assets import assetItemModel, assetListView
from library.asset_grid import AssetGridView
from library.widgets.subcategoriesViews import ExpandableTab, CategoryManager
from library.widgets.metadataView import metadataFormView
from library.widgets.relationshipView import LinkViewWidget
from library.widgets.util import DialogOverlay
from library.widgets.ingest import IngestForm
from library.io.database import LocalThumbnail


description_style = """
<style type="text/css">
table {
    border-width: 12px;
    border-style: solid;
    border-color: rgb(64,64,64);
    border-collapse: collapse;
    border-top: 2px solid #00cccc;
}
td, th {
  padding: 6;
  text-align: left;
}
body {
  padding:50px;
  margin:auto auto;
}
</style>
"""

CATEGORIES = []
PAGE_LIMIT = int(RELIC_PREFS.assets_per_page)

class RelicMainWindow(Ui_RelicMainWindow, QMainWindow):
    def __init__(self, *args, **kwargs):
        super(RelicMainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.app_icon = QIcon(':/resources/app/app_icon.svg')
        self.tray = QSystemTrayIcon(self.app_icon, self)
        self.tray.activated.connect(self.toggleVisibility)
        self.tray.show()
        self.pool = QThreadPool.globalInstance()
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
        self.buttonGroup.buttonClicked.connect(self.updateAssetView)

        category_widgets = self.category_manager.assembleCategories(self.library.categories)
        for index, category in enumerate(category_widgets):
            category.verticalControl.hide()
            self.categoryLayout.insertWidget(index, category)

        self.categoryDock.setTitleBarWidget(self.dockTitleFrame)
        self.attributeDock.setTitleBarWidget(self.attributeDockTitle)
        self.linksDock.setTitleBarWidget(self.linkDockTitle)
        self.linksDock.hide()

        # Shadow graphics
        shadow = QGraphicsDropShadowEffect(self, blurRadius=6.0,
                color=QColor(31, 31, 31), offset=QPoint(0, 0))
        self.categoryDock.setGraphicsEffect(shadow)
        shadow = QGraphicsDropShadowEffect(self, blurRadius=6.0,
                color=QColor(31, 31, 31), offset=QPoint(0, 0))
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
        self.centralwidget.layout().insertWidget(2, self.assets_view)

        self.assets_grid = AssetGridView(PAGE_LIMIT, 30, self)
        self.assets_grid.base_model = self.asset_item_model
        self.assets_grid.hide()
        self.asset_item_model.rowsInserted.connect(self.assets_grid.onRowsInserted)
        self.asset_item_model.modelReset.connect(self.assets_grid.clear)
        self.centralwidget.layout().insertWidget(3, self.assets_grid)
        self.links_view = LinkViewWidget(self)
        self.metatdata_view = metadataFormView(self)
        self.metatdata_view.openDescription.connect(self.showMarkdown)
        self.attributesLayout.addWidget(self.metatdata_view)
        #self.attributeDock.setWidget(self.metatdata_view)
        self.linksDock.setWidget(self.links_view)

        # Signals / Slots
        self.filterBox.textChanged.connect(self.category_manager.filterAll)
        self.linkFilterBox.textChanged.connect(self.links_view.filterAll)
        self.actionPortal.toggled.connect(self.hideDocks)
        self.actionIngest.triggered.connect(self.beginIngest)
        self.descriptionCloseButton.clicked.connect(self.closeOverlay)
        self.actionDocumentation.triggered.connect(self.browseDocumentation)

        self.attrExpandButton.toggled.connect(self.attributeDock.widget().setVisible)
        self.categoryExpandButton.toggled.connect(self.categoryDock.widget().setVisible)
        self.assets_view.selmod.selectionChanged.connect(self.loadAssetData)
        self.assets_view.onLinkLoad.connect(self.loadLinkData)
        self.backButton.clicked.connect(self.assetViewing)
        self.documentationFilterBox.textChanged.connect(self.searchPage)
        self.documentationFilterBox.returnPressed.connect(self.findNextInPage)
        self.viewScaleSlider.valueChanged.connect(self.scaleView)
        db.accessor.imageStreamData.connect(self.updateIcons)
        self.viewScaleSlider.setValue(int(RELIC_PREFS.view_scale))
        self.actionAdministration_Mode.setChecked(int(RELIC_PREFS.edit_mode))

        self.documentationDock.setTitleBarWidget(self.documentationDockTitle)
        self.documentationDock.hide()
        self.documentationDock.setAutoFillBackground(True)
        user = alusers(name=os.getenv('username'))
        user_exists = RELIC_PREFS.user_id
        if not user_exists: # user not cached local OR does not exist
            user_id = user.nameExists()
            if not user_id: # user has not been created yet
                user.create()
                RELIC_PREFS.user_id = user.id
            else:
                RELIC_PREFS.user_id = user_id


    @Slot()
    def scaleView(self, value):
        if value == 0:
            self.attributeDock.hide()
            self.assets_view.hide()
            self.assets_grid.show()
        if value == 1:
            self.assets_view.show()
            self.attributeDock.show()
            self.assets_view.compactMode()
            grid_visible = self.assets_grid.isVisible()
            self.assets_grid.hide()
            if grid_visible:
                self.updateAssetView()
        elif value == 2:
            self.assets_grid.hide()
            self.assets_view.show()
            self.attributeDock.show()
            self.assets_view.iconMode()

        RELIC_PREFS.view_scale = value

    @Slot(str)
    def showMarkdown(self, md_path):
        if not os.path.exists(md_path):
            return
        self.assets_view.hide()
        with open(md_path, 'r') as md_text:
            self.documentationTextBrowser.setMarkdown(md_text.read())
        html_from_markdown = self.documentationTextBrowser.toHtml()
        self.documentationTextBrowser.setHtml(description_style + html_from_markdown)
        self.overlay = DialogOverlay(self, self.documentationDock)

    def closeOverlay(self):
        if self.overlay:
            self.assets_view.show()
            self.removeEventFilter(self.overlay)
            self.overlay.close()

    @Slot()
    def searchPage(self, text):
        textCursor = self.documentationTextBrowser.textCursor()
        textCursor.movePosition(QTextCursor.Start, QTextCursor.MoveAnchor, 1)
        self.documentationTextBrowser.setTextCursor(textCursor)
        self.documentationTextBrowser.find(text)

    @Slot()
    def findNextInPage(self):
        self.documentationTextBrowser.find(self.documentationFilterBox.text())

    @Slot()
    def beginIngest(self):
        self.assets_view.hide()
        ingest = IngestForm()
        self.verticalSpacer.changeSize(0, 0, QSizePolicy.Minimum, QSizePolicy.Minimum) 
        ingest.setCategoryView(self.categoryDock, self.categoryLayout)
        ingest.beforeClose.connect(self.onIngestClosed)
        self.category_manager.blockSignals(True)
        DialogOverlay(self, ingest, modal=False)
        return ingest

    @Slot()
    def externalPluginCommand(self, asset_data):
        ingest = self.beginIngest()
        ingest.collectAssets(asset_data)

    @Slot()
    def browseTo(self, path):
        """Auto browses to the path supplied through 3 sections,
        Category / Subcategory / Asset

        Parameters
        ----------
        path : str
            relative path to asset EXAMPLE: "relic://4/cars/F150"
        """
        try:
            _, _, _category, _id, subcategory, name = path.split('/')
        except:
            return
        category_id = int(_category)
        asset_id = int(_id)
        # Set the UI to reflect our asset category.
        for category in self.library.categories:
            if category.id == category_id:
                category.tab.expandState()
                # Scroll to the subcategory tree item in UI.
                category.tree.findInTree(subcategory)
            else:
                category.tab.collapseState()
        self.assets_view.clear()

        # construct our asset and add it to the main view. 
        asset_constructor = getCategoryConstructor(category_id)
        asset = asset_constructor()
        asset.fetch(id=asset_id)
        asset.category = category_id
        self.assets_view.addAsset(asset)
        asset.fetchIcon()
        asset.related(noassets=True)
        self.metatdata_view.loadAssets([asset])

    @Slot()
    def onIngestClosed(self, dock):
        self.assets_view.show()
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)
        self.category_manager.blockSignals(False)
        try:
            self.verticalSpacer.changeSize(0, 0, QSizePolicy.Minimum, QSizePolicy.MinimumExpanding) 
        except:pass

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

    @Slot()
    def assetViewing(self):
        self.links_view.clear()
        self.linksDock.hide()
        self.assets_view.show()

    @Slot()
    def updateAssetView(self, obj=None):
        sender = self.sender()
        if self.assets_view.editor:
            self.assets_view.editor.close()
        self.pool.clear()
        if isinstance(obj, dict):
            categories = obj.copy()
        else:
            categories = self.category_manager.selected_subcategories.copy()

        # Only re-query the database if the searchbox has changed
        new_search = False

        categories_to_search = self.library.validateCategories(categories)
        # Split text into list of search term keywords
        text = self.searchBox.text()
        if text:
            categories_to_search['keywords'] = text.split(' ')
        use_collections = self.collectionRadioButton.isChecked()
        categories_to_search['exclude_type'] = 5 if use_collections else 3
        new_search = self.library.search(categories_to_search)
        asset_total = len(self.library.assets)
            
        self.assets_view.clear()

        if new_search or sender not in [self.searchBox, self.category_manager]:
            page = self.pageSpinBox.value()
            skip_icons = not self.assets_grid.isVisible()
            for asset in self.library.load(page, PAGE_LIMIT, categories, icons=skip_icons):
                on_complete = partial(setattr, asset, 'icon')
                if skip_icons:
                    worker = LocalThumbnail(asset.network_path.suffixed('_icon', '.jpg'), on_complete)
                    self.pool.start(worker)
                self.assets_view.addAsset(asset)
            asset_total = len(self.library.assets_filtered)

            self.assets_view.scrollTo(self.assets_view.model.index(0, 0, QModelIndex()))
        page_count = math.ceil(asset_total / PAGE_LIMIT) or 1
        self.pageSpinBox.setSuffix('/' + str(page_count))
        self.pageSpinBox.setMaximum(page_count)
        msg = 'Search results: {} Assets...'.format(asset_total)
        self.statusbar.showMessage(msg)

    @Slot()
    def loadAssetData(self, selection):
        sender = self.sender()
        if sender.parent().drag_select:
            # Better multi-select performance
            return

        indexes = self.assets_view.selectedIndexes()

        indexes = set(self.assets_view.selectedIndexes())
        [indexes.add(x) for x in selection.indexes()]

        assets = [x.data(polymorphicItem.Object) for x in indexes]
        if assets:
            asset = assets[-1] 
            asset.related(noassets=True)
            self.metatdata_view.loadAssets(assets)
            if self.previewCheckBox.isChecked():
                path = asset.network_path
                peakPreview(path)

    @Slot()
    def loadLinkData(self, index):
        """Load related assets via links from relationships.

        Parameters
        ----------
        index : QModelIndex
            the index which this slot connects to
        """

        self.assets_view.hide()

        indices = set(self.assets_view.selectedIndexes())
        indices.add(index)

        linked_assets = []
        for index in indices:
            asset = index.data(polymorphicItem.Object)
            asset.related()
            linked_assets.extend(asset.upstream)

        self.links_view.updateGroups(linked_assets, clear=True)
        self.linksDock.show()

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
        RELIC_PREFS.edit_mode = int(toggle)

    @Slot()
    def browseDocumentation(self):
        site = RELIC_PREFS.host
        url = f'{site}documentation/index.html'
        webbrowser.open(url)

def onStateChange(state):
    if state == Qt.ApplicationState.ApplicationActive:
        db.accessor.makeConnection()

def main(args):
    app = qApp or QApplication(sys.argv)
    ctypes.windll.kernel32.SetConsoleTitleW("Relic")
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(u"resarts.relic")
    window = RelicMainWindow()
    # Startup the plugin server
    ingest_server = server.StrandServer('relic')
    ingest_server.incomingData.connect(window.externalPluginCommand)
    ingest_server.incomingFile.connect(window.browseTo)
    window.resize(1600, 925)
    window.show()
    if args:
        if args.path:
            window.browseTo(args.path)
    app.applicationStateChanged.connect(onStateChange)
    sys.exit(app.exec_())
