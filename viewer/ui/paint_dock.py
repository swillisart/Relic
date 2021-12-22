# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'paint_dock.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

import resources_rc

class Ui_AnnotateDock(object):
    def setupUi(self, AnnotateDock):
        if not AnnotateDock.objectName():
            AnnotateDock.setObjectName(u"AnnotateDock")
        AnnotateDock.resize(165, 234)
        AnnotateDock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName(u"dockWidgetContents")
        self.gridLayout_3 = QGridLayout(self.dockWidgetContents)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setContentsMargins(3, 3, 3, 3)
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setSpacing(3)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(3, 3, 3, 3)
        self.saveButton = QPushButton(self.dockWidgetContents)
        self.saveButton.setObjectName(u"saveButton")

        self.horizontalLayout_4.addWidget(self.saveButton)

        self.clearButton = QPushButton(self.dockWidgetContents)
        self.clearButton.setObjectName(u"clearButton")

        self.horizontalLayout_4.addWidget(self.clearButton)


        self.gridLayout_3.addLayout(self.horizontalLayout_4, 1, 0, 1, 1)

        self.scrollArea = QScrollArea(self.dockWidgetContents)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 157, 169))
        self.gridLayout_4 = QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.gridLayout_4.setContentsMargins(4, 4, 4, 4)
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(3)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(3, 3, 3, 3)
        self.brushToolButton = QToolButton(self.scrollAreaWidgetContents)
        self.brushToolButton.setObjectName(u"brushToolButton")
        self.brushToolButton.setStyleSheet(u"")
        icon = QIcon()
        icon.addFile(u":/resources/brush_tool.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.brushToolButton.setIcon(icon)
        self.brushToolButton.setIconSize(QSize(32, 32))
        self.brushToolButton.setCheckable(True)
        self.brushToolButton.setChecked(True)
        self.brushToolButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.brushToolButton.setArrowType(Qt.NoArrow)

        self.horizontalLayout_2.addWidget(self.brushToolButton)

        self.shapeToolButton = QToolButton(self.scrollAreaWidgetContents)
        self.shapeToolButton.setObjectName(u"shapeToolButton")
        icon1 = QIcon()
        icon1.addFile(u":/resources/shape_tool.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.shapeToolButton.setIcon(icon1)
        self.shapeToolButton.setIconSize(QSize(32, 32))
        self.shapeToolButton.setCheckable(True)
        self.shapeToolButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        self.horizontalLayout_2.addWidget(self.shapeToolButton)

        self.textToolButton = QToolButton(self.scrollAreaWidgetContents)
        self.textToolButton.setObjectName(u"textToolButton")
        icon2 = QIcon()
        icon2.addFile(u":/resources/text_tool.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.textToolButton.setIcon(icon2)
        self.textToolButton.setIconSize(QSize(32, 32))
        self.textToolButton.setCheckable(True)
        self.textToolButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        self.horizontalLayout_2.addWidget(self.textToolButton)


        self.gridLayout_4.addLayout(self.horizontalLayout_2, 0, 0, 1, 1)

        self.shapeFrame = QFrame(self.scrollAreaWidgetContents)
        self.shapeFrame.setObjectName(u"shapeFrame")
        self.shapeFrame.setFrameShape(QFrame.StyledPanel)
        self.shapeFrame.setFrameShadow(QFrame.Raised)
        self.gridLayout_2 = QGridLayout(self.shapeFrame)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.shapeTypeCombobox = QComboBox(self.shapeFrame)
        self.shapeTypeCombobox.addItem("")
        self.shapeTypeCombobox.addItem("")
        self.shapeTypeCombobox.addItem("")
        self.shapeTypeCombobox.addItem("")
        self.shapeTypeCombobox.setObjectName(u"shapeTypeCombobox")
        self.shapeTypeCombobox.setFrame(True)

        self.gridLayout_2.addWidget(self.shapeTypeCombobox, 0, 1, 1, 1)

        self.shapeTypeLabel = QLabel(self.shapeFrame)
        self.shapeTypeLabel.setObjectName(u"shapeTypeLabel")
        self.shapeTypeLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_2.addWidget(self.shapeTypeLabel, 0, 0, 1, 1)


        self.gridLayout_4.addWidget(self.shapeFrame, 1, 0, 1, 1)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.gridLayout_3.addWidget(self.scrollArea, 0, 0, 1, 1)

        AnnotateDock.setWidget(self.dockWidgetContents)

        self.retranslateUi(AnnotateDock)

        QMetaObject.connectSlotsByName(AnnotateDock)
    # setupUi

    def retranslateUi(self, AnnotateDock):
        AnnotateDock.setWindowTitle(QCoreApplication.translate("AnnotateDock", u"Annotate", None))
        self.saveButton.setText(QCoreApplication.translate("AnnotateDock", u"Save", None))
        self.clearButton.setText(QCoreApplication.translate("AnnotateDock", u"Clear", None))
        self.brushToolButton.setText(QCoreApplication.translate("AnnotateDock", u"Brush", None))
        self.shapeToolButton.setText(QCoreApplication.translate("AnnotateDock", u"Shape", None))
        self.textToolButton.setText(QCoreApplication.translate("AnnotateDock", u"Text", None))
        self.shapeTypeCombobox.setItemText(0, QCoreApplication.translate("AnnotateDock", u"Rectangle", None))
        self.shapeTypeCombobox.setItemText(1, QCoreApplication.translate("AnnotateDock", u"Line", None))
        self.shapeTypeCombobox.setItemText(2, QCoreApplication.translate("AnnotateDock", u"Ellipse", None))
        self.shapeTypeCombobox.setItemText(3, QCoreApplication.translate("AnnotateDock", u"Circle", None))

        self.shapeTypeLabel.setText(QCoreApplication.translate("AnnotateDock", u"Type:", None))
    # retranslateUi

