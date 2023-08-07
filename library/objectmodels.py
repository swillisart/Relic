from collections import Sequence, UserString
from enum import IntEnum

from extra_types.flag_enum import FlagEnumAuto, EnumAuto, Flag, Enumerant
from extra_types.properties import slot_property
from extra_types.composable import SlotsCompose, Composable
from extra_types import Duration

from PySide6.QtCore import QObject, QRect, QSettings, Qt, Slot, QFile
from PySide6.QtGui import QColor, QIcon, QStandardItem, QImage, QFont, QPainterPath
import relic.config as config
from relic.qt.delegates import (IMAGE_CACHE, CompactImageIndicator,PreviewImageIndicator, ColorIndicator, Title, BaseItemDelegate, IconIndicator, TextDecorationIndicator, ProgressIndicator,
                                TitleIndicator, TextIndicator, Statuses, Indication, ItemDispalyModes, AdvanceAxis, flipRect)
from relic.gui import CategoryColor, TypeIndicator

from relic.base import Fields
from relic.local import (Alusers, Category, buildObjectMixinMap, Relationships,
                        Subcategory, Tags, TempAsset)
from relic.scheme import Table, AssetType, TagType, UserType
from sequence_path.main import SequencePath as Path

from library.io.networking import RelicClientSession

session = RelicClientSession(RelicClientSession.URI)

PROJECT_STORAGE = Path(config.PROJECT_STORAGE.format(project='relic'))
NETWORK_STORAGE = Path(config.NETWORK_STORAGE)

TL = Qt.AlignTop | Qt.AlignLeft
TR = Qt.AlignTop | Qt.AlignRight
BL = Qt.AlignBottom | Qt.AlignLeft
BR = Qt.AlignBottom | Qt.AlignRight


class DurationIndicator(object):

    def __init__(self, duration):
        self.value = str(Duration(duration)) if duration else ''

    @staticmethod
    def draw(painter, text, bounds, align):
        new_font = QFont('Ebrima', 8, QFont.Normal)
        new_font.setStyleHint(QFont.TypeWriter) 
        painter.setFont(new_font)        
        painter.setPen(QColor(175, 175, 175))
        text_repr = str(text)
        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(text_repr)
        text_rect = QRect(2, 2, text_width, metrics.height())
        rect = flipRect(text_rect, align, bounds)
        bounding_rect = rect.adjusted(-2, -1, 2, 1)
        painter.fillRect(bounding_rect, QColor(43,43,43))
        painter.drawText(rect, text_repr)
        return bounding_rect


class CountIndicator(object):

    def __init__(self, count):
        self.value = count

    @staticmethod
    def draw(painter, text, bounds, align):
        if text == '0':
            return QRect()
        text_repr = '({})'.format(text)
        new_font = QFont('Ebrima', 9, QFont.Normal)
        new_font.setStyleHint(QFont.TypeWriter) 
        painter.setFont(new_font)
        painter.setPen(QColor(175, 175, 175))
        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(text_repr)
        text_rect = QRect(2, 2, text_width, metrics.height())
        rect = flipRect(text_rect, align, bounds)
        bounding_rect = rect.adjusted(-2, 0, 2, 0)
        painter.drawText(rect, text_repr)
        return bounding_rect


class ExtentIndicator(object):

    def __init__(self, text):
        self.value = text

    @staticmethod
    def draw(painter, text, bounds, align):
        text_repr = str(text)
        if text_repr == '0':
            return QRect()
        new_font = QFont('Ebrima', 9, QFont.Normal)
        new_font.setStyleHint(QFont.TypeWriter)
        painter.setFont(new_font)
        painter.setPen(QColor(200, 200, 200))
        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(text_repr)
    
        text_rect = QRect(1, 1, text_width, metrics.height())
        rect = flipRect(text_rect, align, bounds)
        path = QPainterPath()
        bounding_rect = rect.adjusted(-2, 2, 2, -1)
        path.addRoundedRect(bounding_rect, 4, 4)
        painter.fillPath(path, QColor(92,92,92))
        painter.drawText(rect, text_repr)
        return bounding_rect


class FieldMixin(object):
    # TODO: Add ImageableMixin for the image handling in delegates
    __slots__ = ()

    INDICATIONS = []

    def __init__(self, *args, **kwargs):
        super(FieldMixin, self).__init__(*args, **kwargs)

    @staticmethod
    def setIndications(value):
        FieldMixin.INDICATIONS.clear()
        BaseItemDelegate.VIEW_MODE = ItemDispalyModes[value]
        if value == ItemDispalyModes.TREE:
           FieldMixin.INDICATIONS.extend([
                Indication('category', CategoryColor, BL, AdvanceAxis.X),
                Indication('title', TitleIndicator, TL, AdvanceAxis.X),
                #Indication('type', TypeIndicator, BR, AdvanceAxis.X),
                Indication('count', CountIndicator, BR, AdvanceAxis.X),
                #Indication('status', Statuses, BR, AdvanceAxis.X),
            ])
        if value == ItemDispalyModes.COMPACT:
            FieldMixin.INDICATIONS.extend([
                Indication('image', CompactImageIndicator, TL, AdvanceAxis.X),
                Indication('category', CategoryColor, BL, AdvanceAxis.X),
                Indication('title', TitleIndicator, TL, AdvanceAxis.NONE),
                Indication('type', TypeIndicator, BL, AdvanceAxis.X),
                Indication('resolution', ExtentIndicator, BL, AdvanceAxis.X),
                #Indication('status', Statuses, BL, AdvanceAxis.NONE),
                Indication('duration', DurationIndicator, TR, AdvanceAxis.NONE),
                Indication('count', CountIndicator, BR, AdvanceAxis.NONE),
            ])
        elif value == ItemDispalyModes.THUMBNAIL:
            FieldMixin.INDICATIONS.extend([
                Indication('image', PreviewImageIndicator, TL, AdvanceAxis.Y),
                Indication('progress', ProgressIndicator, TL, AdvanceAxis.Y),
                Indication('category', CategoryColor, BL, AdvanceAxis.X),
                Indication('title', TitleIndicator, TL, AdvanceAxis.NONE),
                Indication('type', TypeIndicator, BL, AdvanceAxis.X),
                Indication('resolution', ExtentIndicator, BL, AdvanceAxis.X),
                #Indication('status', Statuses, BL, AdvanceAxis.NONE),
                Indication('count', CountIndicator, BR, AdvanceAxis.NONE),
                Indication('duration', DurationIndicator, TR, AdvanceAxis.NONE),
            ])

    @property
    def icon(self):
        return self._icon

    @icon.setter
    def icon(self, image):
        if isinstance(image, QImage):
            key = image.cacheKey()
            IMAGE_CACHE[key] = image
        else:
            key = image or ''
        self._icon = key

    def __del__(self):
        try:
            IMAGE_CACHE.pop(self._icon)
            [IMAGE_CACHE.pop(x) for x in self.video]
        except:
            pass # already deleted or not in cache

    @property
    def image(self):
        return self.icon

    @slot_property
    def title(self):
        return Title(self.name)

    @property
    def relationMap(self):
        return int(Table[self.categoryName])

    def update(self, fields=None):
        data = self.export
        export_data = {}
        fields = fields + ['id'] if isinstance(fields, list) else self.__slots__

        for x in data:
            if self.getLabel(x) in fields:
                if not isinstance(data[x], tuple):
                    export_data[x] = (data[x],)
        update_data = {self.categoryName: export_data}
        session.updateassets.execute(update_data)

    def remove(self):
        if isinstance(self.id, int):
            ids = (self.id, )
        else:
            ids = self.id

        if hasattr(self, 'path'):
            session.deleteassets.execute([str(self.relativePath.parent)])

        session.removeassets.execute({self.categoryName: ids})

    def createNew(self):
        data = {self.categoryName: [self.export]}
        session.createassets.execute(data)

    @staticmethod
    def removeAll(relations):
        session.removerelationships.execute(relations)

    def linkTo(self, downstream):
        relation = relationships(
            category_map=self.relationMap,
            category_id=self.id,
            links=downstream.links,
        )
        relation.create()

    def unlinkTo(self, asset):
        relation = relationships(
            category_map=self.relationMap,
            category_id=self.id,
            links=asset.links,
        )
        relationships.removeAll([relation.export])

    def getLabel(self, i):
        return self.__slots__[i]

    @property
    def local_path(self):
        return PROJECT_STORAGE / str(self.relativePath)

    @property
    def network_path(self):
        return NETWORK_STORAGE / str(self.relativePath)

    @property
    def icon_path(self):
        return self.network_path.suffixed('_icon', '.jpg')

    @property
    def relativePath(self):
        stem = str(self.path).rsplit('/', 1)[-1]
        partial_path = Path(self.categoryName) / str(self.path)
        return partial_path.parents(0) / partial_path.name / stem

    def fetchIcon(self):
        rc = 'retrieveIcon/{}'.format(self.icon_path)
        db.accessor.doStream(rc, self.id)

    def stream_video_to(self, slot=None):
        video_path = self.relativePath.suffixed('_icon', ext='.mp4')
        session.videostream.execute(str(video_path))

    @property
    def export(self):
        indexed_attributes = {}
        for i, x in enumerate(self.__slots__):
            attr = getattr(self, x)
            # Convert to id if morphic object.
            # Only allow json serializable data.
            if attr is None:
                continue
            elif isinstance(attr, (str, Path, UserString)):
                attr = str(attr)
            elif isinstance(attr, int):
                attr = int(attr)
            elif isinstance(attr, tuple): # Sequence
                pass #attr = tuple(attr)
            elif isinstance(attr, QStandardItem):
                relation = attr.data(Qt.UserRole)
                if relation:
                    attr = relation.export
                else:
                    continue
            else:
                continue

            indexed_attributes[i] = attr

        return indexed_attributes

    @property
    def labels(self):
        return tuple(x for x in self.__slots__ if getattr(self, x) is not None)

    @property
    def values(self):
        return [getattr(self, x) for x in self.__slots__]

    @staticmethod
    def recurseDependencies(asset):
        """Recursively accesses an assets upstream dependencies.
        """
        variant = AssetType.VARIANT
        if isinstance(asset.upstream, list):
            for upstream in asset.upstream:
                if upstream.type != variant:
                    yield from FieldMixin.recurseDependencies(upstream)
        yield asset

    def createCollection(self, link_mapping):
        if self.type != Type.COLLECTION:
            return
        data = {
            self.categoryName: self.export,
            'link_map': link_mapping 
        }
        session.createcollection.execute(data)

    @property
    def count(self):
        return self.dependencies

TempAsset.INDICATIONS = FieldMixin.INDICATIONS

# TODO: TEMPORARY solution for ingestion methods without inheritance.
#      this should be refactored to better handle temporary assets.
TempAsset.icon = FieldMixin.icon
TempAsset.image = FieldMixin.image
TempAsset.__del__ = FieldMixin.__del__
TempAsset.title = FieldMixin.title
# END TEMPORARY SOLUTION

class Library(QObject):

    categories = []
    assets = []
    assets_filtered = []

    def __init__(self):
        super(Library, self).__init__()

    def validateCategories(self, categories):
        if not categories:
            categories = dict.fromkeys(range(len(Category)))
        return categories

    def fetchCategories(self):
        # fill empty categories
        for x in Category:
            empty_category = category(x.name, x.value)
            self.categories.append(empty_category)

        session.getcategories.execute([])

class category(object):
    def __init__(self, name, id):
        self.name = name.capitalize()
        self.id = id
        self.count = 0
        self.subcategory_by_id = {}
        self.tree = None # QTreeView
        self.tab = None # TabWidget


@SlotsCompose.add('value')
class FolderIconIndicator(Composable):

    @staticmethod
    def draw(painter, icon, bounds, align):
        rect = flipRect(QRect(0, 0, 16, 16), align, bounds)
        icon.paint(painter, rect)
        return rect

    def value(self, value):
        fp = ':resources/subcategories/{}.png'.format(value)
        resource = fp if QFile.exists(fp) else ':app/folder.svg'
        return QIcon(resource)


class subcategory(Subcategory, FieldMixin):
    """
    >>> repr(subcategory(name='test', category=0))
    "subcategory(name='test', id=None, category=0, links=None, count=None, )"
    """

    LINK_CALLBACK = None 
    INDICATIONS = [
        Indication('name', FolderIconIndicator, TL, AdvanceAxis.X),
        Indication('title', TitleIndicator, TL, AdvanceAxis.X),
    ]

    def createNew(self):
        data = {self.categoryName: [self.export]}
        session.createsubcategory.execute(data)

    def relocate(self, old_parent=None, new_parent=None):
        """Relocates the subcategory to a new parent or root level.

        Parameters
        ----------
        old_parent : subcategory
            source parent subcategory to update
        new_parent : subcategory, optional
            destination parent subcategory, by default None
        """
        data = {}
        if old_parent:
            data[old_parent.id] = -self.count

        if new_parent:
            data[new_parent.id] = self.count
        self.update(fields=['links'])
        session.updatesubcategorycounts.execute(data)
    
    def relink(self):
        relation = relationships(
            category_map=self.relationMap,
            category_id=self.upstream,
        )
        session.linksubcategories.execute([relation.export])

    def unlink(self):
        """Clears the subcategory "link" field (setting to 0 to make top level).
        Removes the subcategory->subcategory relationship entries.
        """

        relation = relationships(
            category_map=self.relationMap,
            category_id=self.upstream,
            links=self.links,
        )
        relationships.removeAll([relation.export])
        self.links = 0

    @staticmethod
    def _onRelink(obj, links, old_parent=None, new_parent=None):
        obj.links = links
        obj.relocate(old_parent, new_parent)

    @classmethod
    def onRelink(cls, links):
        if cls.LINK_CALLBACK:
            for link in links:
                cls.LINK_CALLBACK(link)
            cls.LINK_CALLBACK = None


user_type_data = {x.name: ':UserType/{}'.format(x.name) for x in UserType}
UserTypeIndicator = EnumAuto.fromDataConstructor('UserTypeIndicator', user_type_data, IconIndicator)

tag_type_data = {x.name: ':TagType/{}'.format(x.name) for x in TagType}
TagTypeIndicator = EnumAuto.fromDataConstructor('TagTypeIndicator', tag_type_data, IconIndicator)


class tags(Tags, FieldMixin):

    INDICATIONS = [
        Indication('type', TagTypeIndicator, TL, AdvanceAxis.X),
        Indication('title', TitleIndicator, TL, AdvanceAxis.X),
    ]
    def createNew(self, id_mapping):
        data = {
            self.categoryName: [self.export],
            'id_map': id_mapping
        }
        session.createtag.execute(data)

class alusers(Alusers, FieldMixin):

    INDICATIONS = [
        Indication('type', UserTypeIndicator, TL, AdvanceAxis.X),
        Indication('title', TitleIndicator, TL, AdvanceAxis.X),
    ]
    def createNew(self, id_mapping):
        data = {
            self.categoryName: [self.export],
            'id_map': id_mapping
        }
        session.createuser.execute(data)

class relationships(Relationships, FieldMixin):

    def create(self):
        relation = [self.category_map, self.category_id, self.links]
        session.createrelationships.execute([relation])

relational_map = {
    'relationships': relationships,
    'alusers': alusers,
    'tags': tags,
    'subcategory': subcategory,
}

OBJECT_MAP = buildObjectMixinMap(FieldMixin)
OBJECT_MAP.update(relational_map)

def getCategoryConstructor(category):
    constructor = OBJECT_MAP.get(category, TempAsset)
    return constructor

def appendCreate(asset, name, new):
    value = getattr(asset, name)

    if isinstance(value, list):
        value.append(new)
        setattr(asset, name, value)
    else:
        setattr(asset, name, [new])

def attachSubcategory(asset, category_obj):
    for _subcategory in category_obj.subcategory_by_id.values():
        if str(asset.path).startswith(_subcategory.name):
            asset.subcategory = _subcategory

def attachLinkToAsset(primary_asset, link_asset):
    category_name = link_asset.categoryName
    if isinstance(link_asset, subcategory):
        primary_asset.subcategory = link_asset
    elif hasattr(primary_asset, category_name):
        appendCreate(primary_asset, category_name, link_asset)
    else:
        try:
            link_asset.path = Path(link_asset.path)
        except:pass
        category_id = int(Category[category_name.upper()])
        link_asset.category = category_id
        category_obj = Library.categories[category_id]
        attachSubcategory(link_asset, category_obj)
        appendCreate(primary_asset, 'upstream', link_asset)
        appendCreate(link_asset, 'downstream', primary_asset)
