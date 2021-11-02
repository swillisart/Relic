import sys

from sequencePath import sequencePath as Path

from PySide6.QtGui import QStandardItem
from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import QApplication

from library.io.database import AssetDatabase
from library.config import RELIC_PREFS

db = AssetDatabase(RELIC_PREFS.host)

RELATE_MAP = {
    # Data Tables
    'relationships': 0,
    'alusers': 1,
    'tags': 2,
    'subcategory': 3,
    # Categories
    'references': 4,
    'modeling': 5,
    'elements': 6,
    'lighting': 7,
    'shading': 8,
    'software': 9,
    'mayatools': 10,
    'nuketools': 11,
}
 
LOCAL_STORAGE = Path(RELIC_PREFS.local_storage.format(project='relic'))
NETWORK_STORAGE = Path(RELIC_PREFS.network_storage)

class BaseFields(object):
    __slots__ = ()

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
        return self.__class__.__name__

    @property
    def relationMap(self):
        return RELATE_MAP.get(self.categoryName)

    def create(self):
        data = {self.categoryName: self.export}
        self.id = db.accessor.doRequestWithResult('createAsset', data)

    def update(self, fields=None):
        data = self.export
        export_data = {}
        fields = fields + ['id'] if isinstance(fields, list) else self.__slots__

        for x in data:
            if self.getLabel(x) in fields:
                if not isinstance(data[x], tuple):
                    export_data[x] = (data[x],)
        update_data = {self.categoryName: export_data}
        db.accessor.doRequest('updateAssets', update_data)

    def nameExists(self):
        rc = 'nameExists/{}/{}'.format(self.categoryName, self.name)
        return db.accessor.doRequestWithResult(rc)

    def remove(self):
        if isinstance(self.id, int):
            ids = (self.id, )
        else:
            ids = self.id
        can_delete = True
        if hasattr(self, 'path'):
            db.accessor.doRequestWithResult('deleteAsset/{}'.format(str(self.relativePath.parent)))

        rc = 'removeAssets/{}'.format(self.categoryName)
        db.accessor.doRequestWithResult(rc, ids)

    def fetch(self, id=False):
        rc = 'fetchAsset/{}'.format(self.categoryName)
        if id:
            rc = 'getAssetById/{}'.format(self.categoryName)
            result = db.accessor.doRequestWithResult(rc, [id])
        else:
            result = db.accessor.doRequestWithResult(rc, self.export)

        for i, x in enumerate(self.__slots__):
            try:
                setattr(self, x, result[i])
            except:
                setattr(self, x, None)

    def search(self, text):
        rc = 'searchCategory/{}/{}'.format(self.categoryName, text)
        results = db.accessor.doRequestWithResult(rc)
        return results

    def linkTo(self, asset):
        relation = relationships(
            category_map=self.relationMap,
            category_id=self.id,
            link=asset.links,
        )
        relation.create()

    def unlinkTo(self, asset):
        relation = relationships(
            category_map=self.relationMap,
            category_id=self.id,
            link=asset.links,
        )
        relation.fetch()
        relation.remove()
    
    def related(self, noassets=False):
        rc = 'retrieveLinks/{}/{}'.format(self.links, int(noassets))
        related = db.accessor.doRequestWithResult(rc)
        self.upstream = []
        if not related or isinstance(related, list):
            return False
        for category_name, value in related.items():
            for index, name in enumerate(allCategories.__slots__):
                if category_name == name:
                    category_id = index 
            asset_constructor = getCategoryConstructor(category_name)
            metadata_results = []
            for x in value:
                asset_obj = asset_constructor(*x)
                linked_asset = polymorphicItem(fields=asset_obj)
                if hasattr(self, category_name):
                    metadata_results.append(linked_asset)
                else:
                    linked_asset.path = Path(linked_asset.path)
                    linked_asset.category = category_id
                    category_obj = Library.categories.get(category_id)

                    if category_obj:
                        subcategory_link = relationships(link=linked_asset.links, category_map=3)
                        subcategory_link.fetch()
                        subcategory = category_obj.subcategory_by_id.get(subcategory_link.category_id)
                        linked_asset.subcategory = subcategory

                    self.upstream.append(linked_asset)

            if metadata_results:
                setattr(self, category_name, metadata_results)

        return self.upstream

    def moveToSubcategory(self, new_subcategory):
        """ re-categorization of an asset
        Moves this asset from it's current category to a new one.

        Parameters
        ----------
        new_subcategory : subcategory
            the destination subcategory
        """

        subcategory_link = relationships(link=self.links, category_map=3)
        subcategory_link.fetch()
        # Retrieve our view item from the global cache.
        category_obj = Library.categories.get(self.category)
        old_category = category_obj.subcategory_by_id.get(subcategory_link.category_id)

        old = old_category.data(polymorphicItem.Object)
        new = new_subcategory.data(polymorphicItem.Object)
        if old == new:
            return
        stem = str(self.path).rsplit('/', 1)[-1]
        folder = stem.split('.')[0]
        # Tell the server to move/rename the on-disk files.
        data = {
            'source': self.categoryName + '/' + old.name + '/' + folder,
            'destination': self.categoryName + '/' + new.name + '/' + folder
        }
        db.accessor.doRequestWithResult('moveAsset', data)

        # Update the subcategory counts.
        old.count -= 1
        new.count += 1
        old.update(fields=['count'])
        new.update(fields=['count'])
        # Update the relationship id to point to our new subcategory.
        subcategory_link.category_id = new_subcategory.id
        subcategory_link.update(fields=['category_id'])
        # Update the asset path to point to the new subcategory.
        self.path = new.name + '/' + stem
        self.update(fields=['path'])

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

    def stream_video_to(self, slot):
        video_path = self.relativePath.suffixed('_icon', ext='.mp4')
        rc = 'retrieveVideo/{}/0/0'.format(video_path)
        db.accessor.videoStreamData.connect(slot)
        db.accessor.doStream(rc, self.id)

    def busy(self):
        status = db.accessor.response is not None
        return status

    @property
    def export(self):
        indexed_attributes = {}
        for i, x in enumerate(self.__slots__):
            attr = getattr(self, x)

            # Convert to id if morphic a object.
            if isinstance(attr, Path):
                attr = str(attr)

            # Only allow json serializable data.
            serializable_types = [str, int, tuple]
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


class allCategories(object):
    __slots__ = (
        'references',
        'modeling',
        'elements',
        'lighting',
        'shading',
        'software',
        'mayatools',
        'nuketools',
    )
    slot_range = range(len(__slots__))

    def __init__(self):
        for i in allCategories.slot_range:
            setattr(self, self.__slots__[i], i)

    def __iter__(self):
        for i in allCategories.slot_range:
            yield self.get(i)

    def getLabel(self, i):
        return self.__slots__[i]

    def get(self, i):
        return getattr(self, self.__slots__[i])

    def set(self, i, data):
        return setattr(self, self.__slots__[i], data)
    
    def fetch(self):
        data = db.accessor.doRequestWithResult('getCategories')
        # fill empty categories
        for i in allCategories.slot_range:
            self.set(i, category(self.getLabel(i), i))
    
        # populate categories with subcategory data
        for x in data:
            subcat = subcategory(*x)
            k = 0 if not subcat.category else subcat.category
            subcat.count = 0 if subcat.count is None else subcat.count
            assigned = self.get(k)
            assigned.subcategory_by_id[subcat.id] = polymorphicItem(fields=subcat)
            self.set(k, assigned)


class Library(object):

    categories = allCategories()
    assets = []

    def __init__(self):
        self.assets_filtered = []
        self.categories.fetch()

    def validateCategories(self, categories):
        if not categories:
            categories = dict.fromkeys(self.categories.slot_range)
        return categories

    def search(self, categories_to_search, filters=None, image=None):
        if categories_to_search.get('keywords'):
            search_results = db.accessor.doRequestWithResult('searchKeywords', categories_to_search)
        else:
            if not categories_to_search:
                return False
            search_results = db.accessor.doRequestWithResult('searchCategories', categories_to_search)
            
        self.assets = []
        if not search_results:
            return False
        for category in search_results:
            try:
                category_int = int(category)
            except:
                continue

            asset_constructor = getCategoryConstructor(category_int)

            for data in search_results[category]:
                if len(data) == 3:
                    _id, subcategory_id, tag_ids = data
                    asset = (category_int, _id, tag_ids, subcategory_id, asset_constructor)
                    self.assets.append(asset)
                else:
                    subcategory_id, _ids = data
                    tag_ids = []
                    for x in _ids:
                        asset = (category_int, x, tag_ids, subcategory_id, asset_constructor)
                        self.assets.append(asset)

        # Sort the assets by the total number of tag_ids (index 2)
        self.assets = sorted(self.assets, key=lambda x: len(x[2]), reverse=True)
        return True

    def load(self, page, limit, categories, icons=True):
        selected_subcategories = []
        categories_to_search = self.validateCategories(categories).keys()
        for x in categories:
            if x not in ['keywords', 'exclude_type']:
                selected_subcategories.extend(categories[x])

        self.assets_filtered = []
        search_data = []
        for asset in self.assets: 
            category, _id, tags, subcategory, asset_constructor = asset
            if category in categories_to_search:
                if selected_subcategories:
                    if subcategory in selected_subcategories:
                        search_data.append([category, _id])
                        self.assets_filtered.append(asset)
                else:
                    search_data.append([category, _id])
                    self.assets_filtered.append(asset)
        offset = int(((page * limit) - limit)) if page else 0
        search_data = search_data[offset:(offset+limit)]
        filtered = self.assets_filtered[offset:(offset+limit)]
        data = db.accessor.doRequest('retrieveAssets', search_data)

        if data:
            for i, x in enumerate(filtered):
                category, _id, tags, subcategory, asset_constructor = x
                asset_fields = data[i]
                asset_fields.extend([tags, []])
                asset = asset_constructor(*asset_fields)
                asset.category = category
                category_obj = self.categories.get(category)
                if category_obj:
                    subcategory = category_obj.subcategory_by_id.get(subcategory)
                    asset.subcategory = subcategory

                yield asset
                #if icons and asset.path:
                #    asset.fetchIcon()


class category(object):
    def __init__(self, name, id):
        self.name = name.capitalize()
        self.id = id
        self.count = 0
        self.icon = ':/resources/categories/{}.svg'.format(self.name.lower())
        self.subcategory_by_id = {}
        self.tree = None # QTreeView
        self.tab = None # TabWidget
        #self.assets = []


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
    )
    NAME, ID, CATEGORY, LINK, COUNT = range(5)


class tags(BaseFields):

    __slots__ = (
        'name',
        'id',
        'datecreated',
        'type',
        'links',
    )


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
        self.link = db.accessor.doRequestWithResult(
            'createRelationship',
            [self.link, self.category_map, self.category_id]
        )

    def remove(self):
        if isinstance(self.id, int):
            ids = (self.id, )
        else:
            ids = self.id
        rc = 'removeRelationship/{}'.format(self.categoryName)
        db.accessor.doRequestWithResult(rc, ids)

class details:
    """
    Details / Info:
        description
        type
        class
        rating
        quality
        resolution

    Structure:
        category + subcategory + path + name (combo of widgets)
        dependencies
        links
        tags
        users

    System:
        datecreated
        datemodified
        filesize
        local
        id
        filehash
        proxy

        icon
        video
    """

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
        'local',
        'icon',
        'video',
        'subcategory',
        'category',
        'upstream',
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
        'colormatrix'
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

class polymorphicItem(QStandardItem):

    Object = Qt.UserRole + 1

    def __init__(self, parent=None, fields=None):
        super(polymorphicItem, self).__init__(parent)
        self.setData(fields.name, Qt.DisplayRole)
        self.setData(fields, polymorphicItem.Object)
        for x in fields.__slots__:
            AttrDescriptor.buildNodeAttr(self.__class__, x)

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.text())        

    def __str__(self):
        return self.text()

    def __int__(self):
        return self.data(role=polymorphicItem.Object).id

    def type(self):
        return(Qt.UserType + 1)

    def clone(self):
        obj = polymorphicItem(fields=self.data(role=polymorphicItem.Object))
        return obj
    

class AttrDescriptor(object):
    def __init__(self, plug):
        self.plug = plug

    def __get__(self, obj, objType):
        return getattr(obj.data(role=polymorphicItem.Object), self.plug)

    def __set__(self, obj, value):
        item = obj.data(role=polymorphicItem.Object)
        setattr(item, self.plug, value)
        obj.setData(item, polymorphicItem.Object)

    @staticmethod
    def buildNodeAttr(cls, attr):
        setattr(cls, attr, AttrDescriptor(attr))

def getCategoryConstructor(category):
    if isinstance(category, int):
        category_name = allCategories.__slots__[category]
        constructor = globals()[category_name]
    elif isinstance(category, str):
        constructor = globals()[category]
    return constructor