from collections import Sequence, UserString
from enum import IntEnum

from extra_types.flag_enum import FlagEnumAuto, EnumAuto, Flag, Enumerant
from extra_types.properties import slot_property

from PySide6.QtCore import QObject, QRect, QSettings, Qt, Slot
from PySide6.QtGui import QColor, QIcon, QStandardItem, QImage
import relic.config as config
from relic.qt.delegates import (IMAGE_CACHE, CompactImageIndicator,PreviewImageIndicator, ColorIndicator, Title, BaseItemDelegate, IconIndicator, TextDecorationIndicator, ProgressIndicator,
                                TitleIndicator, TextIndicator, Statuses, Indication, ItemDispalyModes, AdvanceAxis)
from relic.gui import CategoryColor, TypeIndicator

from relic.base import Fields
from relic.local import (Alusers, Category, buildObjectMixinMap, Relationships,
                        Subcategory, Tags, TempAsset)
from relic.scheme import Table, AssetType
from sequence_path.main import SequencePath as Path

from library.io.networking import RelicClientSession

session = RelicClientSession(RelicClientSession.URI)

PROJECT_STORAGE = Path(config.PROJECT_STORAGE.format(project='relic'))
NETWORK_STORAGE = Path(config.NETWORK_STORAGE)

#res_uri = ':{}/{}'
#types = {x.name: QIcon(res_uri.format(AssetType.__name__, x.name)) for x in AssetType}
'''
CategoryColor = EnumAuto.fromDataConstructor('CategoryColor',
    {
        '__order__': Category.__order__,
        'REFERENCES': (168, 58, 58),
        'MODELING': (168, 58, 58),
        'REFERENCES': (168, 58, 58),
        'REFERENCES': (168, 58, 58),
    },
    ColorIndicator,
)
'''

TL = Qt.AlignTop | Qt.AlignLeft
TR = Qt.AlignTop | Qt.AlignRight
BL = Qt.AlignBottom | Qt.AlignLeft
BR = Qt.AlignBottom | Qt.AlignRight
'''
print('display', int(Qt.DisplayRole))
print('decor', int(Qt.DecorationRole))
print('edit', int(Qt.EditRole))
print('tooltip', int(Qt.ToolTipRole))
print('statusbartip', int(Qt.StatusTipRole))
print('sizehint', int(Qt.SizeHintRole))
print('checkable', int(Qt.CheckStateRole))
print('user', int(Qt.UserRole))
'''

class FieldMixin(object):
    # TODO: Add ImageableMixin for the image handling in delegates
    __slots__ = ()

    INDICATIONS = []

    def __init__(self, *args, **kwargs):
        super(FieldMixin, self).__init__(*args, **kwargs)

    @staticmethod
    def setIndications(value):
        BaseItemDelegate.VIEW_MODE = ItemDispalyModes[value]
        if value == ItemDispalyModes.TREE:
           FieldMixin.INDICATIONS = [
                Indication('category', CategoryColor, BL, AdvanceAxis.X),
                Indication('title', TitleIndicator, TL, AdvanceAxis.X),
                #Indication('type', TypeIndicator, BR, AdvanceAxis.X),
                Indication('count', TextIndicator, BR, AdvanceAxis.X),
                Indication('status', Statuses, BR, AdvanceAxis.X),
            ]
        if value == ItemDispalyModes.COMPACT:
            FieldMixin.INDICATIONS = [
                Indication('image', CompactImageIndicator, TL, AdvanceAxis.X),
                Indication('category', CategoryColor, BL, AdvanceAxis.X),
                Indication('title', TitleIndicator, TL, AdvanceAxis.NONE),
                Indication('type', TypeIndicator, BL, AdvanceAxis.NONE),
                Indication('status', Statuses, BL, AdvanceAxis.NONE),
                Indication('count', TextIndicator, BR, AdvanceAxis.NONE),
            ]
        elif value == ItemDispalyModes.THUMBNAIL:
            FieldMixin.INDICATIONS = [
                Indication('image', PreviewImageIndicator, TL, AdvanceAxis.Y),
                Indication('progress', ProgressIndicator, TL, AdvanceAxis.Y),
                Indication('category', CategoryColor, BL, AdvanceAxis.X),
                Indication('title', TitleIndicator, TL, AdvanceAxis.NONE),
                Indication('type', TypeIndicator, BL, AdvanceAxis.NONE),
                Indication('status', Statuses, BL, AdvanceAxis.NONE),
                Indication('count', TextIndicator, BR, AdvanceAxis.NONE),
            ]

    @property
    def icon(self):
        return self._icon

    @icon.setter
    def icon(self, image):
        if isinstance(image, QImage):
            key = image.cacheKey()
            IMAGE_CACHE[key] = image
        else:
            key = image
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

class subcategory(Subcategory, FieldMixin):
    """
    >>> repr(subcategory(name='test', category=0))
    "subcategory(name='test', id=None, category=0, links=None, count=None, )"
    """

    LINK_CALLBACK = None 

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

class tags(Tags, FieldMixin):

    def createNew(self, id_mapping):
        data = {
            self.categoryName: [self.export],
            'id_map': id_mapping
        }
        session.createtag.execute(data)

class alusers(Alusers, FieldMixin):

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

def attachLinkToAsset(asset, link_item):
    link_item_asset = link_item.data(Qt.UserRole)
    category_name = link_item_asset.categoryName
    if isinstance(link_item_asset, subcategory):
        asset.subcategory = link_item
    elif hasattr(asset, category_name):
        appendCreate(asset, category_name, link_item)
    else:
        try:
            link_item_asset.path = Path(link_item_asset.path)
        except:pass
        category_id = int(Category[category_name.upper()])
        link_item_asset.category = category_id
        category_obj = Library.categories[category_id]
        attachSubcategory(link_item_asset, category_obj)
        appendCreate(asset, 'upstream', link_item)
        appendCreate(link_item, 'downstream', asset)
