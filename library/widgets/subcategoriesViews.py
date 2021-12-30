import functools
import json
import os

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
        self.setDefaultDropAction(Qt.MoveAction)
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
            self.update()

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
            if not tree_item.link or tree_item.link <= 0:
                model_root_item.appendRow(tree_item)
            else:
                parent = data.get(tree_item.link)
                parent.appendRow(tree_item)
            
            if not tree_item.link:
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
            self.update()
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
        new_item = subcategory(name=name, category=self.category.id)

        if selection:
            item = self.indexToItem(selection[0])
            new_item.link = (self.category.id, item.id)
            new_item.create()
            new_item.count = 0
            tree_item = polymorphicItem(fields=new_item)

            if item.hasChildren():
                item.appendRow(tree_item)
            else:
                item.setChild(item.index().row(), tree_item)
        else:
            new_item.create()
            new_item.count = 0
            tree_item = polymorphicItem(fields=new_item)
            self.model.invisibleRootItem().appendRow(tree_item)

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
            """
            # Use the recursive nature of getCounts to fetch tree descendent ids.
            self.counts = {}
            self.recursiveCountCursor(item, collect=True, up=False, down=True)
            [ids.append(x) for x in self.counts]
            if item:
                self.category.count += -(item.count)
                item_removal = item.parent()
                if item_removal is None:
                    item_removal = self.model.invisibleRootItem()
                item_removal.takeRow(item.index().row() - i)
            """
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
            self.counts = {}
            self.recursiveCountCursor(item, collect=True, up=False, down=True)

            [ids.append(x) for x in self.counts]
            if item:
                self.category.count += -(item.count) 
                item_removal = item.parent()
                if item_removal is None:
                    item_removal = self.model.invisibleRootItem()
                item_removal.takeRow(item.index().row() - i)

        subcategory(id=tuple(ids)).remove()
        self.modifications.emit(True)

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
        if event.mimeData().hasUrls():
            # ensure the payload category matches the current tree's category
            category = self.category.name.lower()
            payload = json.loads(event.mimeData().text())
            if category in payload.keys():
                event.acceptProposedAction()
        else:
            selection = self.selectedIndexes()
            # Reset counts data to build our items
            if len(selection) != 1:
                return

            item = self.indexToItem(selection[0])
            if not item:
                return
            self.drag_item = item
            parent_item = item.parent()
            if parent_item:
                self.getCounts(parent_item)
                self.counts = {k: -item.count for k, v in self.counts.items()}
            return super(subcategoryTreeView, self).dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            self.setFocus()
            self.update()
        super(subcategoryTreeView, self).dragMoveEvent(event)
        event.acceptProposedAction()

    def dropEvent(self, event):
        if not int(RELIC_PREFS.edit_mode):
            return
        mime = event.mimeData()
        index = self.indexAt(event.pos())

        # Drag and drop re-categorization (from the asset list view)
        if mime.hasUrls() and index.isValid():
            subcategory_item = self.indexToItem(index)
            if not subcategory_item:
                return event.reject()

            dst = subcategory_item.name
            accepted_item, ok = QInputDialog.getItem(self,
                'Re-parent Asset',
                'Move the assets subcategory into "{}"?'.format(dst),
                ['Move Assets'], True)
            if not ok:
                return

            event.setDropAction(Qt.MoveAction)
            event.accept()
            payload = json.loads(mime.text())
            for key, values in payload.items():
                constructor = getattr(objectmodels, str(key))
                for fields in values:
                    asset = constructor(**fields)
                    asset.moveToSubcategory(subcategory_item)
        else:
            # Re-parenting a subcategory check if user wants to move.
            src = self.drag_item.name
            if index.isValid():
                dst = self.indexToItem(index).name
            else:
                dst = 'Root'
            accepted_item, ok = QInputDialog.getItem(self,
                'Re-parent Subcategory',
                'Move the item from "{}" to "{}"?'.format(src, dst),
                [self.drag_item.name], True)

            if not ok:
                return

            # Apply subtractions regardless of destination.
            self.updateCounts()

            if index.isValid():
                item = self.indexToItem(index)
                if not item:
                    return event.reject()

                dropIndicatorPosition = self.getItemRelativePosition(
                    event.pos(), self.visualRect(index)
                )
                if dropIndicatorPosition in (self.AboveItem, self.BelowItem):
                    item = item.parent()
                if item: # Apply additions.
                    if item.id != self.drag_item.id:
                        self.getCounts(item)
                        self.counts = {k: self.drag_item.count for k, v in self.counts.items()}
                        self.updateCounts()
                        current_link = self.drag_item.link
                        current_id = self.drag_item.id
                        new_parent = item.id

                        # Check if current item has relations (link) created.
                        if not current_link:
                            relation = relationships(
                                category_id=new_parent,
                                category_map=3
                            )
                            relation.create()
                            # Update subcategory with permanent link
                            subcategory(
                                id=current_id,
                                link=relation.link,
                            ).update(fields=['link'])
                        else:
                            # Only need to update with new category_id for link
                            relation = relationships(
                                category_id=current_link,
                                category_map=3
                            )
                            relation.fetch()
                            relation.category_id = new_parent
                            relation.update(fields=['category_id'])
                            self.drag_item.link = new_parent
            else:
                # Set subcategory link to zero if making top level
                relation = relationships(
                    category_id=self.drag_item.link,
                    category_map=3
                )
                relation.fetch()
                relation.remove()
                subcategory(
                    id=self.drag_item.id,
                    link=0,
                ).update(fields=['link'])
                self.drag_item.link = None
                self.counts = {}
            super(subcategoryTreeView, self).dropEvent(event)
            del self.drag_item

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

    def __init__(self, *args, **kwargs):
        super(CategoryManager, self).__init__(*args, **kwargs)
        self.selected_subcategories = {}
        self.all_categories = []

    def assembleCategories(self, categories):
        self.clearAllModels()
        for category in categories:

            tree = subcategoryTreeView(category=category)
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
            self.selected_subcategories[sender.category.id] = []
            self.onSelection.emit(self.selected_subcategories)
        else:
            try:
                selected = self.selected_subcategories.pop(sender.category.id)
                self.onSelection.emit(selected)
            except KeyError:
                pass

    @Slot()
    def getAllSelectedItems(self, selection):
        self.selected_subcategories = {}
        for category in self.all_categories:
            if category.tab.state:
                ids = category.tree.getSelectionIds()
                c = category.id
                if self.selected_subcategories.get(c):
                    self.selected_subcategories[c].extend(ids)
                else:
                    self.selected_subcategories[c] = ids
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

"""
class ResizeFilter(QObject):

    def eventFilter(self, widget, event):
        parent = self.parent()
        if widget is parent and event.type() == QEvent.Resize:
                self.setGeometry(parent.rect())
                return True
        else:
            return False
"""

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
        self.height_store = h if h > 120 else 76

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
        self.state = True
        self.checkButton.setChecked(True)
        self.ContentFrame.setVisible(True)

    def collapseState(self):
        self.state = False
        self.checkButton.setChecked(False)
        self.ContentFrame.setVisible(False)

    def toggleState(self):
        self.state = not self.state
        if self.state:
            self.setFixedHeight(self.expand_height)
        else:
            self.expand_height = self.size().height()
            self.setFixedHeight(29)
        self.checkButton.nextCheckState()
        self.ContentFrame.setVisible(self.state)
        self.collapseExpand.emit(self.state)
