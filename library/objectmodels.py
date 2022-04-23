import sys

from enum import IntEnum
from extra_types.enums import AutoEnum
from qtshared6.delegates import Statuses, TextIndicator, ColorIndicator, IconIndicator, scale_icon

from sequence_path.main import SequencePath as Path
from qtshared6.utils import polymorphicItem

from PySide6.QtGui import QColor, QPixmap
from PySide6.QtCore import Qt, QSettings, QObject, Slot, QRect

from library.io.networking import RelicClientSession
from library.config import RELIC_PREFS, Classification

session = RelicClientSession(RelicClientSession.URI)

LOCAL_STORAGE = Path(RELIC_PREFS.local_storage.format(project='relic'))
NETWORK_STORAGE = Path(RELIC_PREFS.network_storage)
serializable_types = [str, int, tuple]

class Type(IconIndicator):
    NONE = {}
    COMPONENT = {'data': scale_icon(QPixmap('resources/asset_types/component.svg'))}
    ASSET = {'data': scale_icon(QPixmap('resources/asset_types/asset.svg'))}
    COLLECTION = {'data': scale_icon(QPixmap('resources/asset_types/collection.svg'))}
    MOTION = {'data': scale_icon(QPixmap('resources/asset_types/motion.svg'))}
    VARIANT = {'data': scale_icon(QPixmap('resources/asset_types/variant.svg'))}
    REFERENCE = {'data': scale_icon(QPixmap('resources/asset_types/reference.svg'))}

class CategoryColor(ColorIndicator):
    references = {'data': QColor(168, 58, 58)}
    modeling = {'data': QColor(156, 156, 156)}
    elements = {'data': QColor(198, 178, 148)}
    lighting = {'data': QColor(188, 178, 98)}
    shading = {'data': QColor(168, 58, 198)}
    software = {'data': QColor(168, 168, 198)}
    mayatools = {'data': QColor(66, 118, 150)}
    nuketools = {'data': QColor(168, 168, 198)}


class BaseFields(object):
    __slots__ = ()

    class Indicators(AutoEnum):
        type =       {'data': Type, 'rect': QRect(12, -22, 16, 16)}
        category =   {'data': CategoryColor, 'rect': QRect(6, -6, 3, -48)}
        status =     {'data': Statuses, 'rect': QRect(30, -22, 16, 16)}
        resolution = {'data': TextIndicator, 'rect': QRect(50, -22, 0, 16)}

    def __init__(self, *args, **kwargs):
        if args:
            for i, x in enumerate(self.__slots__):
                try:
                    setattr(self, x, args[i])
                except:
                    setattr(self, x, None)
        else:
            for i, x in enumerate(self.__slots__):
                bykeword = kwargs.get(x)
                byindex = kwargs.get(str(i))
                attr = byindex if bykeword is None else bykeword
                setattr(self, x, attr)

    def __eq__(self, other):
        return self.id == other

    def __iter__(self):
        for i, x in enumerate(self.__slots__):
            attr = getattr(self, x)
            yield i, x, attr 

    def __str__(self):
        attrs = ', '.join(['{}: {}'.format(x, getattr(self, x)) for x in self.__slots__])
        return '<class {}> ({})'.format(self.categoryName, attrs) 

    def __repr__(self):
        args = ''
        for i, x in enumerate(self.__slots__):
            attr = getattr(self, x)
            if isinstance(attr, str):
                attr_fmt = "'{}'".format(attr)
            else:
                attr_fmt = attr
            args += "{}={}, ".format(x, attr_fmt)

        return '{}({})'.format(self.categoryName, args)

    @property
    def categoryName(self):
        return self.__class__.__name__.lower()

    @property
    def relationMap(self):
        return int(Category[self.categoryName.upper()])

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
            link=downstream.links,
        )
        relation.create()

    def unlinkTo(self, asset):
        relation = relationships(
            category_map=self.relationMap,
            category_id=self.id,
            link=asset.links,
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

            # Convert to id if morphic a object.
            if isinstance(attr, Path):
                attr = str(attr)

            # Only allow json serializable data.
            is_serial = [type(attr) is t for t in serializable_types]

            if attr is not None and any(is_serial):
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
                    yield from BaseFields.recurseDependencies(upstream)
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
    def thumbnail(self):
        return self.icon

    @thumbnail.setter
    def thumbnail(self, other):
        self.icon = other

    @property
    def count(self):
        return self.dependencies


class allCategories(QObject):
    slots = (
        'references',
        'modeling',
        'elements',
        'lighting',
        'shading',
        'software',
        'mayatools',
        'nuketools',
    )
    slot_range = range(len(slots))

    def __init__(self):
        super(allCategories, self).__init__()
        for i in allCategories.slot_range:
            setattr(self, self.slots[i], i)

    def __iter__(self):
        for i in allCategories.slot_range:
            yield self.get(i)

    def getLabel(self, i):
        return self.slots[i]

    def get(self, i):
        return getattr(self, self.slots[i])

    def set(self, i, data):
        return setattr(self, self.slots[i], data)

    def fetch(self):
        # fill empty categories
        for i in allCategories.slot_range:
            self.set(i, category(self.getLabel(i), i))
        session.getcategories.execute([])

class Library(QObject):

    categories = allCategories()
    assets = []
    assets_filtered = []

    def __init__(self):
        super(Library, self).__init__()
        
    def validateCategories(self, categories):
        if not categories:
            categories = dict.fromkeys(self.categories.slot_range)
        return categories

class category(object):
    def __init__(self, name, id):
        self.name = name.capitalize()
        self.id = id
        self.count = 0
        self.icon = ':/resources/categories/{}.svg'.format(self.name.lower())
        self.subcategory_by_id = {}
        self.tree = None # QTreeView
        self.tab = None # TabWidget

class subcategory(BaseFields):
    """
    >>> repr(subcategory(name='test', category=0))
    "subcategory(name='test', id=None, category=0, link=None, count=None, )"
    """
    __slots__ = (
        'name',
        'id',
        'category',
        'link',
        'count',
        'upstream', # This is not a modifiable database field.
    )

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

        self.update(fields=['link'])
        session.updatesubcategorycounts.execute(data)
    
    def relink(self):
        relation = relationships(
            category_map=self.relationMap,
            category_id=self.upstream,
        )
        session.linksubcategories.execute([relation.export])

    def unlink(self):
        relation = relationships(
            category_map=self.relationMap,
            category_id=self.upstream,
            link=self.link,
        )
        relationships.removeAll([relation.export])
        self.link = 0

    #def reparentSubcategoryToRoot(self, current, old_parent):
        # Set subcategory link to zero if making top level.

    @staticmethod
    def _onRelink(obj, link, old_parent=None, new_parent=None):
        obj.link = link
        obj.relocate(old_parent, new_parent)

    @classmethod
    def onRelink(cls, links):
        if cls.LINK_CALLBACK:
            for link in links:
                cls.LINK_CALLBACK(link)
        cls.LINK_CALLBACK = None

class tags(BaseFields):

    __slots__ = (
        'name',
        'id',
        'datecreated',
        'type',
        'links',
    )

    def createNew(self, id_mapping):
        data = {
            self.categoryName: [self.export],
            'id_map': id_mapping
        }
        session.createtag.execute(data)

class alusers(BaseFields):
    """
    >>> repr(alusers(name='swillis'))
    "alusers(name='swillis', id=None, datecreated=None, type=None, links=None, )"
    """
    __slots__ = (
        'name',
        'id',
        'datecreated',
        'type',
        'links',
    )

    def createNew(self, id_mapping):
        data = {
            self.categoryName: [self.export],
            'id_map': id_mapping
        }
        session.createuser.execute(data)

class relationships(BaseFields):
    """
    >>> repr(relationships(category_id=0, category_map=0))
    "relationships(id=None, link=None, category_id=0, category_map=0, )"
    """
    __slots__ = (
        'id',
        'link',
        'category_id',
        'category_map',
    )

    def create(self):
        relation = [self.category_map, self.category_id, self.link]
        session.createrelationships.execute([relation])

    @staticmethod
    def removeAll(relations):
        session.removerelationships.execute(relations)


class relic_asset:
    base = [
        'name',
        'id',
        'path',
        'description',
        'datecreated',
        'datemodified',
        'links',
        'resolution',
        'class',
        'rating',
        'proxy',
        'filesize',
        'quality',
        'type',
        'filehash',
        'dependencies',
    ]
    extra = [
        'tags',
        'alusers',
        'status',
        'icon',
        'video',
        'subcategory',
        'category',
        'upstream',
        'downstream',
        'traversed',
        'progress',
    ]

class temp_asset(BaseFields):
    """used to house all possible attributes for constructing an asset
    which does not yet exist in the library.
    """
    attrs = [
        'duration',
        'framerate',
        'polycount',
        'textured',
        'colormatrix',
        'aces',
        'denoise',
    ]
    __slots__ = tuple(
        relic_asset.base + attrs + relic_asset.extra
    )

class references(BaseFields):
    attrs = [
        'hasnodes', # Make Tag
        'duration',
        'framerate'
    ]
    __slots__ = tuple(
        relic_asset.base + attrs + relic_asset.extra
    )

class modeling(BaseFields):
    attrs = [
        'polycount',
        'textured'
    ]
    __slots__ = tuple(
        relic_asset.base + attrs + relic_asset.extra
    )

class elements(BaseFields):
    attrs = [
        'hasnodes', # Make Tag
        'duration',
        'framerate'
    ]
    __slots__ = tuple(
        relic_asset.base + attrs + relic_asset.extra
    )

class software(BaseFields):
    attrs = [
        'license',
    ]
    __slots__ = tuple(
        relic_asset.base + attrs + relic_asset.extra
    )

class lighting(BaseFields):
    attrs = [
        'renderer',
    ]
    __slots__ = tuple(
        relic_asset.base + attrs + relic_asset.extra
    )

class shading(BaseFields):
    attrs = [
        'renderer',
    ]
    __slots__ = tuple(
        relic_asset.base + attrs + relic_asset.extra
    )

class nuketools(BaseFields):
    attrs = [
        'nodecount',
    ]
    __slots__ = tuple(
        relic_asset.base + attrs + relic_asset.extra
    )

class mayatools(BaseFields):
    attrs = [
        'nodecount',
    ]
    __slots__ = tuple(
        relic_asset.base + attrs + relic_asset.extra
    )


class Category(AutoEnum):
    RELATIONSHIPS = {'type': relationships,}
    ALUSERS = {'type': alusers,}
    TAGS = {'type': tags,}
    SUBCATEGORY = {'type': subcategory,}
    REFERENCES = {'type': references, }
    MODELING = {'type': modeling,}
    ELEMENTS = {'type': elements,}
    LIGHTING = {'type': lighting,}
    SHADING = {'type': shading,}
    SOFTWARE = {'type': software,}
    MAYATOOLS = {'type': mayatools,}
    NUKETOOLS = {'type': nuketools,}


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
    constructor = OBJECT_MAP.get(category, temp_asset)
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
    category_name = link_item_asset.__class__.__name__
    if isinstance(link_item_asset, subcategory):
        asset.subcategory = link_item
    elif hasattr(asset, category_name):
        appendCreate(asset, category_name, link_item)
    else:
        try:
            link_item_asset.path = Path(link_item_asset.path)
        except:pass
        category_id = allCategories.slots.index(category_name)
        link_item_asset.category = category_id
        category_obj = Library.categories.get(category_id)
        attachSubcategory(link_item_asset, category_obj)
        appendCreate(asset, 'upstream', link_item)
        appendCreate(link_item, 'downstream', asset)
