from functools import partial

from PySide6.QtCore import QThreadPool, Signal, Slot, QRect, Qt, QSize, QPoint, QSortFilterProxyModel
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QVBoxLayout, QLayout, QSizePolicy, QWidget, QSpacerItem, QFrame, QScrollArea

from relic import scheme
from qtshared6.utils import polymorphicItem
from library.widgets.assets_alt import AssetItemModel, AssetListView

from relic.qt.expandable_group import ExpandableGroup
from library.io.util import LocalThumbnail

class assetTypeFilter(QSortFilterProxyModel):
    def __init__(self, attr, parent=None):
        super(assetTypeFilter, self).__init__(parent)
        self.attr = attr
        self.text = ''

    def filterAcceptsRow(self, sourceRow, sourceParent):
        idx = self.sourceModel().index(sourceRow, 0, sourceParent)
        asset = idx.data(polymorphicItem.Object)
        if not asset:
            return False
        # Filter asset types
        if idx.isValid() and asset.type == self.attr:
            if self.text == '' or self.text.lower() in asset.name.lower():
                return True
            else:
                return False
        else:
            return False


class ExpandableTab(ExpandableGroup):
    BASE_HEIGHT = 300
    def __init__(self, asset_type):
        super(ExpandableTab, self).__init__(content=None)
        icon = QIcon(':AssetType/{}'.format(asset_type.upper()))
        self.iconButton.setIcon(icon)
        self.nameLabel.setText(asset_type + 's')
        self.styledLine_1.hide()


class LinkViewWidget(QScrollArea):

    itemDeletion = Signal(list)
    onSelection = Signal(object)

    def __init__(self, *args, **kwargs):
        super(LinkViewWidget, self).__init__(*args, **kwargs)
        self.central = QFrame(self)
        layout = QVBoxLayout(self.central)
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(3, 3, 3, 3)
        self.setWidget(self.central)
        self.setWidgetResizable(True)
        self.model = AssetItemModel(self)
        self.all_tabs = []
        self.all_views = []
        self.asset_type_counter = {}
        self.createGroups()
        spacer = QSpacerItem(100, 100, QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        layout.addItem(spacer)
        self.pool = QThreadPool.globalInstance()

    def createGroups(self):
        labels = [x.name.capitalize() for x in scheme.AssetType if x.value]
        tab_layout = self.central.layout()
        for index, asset_type in enumerate(labels):
            view = AssetListView(self)
            proxyModel = assetTypeFilter(index+1)
            proxyModel.setDynamicSortFilter(True)
            proxyModel.setSourceModel(self.model)
            view.setModel(proxyModel)
            view.selectionModel().selectionChanged.connect(self.parent().loadAssetData)
            view.onLinkRemove.connect(self.parent().unlinkAsset)
            view.onLinkLoad.connect(self.parent().loadLinkData)

            tab = ExpandableTab(asset_type)
            tab.setParent(self.central)
            tab.frame.layout().insertWidget(1, view)
            tab.model = proxyModel
            self.all_tabs.append(tab)
            self.all_views.append(view)
            tab_layout.addWidget(tab)
        self.clear()

    def clear(self):
        self.model.clear()
        self.asset_type_counter = {}

    def updateGroups(self, assets, clear=False):
        if clear:
            self.pool.clear()
            self.clear()

        for asset in assets:
            asset.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
            asset.setCheckable(True)
            self.model.appendRow(asset)
            type_count = self.asset_type_counter.get(asset.type) or 0
            self.asset_type_counter[asset.type] = type_count + 1
            asset_obj = asset.data(polymorphicItem.Object)
            on_complete = partial(setattr, asset, 'icon')
            worker = LocalThumbnail(asset_obj.network_path.suffixed('_icon', '.jpg'), on_complete)
            self.pool.start(worker)
            #asset_obj.fetchIcon()

        for index, tab in enumerate(self.all_tabs):
            count = self.asset_type_counter.get(index+1) or 0
            if count == 0:
                tab.hide()
            else:
                tab.countSpinBox.setValue(count)
                tab.show()


    def getAllSelectedIndexes(self):
        all_idx = [] 
        for view in self.all_views:
            all_idx.extend(view.selectedIndexes())
            if view.editor: #CRITICAL
                view.editor.close()
        return all_idx

    def filterAll(self, text):
        for x in self.all_tabs:
            x.model.text = text
            x.model.endResetModel()
