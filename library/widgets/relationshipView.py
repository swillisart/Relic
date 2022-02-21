from functools import partial

from PySide6.QtCore import QThreadPool, Signal, Slot, QRect, Qt, QSize, QPoint, QSortFilterProxyModel
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QVBoxLayout, QLayout, QSizePolicy, QWidget

from library.widgets.metadataView import typeWidget
from library.widgets.assets import assetItemModel, assetListView, polymorphicItem
from library.ui.expandableTabs import Ui_ExpandableTabs
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


class ExpandableTab(Ui_ExpandableTabs, QWidget):

    collapseExpand = Signal(bool)

    def __init__(self, parent, asset_type):
        super(ExpandableTab, self).__init__(parent)
        self.setupUi(self)
        self.state = False
        icon = QIcon(':/resources/asset_types/{}.svg'.format(asset_type.lower()))
        self.iconButton.setIcon(icon)
        self.nameLabel.setText(asset_type + 's')
        self.styledLine_1.hide()

        for x in [self.countSpinBox, self.checkButton, self.iconButton]:
            x.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.ContentFrame.setVisible(False)

    def mousePressEvent(self, event):
        super(ExpandableTab, self).mousePressEvent(event)
        if self.HeaderFrame.underMouse():
            self.toggleState()

    def toggleState(self):
        self.state = not self.state
        self.collapseExpand.emit(self.state)
        self.checkButton.nextCheckState()
        self.ContentFrame.setVisible(self.state)


class LinkViewWidget(QWidget):

    itemDeletion = Signal(list)
    onSelection = Signal(object)

    def __init__(self, *args, **kwargs):
        super(LinkViewWidget, self).__init__(*args, **kwargs)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignTop)
        self.inactive_layout = FlowLayout()
        self.inactive_layout.setAlignment(Qt.AlignTop)
        self.main_layout.addLayout(self.inactive_layout)
        self.setLayout(self.main_layout)
        self.model = assetItemModel(self)
        self.all_tabs = []
        self.all_views = [] 
        self.asset_type_counter = {}
        self.createGroups()
        self.pool = QThreadPool.globalInstance()

    def createGroups(self):
        for index, asset_type in enumerate(typeWidget.LABELS):
            view = assetListView(self)
            proxyModel = assetTypeFilter(index+1)
            proxyModel.setDynamicSortFilter(True)
            proxyModel.setSourceModel(self.model)
            view.setModel(proxyModel)
            view.selmod.selectionChanged.connect(self.parent().loadAssetData)
            view.onLinkRemove.connect(self.parent().unlinkAsset)
            view.onLinkLoad.connect(self.parent().loadLinkData)

            tab = ExpandableTab(self, asset_type)
            tab.collapseExpand.connect(self.shuffleActiveLayouts)
            tab.frame.layout().insertWidget(1, view)
            tab.model = proxyModel
            self.all_tabs.append(tab)
            self.all_views.append(view)
            self.inactive_layout.addWidget(tab)
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

    @Slot(bool)
    def shuffleActiveLayouts(self, state):
        expandableFrame = self.sender()
        if state:
            self.inactive_layout.removeWidget(expandableFrame)
            self.main_layout.addWidget(expandableFrame)
        else:
            self.main_layout.removeWidget(expandableFrame)
            self.inactive_layout.addWidget(expandableFrame)

    def getAllSelectedIndexes(self):
        all_idx = [] 
        for view in self.all_views:
            all_idx.extend(view.selectedIndexes())
            if view.editor: #CRITICAL
                view.editor.close()
        return all_idx

    def iterateTypeGroups(self):
        for x in self.children():
            if isinstance(x, ExpandableTab):
                yield x

    def filterAll(self, text):
        for x in self.iterateTypeGroups():
            x.model.text = text
            x.model.endResetModel()


class FlowLayout(QLayout):
    def __init__(self, parent=None):
        super(FlowLayout, self).__init__(parent)

        if parent is not None:
            self.setContentsMargins(QMargins(4, 4, 4, 4))

        self._item_list = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self._item_list.append(item)

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if index >= 0 and index < len(self._item_list):
            return self._item_list[index]

        return None

    def takeAt(self, index):
        if index >= 0 and index < len(self._item_list):
            return self._item_list.pop(index)

        return None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self._do_layout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()

        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())

        size += QSize(2 * self.contentsMargins().top(),
                      2 * self.contentsMargins().top())
        return size

    def _do_layout(self, rect, test_only):
        x = rect.x()
        y = rect.y()
        line_height = 0
        spacing = self.spacing()

        for item in self._item_list:
            style = item.widget().style()
            layout_spacing_x = style.layoutSpacing(QSizePolicy.PushButton,
                                                   QSizePolicy.PushButton,
                                                   Qt.Horizontal)
            layout_spacing_y = style.layoutSpacing(QSizePolicy.PushButton,
                                                   QSizePolicy.PushButton,
                                                   Qt.Vertical)
            space_x = spacing + layout_spacing_x
            space_y = spacing + layout_spacing_y
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y()
