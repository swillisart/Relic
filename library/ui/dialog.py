# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.1.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

import relic_resources_rc
import resources_rc

class Ui_RelicMainWindow(object):
    def setupUi(self, RelicMainWindow):
        if not RelicMainWindow.objectName():
            RelicMainWindow.setObjectName(u"RelicMainWindow")
        RelicMainWindow.resize(1124, 710)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(RelicMainWindow.sizePolicy().hasHeightForWidth())
        RelicMainWindow.setSizePolicy(sizePolicy)
        icon = QIcon()
        icon.addFile(u":/resources/icons/app_icon.png", QSize(), QIcon.Normal, QIcon.Off)
        RelicMainWindow.setWindowIcon(icon)
        RelicMainWindow.setStyleSheet(u"QWidget {\n"
"	background-color: rgb(68, 68, 68);\n"
"    color: rgb(200, 200, 200);\n"
"    selection-background-color: rgb(126, 126, 126);\n"
"    selection-color: rgb(250, 250, 250);\n"
"}\n"
"QMainWindow::separator {\n"
"  width: 0px;\n"
"  border: 2px solid rgb(43,43,43);\n"
"  border-right: 1px solid rgb(108,108,108);\n"
"  border-bottom: 1px solid rgb(108,108,108);\n"
"  border-radius: 0px;\n"
"  margin: 11px;\n"
"}\n"
"QMainWindow::separator:hover {\n"
"  border-right: 1px solid rgb(150, 146, 137);\n"
"  border-bottom: 1px solid rgb(150, 146, 137);\n"
"}\n"
"QPushButton:hover {\n"
"    color: rgb(250, 250, 250);\n"
"    background-color: rgb(108, 108, 108);\n"
" }\n"
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
""
                        "    padding-left: 2px;\n"
"    margin-left: 0px;\n"
"    margin-right: 0px;\n"
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
"    image: url(:/resources/checkbox_checked.svg);\n"
"}\n"
"QMenu::indicator:non-exclusive:unchecked {\n"
"    image: url(:/resources/checkbox.svg);\n"
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
"*"
                        "/\n"
"}\n"
"\n"
"/* QSlider ---------------------------------------------------------------- */\n"
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
"    border: 1px solid rgb(68, 68, "
                        "68);\n"
"    border-radius: 4px;\n"
"    margin: 0px;\n"
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
        RelicMainWindow.setAnimated(True)
        RelicMainWindow.setDockNestingEnabled(True)
        self.actionPreferences = QAction(RelicMainWindow)
        self.actionPreferences.setObjectName(u"actionPreferences")
        self.actionExit = QAction(RelicMainWindow)
        self.actionExit.setObjectName(u"actionExit")
        self.actionAdministration_Mode = QAction(RelicMainWindow)
        self.actionAdministration_Mode.setObjectName(u"actionAdministration_Mode")
        self.actionAdministration_Mode.setCheckable(True)
        self.actionDocumentation = QAction(RelicMainWindow)
        self.actionDocumentation.setObjectName(u"actionDocumentation")
        icon1 = QIcon()
        icon1.addFile(u":/resources/radio_unchecked.png", QSize(), QIcon.Normal, QIcon.Off)
        self.actionDocumentation.setIcon(icon1)
        self.actionIngest = QAction(RelicMainWindow)
        self.actionIngest.setObjectName(u"actionIngest")
        icon2 = QIcon()
        icon2.addFile(u":/resources/icons/folder.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.actionIngest.setIcon(icon2)
        self.centralwidget = QWidget(RelicMainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(9, 9, 9, 9)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 8, 0, 8)
        self.listView = QListView(self.centralwidget)
        self.listView.setObjectName(u"listView")
        self.listView.setSizeAdjustPolicy(QAbstractScrollArea.AdjustIgnored)
        self.listView.setEditTriggers(QAbstractItemView.CurrentChanged)
        self.listView.setDragEnabled(True)
        self.listView.setDragDropMode(QAbstractItemView.DragDrop)
        self.listView.setDefaultDropAction(Qt.CopyAction)
        self.listView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.listView.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.listView.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.listView.setFlow(QListView.LeftToRight)
        self.listView.setProperty("isWrapping", True)
        self.listView.setResizeMode(QListView.Adjust)
        self.listView.setUniformItemSizes(True)
        self.listView.setWordWrap(False)
        self.listView.setSelectionRectVisible(True)
        self.listView.setItemAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.listView)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setSpacing(6)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(9, 0, 0, 0)
        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(u"label")

        self.horizontalLayout_3.addWidget(self.label)

        self.horizontalSlider = QSlider(self.centralwidget)
        self.horizontalSlider.setObjectName(u"horizontalSlider")
        self.horizontalSlider.setStyleSheet(u"")
        self.horizontalSlider.setMaximum(2)
        self.horizontalSlider.setPageStep(1)
        self.horizontalSlider.setValue(1)
        self.horizontalSlider.setOrientation(Qt.Horizontal)
        self.horizontalSlider.setTickPosition(QSlider.NoTicks)

        self.horizontalLayout_3.addWidget(self.horizontalSlider)


        self.horizontalLayout_2.addLayout(self.horizontalLayout_3)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_3)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setSpacing(6)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(-1, -1, 3, -1)
        self.pushButton_2 = QPushButton(self.centralwidget)
        self.pushButton_2.setObjectName(u"pushButton_2")
        self.pushButton_2.setStyleSheet(u"QPushButton {\n"
"    padding: 2px;\n"
"	border: none;\n"
"}")
        icon3 = QIcon()
        icon3.addFile(u":/resources/icons/pageArrowLeft.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_2.setIcon(icon3)
        self.pushButton_2.setIconSize(QSize(20, 20))

        self.horizontalLayout_4.addWidget(self.pushButton_2)

        self.spinBox = QSpinBox(self.centralwidget)
        self.spinBox.setObjectName(u"spinBox")
        self.spinBox.setStyleSheet(u"QAbstractSpinBox {\n"
"    padding: 1px;\n"
"    padding-left: 4px;\n"
"    margin: 1px;\n"
"    border: 1px solid rgb(43, 43, 43);\n"
"\n"
"}")
        self.spinBox.setFrame(False)
        self.spinBox.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.spinBox.setMaximum(9999)
        self.spinBox.setValue(1)

        self.horizontalLayout_4.addWidget(self.spinBox)

        self.pushButton_3 = QPushButton(self.centralwidget)
        self.pushButton_3.setObjectName(u"pushButton_3")
        self.pushButton_3.setStyleSheet(u"QPushButton {\n"
"    padding: 2px;\n"
"	border: none;\n"
"}")
        icon4 = QIcon()
        icon4.addFile(u":/resources/icons/pageArrow.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_3.setIcon(icon4)
        self.pushButton_3.setIconSize(QSize(20, 20))

        self.horizontalLayout_4.addWidget(self.pushButton_3)


        self.horizontalLayout_2.addLayout(self.horizontalLayout_4)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        RelicMainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(RelicMainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1124, 22))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuEdit = QMenu(self.menubar)
        self.menuEdit.setObjectName(u"menuEdit")
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName(u"menuHelp")
        RelicMainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(RelicMainWindow)
        self.statusbar.setObjectName(u"statusbar")
        self.statusbar.setSizeGripEnabled(True)
        RelicMainWindow.setStatusBar(self.statusbar)
        self.categoryDock = QDockWidget(RelicMainWindow)
        self.categoryDock.setObjectName(u"categoryDock")
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName(u"dockWidgetContents")
        self.categoryDock.setWidget(self.dockWidgetContents)
        RelicMainWindow.addDockWidget(Qt.LeftDockWidgetArea, self.categoryDock)
        self.searchDock = QDockWidget(RelicMainWindow)
        self.searchDock.setObjectName(u"searchDock")
        self.searchDock.setStyleSheet(u"QDockWidget::title {\n"
"    border: 0px;\n"
"	padding: 0px;\n"
"	margin: 0px;\n"
"    width: 0px;\n"
"    height: 0px;\n"
"}\n"
"")
        self.searchDock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.dockWidgetContents_2 = QWidget()
        self.dockWidgetContents_2.setObjectName(u"dockWidgetContents_2")
        self.gridLayout = QGridLayout(self.dockWidgetContents_2)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(9, 9, 9, 9)
        self.gridLayout.setObjectName(u"gridLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 0, 0, 1, 1)

        self.frame = QFrame(self.dockWidgetContents_2)
        self.frame.setObjectName(u"frame")
        sizePolicy1 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy1)
        self.frame.setStyleSheet(u"QFrame {\n"
"    border: 2px solid rgb(43, 43, 43);\n"
"    background-color: rgb(43, 43, 43);\n"
"    border-radius: 3px;\n"
"}\n"
"QFrame:hover {\n"
"    border: 2px solid rgb(150, 146, 137);\n"
"}")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Plain)
        self.horizontalLayout = QHBoxLayout(self.frame)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setContentsMargins(9, 9, 9, 9)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.pushButton = QPushButton(self.frame)
        self.pushButton.setObjectName(u"pushButton")
        self.pushButton.setStyleSheet(u"QPushButton {\n"
"    background-color: rgb(43, 43, 43);\n"
"    padding: 2px;\n"
"	border: none;\n"
"}")
        icon5 = QIcon()
        icon5.addFile(u":/resources/icons/search.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton.setIcon(icon5)
        self.pushButton.setIconSize(QSize(20, 20))
        self.pushButton.setFlat(False)

        self.horizontalLayout.addWidget(self.pushButton)

        self.lineEdit = QLineEdit(self.frame)
        self.lineEdit.setObjectName(u"lineEdit")
        sizePolicy2 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.lineEdit.sizePolicy().hasHeightForWidth())
        self.lineEdit.setSizePolicy(sizePolicy2)
        self.lineEdit.setMinimumSize(QSize(256, 26))
        self.lineEdit.setStyleSheet(u"QLineEdit { padding: 0px;}\n"
"")
        self.lineEdit.setFrame(False)
        self.lineEdit.setClearButtonEnabled(True)

        self.horizontalLayout.addWidget(self.lineEdit)


        self.gridLayout.addWidget(self.frame, 0, 1, 1, 1)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_2, 0, 2, 1, 1)

        self.searchDock.setWidget(self.dockWidgetContents_2)
        RelicMainWindow.addDockWidget(Qt.TopDockWidgetArea, self.searchDock)
        self.attributeDock = QDockWidget(RelicMainWindow)
        self.attributeDock.setObjectName(u"attributeDock")
        self.dockWidgetContents_3 = QWidget()
        self.dockWidgetContents_3.setObjectName(u"dockWidgetContents_3")
        self.attributeDock.setWidget(self.dockWidgetContents_3)
        RelicMainWindow.addDockWidget(Qt.RightDockWidgetArea, self.attributeDock)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.menuFile.addAction(self.actionPreferences)
        self.menuFile.addAction(self.actionExit)
        self.menuEdit.addAction(self.actionAdministration_Mode)
        self.menuEdit.addAction(self.actionIngest)
        self.menuHelp.addAction(self.actionDocumentation)

        self.retranslateUi(RelicMainWindow)

        QMetaObject.connectSlotsByName(RelicMainWindow)
    # setupUi

    def retranslateUi(self, RelicMainWindow):
        RelicMainWindow.setWindowTitle(QCoreApplication.translate("RelicMainWindow", u"Relic", None))
        self.actionPreferences.setText(QCoreApplication.translate("RelicMainWindow", u"Preferences", None))
        self.actionExit.setText(QCoreApplication.translate("RelicMainWindow", u"Exit", None))
        self.actionAdministration_Mode.setText(QCoreApplication.translate("RelicMainWindow", u"Administration Mode", None))
        self.actionDocumentation.setText(QCoreApplication.translate("RelicMainWindow", u"Documentation", None))
        self.actionIngest.setText(QCoreApplication.translate("RelicMainWindow", u"Ingest", None))
        self.label.setText(QCoreApplication.translate("RelicMainWindow", u"Scale", None))
        self.pushButton_2.setText("")
        self.spinBox.setPrefix(QCoreApplication.translate("RelicMainWindow", u"Page ", None))
        self.pushButton_3.setText("")
        self.menuFile.setTitle(QCoreApplication.translate("RelicMainWindow", u"File", None))
        self.menuEdit.setTitle(QCoreApplication.translate("RelicMainWindow", u"Edit", None))
        self.menuHelp.setTitle(QCoreApplication.translate("RelicMainWindow", u"Help", None))
#if QT_CONFIG(statustip)
        self.statusbar.setStatusTip("")
#endif // QT_CONFIG(statustip)
        self.categoryDock.setWindowTitle(QCoreApplication.translate("RelicMainWindow", u"deads", None))
        self.pushButton.setText("")
        self.lineEdit.setPlaceholderText(QCoreApplication.translate("RelicMainWindow", u"Search...", None))
    # retranslateUi

