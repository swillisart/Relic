# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'compact_delegate.ui'
##
## Created by: Qt User Interface Compiler version 6.1.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

import relic_resources_rc

class Ui_CompactDelegate(object):
    def setupUi(self, CompactDelegate):
        if not CompactDelegate.objectName():
            CompactDelegate.setObjectName(u"CompactDelegate")
        CompactDelegate.resize(267, 58)
        CompactDelegate.setStyleSheet(u"QWidget {\n"
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
"    image: url(:/resources/checkbox_checked_hover.svg);\n"
"}\n"
"QCheckBox::indicator:unchecked:hover,\n"
"QTreeView::indicator:unchecked:hover,\n"
"QListView::indicator:unchecked:hover {\n"
"    image: url(:/resources/checkbox_hover.svg"
                        ");\n"
"}\n"
"QCheckBox::indicator {\n"
"    width: 14px;\n"
"    height: 14px;\n"
"}\n"
"QCheckBox::indicator:checked,\n"
"QTreeView::indicator:checked,\n"
"QListView::indicator:checked {\n"
"    image: url(:/resources/checkbox_checked.svg);\n"
"}\n"
"\n"
"QCheckBox::indicator:checked:hover,\n"
"QTreeView::indicator:checked:hover,\n"
"QListView::indicator:checked:hover {\n"
"    image: url(:/resources/checkbox_checked_hover.svg);\n"
"}\n"
"\n"
"QCheckBox::indicator:unchecked,\n"
"QTreeView::indicator:unchecked,\n"
"QListView::indicator:unchecked {\n"
"    color: rgb(43, 43, 43);\n"
"    image: url(:/resources/checkbox.svg);\n"
"}")
        self.verticalLayout_3 = QVBoxLayout(CompactDelegate)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame(CompactDelegate)
        self.frame.setObjectName(u"frame")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy)
        self.frame.setMinimumSize(QSize(0, 0))
        self.frame.setFocusPolicy(Qt.ClickFocus)
        self.frame.setAutoFillBackground(False)
        self.frame.setStyleSheet(u"QWidget{\n"
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
"}")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.frame.setProperty("selected", False)
        self.verticalLayout_2 = QVBoxLayout(self.frame)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.HeaderFrame = QFrame(self.frame)
        self.HeaderFrame.setObjectName(u"HeaderFrame")
        sizePolicy.setHeightForWidth(self.HeaderFrame.sizePolicy().hasHeightForWidth())
        self.HeaderFrame.setSizePolicy(sizePolicy)
        self.HeaderFrame.setMinimumSize(QSize(0, 0))
        self.HeaderFrame.setFocusPolicy(Qt.ClickFocus)
        self.HeaderFrame.setAutoFillBackground(False)
        self.HeaderFrame.setStyleSheet(u"QWidget{\n"
"	background-color: rgb(62, 62, 62);\n"
"}\n"
"QFrame{\n"
"    background-color: rgb(62, 62, 62);\n"
"    border: none;\n"
"}")
        self.HeaderFrame.setFrameShape(QFrame.StyledPanel)
        self.HeaderFrame.setFrameShadow(QFrame.Raised)
        self.HeaderFrame.setMidLineWidth(0)
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
        self.horizontalLayout_7.setSpacing(3)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)

        self.horizontalLayout_5.addWidget(self.dockTitleWidgets)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(3)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.styledLine_2 = QFrame(self.HeaderFrame)
        self.styledLine_2.setObjectName(u"styledLine_2")
        self.styledLine_2.setMinimumSize(QSize(4, 0))
        self.styledLine_2.setStyleSheet(u"QFrame {background-color: rgb(92, 92, 142);border: none}")
        self.styledLine_2.setFrameShadow(QFrame.Plain)
        self.styledLine_2.setLineWidth(0)
        self.styledLine_2.setMidLineWidth(0)
        self.styledLine_2.setFrameShape(QFrame.VLine)

        self.verticalLayout.addWidget(self.styledLine_2)

        self.styledLine = QFrame(self.HeaderFrame)
        self.styledLine.setObjectName(u"styledLine")
        self.styledLine.setMinimumSize(QSize(4, 0))
        self.styledLine.setStyleSheet(u"QFrame {background-color: rgb(150, 146, 137);border: none}")
        self.styledLine.setFrameShadow(QFrame.Plain)
        self.styledLine.setLineWidth(0)
        self.styledLine.setMidLineWidth(0)
        self.styledLine.setFrameShape(QFrame.VLine)

        self.verticalLayout.addWidget(self.styledLine)


        self.horizontalLayout_5.addLayout(self.verticalLayout)

        self.headerLayout = QHBoxLayout()
        self.headerLayout.setSpacing(3)
        self.headerLayout.setObjectName(u"headerLayout")
        self.headerLayout.setContentsMargins(3, 0, 3, 0)
        self.label = QLabel(self.HeaderFrame)
        self.label.setObjectName(u"label")
        sizePolicy1 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy1)
        self.label.setMinimumSize(QSize(72, 48))
        self.label.setSizeIncrement(QSize(0, 0))
        self.label.setStyleSheet(u"border: 1px solid rgb(55, 55, 55);")

        self.headerLayout.addWidget(self.label)

        self.nameLabel = QLabel(self.HeaderFrame)
        self.nameLabel.setObjectName(u"nameLabel")
        font = QFont()
        font.setPointSize(10)
        self.nameLabel.setFont(font)
        self.nameLabel.setStyleSheet(u"border:none;")
        self.nameLabel.setFrameShape(QFrame.NoFrame)
        self.nameLabel.setFrameShadow(QFrame.Sunken)
        self.nameLabel.setMargin(4)

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
        icon = QIcon()
        icon.addFile(u":/resources/icons/folder_link.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.linksButton.setIcon(icon)
        self.linksButton.setIconSize(QSize(24, 24))
        self.linksButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        self.headerLayout.addWidget(self.linksButton)

        self.horizontalSpacer = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.headerLayout.addItem(self.horizontalSpacer)


        self.horizontalLayout_5.addLayout(self.headerLayout)

        self.typeIcon = QToolButton(self.HeaderFrame)
        self.typeIcon.setObjectName(u"typeIcon")
        self.typeIcon.setFocusPolicy(Qt.NoFocus)
        self.typeIcon.setStyleSheet(u"padding: -2px;\n"
"border: none;\n"
"margin-right: 4px;")
        icon1 = QIcon()
        icon1.addFile(u":/resources/icons/component.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.typeIcon.setIcon(icon1)
        self.typeIcon.setIconSize(QSize(24, 24))

        self.horizontalLayout_5.addWidget(self.typeIcon)

        self.iconButton = QToolButton(self.HeaderFrame)
        self.iconButton.setObjectName(u"iconButton")
        self.iconButton.setFocusPolicy(Qt.NoFocus)
        self.iconButton.setStyleSheet(u"padding: -2px;\n"
"border: none;\n"
"margin-right: 4px;")
        icon2 = QIcon()
        icon2.addFile(u":/resources/icons/collection.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.iconButton.setIcon(icon2)
        self.iconButton.setIconSize(QSize(24, 24))

        self.horizontalLayout_5.addWidget(self.iconButton)


        self.verticalLayout_2.addWidget(self.HeaderFrame)

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
"	margin-left: 5px;\n"
"	margin-right: 4px;\n"
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


        self.verticalLayout_3.addWidget(self.frame)


        self.retranslateUi(CompactDelegate)

        QMetaObject.connectSlotsByName(CompactDelegate)
    # setupUi

    def retranslateUi(self, CompactDelegate):
        CompactDelegate.setWindowTitle(QCoreApplication.translate("CompactDelegate", u"Form", None))
        self.label.setText("")
        self.nameLabel.setText(QCoreApplication.translate("CompactDelegate", u"MyAsset01", None))
#if QT_CONFIG(tooltip)
        self.linksButton.setToolTip(QCoreApplication.translate("CompactDelegate", u"Total number of Links.\n"
"Press to open the Asset's Upstream Dependencies (Links)", None))
#endif // QT_CONFIG(tooltip)
        self.linksButton.setText(QCoreApplication.translate("CompactDelegate", u"12", None))
#if QT_CONFIG(tooltip)
        self.typeIcon.setToolTip(QCoreApplication.translate("CompactDelegate", u"Asset Type", None))
#endif // QT_CONFIG(tooltip)
        self.typeIcon.setText(QCoreApplication.translate("CompactDelegate", u"...", None))
#if QT_CONFIG(tooltip)
        self.iconButton.setToolTip(QCoreApplication.translate("CompactDelegate", u"Asset Type", None))
#endif // QT_CONFIG(tooltip)
        self.iconButton.setText(QCoreApplication.translate("CompactDelegate", u"...", None))
    # retranslateUi

