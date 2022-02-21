import datetime
import time
from functools import partial

import numpy as np
from PySide6.QtCore import QObject, QRect, QSignalBlocker, QSize, Signal, Slot
from PySide6.QtGui import (QCursor, QFont, QIcon, QPainter, QStandardItemModel,
                           Qt, QTextDocument)
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QFrame,
                               QGridLayout, QLabel, QListView, QMenu,
                               QSizePolicy, QSpacerItem, QSpinBox,
                               QStyledItemDelegate, QStyleOptionViewItem,
                               QTextBrowser, QWidget)

from library.config import RELIC_PREFS
from library.objectmodels import (session, allCategories, alusers, polymorphicItem,
                                  relationships, subcategory, tags, attachLinkToAsset)
from library.widgets.util import ListViewFiltered, modifySVG, rasterizeSVG

from sequencePath import sequencePath as Path

TYPE_LABELS = ['Component', 'Asset', 'Collection', 'Motion', 'Variant',
    'Reference']
TYPE_ICONS = [QIcon(':/resources/asset_types/{}.svg'.format(x.lower())) for x in TYPE_LABELS]
CATEGORY_ICONS = [QIcon(':/resources/categories/{}.svg'.format(x.lower())) for x in allCategories.slots]

class UpdatableField(QObject):

    @Slot()
    def updateValue(self, value):
        """If in edit mode updates the database using the fields class name 
        minus the "Widget" suffix.

        Parameters
        ----------
        value : serializable (str, int, list)  
            the new field value 
        """
        if int(RELIC_PREFS.edit_mode):
            field = self.__class__.__name__.replace('Widget', '')
            if field == 'type':
                value += 1
            for asset in self.parent().selected_assets:
                setattr(asset, field, value)
                asset.update(fields=[field])


class MetaLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super(MetaLabel, self).__init__(*args, **kwargs)
        font = QFont()
        font.setPointSize(8)
        font.setBold(True)
        self.setFont(font)

class metadataFormView(QFrame):

    openDescription = Signal(Path)

    def __init__(self, *args, **kwargs):
        super(metadataFormView, self).__init__(*args, **kwargs)
        self.layout = QGridLayout(self)
        self.setAutoFillBackground(True)

    def clearLayout(self):
        layout = self.layout
        for i in reversed(range(layout.count())): 
            item = layout.itemAt(i)
            w = item.widget()
            if isinstance(item, (QSpacerItem, QHLine)):
                layout.takeAt(i)
            elif w:
                w.hide()
                if isinstance(w, metadataRelationView):
                    w.clear()
                elif not isinstance(w, (QHLine, MetaLabel)):
                    w.reset()
                

    def createWidget(self, label, value):
        # Create our widget from globals
        meta_constructor = globals()[label+'Widget']
        meta_widget = meta_constructor(self)
        meta_label = MetaLabel(label.capitalize() + ' :')
        return meta_widget, meta_label

    def loadAssets(self, assets):
        self.clearLayout()
        self.selected_assets = assets
        asset = assets[-1]
        line_offset = 0
        for i, label, value in asset:
            try:
                if hasattr(self, label):
                    meta_widget = getattr(self, label)
                    meta_label = getattr(self, label+'Label')
                else:
                    meta_widget, meta_label = self.createWidget(label, value)
                    setattr(self, label, meta_widget)
                    setattr(self, label+'Label', meta_label)
                if isinstance(meta_widget, classWidget):
                    meta_widget.enableClassBoxFilter(asset.category)
                if value:
                    meta_widget.setValue(value)

                if isinstance(value, list):
                    meta_label.setText('{} : {} '.format(label.capitalize(), len(value)))

                self.layout.addWidget(meta_label, line_offset, 0, 1, 1, Qt.AlignTop)
                self.layout.addWidget(meta_widget, line_offset, 1, 1, 1, Qt.AlignRight | Qt.AlignTop)

                self.layout.addWidget(QHLine(), line_offset + 1, 0, 1, 2)
                self.layout.addWidget(QHLine(), line_offset + 1, 1, 1, 2)
                meta_label.show()
                meta_widget.show()
            except Exception as exerr:
                #print('No widget for {}'.format(exerr))
                pass
            line_offset += (i + 2)

        spacer = QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout.addItem(spacer)

class baseRating(QWidget, UpdatableField):

    def __init__(self, *args, **kwargs):
        super(baseRating, self).__init__(*args, **kwargs)
        self.rating = 0
        self.setCount(5)
        self.setSpaces()
        self.setMinimumHeight(18)

    def reset(self):
        self.setValue(0)

    def setCount(self, count):
        self.count = count + 1

    def setValue(self, rating):
        self.rating = rating

    def setSpaces(self):
        """Gets the width of the widget and creates range of evenly
        spaced clickable images.
        """
        self.spaces = np.linspace(0, self.width(), self.count)

    def setRepeatImage(self, img_path):
        self.img = rasterizeSVG(img_path)
        find = r'rgb\([0-9]+,[0-9]+,[0-9]+\)'
        replace = 'rgb(100,100,100)'
        self.img_disabled = modifySVG(
            img_path, find, replace, regex=True, size_override=QSize(28,28)
        )

    def resizeEvent(self, event):
        super(baseRating, self).resizeEvent(event)
        self.setSpaces()

    def mousePressEvent(self, event):
        super(baseRating, self).mousePressEvent(event)
        if event.buttons() == Qt.LeftButton:
            # Get the closest rating index by relative click position
            axis = event.x()
            previous = self.rating
            for i, x in enumerate(self.spaces):
                if axis > x - (self.spaces[1]):
                    new = i
                    self.rating = new
            if new != previous:
                self.updateValue(new)

    def paintEvent(self, event):
        super(baseRating, self).paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        offset = 40  # inital offset to increment
        spacing = self.spaces[1]

        # Draw all disabled images
        for i, x in enumerate(self.spaces):
            rect = QRect(x, 0, spacing, spacing)
            painter.drawPixmap(rect, self.img_disabled)

            # Draw Enabled images in range up the current value
            if i < self.rating:
                painter.drawPixmap(rect, self.img)
                offset += 40


class baseSpinBox(QSpinBox):
    def __init__(self, *args, **kwargs):
        super(baseSpinBox, self).__init__(*args, **kwargs)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._createContextMenus)
        self.setMaximum(100000)

    @Slot()
    def _createContextMenus(self, value):
        context_menu = QMenu(self)
        if int(RELIC_PREFS.edit_mode):
            update_action = context_menu.addAction('Update')
            update_action.triggered.connect(self.update_asset)
        context_menu.exec(QCursor.pos())

    @Slot()
    def update_asset(self):
        self.updateValue(self.value())

    def reset(self):
        self.setValue(0)


class baseLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super(baseLabel, self).__init__(*args, **kwargs)

    def setValue(self, value):
        self.setText(str(value))
    
    def reset(self):
        self.clear()


class dateLabel(baseLabel):
    def __init__(self, *args, **kwargs):
        super(dateLabel, self).__init__(*args, **kwargs)

    def setValue(self, value):
        date = datetime.datetime.strptime(value,'%Y-%m-%d %H:%M:%S.%f')
        self.setText(date.strftime("%b %d, %Y %H:%M"))


class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class QVLine(QFrame):
    def __init__(self):
        super(QVLine, self).__init__()
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Sunken)


class relationDelegate(QStyledItemDelegate):

    def paint(self, painter, option, index):
        option.decorationPosition = QStyleOptionViewItem.Left
        #option.decorationAlignment = (QStyleOptionViewItem.Left | Qt.AlignVCenter)

        super(relationDelegate, self).paint(painter, option, index)

    def sizeHint(self, option, index):
        bounds = option.fontMetrics.boundingRect(
            option.rect, 0, str(index.data(Qt.DisplayRole))
        )
        return bounds.size() + QSize(option.decorationSize.width() * 3, 6)


class tagListViewer(ListViewFiltered):

    def __init__(self, parent):
        super(tagListViewer, self).__init__(parent)
        self.checked_db = False
        session.searchcategory.callback.connect(self.filterCallback)

    @Slot(list)
    def filterCallback(self, results):
        for x in results:
            tag = tags(*x)
            tag_item = polymorphicItem(fields=tag)
            self.itemModel.appendRow(tag_item)

    def filterRegExpChanged(self):
        # Search database
        text = self.searchBox.text()
        if len(text) >= 3 and not self.checked_db:
            self.checked_db = True
            session.searchcategory.execute('tags', text)
        elif len(text) == 0:
            self.checked_db = False
            self.proxyModel.setFilterRegularExpression(None)
            self.itemModel.clear()
        else:
            super(tagListViewer, self).filterRegExpChanged()

    def sizeHint(self):
        return QSize(275, 250)


class userListViewer(ListViewFiltered):

    def __init__(self, parent):
        super(userListViewer, self).__init__(parent)
        self.checked_db = False
        session.searchcategory.callback.connect(self.filterCallback)


    @Slot(list)
    def filterCallback(self, results):
        for x in results:
            user = alusers(*x)
            user_item = polymorphicItem(fields=user)
            self.itemModel.appendRow(user_item)

    def filterRegExpChanged(self):
        # Search database
        text = self.searchBox.text()
        if len(text) >= 3 and not self.checked_db:
            self.checked_db = True
            session.searchcategory.execute('alusers', text)
        elif len(text) == 0:
            self.checked_db = False
            self.proxyModel.setFilterRegularExpression(None)
            self.itemModel.clear()
        else:
            super(userListViewer, self).filterRegExpChanged()

    def sizeHint(self):
        return QSize(275, 250)


class metadataRelationView(QListView):

    def __init__(self, parent):
        super(metadataRelationView, self).__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setItemDelegate(relationDelegate())
        self.setFlow(QListView.LeftToRight)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setViewMode(QListView.IconMode)
        self.setIconSize(QSize(16, 16))
        self.setResizeMode(QListView.Adjust)
        self.setMovement(QListView.Static)
        self.setWordWrap(False)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.lastClickTime = time.time()
        self.setMinimumHeight(32)
        self.setUniformItemSizes(False)

        self.icons = {}
        self.defaultIcon = QIcon()
        self.itemModel = QStandardItemModel(self)
        self.setModel(self.itemModel)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._createContextMenus)
        self.setStyleSheet('background-color: rgb(43, 43, 43);padding: 2px;')
        self.constructor = None
        self.last_selection = None

    @Slot()
    def onLinkItem(self, primary_asset):
        item = polymorphicItem(fields=primary_asset)
        relations = []
        for asset in self.parent().selected_assets:
            relation = [primary_asset.relationMap, primary_asset.id, asset.links]
            relations.append(relation)
            attachLinkToAsset(asset, item)

        session.createrelationships.execute(relations)
        self.addItems([item])

    @Slot()
    def createNewItem(self, name):
        if self.last_selection:
            return
        primary_asset = self.constructor(name=name)
        id_mapping = []
        self.last_selection = self.parent().selected_assets
        for asset in self.last_selection:
            id_mapping.append([primary_asset.relationMap, asset.links])

        primary_asset.createNew(id_mapping)

    @Slot(dict)
    def onCreate(self, data):
        if not self.last_selection:
            return
        for category_name, assets in data.items():
            for fields in assets:
                asset = self.constructor(**fields)
                item = polymorphicItem(fields=asset)
                for downstream in self.last_selection:
                    if isinstance(asset, tags):
                        downstream.tags.append(item)
                    elif isinstance(asset, alusers):
                        downstream.alusers.append(item)
                self.addItems([item])
        self.last_selection = None

    def _createContextMenus(self, value):
        context_menu = QMenu(self)
        if int(RELIC_PREFS.edit_mode):
            new_action = context_menu.addAction("Add New")
            new_action.triggered.connect(self.relationalDataLinks.show)
            remove_action = context_menu.addAction("Remove Selected")
            remove_action.triggered.connect(self.removeSelectedItems)

        context_menu.exec(QCursor.pos())

    def removeSelectedItems(self):
        selection = reversed(sorted(self.selectedIndexes()))
        relations = []
        primary_asset = self.parent().selected_assets[-1]
        for x in selection:
            item = x.data(polymorphicItem.Object)
            relation = relationships(
                category_map=self.category_map,
                category_id=item.id,
                link=primary_asset.links,
            )
            relations.append(relation.export)
            if primary_asset.tags:
                for index, user in enumerate(primary_asset.tags):
                    if user.id == item.id:
                        primary_asset.tags.pop(index)
                        break
            if primary_asset.alusers:
                for index, user in enumerate(primary_asset.alusers):
                    if user.id == item.id:
                        primary_asset.alusers.pop(index)
                        break

            self.itemModel.takeRow(x.row())

        relationships.removeAll(relations)

    def sizeHint(self):
        return QSize(1920, 32)

    def setValue(self, value):
        if value:
            self.addItems(value, replace=True)

    def setDefaultIcon(self, icon):
        self.defaultIcon = icon

    def addItems(self, items, replace=False):
        if replace:
            self.clear()
        for asset in items:
            icon_map = self.icons.get(asset.type) or self.icons.get(0) 
            if icon_map:
                asset.setIcon(icon_map)
            else:
                asset.setIcon(self.defaultIcon)
            asset.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.itemModel.appendRow(asset)

    def clear(self):
        self.itemModel.clear()

    def mousePressEvent(self, event):
        index = self.indexAt(event.pos())
        if event.button() == Qt.LeftButton:
            timediff = -(self.lastClickTime - time.time())
            if float(timediff) < float(0.25):
                self.relationalDataLinks.show()
            self.lastClickTime = time.time()

        return super(metadataRelationView, self).mousePressEvent(event)
        

    def sizeHint(self):
        return QSize(1920, 32)


class tagsWidget(metadataRelationView):

    def __init__(self, parent=None):
        super(tagsWidget, self).__init__(parent)
        self.setMinimumHeight(72)

        self.icons = {
            0: QIcon(":/resources/app/tagIcon.svg"),
            1: QIcon(modifySVG(":/resources/app/tagIcon.svg", '(200,157,8)', '(175,115,250)')),
            2: QIcon(":/resources/app/plugin.svg")
        }
        self.category_map = 2
        # Item editor
        self.relationalDataLinks = tagListViewer(self)
        self.relationalDataLinks.hide()
        self.relationalDataLinks.newItem.connect(self.createNewItem)
        self.relationalDataLinks.linkItem.connect(self.onLinkItem)
        session.createtag.callback.connect(self.onCreate)
        self.constructor = tags


class alusersWidget(metadataRelationView):

    def __init__(self, parent=None):
        super(alusersWidget, self).__init__(parent)
        self.icons = {
            0: QIcon(":/resources/app/user.png"),
        }
        self.category_map = 1
        # Item editor
        self.relationalDataLinks = userListViewer(self)
        self.relationalDataLinks.hide()
        self.relationalDataLinks.newItem.connect(self.createNewItem)
        self.relationalDataLinks.linkItem.connect(self.onLinkItem)
        session.createuser.callback.connect(self.onCreate)
        self.constructor = alusers


class qualityWidget(baseRating):

    def __init__(self, *args, **kwargs):
        super(qualityWidget, self).__init__(*args, **kwargs)
        self.setRepeatImage(":/resources/app/star.svg")
        self.setCount(5)

    def sizeHint(self):
        return QSize(86, 38)


class ratingWidget(baseRating):

    def __init__(self, *args, **kwargs):
        super(ratingWidget, self).__init__(*args, **kwargs)
        self.setRepeatImage(":/resources/app/heart.svg")
        self.setCount(10)

    def sizeHint(self):
        return QSize(200, 36)


class descriptionWidget(QLabel, UpdatableField):
    def __init__(self, *args, **kwargs):
        super(descriptionWidget, self).__init__(*args, **kwargs)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setWordWrap(True)
        self.setTextInteractionFlags(
            Qt.LinksAccessibleByKeyboard|Qt.LinksAccessibleByMouse|
            Qt.TextBrowserInteraction|Qt.TextEditable|Qt.TextEditorInteraction|
            Qt.TextSelectableByKeyboard|Qt.TextSelectableByMouse)
        self.linkActivated.connect(self.onActivated)
        self.base_url = "<a style='color: rgb(92,108,245)' href=\"NONE\">{}</a>"
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._createContextMenus)

    def _createContextMenus(self, value):
        context_menu = QMenu(self)
        if int(RELIC_PREFS.edit_mode):
            update_action = context_menu.addAction('Update')
            update_action.triggered.connect(self.update_asset)
        context_menu.exec(QCursor.pos())

    def update_asset(self):
        parent = self.parent()
        selected = parent.selected_assets[-1]
        doc = self.findChild(QTextDocument)
        self.updateValue(doc.toPlainText())
        path = selected.network_path.suffixed('_description', '.md')
        with open(str(path), 'w') as fp:
            fp.write('')
        parent.openDescription.emit(path)

    @Slot()
    def onActivated(self, link_url):
        parent = self.parent()
        selected = parent.selected_assets[-1]
        path = selected.network_path.suffixed('_description', '.md')
        parent.openDescription.emit(path)

    def setValue(self, value):
        url = self.base_url.format(value) 
        self.setText(url)

    def sizeHint(self):
        return QSize(1920, 96)

    def reset(self):
        self._value = ''
        self.setText('No Description...')

class typeWidget(QComboBox, UpdatableField):

    LABELS = TYPE_LABELS
    ICONS = TYPE_ICONS

    def __init__(self, *args, **kwargs):
        super(typeWidget, self).__init__(*args, **kwargs)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setIconSize(QSize(22, 22))
        for index, icon in enumerate(self.ICONS):
            self.addItem(icon, self.LABELS[index])
        self.currentIndexChanged.connect(self.updateValue)

    def setValue(self, value):
        with QSignalBlocker(self):
            self.setCurrentIndex(int(value)-1)

    def reset(self):
        with QSignalBlocker(self):
            self.setCurrentIndex(0)


class classWidget(QComboBox, UpdatableField):

    classifications = [
        '',
        'Texture',
        'Model',
        'Animation',
        'Shader',
        'Area_Light',
        'IBL_Probe',
        'IES',
        '2D_Element',
        '3D_Element',
        'Reference',
        'Tool',
    ]
    class_by_category_id = {
        0: ['Reference',],
        1: ['Model',],
        2: ['2D_Element', '3D_Element',],
        3: ['Area_Light', 'IBL_Probe', 'IES',],
        4: ['Texture', 'Shader',],
        5: ['Tool',],
        6: ['Animation',]
    }
    def __init__(self, *args, **kwargs):
        super(classWidget, self).__init__(*args, **kwargs)
        for x in self.classifications:
            self.addItem(x)
        self.currentIndexChanged.connect(self.updateValue)

    def enableClassBoxFilter(self, category_id):

        acceptable_items = self.class_by_category_id.get(category_id, 'Tool')

        for i in range(self.model().rowCount()):
            index = self.model().index(i, 0)
            item = self.model().item(i, 0)
            if index.data() in acceptable_items:
                item.setEnabled(1)
            else:
                item.setEnabled(0)

    def setValue(self, value):
        with QSignalBlocker(self):
            self.setCurrentIndex(value)

    def reset(self):
        with QSignalBlocker(self):
            self.setCurrentIndex(0)


class datecreatedWidget(dateLabel):
    def __init__(self, *args, **kwargs):
        super(datecreatedWidget, self).__init__(*args, **kwargs)


class datemodifiedWidget(dateLabel):
    def __init__(self, *args, **kwargs):
        super(datemodifiedWidget, self).__init__(*args, **kwargs)


class resolutionWidget(baseLabel):
    def __init__(self, *args, **kwargs):
        super(resolutionWidget, self).__init__(*args, **kwargs)


class filesizeWidget(baseLabel):
    def __init__(self, *args, **kwargs):
        super(filesizeWidget, self).__init__(*args, **kwargs)

    def setValue(self, value):
        megabytes = "{:,} MB".format(int(value) / 1000)
        self.setText(megabytes)


class filehashWidget(baseLabel):
    pass

class proxyWidget(baseLabel):
    pass

class nameWidget(descriptionWidget):
    def __init__(self, *args, **kwargs):
        super(nameWidget, self).__init__(*args, **kwargs)

    def setValue(self, value):
        self.setText(value)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.update_asset()
        else:
            super(nameWidget, self).keyPressEvent(event)


class dependenciesWidget(baseSpinBox, UpdatableField):
    pass

class durationWidget(baseSpinBox, UpdatableField):
    def __init__(self, *args, **kwargs):
        super(durationWidget, self).__init__(*args, **kwargs)
        self.setSuffix(' Sec')

class framerateWidget(baseSpinBox, UpdatableField):
    def __init__(self, *args, **kwargs):
        super(framerateWidget, self).__init__(*args, **kwargs)
        self.setSuffix(' fps')

class nodecountWidget(baseLabel):
    pass

class idWidget(baseLabel):
    pass

class linksWidget(baseLabel):
    pass

class pathWidget(descriptionWidget):
    def __init__(self, *args, **kwargs):
        super(pathWidget, self).__init__(*args, **kwargs)

    def setValue(self, value):
        self.setText(str(value))

    def reset(self):
        self._value = ''
        self.setText('None')

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.update_asset()
        else:
            super(pathWidget, self).keyPressEvent(event)

class categoryWidget(QComboBox):

    LABELS = allCategories.slots
    ICONS = CATEGORY_ICONS

    def __init__(self, *args, **kwargs):
        super(categoryWidget, self).__init__(*args, **kwargs)
        self.setIconSize(QSize(22, 22))
        for index, icon in enumerate(self.ICONS):
            self.addItem(icon, self.LABELS[index].capitalize())
        self.setEditable(False)

    def setValue(self, value):
        if value:
            self.setCurrentIndex(int(value))

    def reset(self):
        self.setCurrentIndex(0)


class subcategoryWidget(QComboBox):

    def __init__(self, *args, **kwargs):
        super(subcategoryWidget, self).__init__(*args, **kwargs)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setIconSize(QSize(22, 22))
        self.setEditable(False)

    def setValue(self, value):
        self.clear()
        icon = QIcon(':/resources/general/folder.svg')
        try:
            self.addItem(icon, value[0].name)
        except Exception as exerr:
            self.addItem(icon, str(value))

    def reset(self):
        self.setCurrentIndex(0)
