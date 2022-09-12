import ctypes
import math
import os
import subprocess
import sys
from collections import defaultdict
from functools import partial

# -- First-party --
import qtshared6.resources
# -- Third-party --
from PySide6.QtCore import (QItemSelectionModel, QModelIndex, QThreadPool,
                            QTimer, Slot)
from PySide6.QtGui import QIcon, QPixmap, Qt
from PySide6.QtWidgets import (QApplication, QMainWindow, QSizePolicy,
                               QSystemTrayIcon, QToolButton, QWidget)
from qtshared6.delegates import BaseItemDelegate, ItemDispalyModes
from qtshared6.utils import polymorphicItem
from relic.local import Relational
from sequence_path.main import SequencePath as Path
from strand import server

from library.config import RELIC_PREFS, peakPreview
from library.io.util import LocalThumbnail
from library.objectmodels import (Category, Library, Type, alusers,
                                  attachLinkToAsset, getCategoryConstructor,
                                  relationships, session, subcategory)
# -- Module --
from library.ui.dialog import Ui_RelicMainWindow
from library.widgets import description
from library.widgets.fields import ItemState
from library.widgets.assets_alt import AssetItemModel, AssetListView
from library.widgets.metadata_view import MetadataView
from library.widgets.preference_view import PreferencesDialog, ViewScale
from library.widgets.relationshipView import LinkViewWidget
from library.widgets.subcategoriesViews import CategoryManager, ExpandableTab
from library.widgets.util import DialogOverlay

CATEGORIES = []

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
        self.app_icon = QIcon(':/resources/app/app_icon.svg')
        self.tray = QSystemTrayIcon(self.app_icon, self)
        self.tray.activated.connect(self.toggleVisibility)
        self.tray.show()
        self.pool = QThreadPool.globalInstance()
        # Assign the dock's title bar to search widget 
        # then set the dock's widget to an empty widget so separators disappear
        empty_widget = QWidget(self)
        empty_widget.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed))
        self.searchDock.setTitleBarWidget(self.searchDock.widget())
        self.searchDock.setWidget(empty_widget)
        self.resizeDocks([self.searchDock], [0], Qt.Horizontal) # (QTBUG-65592) fixes dock resize
        self.library = Library()
        self.category_manager = CategoryManager(self)
        self.category_manager.onSelection.connect(self.searchLibrary)
        self.category_manager.onAssetDrop.connect(self.assetSubcategoryDrop)
        self.category_manager.externalFilesDrop.connect(self.externalSubcategoryDrop)
        self.searchBox.returnPressed.connect(self.searchLibrary)
        self.pageSpinBox.valueChanged.connect(self.updateAssetView)
        self.buttonGroup.buttonClicked.connect(self.updateAssetView)
        self.collectionRadioButton.toggled.connect(self.searchLibrary)
        self.categoryDock.setTitleBarWidget(self.dockTitleFrame)
        self.attributeDock.setTitleBarWidget(self.attributeDockTitle)
        self.linksDock.setTitleBarWidget(self.linkDockTitle)
        self.linksDock.hide()

        self.attributeDock.setAutoFillBackground(True)
        self.categoryDock.setAutoFillBackground(True)
        self.linksDock.setAutoFillBackground(True)

        # Creates asset view
        self.assets_view = AssetListView(self)
        self.assets_view.doubleClicked.connect(self.loadLinkData)

        self.asset_item_model = AssetItemModel()
        self.assets_view.setModel(self.asset_item_model)
        self.centralwidget.layout().insertWidget(2, self.assets_view)

        self.noSearchResultsPage.hide()
        self.links_view = LinkViewWidget(self)
        self.metadata_view = MetadataView(self)
        self.metadata_view.openDescription.connect(self.loadCurrentAssetsDescription)
        self.metadata_view.fieldChanged.connect(self.updateAssetFromField)
        self.attributesLayout.addWidget(self.metadata_view)
        self.linksDock.setWidget(self.links_view)

        # Signals / Slots
        self.filterBox.textChanged.connect(self.category_manager.filterAll)
        self.linkFilterBox.textChanged.connect(self.links_view.filterAll)
        self.actionPortal.toggled.connect(self.hideDocks)
        self.actionRecurseSubcategory.setChecked(int(RELIC_PREFS.recurse_subcategories))
        self.actionRecurseSubcategory.toggled.connect(self.recursiveSubcategories)
        self.actionIngest.triggered.connect(self.beginIngest)
        self.actionPreferences.triggered.connect(self.showPreferences)
        self.actionDocumentation.triggered.connect(self.browseDocumentation)
        self.actionReconnect.triggered.connect(session.rebind)

        self.attrExpandButton.toggled.connect(self.attributeDock.widget().setVisible)
        self.categoryExpandButton.toggled.connect(self.categoryDock.widget().setVisible)

        self.assets_view.selectionModel().selectionChanged.connect(self.loadAssetData)
        self.assets_view.assetsDeleted.connect(session.updatesubcategorycounts.execute)
        self.assets_view.onExecuted.connect(self.open_file)

        for view in self.links_view.all_views:
            view.assetsDeleted.connect(session.updatesubcategorycounts.execute)
            view.onExecuted.connect(self.open_file)

        self.backButton.clicked.connect(self.assetViewing)
        self.description_window.text_browser.linkToDescription.connect(self.assets_view.clipboardCopy) 
        self.description_window.text_browser.assetClicked.connect(self.browseTo) 
        self.scaleView(int(ViewScale[RELIC_PREFS.view_scale]))
        self.viewScaleSlider.valueChanged.connect(self.scaleView)
        self.viewScaleSlider.setValue(int(ViewScale[RELIC_PREFS.view_scale]))
        self.actionAdministration_Mode.setChecked(int(RELIC_PREFS.edit_mode))
        self.edit_status.setVisible(int(RELIC_PREFS.edit_mode))

        self.clearSearchButton.clicked.connect(self.clearSearch)
        self.clearSubcategoryButton.clicked.connect(self.clearSubcategorySelection)
        session.searchkeywords.callback.connect(self.onSearchResults)
        session.searchcategories.callback.connect(self.onSearchResults)
        session.retrieveassets.callback.connect(self.onFilterResults)
        session.socket.connected.connect(self.onConnect)
        session.getcategories.callback.connect(self.onCategories)
        session.retrievelinks.callback.connect(self.onAssetsLoaded)
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

        self.asset_startup_path = None
        self._ingester = None
        self.preferences_dialog = None
        self.block_search = False

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
        if name in Relational.__members__.keys():
            # Update asset relationship mappings
            for item in value:
                relation_asset = item.data(polymorphicItem.Object)
                if relation_asset.status == ItemState.NEW:
                    # CREATE relation asset
                    id_mapping = []
                    for asset in self.selected_assets:
                        id_mapping.append([relation_asset.relationMap, asset.links])
                    relation_asset.createNew(id_mapping)
                elif relation_asset.status == ItemState.LINK:
                    # LINK existing relation asset
                    relations = []
                    for asset in self.selected_assets: 
                        relation = [relation_asset.relationMap, relation_asset.id, asset.links]
                        relations.append(relation)
                        attachLinkToAsset(asset, item) # UI atttachment
                    session.createrelationships.execute(relations)
                elif relation_asset.status == ItemState.REMOVE:
                    for asset in self.selected_assets: 
                        relation_asset.unlinkTo(asset)
                        self.detachLinkedAsset(asset, item)
            self.metadata_view.setAssets(self.selected_assets)
    
        else: # Update the asset field
            for asset in self.selected_assets:
                setattr(asset, name.lower(), value)
                asset.update(fields=[name.lower()])

    @Slot(QModelIndex)
    def open_file(self, index):
        asset = index.data(polymorphicItem.Object)
        if asset:
            filepath = asset.network_path
            ext = filepath.ext.lower()
            if ext == '.exe':
                # Launch software executable
                with open(str(filepath), 'r') as fp:
                    subprocess.Popen('"{}"'.format(fp.read()))
                return
            else:
                peakPreview(filepath)

    @Slot(bytes)
    def setVideo(self, data):
        views = [view for view in self.links_view.all_views]
        views.insert(0, self.assets_view)

        for view in views:
            if not view.lastIndex or not view.lastIndex.isValid():
                continue
            asset = view.lastIndex.data(polymorphicItem.Object)
            if asset:
                on_complete = partial(setattr, asset, 'video')
                worker = LocalThumbnail(data, on_complete)
                self.pool.start(worker)

    @Slot(dict)
    def recieveNewSubcategory(self, data):
        library_categories = self.library.categories
        for category_name, assets in data.items():
            for fields in assets:
                asset_obj = subcategory(**fields)
                category = library_categories.get(int(asset_obj.category))
                category.tree.onNewSubcategory(asset_obj)

    @Slot(int, list)
    def externalSubcategoryDrop(self, category_id: int, paths: list):
        self.beginIngest()
        self.ingest_form.categoryComboBox.setCurrentIndex(category_id)
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
        assets = [index.data(polymorphicItem.Object) for index in self.assets_view.selectedIndexes()]
        new = new_subcategory.data(polymorphicItem.Object)
        data = defaultdict(list)
        relations = []
        for asset in assets:
            old = asset.subcategory.data(polymorphicItem.Object)
            if old.id == new.id or old.category != new.category:
                # Don't link subcategories to themselves or cross categorize.
                continue
            subcategory_relation = relationships(
                link=asset.links,
                category_map=3
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
        self.library.categories.fetch()

    @Slot(list)
    def onCategories(self, data):
        category_obj = self.library.categories
        # populate categories with subcategory data
        for x in data:
            subcat = subcategory(*x)
            k = 0 if not subcat.category else subcat.category
            subcat.count = 0 if subcat.count is None else subcat.count
            assigned = category_obj.get(k)
            assigned.subcategory_by_id[subcat.id] = polymorphicItem(fields=subcat)
            category_obj.set(k, assigned)

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
        elif value == 2:
            BaseItemDelegate.VIEW_MODE = ItemDispalyModes.THUMBNAIL
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

    @Slot()
    def beginIngest(self):
        self.scaleView(1)
        self.assets_view.hide()
        self.attributeDock.hide()
        self.verticalSpacer.changeSize(0, 0, QSizePolicy.Minimum, QSizePolicy.Minimum) 
        self.ingest_form.setCategoryView(self.categoryDock, self.categoryLayout)
        self.category_manager.blockSignals(True)
        DialogOverlay(self, self.ingest_form, modal=False)

    @Slot()
    def externalPluginCommand(self, asset_data):
        self.toggleVisibility(QSystemTrayIcon.ActivationReason.Trigger, force=True)
        self.beginIngest()
        delay_call = lambda : self._ingester.collectAssetsFromPlugin(asset_data)
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
        self.searchLibrary()
        # Inject specific asset into the search filter adding to the main view. 
        #filtered = [[category_id, asset_id, [], _subcategory]]
        #self.onFilterResults(filtered)
        if '#' in name:
            name, description = name.split('#')
            self.loadCurrentAssetsDescription(asset)

    @Slot()
    def loadCurrentAssetsDescription(self, asset=None):
        if not asset:
            if not self.selected_assets:
                return
            asset = self.selected_assets[-1]
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
        try:
            self.verticalSpacer.changeSize(0, 0, QSizePolicy.Minimum, QSizePolicy.MinimumExpanding) 
        except:pass

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
            return
        else:
            self.block_search = True
        self.assetViewing()
        subcategories = self.category_manager.selected_subcategories.copy()
        search_filter = self.library.validateCategories(subcategories)
        # Define the search class mode. 
        use_collections = self.collectionRadioButton.isChecked()
        search_filter['exclude_type'] = 5 if use_collections else 3
        # Split text into list of search term keywords.
        text = self.searchBox.text()
    
        if text:
            search_filter['keywords'] = text.split(' ')
            session.searchkeywords.execute(search_filter)
        else:
            session.searchcategories.execute(search_filter)
            
        unblocker = lambda : setattr(self, 'block_search', False)
        QTimer.singleShot(1000, unblocker)

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
        page_count = math.ceil(asset_total / int(RELIC_PREFS.assets_per_page)) or 1
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
            category_obj = self.library.categories.get(category)
            if category_obj:
                subcategory = category_obj.subcategory_by_id.get(subcategory)
                asset.subcategory = subcategory

            #if icons and asset.path:
            #    asset.fetchIcon()
            item = polymorphicItem(fields=asset)
            if load_icons:
                on_complete = partial(setattr, asset, 'icon')
                icon_path = asset.network_path.suffixed('_icon', '.jpg')
                worker = LocalThumbnail(icon_path, on_complete, item)
                self.pool.start(worker)
            item_model.appendRow(item)
            link_ids.append(asset.links)

        session.retrievelinks.execute(link_ids)
        self.assets_view.scrollTo(self.assets_view.model.index(0, 0, QModelIndex()))
        self.block_search = False

    def filterAssets(self):
        categories = self.category_manager.selected_subcategories.copy()
        limit = int(RELIC_PREFS.assets_per_page)
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
        assets = [index.data(polymorphicItem.Object) for index in selection.indexes()]        
        if not assets:
            return
        self.selected_assets = assets
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
                    category_name = Category(categories[index]).name.lower()
                    assets = dependencies.get(category_name)
                    _id = ids[index]
                    upstream = [x for x in assets if x.id == _id]
                    for asset in upstream:
                        attachLinkToAsset(primary_asset, asset)

    @Slot(dict)
    def onAssetsLoaded(self, data):
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
        model = self.assets_view.model
        link_map = []
        for i in range(len(links)):
            _map = maps[i]
            _id = ids[i]
            for link_item in linked_assets:
                link_item_asset = link_item.data(polymorphicItem.Object)
                if link_item_asset.id == _id and link_item_asset.relationMap == _map:
                    link_map.append(link_item)

        for i in range(model.rowCount()):
            asset = model.index(i, 0).data(polymorphicItem.Object)
            for index, link in enumerate(links):
                if asset.links == link:
                    link_item = link_map[index]
                    attachLinkToAsset(asset, link_item)
            assets.append(asset)

        if not assets:
            return
        # copy upstream icons on empty collections
        for asset in assets:
            if asset.type == Type.COLLECTION:
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
        asset = index.data(polymorphicItem.Object)
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
        for index in indices:
            asset = index.data(polymorphicItem.Object)
            linked_assets.extend(asset.upstream or [])
        if not linked_assets:
            return
        if self.assets_view.isVisible():
            self.assets_view.hide()
        self.assets_view.selectionModel().select(index, QItemSelectionModel.Deselect)

        self.links_view.updateGroups(linked_assets, clear=True)
        if not self.linksDock.isVisible():
            self.linksDock.show()

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
        site = RELIC_PREFS.host
        url = f'{site}documentation/index.html'
        os.startfile(url)

def copyRelatedIcon(asset):
    # TODO: Re-assess if this is really needed.
    if asset.upstream:
        for item in asset.upstream:
            linked_asset = item.data(polymorphicItem.Object)
            related_icon = linked_asset.network_path.suffixed('_icon', '.jpg')
            asset_icon = asset.network_path.suffixed('_icon', '.jpg')
            related_icon.copyTo(asset_icon)
            break


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
    if args and args.path:
        window.asset_startup_path = args.path
    sys.exit(app.exec_())
