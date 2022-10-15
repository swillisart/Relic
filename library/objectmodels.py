import sys
from collections import Sequence
from enum import IntEnum

from extra_types.enums import AutoEnum
from PySide6.QtCore import QObject, QRect, QSettings, Qt, Slot
from PySide6.QtGui import QColor, QPixmap
from relic.qt.delegates import (Indication, ColorIndicator, IconIndicator, Statuses,
                                 TextIndicator)
from qtshared6.utils import polymorphicItem
from relic.base import Fields
from relic.local import (Alusers, Category, Elements, Lighting, Mayatools,
                         Modeling, Nuketools, References, Relationships,
                         Shading, Software, Subcategory, Tags, TempAsset)
from relic.scheme import Table, AssetType
from sequence_path.main import SequencePath as Path

from library.config import RELIC_PREFS
from library.io.networking import RelicClientSession

session = RelicClientSession(RelicClientSession.URI)

LOCAL_STORAGE = Path(RELIC_PREFS.local_storage.format(project='relic'))
NETWORK_STORAGE = Path(RELIC_PREFS.network_storage)

colors = {x.name: QColor(*x.data.color) for x in Category}
types = {x.name: f':AssetType/{x.name}' for x in AssetType}

CategoryColor = ColorIndicator('CategoryColor', colors)
Type = IconIndicator('Type', types)

class FieldMixin(object):
    __slots__ = ()

    INDICATIONS = [
        Indication('type', Type, QRect(12, -22, 16, 16)),
        Indication('category', CategoryColor, QRect(6, -6, 3, -48)),
        Indication('status', Statuses, QRect(30, -22, 16, 16)),
        Indication('resolution', TextIndicator, QRect(50, -22, 0, 16))
    ]

    def __init__(self, *args, **kwargs):
        super(FieldMixin, self).__init__(*args, **kwargs)

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
        return LOCAL_STORAGE / str(self.relativePath)

    @property
    def network_path(self):
        return NETWORK_STORAGE / str(self.relativePath)

    @property
    def relativePath(self):
        stem = str(self.path).rsplit('/', 1)[-1]
        partial_path = Path(self.categoryName) / str(self.path)
        return partial_path.parents(0) / partial_path.name / stem

    def fetchIcon(self):
        icon_path = self.relativePath.suffixed('_icon', ext='.jpg')
        rc = 'retrieveIcon/{}'.format(icon_path)
        db.accessor.doStream(rc, self.id)

    def stream_video_to(self, slot=None):
        video_path = self.relativePath.suffixed('_icon', ext='.mp4')
        #rc = 'retrieveVideo/{}/0/0'.format(video_path)
        #db.accessor.videoStreamData.connect(slot)
        #db.accessor.doStream(rc, self.id)
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
            elif isinstance(attr, (str, Path)):
                attr = str(attr)
            elif isinstance(attr, int):
                attr = int(attr)
            elif isinstance(attr, tuple): # Sequence
                pass #attr = tuple(attr)
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
        if isinstance(asset.upstream, list):
            for upstream in asset.upstream:
                if upstream.type != Type.VARIANT:
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
        self.icon = ':/resources/categories/{}.svg'.format(name.lower())
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


class references(References, FieldMixin):
    pass

class modeling(Modeling, FieldMixin):
    pass

class elements(Elements, FieldMixin):
    pass

class software(Software, FieldMixin):
    pass

class lighting(Lighting, FieldMixin):
    pass

class shading(Shading, FieldMixin):
    pass

class nuketools(Nuketools, FieldMixin):
    pass

class mayatools(Mayatools, FieldMixin):
    pass


OBJECT_MAP = {
    0: references,
    1: modeling,
    2: elements,
    3: lighting,
    4: shading,
    5: software,
    6: mayatools,
    7: nuketools,
    'references': references,
    'modeling': modeling,
    'elements': elements,
    'lighting': lighting,
    'shading': shading,
    'software': software,
    'mayatools': mayatools,
    'nuketools': nuketools,
    'relationships': relationships,
    'alusers': alusers,
    'tags': tags,
    'subcategory': subcategory,
}

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
    link_item_asset = link_item.data(polymorphicItem.Object)
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
