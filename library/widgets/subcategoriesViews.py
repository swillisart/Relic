from functools import partial 
import json
import os
from collections import defaultdict
# -- Module --
from library import objectmodels
from library.config import RELIC_PREFS
from library.objectmodels import polymorphicItem, relationships, subcategory
from library.ui.expandableTabs import Ui_ExpandableTabs
from library.widgets.util import ListViewFiltered, rasterizeSVG
# -- Third-party --
from PySide6.QtCore import (QEvent, QFile, QItemSelectionModel, QObject,
                            QPoint, QRegularExpression, QSize,
                            QSortFilterProxyModel, Signal, Slot)
from PySide6.QtGui import (QAction, QColor, QCursor, QIcon,
                           QRegularExpressionValidator, QStandardItemModel, Qt)
from PySide6.QtWidgets import (QAbstractItemView, QListView, QMenu,
                               QMessageBox, QStyledItemDelegate, QTreeView,
                               QWidget, QInputDialog, QLineEdit)


class recursiveTreeFilter(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(recursiveTreeFilter, self).__init__(parent)
        self.text = ""

    def _accept_index(self, idx):
        if idx.isValid():
            text = idx.data(role=Qt.DisplayRole)

            if text:
                condition = text.lower().find(self.text.lower()) >= 0
            else:
                return False
            if condition:
                return True
            for childnum in range(idx.model().rowCount(parent=idx)):
                if self._accept_index(idx.model().index(childnum, 0, parent=idx)):
                    return True
        return False

    def lessThan(self, left, right):
        leftData = self.sourceModel().data(left)
        rightData = self.sourceModel().data(right)
        return leftData > rightData

    def filterAcceptsRow(self, sourceRow, sourceParent):
        """Only first column in model for search

        Args:
            sourceRow ([type]): [description]
            sourceParent ([type]): [description]
        """

        idx = self.sourceModel().index(sourceRow, 0, sourceParent)
        return self._accept_index(idx)


class subcategoryDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super(subcategoryDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
        super(subcategoryDelegate, self).paint(painter, option, index)
        name_text = index.data(Qt.DisplayRole)
        data = index.data(polymorphicItem.Object)

        fm = painter.fontMetrics()
        lh = fm.lineSpacing() + 18
        #print(self.parent().isExpanded(index))#self.IsExpanded)
        text_width = fm.horizontalAdvance(name_text) + lh
        painter.setPen(QColor(108, 108, 108))
        painter.drawText(
            option.rect.x() + text_width,
            option.rect.y(),
            text_width + option.rect.width(),
            option.rect.height(),
            Qt.AlignVCenter,
            "({})".format(data.count),
        )


class subcategoryTreeView(QTreeView):

    modifications = Signal(bool)

    def __init__(self, category=None):
        super(subcategoryTreeView, self).__init__()
        self.category = category
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setHeaderHidden(True)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        #self.setRootIsDecorated(False)
        self.setDropIndicatorShown(True)
        self.setDragDropOverwriteMode(False)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.CopyAction)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._createContextMenus)
        self.setMouseTracking(True)
        self.setItemDelegate(subcategoryDelegate())

        # Setup model and proxy for sorting
        self.model = QStandardItemModel(self)
        proto_item = polymorphicItem(fields=subcategory(name='', count=0))
        self.model.setItemPrototype(proto_item)
        self.proxyModel = recursiveTreeFilter()
        self.proxyModel.setSortCaseSensitivity(Qt.CaseInsensitive)
        self.proxyModel.setSortRole(Qt.DisplayRole)
        self.proxyModel.setSourceModel(self.model)
        self.setModel(self.proxyModel)
        self.subcategoryListView = ListViewFiltered(self)
        self.subcategoryListView.newItem.connect(self.newSubcategory)
        self.subcategoryListView.renameItem.connect(self.renameSubcategory)
        self.subcategoryListView.hide()

        self.selection_model = self.selectionModel()
        self.selection_model.selectionChanged.connect(self.resizeToSel)

        self.drag_item = None
        self.new_item_parent = None
        self.counts = {}
        # Actions
        self.actionCreate = QAction('Create New', self)
        self.actionCreate.triggered.connect(self.listViewNewMode)
        self.actionRename = QAction('Rename Selected', self)
        self.actionRename.triggered.connect(self.listViewRenameMode)
        self.actionDelete = QAction('Remove Selected', self)
        self.actionDelete.triggered.connect(self.removeSubcategory)
        self.actionRecount = QAction('Re-synchronize Count', self)
        self.actionRecount.triggered.connect(self.resyncSubcategoryCount)
        self.folder_icon = QIcon(':resources/general/folder.svg')

    def mousePressEvent(self, event):
        index = self.indexAt(event.pos())
        pop = index in self.selectedIndexes()
        super(subcategoryTreeView, self).mousePressEvent(event)
        if not index.isValid():
            self.selection_model.clearSelection()

        if pop and event.buttons() == Qt.LeftButton:
            self.selection_model.select(index, QItemSelectionModel.Deselect)

    def resizeToSel(self):
        self.resizeColumnToContents(0)

    def listViewNewMode(self):
        self.subcategoryListView.rename_mode = False
        self._showSubcategoryLister()

    def listViewRenameMode(self):
        self.subcategoryListView.rename_mode = True
        self._showSubcategoryLister()

    def _showSubcategoryLister(self):
        self.subcategoryListView.addItems(self.model, replace=True)
        self.subcategoryListView.proxyModel.endResetModel()
        self.subcategoryListView.show()

    def loadTreeFromData(self, data):
        """Loads the tree from data.
        """
        model_root_item = self.model.invisibleRootItem()
        count = 0

        # Assign an subcategory icon from resource file.
        for x in data:
            tree_item = data[x]
            fp = ':resources/subcategories/{}.png'.format(tree_item.name)
            tree_icon = QIcon(fp) if QFile.exists(fp) else self.folder_icon
            tree_item.setIcon(tree_icon)

            # If the subcategory does not have a link-to-parent relationship
            # consider it a root subcategory at the top of the tree.
            if not tree_item.upstream or tree_item.upstream <= 0:
                model_root_item.appendRow(tree_item)
            else:
                parent = data.get(tree_item.upstream)
                parent.appendRow(tree_item)
            
            if not tree_item.upstream:
                count += tree_item.count if tree_item.count else 0
        self.proxyModel.sort(0, Qt.DescendingOrder)
        return count

    def expandAll(self):
        """Visual expansion of all items with children.
        """
        for i in range(self.model.rowCount()):
            index = self.model.index(i, 0)
            proxy_index = self.proxyModel.mapFromSource(index)
            item = self.model.itemFromIndex(index)
            if item.hasChildren():
                self.setExpanded(proxy_index, True)

    def findInTree(self, attr, variable='name'):
        """Finds an item in the tree by the attribute value.
        """
        for i in range(self.model.rowCount()):
            index = self.model.index(i, 0)
            proxy_index = self.proxyModel.mapFromSource(index)
            item = self.model.itemFromIndex(index)
            self.setExpanded(proxy_index, True)
            if found := self.recurseFindTreeItem(attr, item, variable):
                return found

    def recurseFindTreeItem(self, attr, item, variable):
        """Iterates the tree attempting to find an item attribute value
        matching the provided variable.

        Parameters
        ----------
        attr : value of attribute
            Could be name or id
        item : QStandardItem
            the item to recurse through
        variable : str
            the name of the attribute (variable)

        Returns
        -------
        QStandardItem or None
            The found item which matches the attribute value.
        """
        index = item.index()
        proxy_index = self.proxyModel.mapFromSource(index)
        item = self.model.itemFromIndex(index)
        self.setExpanded(proxy_index, True)
        if getattr(item, variable) == attr:
            self.scrollTo(proxy_index)
            # For some reason this doesn't work...
            self.selection_model.select(proxy_index, QItemSelectionModel.ClearAndSelect)
            return item

        if item.hasChildren():
            for i in range(item.rowCount()):
                child_item = item.child(i, 0)
                if found := self.recurseFindTreeItem(attr, child_item, variable):
                    return found

    def _createContextMenus(self, value):
        context_menu = QMenu(self)
        expand = context_menu.addAction("Expand All")
        expand.triggered.connect(self.expandAll)
        collapse = context_menu.addAction("Collapse All")
        collapse.triggered.connect(self.collapseAll)
        
        if bool(int(RELIC_PREFS.edit_mode)):
            context_menu.addAction(self.actionRecount)
            context_menu.addAction(self.actionCreate)
            context_menu.addAction(self.actionRename)
            context_menu.addAction(self.actionDelete)

        context_menu.exec(QCursor.pos())

    def indexToItem(self, index):
        remapped_index = self.proxyModel.mapToSource(index)
        item = self.model.itemFromIndex(remapped_index)
        return item

    @Slot()
    def newSubcategory(self, name):
        """Inserts a named subcategory into the category tree.
        """
        selection = self.selectedIndexes()
        new_item = subcategory(
            name=name,
            category=self.category.id,
            count=0,
        )
        if selection:
            item = self.indexToItem(selection[-1])
            new_item.link = (self.category.id, item.id)
            self.new_item_parent = item
        new_item.createNew()

    def onNewSubcategory(self, new_asset):
        new_item = polymorphicItem(fields=new_asset)
        parent_item = self.new_item_parent
        if not parent_item:
            self.model.invisibleRootItem().appendRow(new_item)
        elif parent_item.hasChildren():
            parent_item.appendRow(new_item)
        else:
            parent_item.setChild(parent_item.index().row(), new_item)
        self.new_item_parent = None

    @Slot()
    def renameSubcategory(self, name):
        selection = self.selectedIndexes()
        if not selection: return

        item = self.indexToItem(selection[0])
        item.setData(name, Qt.DisplayRole)
        item.name = name
        subcategory(id=item.id,name=item.name).update(fields=['name'])
        self.modifications.emit(True)

    @Slot()
    def resyncSubcategoryCount(self):
        """Removes the treeView's selected category
        """
        selection = self.selectedIndexes()
        new_count, ok = QInputDialog.getInt(self, 'Update Count',
                "Count :")#, default_name)
        if not ok:
            return

        for i, index in enumerate(selection):
            item = self.indexToItem(index)
            difference = new_count - item.count
            self.category.count += difference
            asset = index.data(polymorphicItem.Object)
            asset.count = new_count
            asset.update(fields=['count'])
            self.updateSubcategoryCounts(item)
        self.modifications.emit(True)

    @Slot()
    def removeSubcategory(self):
        """Removes the treeView's selected category
        """
        selection = self.selectedIndexes()

        msg = 'Removing this Subcategory will remove all descendent subcategories as well.'
        message = QMessageBox(QMessageBox.Warning, 'Are you sure?', msg,
                QMessageBox.NoButton, self)
        message.addButton('Yes', QMessageBox.AcceptRole)
        message.addButton('Cancel', QMessageBox.RejectRole)

        if message.exec_() == QMessageBox.RejectRole:
            return

        ids = []
        for i, item in enumerate(selection):
            item = self.indexToItem(item)
            # Use the recursive nature of getCounts to fetch tree descendent ids.
            for tree_item in CategoryManager.iterateTreeItems(item):
                if tree_item.count > 0:
                    continue
                ids.append(tree_item.id)
                item_parent = tree_item.parent()
                if not item_parent:
                    item_parent = self.model.invisibleRootItem()
                item_parent.takeRow(tree_item.index().row() - i)
        if ids:
            subcategory(id=tuple(ids)).remove()

    def getSelectionIds(self):
        # get all selected subcategory ids
        indexes = self.selectedIndexes()
        ids = []
        for i in indexes:
            item = self.indexToItem(i)
            do_recurse = int(RELIC_PREFS.recurse_subcategories)
            if do_recurse:
                # get all descendant subcategory ids
                self.recursiveCountCursor(item, collect=True, up=False, down=True)
                [ids.append(x) for x in self.counts]
                self.counts = {}
            else:
                ids.append(item.id)

        return ids

    def dragEnterEvent(self, event):
        super(subcategoryTreeView, self).dragEnterEvent(event)
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            # ensure the payload category matches the current tree's category.
            # files / folders dragged from explorer are also accepted as ingests 
            category = self.category.name.lower()
            for url in mime_data.urls():
                if url.toString().startswith('file:///'):
                    event.acceptProposedAction()
                else:
                    payload = json.loads(mime_data.text())
                    if category in payload.keys():
                        event.acceptProposedAction()
                break
        else:
            selection = self.selectedIndexes()
            # Reset counts data to build our items
            if len(selection) != 1:
                return

            item = self.indexToItem(selection[0])
            if not item:
                return
            self.drag_item = item

    def dragMoveEvent(self, event):
        super(subcategoryTreeView, self).dragMoveEvent(event)
        index = self.indexAt(event.pos())
        if not index.isValid() or index in self.selectedIndexes():
            event.ignore()
        elif event.mimeData().hasUrls():
            self.setFocus()
            event.acceptProposedAction()

    def getDropDestinationItem(self, event):
        drop_position = event.pos()
        index = self.indexAt(drop_position)

        if index.isValid():
            destination = self.indexToItem(index)

            #drop_indicator_position = self.getItemRelativePosition(
            #    drop_position, self.visualRect(index))
            # Drop indications for mouse areas which aren't fully over the Item.
            #if drop_indicator_position in (self.AboveItem, self.BelowItem):
            #   destination = destination.parent()
        else:
            destination = None

        return destination

    def dropEvent(self, event):
        if not int(RELIC_PREFS.edit_mode):
            return
        mime = event.mimeData()
        destination_item = self.getDropDestinationItem(event)

        if mime.hasUrls():
            # External filesystem drop.
            if mime.urls()[0].toString().startswith('file:///'):
                paths = [x.toLocalFile() for x in mime.urls()]
                self.externalFilesDrop.emit(self.category.id, paths)
                self.selection_model.select(self.indexAt(event.pos()), QItemSelectionModel.ClearAndSelect)
                return
            elif destination_item: # Drag and drop re-categorization (from the asset list view)
                accepted_item, ok = QInputDialog.getItem(self,
                    'Re-parent Asset',
                    'Move the assets subcategory into "{}"?'.format(destination_item.name),
                    ['Move Assets'], True)
                if not ok:
                    return

            event.setDropAction(Qt.MoveAction)
            event.accept()
            self.onAssetDrop.emit(destination_item)
            return
        
        drag_item = self.drag_item
        item_parent = drag_item.parent()
        current = drag_item.data(polymorphicItem.Object)

        # Re-parenting a subcategory check if user wants to move.
        dst = destination_item.name if destination_item else 'Root'
        accepted_item, ok = QInputDialog.getItem(self,
            'Re-parent Subcategory',
            'Move the item from "{}" to "{}"?'.format(drag_item.name, dst),
            [drag_item.name], True)
        if not ok:
            return

        if destination_item:
            new_parent = destination_item.data(polymorphicItem.Object)

            # Check if current drag item had a parent relation (link) created.
            if item_parent:
                current.unlink()
                old_parent = item_parent.data(polymorphicItem.Object)
                # Unlink from old parent subcategory.
                subcategory.LINK_CALLBACK = partial(subcategory._onRelink,
                    current, old_parent=old_parent, new_parent=new_parent)
            else:
                subcategory.LINK_CALLBACK = partial(subcategory._onRelink,
                    current, new_parent=new_parent)

            # generate relationship with new upstream link
            current.upstream = new_parent.id
            current.relink()
        else:
            if item_parent: # Item has parent and not already in root. 
                old_parent = item_parent.data(polymorphicItem.Object)
                # Unlink from old parent subcategory.
                current.unlink()
                # Relocate the subcategory from old to root.
                current.relocate(old_parent)
                #self.reparentSubcategoryToRoot(current, old_parent)             

        self.drag_item.setData('', role=Qt.DisplayRole)
        super(subcategoryTreeView, self).dropEvent(event)

    @staticmethod
    def _subcategoryRelinkDefault(data, subcategories=None):
        return

    @staticmethod
    def _subcategoryRelink(data, subcategories=None):
        if not subcategories:
            return
        for index, sub in enumerate(subcategories):
            sub.relocate(data[i])

    @Slot(list)
    def onSubcategoryRelink(self, data):
        self._onSubcategoryRelink(data)
        self._onSubcategoryRelink = self._onSubcategoryRelinkDefault


    def updateSubcategoryCounts(self, item, offset=None):
        """Updates related subcategory tree using the base items
        count attribute or a direct offset.

        Parameters
        ----------
        item : QStandardItem.
            The base QItemd to modify hierarchically. 
        offset : int, optional
            if subtracting put a negative offset, by default None
        """
        item_parent = item.parent()
        if item_parent: # Apply additions or subtractions to related subcategories.
            self.getCounts(item_parent)
            offset = offset or item.count
            self.counts = {k: offset for k, v in self.counts.items()}
            self.updateCounts()

    def getItemRelativePosition(self, pos, rect):
        r = QAbstractItemView.OnViewport
        # margin*2 must be smaller than row height, or the drop onItem rect won't show
        margin = 4
        if pos.y() - rect.top() < margin:
            r = QAbstractItemView.AboveItem
        elif rect.bottom() - pos.y() < margin:
            r = QAbstractItemView.BelowItem
        elif pos.y() - rect.top() > margin and rect.bottom() - pos.y() > margin:
            r = QAbstractItemView.OnItem

        return r

    def updateCounts(self, counts=None):
        """
        Recursively Iterate the treeView model and add or subtract 
        from any parent AND child items affected by the change.
        
        Args:
            counts (dict): {'photos': -2, 'utilities': 1}
        """

        for i in range(self.model.rowCount()):
            index = self.model.index(i, 0)
            tree_item = self.model.itemFromIndex(index)
            self.recursiveCountCursor(tree_item)

    def getCounts(self, tree_item):
        self.counts = {}
        self.recursiveCountCursor(tree_item, collect=True, down=False)

    def recursiveCountCursor(self, tree_item, collect=False, up=True, down=True):
        if not tree_item:
            return
        item_id = tree_item.id
        count_offset = self.counts.get(item_id)

        if count_offset and not collect:
            count_offset = self.counts.pop(item_id)
            self.modifyItemCount(tree_item, count_offset)
        elif collect:
            self.getItemCount(tree_item)

        has_parent = tree_item.parent()
        if has_parent and up:
            self.recursiveCountCursor(has_parent, collect=collect, down=False)

        if tree_item.hasChildren() and down:
            for i in range(tree_item.rowCount()):
                child_index = tree_item.child(i, 0)
                self.recursiveCountCursor(child_index, collect=collect, up=False)

    def modifyItemCount(self, tree_item, offset):
        c = tree_item.count
        c = 0 if not c else c
        tree_item.count = (c + offset)
        subcategory(
            id=tree_item.id,
            count=tree_item.count,
        ).update(fields=['count'])

    def getItemCount(self, tree_item):
        count = tree_item.count
        self.counts[tree_item.id] = count

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F:
            sel = self.selectedIndexes()
            if sel:
                self.scrollTo(sel[0])
        else:
            return super(subcategoryTreeView, self).keyPressEvent(event)


class CategoryManager(QObject):

    onSelection = Signal(dict)
    onAssetDrop = Signal(dict)
    externalFilesDrop = Signal(int, list)

    def __init__(self, *args, **kwargs):
        super(CategoryManager, self).__init__(*args, **kwargs)
        self.selected_subcategories = {}
        self.all_categories = []


    @staticmethod
    def iterateTreeItems(tree_item):
        if not tree_item:
            return
        yield tree_item
        if tree_item.hasChildren():
            for index in range(tree_item.rowCount()):
                child_item = tree_item.child(index, 0)
                yield from CategoryManager.iterateTreeItems(child_item)

    @Slot(dict)
    def receiveNewCounts(self, count_data):
        for cat in self.all_categories:
            tree_view = cat.tree
            item_model = tree_view.model
            for row in range(item_model.rowCount()):
                index = item_model.index(row, 0)
                root_item = item_model.itemFromIndex(index)
                self.setCountData(root_item, tree_view, cat, count_data)
                for tree_item in self.iterateTreeItems(root_item):
                    self.setCountData(tree_item, tree_view, cat, count_data)
            cat.tab.countSpinBox.setValue(cat.count)

    @staticmethod
    def setCountData(tree_item, tree_view, cat, count_data):
        new_count = count_data.get(str(tree_item.id))
        if new_count is not None:
            cat.count += (new_count - tree_item.count)
            tree_item.count = new_count
            tree_view.update(tree_item.index())

    def assembleCategories(self, categories):
        self.clearAllModels()
        for category in categories:

            tree = subcategoryTreeView(category=category)
            tree.onAssetDrop = self.onAssetDrop
            tree.externalFilesDrop = self.externalFilesDrop
            # This is the source of a nasty bug that duplicates items instead of moving in the treeview.
            # make sure to only organize in administration mode.
            tree.selection_model.selectionChanged.connect(self.getAllSelectedItems)

            if category:
                count = tree.loadTreeFromData(category.subcategory_by_id)
                category.count = count
                tab = ExpandableTab(category)
                tab.collapseExpand.connect(self.updateCollapsedItems)
                tab.frame.layout().insertWidget(1, tree)
                category.tab = tab
                category.tree = tree
                self.all_categories.append(category)
                yield tab

    @Slot()
    def updateCollapsedItems(self, state):
        sender = self.sender()
        if state:
            self.getAllSelectedItems(None)
        else:
            try:
                selected = self.selected_subcategories.pop(sender.category.id)
                self.onSelection.emit(selected)
            except KeyError:
                pass

    @Slot()
    def getAllSelectedItems(self, selection):
        self.selected_subcategories = defaultdict(list)
        for category in self.all_categories:
            if category.tab.state:
                ids = category.tree.getSelectionIds()
                c = category.id
                self.selected_subcategories[c].extend(ids)

        self.onSelection.emit(self.selected_subcategories)

    def endResetAllModels(self):
        for category in self.all_categories:
            category.tree.model.endResetModel()

    def clearAllModels(self):
        for category in self.all_categories:
            category.tree.clear()

    def filterAll(self, text):
        for category in self.all_categories:
            self._filterTree(category.tree, text)

    @staticmethod
    def _filterTree(tree, text):
        tree.proxyModel.text = text
        regex = QRegularExpression(text, QRegularExpression.CaseInsensitiveOption)
        tree.proxyModel.setFilterRegularExpression(regex)
        tree.expandAll()



class ExpandableTab(Ui_ExpandableTabs, QWidget):

    collapseExpand = Signal(bool)

    def __init__(self, category, *args, **kwargs):
        super(ExpandableTab, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.state = False
        self.category = category
        self.height_store = 320

        icon = QIcon(category.icon)
        self.iconButton.setIcon(icon)
        self.nameLabel.setText(category.name)
        self.countSpinBox.setValue(category.count)
        for widget in (self.styledLine, self.styledLine_1, self.styledLine_2):
            color = getattr(RELIC_PREFS, category.name.lower() + '_color')
            widget.setStyleSheet(
                'QFrame {{background-color: rgb({});border: none}}'.format(
                    color))

        for x in [self.pushButton, self.pushButton_2, self.countSpinBox, self.checkButton, self.iconButton]:
            x.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.ContentFrame.setVisible(False)
        self.pressing = False

    @property
    def expand_height(self):
        return self.height_store

    @expand_height.setter
    def expand_height(self, h):
        self.height_store = h if h > 120 else 320

    def mousePressEvent(self, event):
        super(ExpandableTab, self).mousePressEvent(event)
        self.global_start = self.mapToGlobal(event.pos())
        if self.HeaderFrame.underMouse():
            self.toggleState()
        elif event.buttons() == Qt.LeftButton and self.verticalControl.underMouse():
            self.last = 0
            self.pressing = True

    def mouseMoveEvent(self, event):
        super(ExpandableTab, self).mouseMoveEvent(event)
        if (event.buttons() & Qt.LeftButton & self.pressing):
            offset = (self.global_start.y() - self.mapToGlobal(event.pos()).y())                
            height_adjust = self.size().height() + -(offset - self.last)
            if not height_adjust <= 76:
                self.setFixedHeight(height_adjust)
            self.last = offset

    def mouseReleaseEvent(self, event):
        super(ExpandableTab, self).mouseReleaseEvent(event)
        self.pressing = False

    def expandState(self):
        self.state = False
        self.toggleState()

    def collapseState(self):
        self.state = True
        self.toggleState()

    def toggleState(self):
        self.state = not self.state
        if self.state:
            self.setFixedHeight(self.expand_height )
        else:
            self.expand_height = self.size().height() 
            self.setFixedHeight(29)
        self.checkButton.setChecked(self.state)
        self.ContentFrame.setVisible(self.state)
        self.collapseExpand.emit(self.state)
