from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from library.widgets.util import ListViewFocus
from library.objectmodels import session

class SimpleAssetView(ListViewFocus):
    def __init__(self, *args, **kwargs):
        super(SimpleAssetView, self).__init__(*args, **kwargs)
        self.setWindowFlags(Qt.Popup | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        session.searchcategory.callback.connect(self.onFilterResults)
        self.constructor = None
        self.checked_db = False

    def setConstructor(self, constructor):
        self.constructor = constructor

    @Slot(list)
    def onFilterResults(self, results):
        if not self.constructor:
            return
        constructor = self.constructor
        item_model = self.itemModel
        for x in results:
            relate = constructor(*x)
            item = QStandardItem(relate.name)
            item.setData(relate, role=Qt.UserRole)
            item_model.appendRow(item)

    def filterRegExpChanged(self):
        text = self.searchBox.text()
        if len(text) >= 3 and not self.checked_db:
            # Search database
            self.checked_db = True
            session.searchcategory.execute(self.constructor.__name__, text)
        elif len(text) == 0:
            self.checked_db = False
            self.proxyModel.setFilterRegularExpression(None)
            self.itemModel.clear()
        else:
            super(SimpleAssetView, self).filterRegExpChanged()

    def sizeHint(self):
        return QSize(275, 250)
