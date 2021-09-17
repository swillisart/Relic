# -- Built-in --
import os
import sys
from functools import partial
from datetime import datetime
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from library.objectmodels import polymorphicItem

class AssetGridView(QTableWidget):
    def __init__(self, *args, **kwargs):
        super(AssetGridView, self).__init__(*args, **kwargs)
        self.base_model = None
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setHorizontalHeaderLabels(['Empty'])
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QAbstractItemView.DoubleClicked |
                                QAbstractItemView.SelectedClicked)

    @Slot()
    def onRowsInserted(self, parent_index, first, last):
        if self.base_model:
            index = self.base_model.index(first, 0)
            asset = index.data(polymorphicItem.Object)
            self.setHorizontalHeaderLabels(list(asset.__slots__))

            for idx, label, value in asset:
                if label in ['datecreated', 'datemodified']:
                    date = datetime.strptime(value,'%Y-%m-%dT%H:%M:%S.%f')
                    value = date.strftime("%m/%d/%y %H:%M")
                else:
                    value = str(value)
                self.setItem(first, idx, QTableWidgetItem(value))
        self.resizeColumnsToContents()
