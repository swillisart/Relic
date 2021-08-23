# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'expandableTabs.ui'
##
## Created by: Qt User Interface Compiler version 6.1.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

import resources_rc

class Ui_ExpandableTabs(object):
    def setupUi(self, ExpandableTabs):
        if not ExpandableTabs.objectName():
            ExpandableTabs.setObjectName(u"ExpandableTabs")
        ExpandableTabs.resize(275, 377)
        ExpandableTabs.setStyleSheet(u"QWidget {\n"
"	background-color: rgb(68, 68, 68);\n"
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
"\n"
"\n"
"/* QMenu ------------------------------------------------------------------ */\n"
"\n"
"QMenu {\n"
"    border: 1px solid rgb(68, 68, 68);\n"
"    background-color: rgb(43, 43, 43);\n"
"    padding: 1px;\n"
"}\n"
"QMenu::separator {\n"
"    height: 1px;\n"
"    background-color: rgb(92, 92, 92);\n"
"    color: rgb(200, 200, 200);\n"
"    padding-left: 2px;\n"
"    margin-left: 0px;\n"
"    m"
                        "argin-right: 0px;\n"
"}\n"
"QMenu::item {\n"
"    padding: 4px;\n"
"    padding-left: 16px;\n"
"    padding-right: 16px;\n"
"    background-color: rgb(68, 68, 68);\n"
"}\n"
"QMenu::indicator {\n"
"    padding: 6px;\n"
"    margin: -1px;\n"
"	width: 13px;\n"
"	height: 13px;\n"
"    background-color: rgb(57, 57, 57);\n"
"}\n"
"QMenu::icon {\n"
"    padding: 4px;\n"
"    margin: 0px;\n"
"	width: 18px;\n"
"	height: 18px;\n"
"    background-color: rgb(57, 57, 57);\n"
"}\n"
"QMenu::indicator:non-exclusive:checked {\n"
"    image: url(:/resources/style/checkbox_checked.svg);\n"
"}\n"
"QMenu::indicator:non-exclusive:unchecked {\n"
"    image: url(:/resources/style/checkbox.svg);\n"
"}\n"
"\n"
"QLineEdit,\n"
"QAbstractSpinBox,\n"
"QTextEdit {\n"
"    background-color: rgb(43, 43, 43);\n"
"/*\n"
"    border: 2px solid rgb(43, 43, 43);\n"
"    border-radius: 3px;\n"
"    color: rgb(200, 200, 200);\n"
"    padding: 1px;\n"
"    margin-top: 0px;\n"
"    padding-left: 0px;\n"
"*/\n"
"}\n"
"\n"
"/* QSlider ------------------"
                        "---------------------------------------------- */\n"
"QSlider::add-page:horizontal, \n"
"QSlider::sub-page:horizontal,\n"
"QSlider::add-page:vertical, \n"
"QSlider::sub-page:vertical {\n"
"    background: rgb(43, 43, 43);\n"
"}\n"
"QSlider::add-page:vertical, \n"
"QSlider::sub-page:vertical {\n"
"    margin-left: 4px;\n"
"    margin-right: 4px;\n"
"}\n"
"QSlider::add-page:horizontal, \n"
"QSlider::sub-page:horizontal {\n"
"    margin-top: 4px;\n"
"    margin-bottom: 4px;\n"
"}\n"
"QSlider::handle:vertical {\n"
"    background: #787878;\n"
"    border: 2px solid rgb(43, 43, 43);\n"
"    width: 8px;\n"
"    height: 6px;\n"
"    margin: 0 -8px;\n"
"    border-radius: 4px;\n"
"}\n"
"QSlider::handle:horizontal {\n"
"    background: #787878;\n"
"    border: 2px solid rgb(43, 43, 43);\n"
"    margin: -8px 0;\n"
"	width: 6px;\n"
"	height: 8px;\n"
"    border-radius: 4px;\n"
"}\n"
"QSlider::groove {\n"
"    background: rgb(43, 43, 43);\n"
"    border: 1px solid rgb(68, 68, 68);\n"
"    border-radius: 4px;\n"
"    margi"
                        "n: 0px;\n"
"}\n"
"QSlider::groove:horizontal {\n"
"    height: 4px;\n"
"}\n"
"QSlider::groove:vertical {\n"
"    width: 4px;\n"
"}\n"
"QSlider::sub-page:vertical:disabled, \n"
"QSlider::sub-page:horizontal:disabled {\n"
"    background: #14506E;\n"
"}\n"
"\n"
"")
        self.verticalLayout = QVBoxLayout(ExpandableTabs)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.HeaderFrame = QFrame(ExpandableTabs)
        self.HeaderFrame.setObjectName(u"HeaderFrame")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.HeaderFrame.sizePolicy().hasHeightForWidth())
        self.HeaderFrame.setSizePolicy(sizePolicy)
        self.HeaderFrame.setFocusPolicy(Qt.ClickFocus)
        self.HeaderFrame.setAutoFillBackground(False)
        self.HeaderFrame.setStyleSheet(u"QFrame{\n"
"    background-color: rgb(57, 57, 57);\n"
"   /* background-color: qlineargradient(y1: 1, y2: -.5, stop: 0 rgb(55, 105, 140), stop: 0.20 rgb(68, 68, 68));*/\n"
"\n"
"    border: 1px solid rgb(43,43,43);\n"
"    border-top: 1px solid rgb(92,92,92);\n"
"	border-radius: 2px;\n"
"    /* border: 2px solid rgb(57,57,57);*/\n"
"	/*border: none;*/\n"
"	padding: 1px;\n"
"}")
        self.HeaderFrame.setFrameShape(QFrame.StyledPanel)
        self.HeaderFrame.setFrameShadow(QFrame.Raised)
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
        self.styledLine_1 = QFrame(self.HeaderFrame)
        self.styledLine_1.setObjectName(u"styledLine_1")
        self.styledLine_1.setMinimumSize(QSize(4, 0))
        self.styledLine_1.setStyleSheet(u"QFrame {\n"
"    background-color: rgb(150, 146, 137);\n"
"	border: none;\n"
"}")
        self.styledLine_1.setFrameShadow(QFrame.Plain)
        self.styledLine_1.setLineWidth(0)
        self.styledLine_1.setMidLineWidth(0)
        self.styledLine_1.setFrameShape(QFrame.VLine)

        self.horizontalLayout.addWidget(self.styledLine_1)

        self.styledLine_2 = QFrame(self.HeaderFrame)
        self.styledLine_2.setObjectName(u"styledLine_2")
        self.styledLine_2.setMinimumSize(QSize(2, 0))
        self.styledLine_2.setMaximumSize(QSize(2, 16777215))
        self.styledLine_2.setStyleSheet(u"QFrame {\n"
"    background-color: rgb(150, 146, 137);\n"
"	border: none;\n"
"}")
        self.styledLine_2.setFrameShadow(QFrame.Plain)
        self.styledLine_2.setLineWidth(0)
        self.styledLine_2.setMidLineWidth(0)
        self.styledLine_2.setFrameShape(QFrame.VLine)

        self.horizontalLayout.addWidget(self.styledLine_2)

        self.iconButton = QToolButton(self.HeaderFrame)
        self.iconButton.setObjectName(u"iconButton")
        self.iconButton.setFocusPolicy(Qt.NoFocus)
        self.iconButton.setStyleSheet(u"padding: -2px;\n"
"margin-right: 4px;\n"
"border: none;\n"
"background-color: rgb(57, 57, 57);")
        icon = QIcon()
        icon.addFile(u":/resources/asset_types/reference.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.iconButton.setIcon(icon)
        self.iconButton.setIconSize(QSize(24, 24))

        self.horizontalLayout.addWidget(self.iconButton)


        self.horizontalLayout_5.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(6)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(6, 0, 6, 0)
        self.nameLabel = QLabel(self.HeaderFrame)
        self.nameLabel.setObjectName(u"nameLabel")
        font = QFont()
        font.setPointSize(10)
        self.nameLabel.setFont(font)
        self.nameLabel.setStyleSheet(u"border:none;")
        self.nameLabel.setFrameShape(QFrame.NoFrame)
        self.nameLabel.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_2.addWidget(self.nameLabel)

        self.countSpinBox = QSpinBox(self.HeaderFrame)
        self.countSpinBox.setObjectName(u"countSpinBox")
        self.countSpinBox.setFocusPolicy(Qt.NoFocus)
        self.countSpinBox.setStyleSheet(u"background-color: rgb(57, 57, 57);\n"
"border:none;")
        self.countSpinBox.setReadOnly(True)
        self.countSpinBox.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.countSpinBox.setMaximum(999999)
        self.countSpinBox.setValue(318)

        self.horizontalLayout_2.addWidget(self.countSpinBox)

        self.horizontalSpacer_4 = QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_4)


        self.horizontalLayout_5.addLayout(self.horizontalLayout_2)

        self.checkButton = QToolButton(self.HeaderFrame)
        self.checkButton.setObjectName(u"checkButton")
        self.checkButton.setEnabled(True)
        self.checkButton.setFocusPolicy(Qt.NoFocus)
        self.checkButton.setStyleSheet(u"QToolButton {\n"
"    padding: 0px;\n"
"    margin: 1px;\n"
"    background-color: rgb(57, 57, 57);\n"
"	border :none;\n"
"}\n"
"QToolButton:hover {\n"
"    background-color: rgb(92, 92, 92);\n"
"    color: rgb(250, 250, 250);\n"
"}")
        icon1 = QIcon()
        icon1.addFile(u":/resources/app/blankCubeGrey.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon1.addFile(u":/resources/app/treeExpandGrey.svg", QSize(), QIcon.Active, QIcon.On)
        self.checkButton.setIcon(icon1)
        self.checkButton.setCheckable(True)

        self.horizontalLayout_5.addWidget(self.checkButton)


        self.verticalLayout.addWidget(self.HeaderFrame)

        self.ContentFrame = QFrame(ExpandableTabs)
        self.ContentFrame.setObjectName(u"ContentFrame")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.ContentFrame.sizePolicy().hasHeightForWidth())
        self.ContentFrame.setSizePolicy(sizePolicy1)
        self.ContentFrame.setStyleSheet(u"")
        self.ContentFrame.setFrameShape(QFrame.StyledPanel)
        self.ContentFrame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_3 = QHBoxLayout(self.ContentFrame)
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(10, 0, 0, 0)
        self.styledLine = QFrame(self.ContentFrame)
        self.styledLine.setObjectName(u"styledLine")
        self.styledLine.setMinimumSize(QSize(2, 0))
        self.styledLine.setMaximumSize(QSize(2, 16777215))
        self.styledLine.setStyleSheet(u"QFrame {\n"
"    background-color: rgb(150, 146, 137);\n"
"	border: none;\n"
"}")
        self.styledLine.setFrameShadow(QFrame.Plain)
        self.styledLine.setLineWidth(0)
        self.styledLine.setMidLineWidth(0)
        self.styledLine.setFrameShape(QFrame.VLine)

        self.horizontalLayout_3.addWidget(self.styledLine)

        self.frame = QFrame(self.ContentFrame)
        self.frame.setObjectName(u"frame")
        sizePolicy1.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy1)
        self.frame.setStyleSheet(u"QWidget {\n"
"	background-color: rgb(48, 48, 48);\n"
"}")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.frame)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.line_4 = QFrame(self.frame)
        self.line_4.setObjectName(u"line_4")
        self.line_4.setFrameShape(QFrame.HLine)
        self.line_4.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_2.addWidget(self.line_4)

        self.line_3 = QFrame(self.frame)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.HLine)
        self.line_3.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_2.addWidget(self.line_3)

        self.verticalControl = QFrame(self.frame)
        self.verticalControl.setObjectName(u"verticalControl")
        sizePolicy.setHeightForWidth(self.verticalControl.sizePolicy().hasHeightForWidth())
        self.verticalControl.setSizePolicy(sizePolicy)
        self.verticalControl.setMinimumSize(QSize(0, 0))
        self.verticalControl.setMaximumSize(QSize(16777215, 10))
        self.verticalControl.setStyleSheet(u"QWidget {\n"
"background-color: transparent;\n"
"}\n"
"QWidget:hover {\n"
"    background-color: rgb(92, 92, 92);\n"
"    border: 1px solid rgb(92, 92, 92);\n"
"}\n"
"QFrame#verticalControl {\n"
"border: 1px solid rgb(68,68,68);\n"
"}\n"
"")
        self.verticalControl.setFrameShape(QFrame.Box)
        self.verticalControl.setFrameShadow(QFrame.Plain)
        self.horizontalLayout_4 = QHBoxLayout(self.verticalControl)
        self.horizontalLayout_4.setSpacing(12)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.frame_3 = QFrame(self.verticalControl)
        self.frame_3.setObjectName(u"frame_3")
        sizePolicy2 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.frame_3.sizePolicy().hasHeightForWidth())
        self.frame_3.setSizePolicy(sizePolicy2)
        self.frame_3.setStyleSheet(u"QFrame {\n"
"    border-radius: 0px;\n"
"	border: 1px dotted gray;	\n"
"	margin: 1px;\n"
"	margin-left: -1px;\n"
"	margin-right: -2px;\n"
"}")
        self.frame_3.setFrameShape(QFrame.StyledPanel)
        self.frame_3.setFrameShadow(QFrame.Plain)
        self.frame_3.setLineWidth(0)
        self.frame_3.setMidLineWidth(0)

        self.horizontalLayout_4.addWidget(self.frame_3)

        self.pushButton = QPushButton(self.verticalControl)
        self.pushButton.setObjectName(u"pushButton")
        sizePolicy3 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.pushButton.sizePolicy().hasHeightForWidth())
        self.pushButton.setSizePolicy(sizePolicy3)
        icon2 = QIcon()
        icon2.addFile(u":/resources/style/stylesheet-branch-openup.png", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton.setIcon(icon2)
        self.pushButton.setIconSize(QSize(10, 10))

        self.horizontalLayout_4.addWidget(self.pushButton)

        self.pushButton_2 = QPushButton(self.verticalControl)
        self.pushButton_2.setObjectName(u"pushButton_2")
        sizePolicy3.setHeightForWidth(self.pushButton_2.sizePolicy().hasHeightForWidth())
        self.pushButton_2.setSizePolicy(sizePolicy3)
        icon3 = QIcon()
        icon3.addFile(u":/resources/style/stylesheet-branch-open.png", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_2.setIcon(icon3)
        self.pushButton_2.setIconSize(QSize(10, 10))

        self.horizontalLayout_4.addWidget(self.pushButton_2)

        self.frame_5 = QFrame(self.verticalControl)
        self.frame_5.setObjectName(u"frame_5")
        sizePolicy2.setHeightForWidth(self.frame_5.sizePolicy().hasHeightForWidth())
        self.frame_5.setSizePolicy(sizePolicy2)
        self.frame_5.setStyleSheet(u"QFrame {\n"
"    border-radius: 0px;\n"
"	border: 1px dotted gray;	\n"
"	margin: 1px;\n"
"	margin-left: -1px;\n"
"	margin-right: -2px;\n"
"}")
        self.frame_5.setFrameShape(QFrame.StyledPanel)
        self.frame_5.setFrameShadow(QFrame.Plain)

        self.horizontalLayout_4.addWidget(self.frame_5)


        self.verticalLayout_2.addWidget(self.verticalControl)


        self.horizontalLayout_3.addWidget(self.frame)


        self.verticalLayout.addWidget(self.ContentFrame)


        self.retranslateUi(ExpandableTabs)

        QMetaObject.connectSlotsByName(ExpandableTabs)
    # setupUi

    def retranslateUi(self, ExpandableTabs):
        ExpandableTabs.setWindowTitle(QCoreApplication.translate("ExpandableTabs", u"Form", None))
        self.iconButton.setText(QCoreApplication.translate("ExpandableTabs", u"...", None))
        self.nameLabel.setText(QCoreApplication.translate("ExpandableTabs", u"References", None))
        self.countSpinBox.setSuffix(QCoreApplication.translate("ExpandableTabs", u" )", None))
        self.countSpinBox.setPrefix(QCoreApplication.translate("ExpandableTabs", u"( ", None))
        self.checkButton.setText(QCoreApplication.translate("ExpandableTabs", u"...", None))
        self.pushButton.setText("")
        self.pushButton_2.setText("")
    # retranslateUi

