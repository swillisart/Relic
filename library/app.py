import ctypes
import math
import os
import subprocess
import sys
from collections import defaultdict
from functools import partial

# -- Third-party --
from PySide6.QtCore import (QItemSelectionModel, QModelIndex, QThreadPool,
                            QTimer, Slot, QSize, QPoint)
from PySide6.QtGui import QIcon, QPixmap, Qt, QImage, QShortcut, QKeySequence, QCursor
from PySide6.QtWidgets import (QApplication, QMainWindow, QSizePolicy,
                               QSystemTrayIcon, QToolButton, QWidget, QLabel)

from relic.local import Relational, Grouping
from relic.scheme import Table, AssetType, Classification
from relic.qt.widgets import DockTitle, GroupView, GroupBox
from relic.qt.delegates import BaseItemDelegate, ItemDispalyModes
from relic.qt.util import readAllContents, polymorphicItem
from relic.qt.expandable_group import ExpandableGroup

from sequence_path.main import SequencePath as Path
from intercom import Server

import library
from library.config import RELIC_PREFS, peakPreview
from library.io.util import LocalThumbnail
from library.objectmodels import (Library, alusers,
                                  attachLinkToAsset, getCategoryConstructor,
                                  relationships, session, subcategory)
# -- Module --
from library.ui.dialog import Ui_RelicMainWindow
from library.widgets import metadata_view, subcategoriesViews, description
from library.widgets.fields import ItemState
from library.widgets.assets_alt import AssetItemModel, AssetListView, THREAD_POOL
from library.widgets.preference_view import PreferencesDialog, ViewScale
from library.widgets.util import DialogOverlay
from library.io.ingest import DEFAULT_ICONS

class LinkTab(ExpandableGroup):
    BASE_HEIGHT = 300

class RelicMainWindow(Ui_RelicMainWindow, QMainWindow):
    def __init__(self, *args, **kwargs):
        super(RelicMainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
        
        self.edit_icon  = QIcon(':status/editing.png')
        self.edit_status = QToolButton(self)
        self.edit_status.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.edit_status.setText('Admin Mode')
        self.edit_status.setIcon(self.edit_icon)

        self.statusbar.addPermanentWidget(self.edit_status, 0)

        self.description_window = description.Window(self)
        self.app_icon = QIcon(':/resources/app/relic.svg')
        self.tray = QSystemTrayIcon(self.app_icon, self)
        self.tray.activated.connect(self.toggleVisibility)
        self.tray.show()
        self.pool = THREAD_POOL
        # Assign the dock's title bar to search widget 
        # then set the dock's widget to an empty widget so separators disappear
        empty_widget = QWidget(self)
        empty_widget.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed))
        self.searchDock.setTitleBarWidget(self.searchDock.widget())
        self.searchDock.setWidget(empty_widget)
        #self.resizeDocks([self.searchDock], [0], Qt.Horizontal) # (QTBUG-65592) fixes dock resize
        self.library = Library()
        self.category_manager = subcategoriesViews.CategoryManager(self)
        self.connect_categories()
        self.searchBox.returnPressed.connect(self.searchLibrary)
        self.pageSpinBox.valueChanged.connect(self.updateAssetView)
        self.buttonGroup.buttonClicked.connect(self.updateAssetView)
        self.collectionRadioButton.toggled.connect(self.searchLibrary)

        # Creates asset view
        self.assets_view = AssetListView(self)
        self.asset_item_model = AssetItemModel(self.assets_view)
        self.assets_view.setModel(self.asset_item_model)
        self.assets_view.doubleClicked.connect(self.loadLinkData)
        self.assets_view.selectionModel().selectionChanged.connect(self.loadAssetData)
        self.assets_view.assetsDeleted.connect(session.updatesubcategorycounts.execute)
        self.assets_view.onExecuted.connect(self.open_file)
    
        self.centralwidget.layout().insertWidget(2, self.assets_view)

        self.noSearchResultsPage.hide()
        link_model = AssetItemModel(self)
        self.links_view = GroupView(link_model, AssetListView, LinkTab, self)
        self.links_view.onGroupsCreated.connect(self.installLinkViewSlots)
        self.metadata_view = metadata_view.MetadataView(self)
        self.metadata_view.openDescription.connect(self.loadCurrentAssetsDescription)
        self.metadata_view.fieldChanged.connect(self.updateAssetFromField)
        self.attributesLayout.addWidget(self.metadata_view)
        self.linksDock.setWidget(self.links_view)

        self.setupDockTitles()

        # Signals / Slots
        self.actionPortal.toggled.connect(self.hideDocks)
        self.actionRecurseSubcategory.setChecked(RELIC_PREFS.recurse_subcategories)
        self.actionRecurseSubcategory.toggled.connect(self.recursiveSubcategories)
        self.actionIngest.triggered.connect(self.beginIngest)
        self.actionPreferences.triggered.connect(self.showPreferences)
        self.actionDocumentation.triggered.connect(self.browseDocumentation)
        readme = lambda x : self.description_window.showMarkdown(':README.md')
        self.actionAbout.triggered.connect(readme)
        self.actionReconnect.triggered.connect(session.rebind)

        self.attrExpandButton.toggled.connect(self.attributeDock.widget().setVisible)
        self.categoryExpandButton.toggled.connect(self.categoryDock.widget().setVisible)


        self.description_window.text_browser.linkToDescription.connect(self.assets_view.clipboardCopy) 
        self.description_window.text_browser.assetClicked.connect(self.browseTo)
        view_scale_value = int(ViewScale[RELIC_PREFS.view_scale])
        self.scaleView(view_scale_value)
        self.viewScaleSlider.valueChanged.connect(self.scaleView)
        self.viewScaleSlider.setValue(view_scale_value)
        self.actionAdministration_Mode.setChecked(RELIC_PREFS.edit_mode)
        self.edit_status.setVisible(RELIC_PREFS.edit_mode)

        self.clearSearchButton.clicked.connect(self.clearSearch)
        self.clearSubcategoryButton.clicked.connect(self.clearSubcategorySelection)
        session.searchkeywords.callback.connect(self.onSearchResults)
        session.searchcategories.callback.connect(self.onSearchResults)
        session.retrieveassets.callback.connect(self.onFilterResults)
        session.socket.connected.connect(self.onConnect)
        session.getcategories.callback.connect(self.onCategories)
        session.retrievelinks.callback.connect(self.onLinksResults)
        session.retrievedependencies.callback.connect(self.onDependencyResults)
        session.createsubcategory.callback.connect(self.recieveNewSubcategory)
        session.moveassets.callback.connect(self.category_manager.receiveNewCounts)
        session.updatesubcategorycounts.callback.connect(self.category_manager.receiveNewCounts)
        session.linksubcategories.callback.connect(subcategory.onRelink)
        session.createuser.callback.connect(self.onUserCreate)
        session.onVideoReceived.connect(self.setVideo)
        session.createtag.callback.connect(self.onRelationCreate)
        session.createuser.callback.connect(self.onRelationCreate)
        self.selected_assets_by_link = {} # Used for dependency linking
        self.selected_assets = [] # Used for dependency linking
        self.startup_callbacks = {} # upon completion of connection and subcategories.
        self.result_callbacks = []
        self.asset_startup_path = None
        self._ingester = None
        self.preferences_dialog = None
        self.block_search = False
        QShortcut(QKeySequence('ctrl+f'), self, self.toFilterBox)

    @Slot()
    def toFilterBox(self):
        position = self.mapFromGlobal(QCursor.pos())
        mapping = {
            self.categoryDock: self.categoryDock.titleBarWidget().filter_box,
            self.attributeDock: self.attributeDock.titleBarWidget().filter_box,
            self.linksDock: self.linksDock.titleBarWidget().filter_box,
        }
        for widget, search in mapping.items():
            if not widget.isVisible():
                continue
            rect = widget.rect()
            g = widget.mapTo(self, rect.topLeft())
            rect = rect.translated(g)
            if rect.contains(position):
                search.button.setChecked(True)
                search.editor.setFocus()
                return

        self.searchBox.setFocus()

    @Slot(list)
    def installLinkViewSlots(self, views):
        for view in views: 
            view.selectionModel().selectionChanged.connect(self.loadAssetData)
            view.onLinkRemove.connect(self.unlinkAsset)
            # on all views
            view.doubleClicked.connect(self.loadLinkData)
            view.assetsDeleted.connect(session.updatesubcategorycounts.execute)
            view.onExecuted.connect(self.open_file)

    @Slot(QModelIndex)
    def open_file(self, index):
        asset = index.data(Qt.UserRole)
        if not asset:
            return
        filepath = asset.network_path
        if filepath.ext.lower() == '.exe':
            # Launch software executable
            with open(str(filepath), 'r') as fp:
                subprocess.Popen('"{}"'.format(fp.read()))
        elif filepath.ext.lower() == '.md':
            self.description_window.showMarkdown(filepath)
        else:
            peakPreview(filepath)

    def setupDockTitles(self):
        attribute_expand_icon = QIcon()
        attribute_expand_icon.addFile(':app/pageArrowLeft.svg', QSize(), QIcon.Normal, QIcon.Off)
        attribute_expand_icon.addFile(':app/pageArrow.svg', QSize(), QIcon.Active, QIcon.On)
        category_expand_icon = QIcon()
        category_expand_icon.addFile(':app/pageArrow.svg', QSize(), QIcon.Normal, QIcon.Off)
        category_expand_icon.addFile(':app/pageArrowLeft.svg', QSize(), QIcon.Active, QIcon.On)
        self.attrExpandButton = QToolButton(self)
        self.attrExpandButton.setIcon(attribute_expand_icon)
        self.categoryExpandButton = QToolButton(self)
        self.categoryExpandButton.setIcon(category_expand_icon)

        back_icon = QIcon(':app/backArrow.svg')
        back_button = QToolButton(self)
        back_button.setText('Back')
        back_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        back_button.setIcon(back_icon)
        back_button.clicked.connect(self.assetViewing)

        links_title = DockTitle('LINKS', back_button, DockTitle.ButtonSide.LEFT, toggle=False, parent=self)
        attribute_title = DockTitle('ATTRIBUTES', self.attrExpandButton, DockTitle.ButtonSide.LEFT, parent=self)
        category_title = DockTitle('CATEGORIES', self.categoryExpandButton, DockTitle.ButtonSide.RIGHT, parent=self)

        self.attributeDock.setTitleBarWidget(attribute_title)
        self.categoryDock.setTitleBarWidget(category_title)
        self.linksDock.setTitleBarWidget(links_title)
        self.linksDock.hide()

        category_title.filter_line.textChanged.connect(self.category_manager.filterAll)
        links_title.filter_line.textChanged.connect(self.links_view.filterAll)
        links_title.addSeparator()
        link_grouping = GroupBox(Grouping, self.links_view)
        link_grouping.setCurrentIndex(0)
        link_layout = links_title.subframe.layout()
        link_layout.addWidget(QLabel('Group :'))
        link_layout.addWidget(link_grouping)

    @staticmethod
    def detachLinkedAsset(primary, relation):
        for attr in [primary.upstream, primary.alusers, primary.tags]:
            if not attr:
                continue
            for i, subasset in enumerate(attr):
                if relation is subasset:
                    attr.pop(i)
                    break

    @Slot(str, object)
    def updateAssetFromField(self, name, value):
        selected_assets = self.selected_assets
        if not selected_assets:
            return
        if name in Relational.__members__.keys():
            # Update asset relationship mappings
            for item in value:
                relation_asset = item.data(Qt.UserRole)
                if relation_asset.status == ItemState.NEW:
                    # CREATE relation asset
                    id_mapping = []
                    for asset in selected_assets:
                        id_mapping.append([relation_asset.relationMap, asset.links])
                    relation_asset.createNew(id_mapping)
                elif relation_asset.status == ItemState.LINK:
                    # LINK existing relation asset
                    relations = []
                    for asset in selected_assets: 
                        relation = [relation_asset.relationMap, relation_asset.id, asset.links]
                        relations.append(relation)
                        attachLinkToAsset(asset, item) # UI atttachment
                    session.createrelationships.execute(relations)
                elif relation_asset.status == ItemState.REMOVE:
                    for asset in selected_assets:
                        relation_asset.unlinkTo(asset)
                        self.detachLinkedAsset(asset, item)
            self.metadata_view.setAssets(selected_assets)
    
        else: # Update the asset field
            for asset in selected_assets:
                attr_name = name.lower()
                if hasattr(asset, attr_name):
                    setattr(asset, attr_name, value)
                    asset.update(fields=[attr_name])

    @Slot(bytes)
    def setVideo(self, data):
        views = [view for view in self.links_view.views]
        views.insert(0, self.assets_view)

        for view in views:
            if not view.lastIndex or not view.lastIndex.isValid():
                continue
            asset = view.lastIndex.data(Qt.UserRole)
            if asset:
                # TODO: this is a temporary local implementation.
                on_complete = partial(setattr, asset, 'video')
                worker = LocalThumbnail(data, on_complete)
                self.pool.start(worker)

    @Slot(dict)
    def recieveNewSubcategory(self, data):
        library_categories = self.library.categories
        for category_name, assets in data.items():
            for fields in assets:
                asset_obj = subcategory(**fields)
                category = library_categories[int(asset_obj.category)]
                category.tree.onNewSubcategory(asset_obj)

    @Slot(int, list)
    def externalSubcategoryDrop(self, category_id: int, paths: list):
        self.beginIngest()
        self.ingest_form.collectPathTextEdit.setPlainText('\n'.join(paths))

    @Slot(polymorphicItem)
    def assetSubcategoryDrop(self, new_subcategory):
        """Re-categorization of an asset
        Moves this asset from it's current subcategory to a new one.

        Parameters
        ----------
        subcategory : subcategory
            destination
        """
        tree = self.sender()
        assets = [index.data(Qt.UserRole) for index in self.assets_view.selectedIndexes()]
        new = new_subcategory.data(Qt.UserRole)
        data = defaultdict(list)
        relations = []
        for asset in assets:
            old = asset.subcategory.data(Qt.UserRole)
            if old.id == new.id or old.category != new.category:
                # Don't link subcategories to themselves or cross categorize.
                continue
            subcategory_relation = relationships(
                links=asset.links,
                category_map=Table.subcategory.index
            )
            data[asset.categoryName].append(asset.export)
            data['old_subcategories'].append(old.export)
            relations.append(subcategory_relation.export)

        if relations:
            data['relationships'] = relations
            data['new_subcategory'] = new.export
            session.moveassets.execute(data)

    @Slot()
    def onConnect(self):
        self.library.fetchCategories()

    @Slot(list)
    def onCategories(self, data):
        category_list = self.library.categories

        # populate categories with subcategory data
        for x in data:
            subcat = subcategory(*x)
            i = 0 if not subcat.category else subcat.category
            subcat.count = 0 if subcat.count is None else subcat.count
            assigned = category_list[i]
            assigned.subcategory_by_id[subcat.id] = polymorphicItem(fields=subcat)
            category_list[i] = assigned

        category_widgets = self.category_manager.assembleCategories(self.library.categories)
        for index, category in enumerate(category_widgets):
            self.categoryLayout.insertWidget(index, category)

        # Now that the connection is complete execute the startup logic.
        if self.asset_startup_path:
            self.browseTo(self.asset_startup_path)

        # Set the current user
        user = alusers(name=os.getenv('username'))
        user_exists = RELIC_PREFS.user_id
        if not user_exists: # user not cached local OR does not exist
            session.createuser.execute({user.categoryName: [user.export]})
        else: # Disconnect callback
            try:
                session.createuser.callback.disconnect(self.onUserCreate)
            except RuntimeError:pass
        #self.tray.showMessage('Connected', 'Relic is now running and connected.', self.app_icon, 2)

        [getattr(self, key)(arg) for key, arg in self.startup_callbacks.items()]
        self.startup_callbacks = {}

    @Slot(dict)
    def onUserCreate(self, data):
        for category_name, assets in data.items():
            for fields in assets:
                new_user = alusers(**fields)
                RELIC_PREFS.user_id = new_user.id
        session.createuser.callback.disconnect(self.onUserCreate)

    @Slot(dict)
    def onRelationCreate(self, data):
        for category_name, assets in data.items():
            for fields in assets:
                constructor = getCategoryConstructor(category_name)
                asset = constructor(**fields)
                item = polymorphicItem(fields=asset)
                for downstream in self.selected_assets:
                    attr = getattr(downstream, category_name)
                    if not attr:
                        setattr(downstream, category_name, [item])
                    else:
                        attr.append(item)


    def clearSearch(self):
        self.searchBox.clear()
        self.updateAssetView()

    def clearSubcategorySelection(self):
        for category in self.library.categories:
            category.tree.selection_model.clearSelection()
        self.updateAssetView()

    @Slot()
    def scaleView(self, value):
        if value == 0:
            # TODO Grouping tree view.
            pass 
        if value == 1:
            BaseItemDelegate.VIEW_MODE = ItemDispalyModes.COMPACT
            BaseItemDelegate.DRAW_PROGRESS = False
        elif value == 2:
            BaseItemDelegate.VIEW_MODE = ItemDispalyModes.THUMBNAIL
            BaseItemDelegate.DRAW_PROGRESS = True
        self.asset_item_model.endResetModel()
        self.links_view.model.endResetModel()
        RELIC_PREFS.view_scale = ViewScale(value).name

    def closeOverlay(self):
        if self.overlay:
            self.assets_view.show()
            self.removeEventFilter(self.overlay)
            self.overlay.close()

    @property
    def ingest_form(self):
        if self._ingester is None:
            from library.widgets.ingest import IngestForm
            ingester = IngestForm()
            ingester.beforeClose.connect(self.onIngestClosed)
            #TODO: make notifications a preference
            collect_finish_msg = lambda x: self.tray.showMessage(
                'Finished Collecting',
                'Relic has completed collection of queued Assets.\nReady to be processed.',
                self.app_icon,
                1
            )
            process_finish_msg = lambda x: self.tray.showMessage(
                'Finished Processing',
                'Relic has processed all the queued Assets.',
                self.app_icon,
                2
            )
            ingester.finishedCollection.connect(collect_finish_msg)
            ingester.finishedProcessing.connect(process_finish_msg)
            self._ingester = ingester
        return self._ingester

    @Slot()
    def showPreferences(self):
        if self.preferences_dialog is None:
            self.preferences_dialog = PreferencesDialog()
        DialogOverlay(self, self.preferences_dialog, modal=True)

    def connect_categories(self):
        self.category_manager.onSelection.connect(self.searchLibrary)
        self.category_manager.onAssetDrop.connect(self.assetSubcategoryDrop)
        self.category_manager.externalFilesDrop.connect(self.externalSubcategoryDrop)

    def disconnect_categories(self):
        self.category_manager.onSelection.disconnect(self.searchLibrary)
        self.category_manager.onAssetDrop.disconnect(self.assetSubcategoryDrop)
        self.category_manager.externalFilesDrop.disconnect(self.externalSubcategoryDrop)
    
    @Slot()
    def beginIngest(self):
        if not self.category_manager.all_categories:
            return
        # make compact temporarily
        BaseItemDelegate.VIEW_MODE = ItemDispalyModes.COMPACT
        self.asset_item_model.endResetModel()
        self.links_view.model.endResetModel()
        self.assets_view.hide()
        self.attributeDock.hide()
        self.ingest_form.setCategoryView(self.categoryDock, self.categoryLayout)
        self.category_manager.blockSignals(True)
        DialogOverlay(self, self.ingest_form, modal=False)

    @Slot()
    def externalPluginCommand(self, asset_data):
        # Delay this function call till after the categories are retrieved.
        if not self.category_manager.all_categories:
            self.startup_callbacks['externalPluginCommand'] = asset_data
            return

        self.toggleVisibility(QSystemTrayIcon.ActivationReason.Trigger, force=True)
        self.beginIngest()
        delay_call = lambda : self.ingest_form.collectAssetsFromPlugin(asset_data)
        self.delay_call = QTimer.singleShot(0.5*1000, delay_call)

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
            _, _, _category, _id, _subcategory, name = path.split('/')
        except:
            return
        category_id = int(_category)
        asset_id = int(_id)
        self.assets_view.clear()

        self.category_manager.blockSignals(True)
        # Set the UI to reflect our asset category.
        for category in self.library.categories:
            if category.id == category_id:
                category.tab.expandState()
                # Scroll to the subcategory tree item in UI.
                category.tree.findInTree(_subcategory)
            else:
                category.tab.collapseState()
        self.category_manager.blockSignals(False)
        try:
            self.searchBox.setText(name.split('.')[0])
        except:
            pass
        # Inject specific asset into the search filter adding to the main view. 
        #filtered = [[category_id, asset_id, [], _subcategory]]
        #self.onFilterResults(filtered)
        if '#' in name:
            self.result_callbacks.append(self.loadCurrentAssetsDescription)
        self.searchLibrary()


    @Slot()
    def loadCurrentAssetsDescription(self):
        if self.selected_assets:
            asset = self.selected_assets[-1]
        else:
            index = self.assets_view.model.index(0, 0, QModelIndex())
            asset = index.data(Qt.UserRole)
        description_path = asset.network_path.suffixed('_description', '.md')
        if not description_path.exists():
            description_path.touch()

        self.description_window.showMarkdown(description_path)
        
    @Slot()
    def onIngestClosed(self, dock):
        self.assets_view.show()
        self.attributeDock.show()
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)
        self.category_manager.blockSignals(False)
        self.scaleView(int(ViewScale[RELIC_PREFS.view_scale]))

    def hideDocks(self, state):
        self.categoryExpandButton.setChecked(state)
        self.attrExpandButton.setChecked(state)

    @Slot()
    def recursiveSubcategories(self, state):
        RELIC_PREFS.recurse_subcategories = int(state)

    @Slot()
    def assetViewing(self):
        self.links_view.clear()
        self.linksDock.hide()
        self.assets_view.show()

    @Slot()
    def updateAssetView(self, arg=None):
        self.pool.clear()
        self.assets_view.clear()
        # Re-apply asset filtering.
        self.filterAssets()

    @Slot()
    def searchLibrary(self):
        """
        Re-queries the database if the searchbox or categories have changed
        """
        if self.block_search:
            QTimer.singleShot(500, self.searchLibrary)
            return
        else:
            self.block_search = True
        self.assetViewing()
        subcategories = self.category_manager.selected_subcategories.copy()
        search_filter = self.library.validateCategories(subcategories)
        # Define the search class mode. 
        use_collections = self.collectionRadioButton.isChecked()
        if use_collections:
            exclude_type = AssetType.VARIANT
        else:
            exclude_type = AssetType.COLLECTION
        search_filter['exclude_type'] = exclude_type
        # Split text into list of search term keywords.
        text = self.searchBox.text()
        if text:
            search_filter['keywords'] = text.split(' ')
            session.searchkeywords.execute(search_filter)
        else:
            session.searchcategories.execute(search_filter)
        
        unblocker = lambda : setattr(self, 'block_search', False)
        QTimer.singleShot(700, unblocker)

    @Slot(dict)
    def onSearchResults(self, search_results):
        self.assets_view.clear()
        if not search_results:
            self.assets_view.hide()
            self.noSearchResultsPage.show()
            self.library.assets = []
            self.pageSpinBox.setMaximum(1)
            self.statusbar.showMessage('Search results: 0 Assets...')
            return
        else:
            self.noSearchResultsPage.hide()
            self.assets_view.show()

        matched_assets = []
        for category in search_results:
            try:
                category_int = int(category)
            except:
                continue

            for data in search_results[category]:
                if len(data) == 3:
                    _id, subcategory_id, tag_ids = data
                    asset = (category_int, _id, tag_ids, subcategory_id)
                    matched_assets.append(asset)
                else:
                    subcategory_id, _ids = data
                    tag_ids = []
                    for x in _ids:
                        asset = (category_int, x, tag_ids, subcategory_id)
                        matched_assets.append(asset)

        asset_total = len(matched_assets)
        page_count = math.ceil(asset_total / RELIC_PREFS.assets_per_page) or 1
        self.pageSpinBox.setSuffix(f'/{page_count}')
        self.pageSpinBox.setMaximum(page_count)
        self.statusbar.showMessage(f'Search results: {asset_total} Assets...')

        # Sort the assets by the total number of tag_ids (index 2)
        self.library.assets = sorted(matched_assets, key=lambda x: len(x[2]), reverse=True)
        self.filterAssets()

    @Slot(list)
    def onFilterResults(self, filter_results):
        load_icons = True #not self.assets_grid.isVisible()
        item_model = self.asset_item_model
        category_list = self.library.categories

        filter_assets = self.library.assets_filtered
        if len(filter_results) != len(filter_assets):
            return

        link_ids = []
        for i, x in enumerate(filter_assets):
            category, _id, tags, subcategory = x
            asset_constructor = getCategoryConstructor(category)

            asset_fields = filter_results[i]
            #asset_fields.extend([tags, []])
            asset = asset_constructor(*asset_fields)
            asset.category = category
            category_obj = category_list[category]
            if category_obj:
                subcategory = category_obj.subcategory_by_id.get(subcategory)
                asset.subcategory = subcategory

            item = polymorphicItem(fields=asset)
            #    asset.fetchIcon()
            if load_icons and asset.classification == Classification.DOCUMENT.value:
                asset.icon = DEFAULT_ICONS.document
            elif load_icons:
                self.loadIcon(asset)
            item_model.appendRow(item)
            link_ids.append(asset.links)
        session.retrievelinks.execute(link_ids)
        self.assets_view.scrollTo(self.assets_view.model.index(0, 0, QModelIndex()))
        self.block_search = False
        [call() for call in self.result_callbacks]
        self.result_callbacks = []

    def filterAssets(self):
        categories = self.category_manager.selected_subcategories.copy()
        limit = RELIC_PREFS.assets_per_page
        page = self.pageSpinBox.value()
        offset = int(((page * limit) - limit)) if page else 0

        selected_subcategories = []
        categories_to_search = self.library.validateCategories(categories).keys()
        for x in categories:
            selected_subcategories.extend(categories[x])

        assets_filtered = []
        search_data = []
        matched_categories = defaultdict(list)
        for asset in self.library.assets:
            category, _id, tags, subcategory = asset
            if category in categories_to_search:
                if selected_subcategories:
                    if subcategory in selected_subcategories:
                        search_data.append([category, _id])
                        assets_filtered.append(asset)
                else:
                    search_data.append([category, _id])
                    assets_filtered.append(asset)

        search_data = search_data[offset:(offset+limit)]
        [matched_categories[category].append(_id) for category, _id in search_data if _id]
        self.library.assets_filtered = assets_filtered[offset:(offset+limit)]
        session.retrieveassets.execute(matched_categories)


    @Slot(QModelIndex)
    def loadAssetData(self, selection):
        sender = self.sender()
        if sender.parent().drag_select:
            # Better multi-select performance
            return
        # Links / Dependencies have already been attached to the assets.
        view = sender.parent()
        indices = view.selectedIndexes()
        assets = [index.data(Qt.UserRole) for index in indices]        
        self.selected_assets = assets
        self.selected_assets_by_link = {}
        if not assets:
            return

        self.metadata_view.setAssets(assets)

        if self.previewCheckBox.isChecked():
            path = assets[-1].network_path
            peakPreview(path)

        assets_by_link = {}
        for asset in assets:
            if not asset.traversed:
                asset.traversed = True
            else:
                continue
            #assets_by_link[asset.links] = asset # Enable this for direct map
            if upstream := asset.upstream:
                for dependency in upstream:
                    assets_by_link[dependency.links] = dependency
        
        link_ids = list(assets_by_link.keys())
        self.selected_assets_by_link = assets_by_link
        if link_ids:
            session.retrievedependencies.execute(link_ids)

    @Slot(dict)
    def onDependencyResults(self, dependencies):
        link_map = dependencies.pop('link_map')
        if not link_map:
            return
        # Pre-create each asset in-place. 
        for category_name, assets in dependencies.items():
            asset_constructor = getCategoryConstructor(category_name)
            for index, fields in enumerate(assets):
                asset_obj = asset_constructor(*fields)
                linked_asset = polymorphicItem(fields=asset_obj)
                dependencies[category_name][index] = linked_asset
    
        # Map the views by link and attach to the selected primary assets
        selection = self.selected_assets_by_link
        for level, mapping in enumerate(link_map):
            for link, values, in mapping.items():
                categories, ids = values
                primary_asset = selection[int(link)]

                for index in range(len(ids)):
                    category_name = Table(categories[index]).name
                    assets = dependencies.get(category_name)
                    _id = ids[index]
                    upstream = [x for x in assets if x.id == _id]
                    print('UNSTABLE', category_name, primary_asset, upstream)
                    for asset in upstream:
                        attachLinkToAsset(primary_asset, asset)

    @Slot(dict)
    def onLinksResults(self, data):
        if not data:
            return

        links = data.pop('links')
        ids = data.pop('category_ids')
        maps = data.pop('category_maps')

        # Construct the metadata asset objects
        linked_assets = []
        for category_name, fields_list in data.items():
            asset_constructor = getCategoryConstructor(category_name)
            for index, fields in enumerate(fields_list):
                asset_obj = asset_constructor(*fields)
                linked_asset = polymorphicItem(fields=asset_obj)
                linked_assets.append(linked_asset)
        assets = []
        link_map = []
        for i in range(len(links)):
            _map = maps[i]
            _id = ids[i]
            for link_item in linked_assets:
                link_item_asset = link_item.data(Qt.UserRole)
                if link_item_asset.id == _id and link_item_asset.relationMap == _map:
                    link_map.append(link_item)
        main_view = self.assets_view
        model = main_view.model if main_view.isVisible() else self.links_view.model
        for i in range(model.rowCount()):
            asset = model.index(i, 0).data(Qt.UserRole)
            for index, link in enumerate(links):
                if asset.links == link:
                    try:
                        link_item = link_map[index]
                        attachLinkToAsset(asset, link_item)
                    except IndexError as exerr:
                        print('failed to attach link to asset', 'Link:', len(links), len(link_map))
            assets.append(asset)

        if not assets:
            return
        # copy upstream icons on empty collections
        for asset in assets:
            if asset.type == AssetType.COLLECTION and asset.upstream:
                icon_path = asset.network_path.suffixed('_icon', '.jpg')
                if not icon_path.exists():
                    copyRelatedIcon(asset)
        self.metadata_view.setAssets(assets)

    @Slot(QModelIndex)
    def unlinkAsset(self, index):
        """Unlinks two assets by removing the relationship.

        Parameters
        ----------
        index : QModelIndex
            the index from which this slot is conecting to
        """
        # TODO: This needs to be refactored to not rely on the asset selection.
        #primary_indices = self.assets_view.selectedIndexes()
        asset = index.data(Qt.UserRole)
        for downstream in asset.downstream:
            asset.unlinkTo(downstream)
            downstream.dependencies -= 1
            downstream.update(fields=['dependencies'])

    @Slot(QModelIndex)
    def loadLinkData(self, index):
        """Load related assets via links from relationships.

        Parameters
        ----------
        index : QModelIndex
            the index from which this slot is conecting to
        """
        sender = self.sender()

        indices = self.assets_view.selectedIndexes()
        if index not in indices:
            indices = self.links_view.getAllSelectedIndexes()

        linked_assets = []
        link_ids = []
        for index in indices:
            asset = index.data(Qt.UserRole)
            upstream = asset.upstream or []
            for x in upstream:
                if x.traversed:
                    continue
                else:
                    x.traversed = True
                link_ids.append(x.links)
            linked_assets.extend(upstream)
        if not linked_assets:
            return
        if self.assets_view.isVisible():
            self.assets_view.hide()
        self.assets_view.selectionModel().select(index, QItemSelectionModel.Deselect)

        self.links_view.updateGroups(linked_assets, clear=True)
        load_icon = self.loadIcon
        [load_icon(x.data(Qt.UserRole)) for x in linked_assets]
        if not self.linksDock.isVisible():
            self.linksDock.show()

        # Fetch the upstream asset sub-links
        session.retrievelinks.execute(link_ids)

    def loadIcon(self, asset):
        on_complete = partial(setattr, asset, 'icon')
        icon_path = asset.network_path.suffixed('_icon', '.jpg')
        worker = LocalThumbnail(icon_path, on_complete)
        self.pool.start(worker)
        #asset_obj.fetchIcon()
        #asset.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
        #asset.setCheckable(True)

    @Slot(QSystemTrayIcon.ActivationReason)
    def toggleVisibility(self, reason, force=False):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.grab()
            self.setVisible(force if force else not self.isVisible())
            self.activateWindow()
            self.raise_()

    @Slot()
    def toggleAdminMode(self, toggle):
        #TODO: query the databse for permissions level
        RELIC_PREFS.edit_mode = int(toggle)
        self.edit_status.setVisible(toggle)

    @Slot()
    def browseDocumentation(self):
        import relic
        site = relic.config.HOST
        url = f'{site}documentation/index.html'
        os.startfile(url)

def copyRelatedIcon(asset):
    # TODO: Re-assess if this is really needed.
    for item in asset.upstream:
        linked_asset = item.data(Qt.UserRole)
        related_icon = linked_asset.network_path.suffixed('_icon', '.jpg')
        asset_icon = asset.network_path.suffixed('_icon', '.jpg')
        related_icon.copyTo(asset_icon)
        break


def main(args):
    app = qApp or QApplication(sys.argv)
    ctypes.windll.kernel32.SetConsoleTitleW('Relic')
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(u'resarts.relic')

    base_style = readAllContents(':/base_style.qss')
    app_style = readAllContents(':/resources/style/app_style.qss')
    app.setStyleSheet(base_style + app_style)

    window = RelicMainWindow()
    window.setWindowTitle(f'Relic {library.__version__}')

    # Startup the plugin server
    ingest_server = Server('relic')
    ingest_server.incomingData.connect(window.externalPluginCommand)
    ingest_server.incomingFile.connect(window.browseTo)
    window.resize(1620, 925)
    window.show()
    if args and args.path:
        window.asset_startup_path = args.path
    sys.exit(app.exec_())
