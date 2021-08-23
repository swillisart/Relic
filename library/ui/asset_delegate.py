# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'asset_delegate.ui'
##
## Created by: Qt User Interface Compiler version 6.1.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

import resources_rc

class Ui_AssetDelegate(object):
    def setupUi(self, AssetDelegate):
        if not AssetDelegate.objectName():
            AssetDelegate.setObjectName(u"AssetDelegate")
        AssetDelegate.resize(296, 239)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(AssetDelegate.sizePolicy().hasHeightForWidth())
        AssetDelegate.setSizePolicy(sizePolicy)
        AssetDelegate.setStyleSheet(u"QWidget {\n"
"	background-color: rgb(76, 76, 76);\n"
"    color: rgb(200, 200, 200);\n"
"    selection-background-color: rgb(126, 126, 126);\n"
"    selection-color: rgb(250, 250, 250);\n"
"    outline: 0;\n"
"}\n"
"QWidget:item {\n"
"    background-color: transparent;\n"
"}\n"
"QWidget:item:hover {\n"
"    background-color: rgba(150, 146, 137, 15);\n"
"    color: rgb(250, 250, 250);\n"
"}\n"
"QWidget:item:selected {\n"
"    background-color: rgb(150, 146, 137);\n"
"    color: rgb(43, 43, 43);\n"
"}\n"
"QPushButton:hover {\n"
"    color: rgb(250, 250, 250);\n"
"    background-color: rgb(108, 108, 108);\n"
" }\n"
"QCheckBox {\n"
"	padding-top: 2px;\n"
"}\n"
"QCheckBox::indicator:checked:hover,\n"
"QTreeView::indicator:checked:hover,\n"
"QListView::indicator:checked:hover {\n"
"    image: url(:/resources/style/checkbox_checked_hover.svg);\n"
"}\n"
"QCheckBox::indicator:unchecked:hover,\n"
"QTreeView::indicator:unchecked:hover,\n"
"QListView::indicator:unchecked:hover {\n"
"    image: url(:/resources/style/checkb"
                        "ox_hover.svg);\n"
"}\n"
"QCheckBox::indicator {\n"
"    width: 14px;\n"
"    height: 14px;\n"
"}\n"
"QCheckBox::indicator:checked,\n"
"QTreeView::indicator:checked,\n"
"QListView::indicator:checked {\n"
"    image: url(:/resources/style/checkbox_checked.svg);\n"
"}\n"
"\n"
"QCheckBox::indicator:checked:hover,\n"
"QTreeView::indicator:checked:hover,\n"
"QListView::indicator:checked:hover {\n"
"    image: url(:/resources/style/checkbox_checked_hover.svg);\n"
"}\n"
"\n"
"QCheckBox::indicator:unchecked,\n"
"QTreeView::indicator:unchecked,\n"
"QListView::indicator:unchecked {\n"
"    color: rgb(43, 43, 43);\n"
"    image: url(:/resources/style/checkbox.svg);\n"
"}")
        self.verticalLayout = QVBoxLayout(AssetDelegate)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.HeaderFrame = QFrame(AssetDelegate)
        self.HeaderFrame.setObjectName(u"HeaderFrame")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.HeaderFrame.sizePolicy().hasHeightForWidth())
        self.HeaderFrame.setSizePolicy(sizePolicy1)
        self.HeaderFrame.setFocusPolicy(Qt.ClickFocus)
        self.HeaderFrame.setAutoFillBackground(False)
        self.HeaderFrame.setStyleSheet(u"QWidget{\n"
"	background-color: rgb(62, 62, 62);\n"
"}\n"
"QFrame{\n"
"    background-color: rgb(62, 62, 62);\n"
"   /* background-color: qlineargradient(y1: 1, y2: -.5, stop: 0 rgb(55, 105, 140), stop: 0.20 rgb(68, 68, 68));*/\n"
"   /* border: 1px solid rgb(43,43,43);*/\n"
"    border: 2px solid rgb(57,57,57);\n"
"	border-radius: 3px\n"
"}\n"
"QFrame[selected=\"true\"]{\n"
"    border: 2px solid rgb(150, 146, 137);\n"
"    border-bottom: 2px solid rgb(57,57,57);\n"
"}")
        self.HeaderFrame.setFrameShape(QFrame.StyledPanel)
        self.HeaderFrame.setFrameShadow(QFrame.Raised)
        self.HeaderFrame.setProperty("selected", False)
        self.horizontalLayout_5 = QHBoxLayout(self.HeaderFrame)
        self.horizontalLayout_5.setSpacing(0)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.dockTitleWidgets = QFrame(self.HeaderFrame)
        self.dockTitleWidgets.setObjectName(u"dockTitleWidgets")
        self.dockTitleWidgets.setStyleSheet(u"border: none;")
        self.dockTitleWidgets.setFrameShape(QFrame.StyledPanel)
        self.dockTitleWidgets.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_7 = QHBoxLayout(self.dockTitleWidgets)
        self.horizontalLayout_7.setSpacing(9)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)

        self.horizontalLayout_5.addWidget(self.dockTitleWidgets)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(5)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.styledLine = QFrame(self.HeaderFrame)
        self.styledLine.setObjectName(u"styledLine")
        self.styledLine.setMinimumSize(QSize(4, 0))
        self.styledLine.setStyleSheet(u"QFrame {background-color: rgb(150, 146, 137);border: none}")
        self.styledLine.setFrameShadow(QFrame.Plain)
        self.styledLine.setLineWidth(0)
        self.styledLine.setMidLineWidth(0)
        self.styledLine.setFrameShape(QFrame.VLine)

        self.horizontalLayout.addWidget(self.styledLine)


        self.horizontalLayout_5.addLayout(self.horizontalLayout)

        self.headerLayout = QHBoxLayout()
        self.headerLayout.setSpacing(6)
        self.headerLayout.setObjectName(u"headerLayout")
        self.headerLayout.setContentsMargins(6, 0, 6, 0)
        self.categoryIcon = QToolButton(self.HeaderFrame)
        self.categoryIcon.setObjectName(u"categoryIcon")
        self.categoryIcon.setStyleSheet(u"border: none;")
        icon = QIcon()
        icon.addFile(u":/resources/categories/shading.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.categoryIcon.setIcon(icon)
        self.categoryIcon.setIconSize(QSize(18, 18))

        self.headerLayout.addWidget(self.categoryIcon)

        self.checkBox = QCheckBox(self.HeaderFrame)
        self.checkBox.setObjectName(u"checkBox")
        sizePolicy.setHeightForWidth(self.checkBox.sizePolicy().hasHeightForWidth())
        self.checkBox.setSizePolicy(sizePolicy)
        self.checkBox.setIconSize(QSize(18, 18))

        self.headerLayout.addWidget(self.checkBox)

        self.nameLabel = QLabel(self.HeaderFrame)
        self.nameLabel.setObjectName(u"nameLabel")
        font = QFont()
        font.setPointSize(10)
        self.nameLabel.setFont(font)
        self.nameLabel.setStyleSheet(u"border:none;")
        self.nameLabel.setFrameShape(QFrame.NoFrame)
        self.nameLabel.setFrameShadow(QFrame.Sunken)

        self.headerLayout.addWidget(self.nameLabel)

        self.linksButton = QToolButton(self.HeaderFrame)
        self.linksButton.setObjectName(u"linksButton")
        self.linksButton.setStyleSheet(u"QToolButton{\n"
"padding: -2px;\n"
"border: none;\n"
"background-color: rgb(62, 62, 62);\n"
"}\n"
"QToolButton:hover{\n"
"background-color: rgb(92, 92, 92);\n"
"}")
        icon1 = QIcon()
        icon1.addFile(u":/resources/general/folder_link.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.linksButton.setIcon(icon1)
        self.linksButton.setIconSize(QSize(24, 24))
        self.linksButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        self.headerLayout.addWidget(self.linksButton)

        self.horizontalSpacer = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.headerLayout.addItem(self.horizontalSpacer)


        self.horizontalLayout_5.addLayout(self.headerLayout)

        self.iconButton = QToolButton(self.HeaderFrame)
        self.iconButton.setObjectName(u"iconButton")
        self.iconButton.setFocusPolicy(Qt.NoFocus)
        self.iconButton.setStyleSheet(u"border: none;\n"
"margin-right: 4px;")
        icon2 = QIcon()
        icon2.addFile(u":/resources/asset_types/collection.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.iconButton.setIcon(icon2)
        self.iconButton.setIconSize(QSize(24, 24))

        self.horizontalLayout_5.addWidget(self.iconButton)


        self.verticalLayout.addWidget(self.HeaderFrame)

        self.frame = QFrame(AssetDelegate)
        self.frame.setObjectName(u"frame")
        self.frame.setStyleSheet(u"QFrame#frame {\n"
"    border: 2px solid rgb(57,57,57);\n"
"    border-top: none;\n"
"	border-radius: 3px\n"
"}\n"
"QFrame#frame[selected=\"true\"] {\n"
"    border: 2px solid rgb(150, 146, 137);\n"
"    border-top: none;\n"
"	border-radius: 3px\n"
"}")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.frame.setProperty("selected", False)
        self.verticalLayout_2 = QVBoxLayout(self.frame)
        self.verticalLayout_2.setSpacing(2)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(2, 0, 2, 0)
        self.progressBar = QProgressBar(self.frame)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setMinimumSize(QSize(0, 0))
        self.progressBar.setMaximumSize(QSize(16777215, 4))
        self.progressBar.setSizeIncrement(QSize(0, 0))
        self.progressBar.setBaseSize(QSize(0, 0))
        self.progressBar.setStyleSheet(u"QProgressBar {\n"
"    background-color: rgb(43, 43, 43);\n"
"    border: 1px solid rgb(68, 68, 68);\n"
"    text-align: center;\n"
"}\n"
"QProgressBar::chunk {\n"
"    background-color: rgb(66, 118, 150);\n"
"    color: rgb(43, 43, 43);\n"
"}\n"
"QProgressBar[complete=\"true\"]::chunk{\n"
"    background-color: rgb(66, 175, 78)\n"
"}")
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(False)
        self.progressBar.setInvertedAppearance(False)
        self.progressBar.setProperty("complete", False)

        self.verticalLayout_2.addWidget(self.progressBar)

        self.line_4 = QFrame(self.frame)
        self.line_4.setObjectName(u"line_4")
        self.line_4.setFrameShape(QFrame.HLine)
        self.line_4.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_2.addWidget(self.line_4)

        self.label = QLabel(self.frame)
        self.label.setObjectName(u"label")
        self.label.setStyleSheet(u"")

        self.verticalLayout_2.addWidget(self.label)

        self.line_3 = QFrame(self.frame)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.HLine)
        self.line_3.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_2.addWidget(self.line_3)


        self.verticalLayout.addWidget(self.frame)


        self.retranslateUi(AssetDelegate)

        QMetaObject.connectSlotsByName(AssetDelegate)
    # setupUi

    def retranslateUi(self, AssetDelegate):
        AssetDelegate.setWindowTitle(QCoreApplication.translate("AssetDelegate", u"Form", None))
        self.categoryIcon.setText(QCoreApplication.translate("AssetDelegate", u"...", None))
        self.checkBox.setText("")
        self.nameLabel.setText(QCoreApplication.translate("AssetDelegate", u"MyAsset01", None))
#if QT_CONFIG(tooltip)
        self.linksButton.setToolTip(QCoreApplication.translate("AssetDelegate", u"Total number of Links.\n"
"Press to open the Asset's Upstream Dependencies (Links)", None))
#endif // QT_CONFIG(tooltip)
        self.linksButton.setText(QCoreApplication.translate("AssetDelegate", u"12", None))
#if QT_CONFIG(tooltip)
        self.iconButton.setToolTip(QCoreApplication.translate("AssetDelegate", u"Asset Type", None))
#endif // QT_CONFIG(tooltip)
        self.iconButton.setText(QCoreApplication.translate("AssetDelegate", u"...", None))
        self.label.setText("")
    # retranslateUi

