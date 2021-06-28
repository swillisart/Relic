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
        RelicMainWindow.resize(1117, 702)
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
"    outline: 0;\n"
"}\n"
"QWidget:item {\n"
"    background-color: transparent;\n"
"}\n"
"QWidget:item:hover {\n"
"    background-color: rgb(150, 146, 137);\n"
"    color: rgb(250, 250, 250);\n"
"}\n"
"QWidget:item:selected {\n"
"    background-color: rgb(150, 146, 137);\n"
"    color: rgb(43, 43, 43);\n"
"}\n"
"QWidget:disabled {\n"
"    background-color: rgb(43, 43, 43);\n"
"    color: rgb(92, 92, 92);\n"
"}\n"
"\n"
"QMainWindow::separator {\n"
"  width: 0px;\n"
"  height: 0px;\n"
"  border: 2px solid rgb(43,43,43);\n"
"  border-right: 1px solid rgb(108,108,108);\n"
"  border-bottom: 1px solid rgb(108,108,108);\n"
"  border-radius: 0px;\n"
"  margin: 8px;\n"
"}\n"
"QMainWindow::separator:hover {\n"
"  border-right: 1px solid rgb(150, 146, 137);\n"
"  border-bottom: 1px solid rgb(150, 146, 137);\n"
"}\n"
"QPushButton {\n"
""
                        "    outline: none;\n"
"    padding: 3px;\n"
"	padding-left: 18px;\n"
"	padding-right: 18px;\n"
"	border: none;\n"
"    background-color: rgb(92, 92, 92);\n"
"}\n"
"QPushButton:hover {\n"
"    color: rgb(250, 250, 250);\n"
"    background-color: rgb(108, 108, 108);\n"
" }\n"
"QScrollArea {\n"
"    border: 1px solid rgb(57, 57, 57);\n"
"}\n"
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
"    b"
                        "ackground-color: rgb(57, 57, 57);\n"
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
"    background-image: url();\n"
"    color: rgb(200, 200, 200);\n"
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
"/* QSlider ---------------------------------------------------------------- */\n"
"QSlider::add-page:horizontal, \n"
"QSlider::sub-page:horizontal,\n"
"QSlider::add-page:vertical, \n"
"QSlider::sub-page:vertical {\n"
"    background: rgb(43, 43, 43);\n"
"}"
                        "\n"
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
"    ba"
                        "ckground: #14506E;\n"
"}\n"
"\n"
"/* QScrollBar ------------------------------------------------------------- */\n"
"\n"
"QScrollBar:horizontal {\n"
"    height: 10px;\n"
"    margin: 0px 16px 0px 16px;\n"
"    border: 1px solid rgb(55, 55, 55);\n"
"    border-radius: 40px;\n"
"    background-color: rgb(55, 55, 55);\n"
"}\n"
"QScrollBar::handle:horizontal {\n"
"    background-color: #787878;\n"
"    border: 0px solid rgb(68, 68, 68);\n"
"    border-radius: 4px;\n"
"    min-width: 8px;\n"
"}\n"
"QScrollBar::add-line:horizontal:hover,\n"
"QScrollBar::add-line:horizontal:on,\n"
"QScrollBar::add-line:horizontal {\n"
"    margin: 0px 3px 0px 0px;\n"
"    border-image: url(:/resources/stylesheet-branch-closed.png);\n"
"    height: 10px;\n"
"    width: 6px;\n"
"    subcontrol-position: right;\n"
"    subcontrol-origin: margin;\n"
"}\n"
"QScrollBar::sub-line:horizontal:hover,\n"
"QScrollBar::sub-line:horizontal:on,\n"
"QScrollBar::sub-line:horizontal {\n"
"    margin: 0px 0px 0px 3px;\n"
"    border-image: url(:/resou"
                        "rces/stylesheet-branch-closedleft.png);\n"
"    height: 10px;\n"
"    width: 6px;\n"
"    subcontrol-position: left;\n"
"    subcontrol-origin: margin;\n"
"}\n"
"QScrollBar:vertical {\n"
"    background-color: rgb(55, 55, 55);\n"
"    width: 10px;\n"
"    margin: 16px 0px 16px 0px;\n"
"    border: 1px solid rgb(55, 55, 55);\n"
"    border-radius: 4px;\n"
"}\n"
"QScrollBar::handle:vertical {\n"
"    background-color: #787878;\n"
"    border: 1px solid rgb(68, 68, 68);\n"
"    min-height: 8px;\n"
"    border-radius: 4px;\n"
"}\n"
"QScrollBar::sub-line:vertical {\n"
"    margin: 3px 0px 0px 0px;\n"
"    border-image: url(:/resources/stylesheet-branch-openup.png);\n"
"    height: 6px;\n"
"    width: 10px;\n"
"    subcontrol-position: top;\n"
"    subcontrol-origin: margin;\n"
"}\n"
"QScrollBar::add-line:vertical {\n"
"    margin: 0px 0px 3px 0px;\n"
"    border-image: url(:/resources/stylesheet-branch-open.png);\n"
"    height: 6px;\n"
"    width: 10px;\n"
"    subcontrol-position: bottom;\n"
"    subcontrol-origi"
                        "n: margin;\n"
"}\n"
"QScrollBar::sub-line:vertical:hover,\n"
"QScrollBar::sub-line:vertical:on {\n"
"    border-image: url(:/resources/stylesheet-branch-openup.png);\n"
"    height: 10px;\n"
"    width: 10px;\n"
"    subcontrol-position: top;\n"
"    subcontrol-origin: margin;\n"
"}\n"
"QScrollBar::add-page:horizontal,\n"
"QScrollBar::sub-page:horizontal,\n"
"QScrollBar::up-arrow:horizontal,\n"
"QScrollBar::down-arrow:horizontal,\n"
"QScrollBar::up-arrow:vertical,\n"
"QScrollBar::down-arrow:vertical,\n"
"QScrollBar::add-page:vertical,\n"
"QScrollBar::sub-page:vertical  {\n"
"    background: none;\n"
"}\n"
"\n"
"QListView,\n"
"QTreeView,\n"
"QTableView,\n"
"QColumnView {\n"
"    border: none;\n"
"}\n"
"QListView::item,\n"
"QTreeView::item,\n"
"QTableView::item,\n"
"QColumnView::item {\n"
"    border-top: none;\n"
"    padding: 0px; /*DO NOT CHANGE*/\n"
"    padding-right: 8px; /*DO NOT CHANGE*/\n"
"    margin-top: 2px;\n"
"    margin-bottom: 2px;\n"
"}\n"
"\n"
"QTreeView::branch {\n"
"    border-top: 0px solid "
                        "rgb(43, 43, 43);\n"
"    border-bottom: 0px solid rgb(43, 43, 43);\n"
"    padding: 4px; /*DO NOT CHANGE*/\n"
"    margin-top: 2px;\n"
"    margin-bottom: 2px;\n"
"}\n"
"QTreeView::branch:has-siblings:!adjoins-item {\n"
"    border-image: url(:/resources/stylesheet-vline.png);\n"
"}\n"
"QTreeView::branch:has-siblings:adjoins-item {\n"
"    border-image: url(:/resources/stylesheet-branch-more.png);\n"
"}\n"
"QTreeView::branch:!has-children:!has-siblings:adjoins-item {\n"
"    border-image: url(:/resources/stylesheet-branch-end.png);\n"
"}\n"
"QTreeView::branch:has-children:!has-siblings:closed,\n"
"QTreeView::branch:closed:has-children:has-siblings {\n"
"    image: url(:/resources/icons/treeExpand.svg);\n"
"}\n"
"QTreeView::branch:open:has-children:!has-siblings,\n"
"QTreeView::branch:open:has-children:has-siblings  {\n"
"    image: url(:/resources/icons/treeCollapse.svg);\n"
"}\n"
"\n"
"\n"
"/* QCombobox -------------------------------------------------------------- */\n"
"QComboBox {\n"
"    border: 0px;\n"
""
                        "    border-radius: 3px;\n"
"    background-color: rgb(92, 92, 92);\n"
"    padding-top: 2px;     /* This fix  #103, #111*/\n"
"    padding-bottom: 1px;  /* This fix  #103, #111*/\n"
"    padding-left: 4px;\n"
"    padding-right: 4px;\n"
"    min-width: 75px;\n"
"}\n"
"QComboBox::drop-down {\n"
"    subcontrol-origin: padding;\n"
"    subcontrol-position: top right;\n"
"    width: 20px;\n"
"    border-left-width: 2px;\n"
"    border-left-color: rgb(68, 68, 68);\n"
"    border-left-style: solid;\n"
"    border-top-right-radius: 0px;\n"
"    border-bottom-right-radius: 0px;\n"
"    padding-right: 3px;\n"
"    margin-left: 6px;\n"
"}\n"
"QComboBox::down-arrow,\n"
"QComboBox::down-arrow:on,\n"
"QComboBox::down-arrow:hover,\n"
"QComboBox::down-arrow:focus {\n"
"    image: url(:/resources/stylesheet-branch-open.png);\n"
"}\n"
"\n"
"\n"
"/* QCheckBox -------------------------------------------------------------- */\n"
"\n"
"\n"
"QCheckBox::indicator:checked:hover,\n"
"QTreeView::indicator:checked:hover,\n"
"QListView:"
                        ":indicator:checked:hover {\n"
"    image: url(:/resources/checkbox_checked_hover.svg);\n"
"}\n"
"QCheckBox::indicator:unchecked:hover,\n"
"QTreeView::indicator:unchecked:hover,\n"
"QListView::indicator:unchecked:hover {\n"
"    image: url(:/resources/checkbox_hover.svg);\n"
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
"}\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
""
                        "\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"/* QTabWiget -------------------------------------------------------------- */\n"
"\n"
"QTabWidget {\n"
"    padding: 4px;\n"
"    padding-left: 16px;\n"
"    padding-right: 16px;\n"
"    selection-background-color: rgb(68, 68, 68);\n"
"    border: 0;\n"
"}\n"
"QTabWidget::tab-bar {\n"
"    alignment: center;\n"
"}\n"
"QTabWidget::pane {\n"
"    border: none;\n"
"    margin: 0px;\n"
"}\n"
"QTabWidget::pane:selected {\n"
"    background-color: rgb(68, 68, 68);\n"
"}\n"
"\n"
"/* QTabBar ---------------------------------------------------------------- */\n"
"\n"
"QTabBar {\n"
"    qproperty-drawBase: 0;\n"
"    border-radius: 3px;\n"
"    margin: 0px;\n"
"    padding: 4px;\n"
"    border: 0;\n"
"    background-color: rgb(68, 68, 68);\n"
"    font: bold 10pt;\n"
"}\n"
"\n"
"QTabBar::tab {\n"
"    border-bottom: 3px solid rgb(55, 55, 55);\n"
"    color: #787878;\n"
"    background-color: rgb(68, 68, 68);\n"
"}\n"
"\n"
"/* QTabBar::tab - selected ---------------"
                        "-------------------------------- */\n"
"\n"
"QTabBar::tab:top:selected:disabled {\n"
"    border-bottom: 3px solid #14506E;\n"
"    color: #787878;\n"
"    background-color: rgb(68, 68, 68);\n"
"}\n"
"QTabBar::tab:bottom:selected:disabled {\n"
"    border-top: 3px solid #14506E;\n"
"    color: #787878;\n"
"    background-color: rgb(68, 68, 68);\n"
"}\n"
"QTabBar::tab:left:selected:disabled {\n"
"    border-left: 3px solid #14506E;\n"
"    color: #787878;\n"
"    background-color: rgb(68, 68, 68);\n"
"}\n"
"QTabBar::tab:right:selected:disabled {\n"
"    border-right: 3px solid #14506E;\n"
"    color: #787878;\n"
"    background-color: rgb(68, 68, 68);\n"
"}\n"
"\n"
"/* QTabBar::tab - !selected and disabled ---------------------------------- */\n"
"\n"
"QTabBar::tab:disabled {\n"
"	margin: 0; padding: 0; border: none;\n"
"}\n"
"QTabBar::tab:top:!selected:disabled {\n"
"    margin-left: 4px;\n"
"    margin-right: 4px;\n"
"    margin-top: 2px;\n"
"    margin-bottom: 1px;\n"
"    padding-left: 10px; \n"
"    paddin"
                        "g-right: 10px;\n"
"    padding-top: 4px;\n"
"    padding-bottom: 4px;\n"
"    min-width: 4px;\n"
"    border-top-left-radius: 3px;\n"
"    border-top-right-radius: 3px;\n"
"    font-weight: normal;\n"
"    border-bottom: 3px solid rgb(68, 68, 68);\n"
"    border-right: 1px solid rgb(68, 68, 68);\n"
"    border-left: 1px solid rgb(68, 68, 68);\n"
"    border-top: 1px solid rgb(68, 68, 68);\n"
"    color: rgb(100, 100, 100);\n"
"}\n"
"QTabBar::tab:bottom:!selected:disabled {\n"
"    border-top: 3px solid rgb(43, 43, 43);\n"
"    color: #787878;\n"
"    background-color: rgb(43, 43, 43);\n"
"}\n"
"QTabBar::tab:left:!selected:disabled {\n"
"    border-right: 3px solid rgb(43, 43, 43);\n"
"    color: #787878;\n"
"    background-color: rgb(43, 43, 43);\n"
"}\n"
"QTabBar::tab:right:!selected:disabled {\n"
"    border-left: 3px solid rgb(43, 43, 43);\n"
"    color: #787878;\n"
"    background-color: rgb(43, 43, 43);\n"
"}\n"
"/* QTabBar::tab - selected ----------------------------------------------- */\n"
"\n"
"QTabBa"
                        "r::tab {\n"
"    background-color: rgb(55, 55, 55);\n"
"    color: rgb(175, 175, 175);\n"
"    margin-left: 4px;\n"
"    margin-right: 4px;\n"
"    margin-top: 2px;\n"
"    margin-bottom: 1px;\n"
"    padding-left: 18px; \n"
"    padding-right: 18px;\n"
"    padding-top: 4px;\n"
"    padding-bottom: 4px;\n"
"    min-width: 4px;\n"
"    border-top-left-radius: 3px;\n"
"    border-top-right-radius: 3px;\n"
"    font-weight: normal;\n"
"    border-bottom: 3px solid rgb(43, 43, 43);\n"
"    border-right: 1px solid rgb(43, 43, 43);\n"
"    border-left: 1px solid rgb(43, 43, 43);\n"
"    border-top: 1px solid rgb(43, 43, 43);\n"
"}\n"
"\n"
"QTabBar::tab:selected {\n"
"    color: rgb(220, 220, 220);\n"
"    background-color: qlineargradient(y1: 1, y2: -.5, stop: 0 rgb(55, 105, 140), stop: 0.20 rgb(68, 68, 68));\n"
"    border-bottom: 2px solid rgb(70, 125, 160);\n"
"    border-right: 1px solid rgb(66, 118, 150);\n"
"    border-left: 1px solid rgb(66, 118, 150);\n"
"    border-top-left-radius: 3px;\n"
"    border-top-"
                        "right-radius: 3px;\n"
"    border-top: 1px solid rgb(43, 43, 43);\n"
"}\n"
"")
        RelicMainWindow.setAnimated(True)
        RelicMainWindow.setDockNestingEnabled(True)
        self.actionPreferences = QAction(RelicMainWindow)
        self.actionPreferences.setObjectName(u"actionPreferences")
        icon1 = QIcon()
        icon1.addFile(u":/resources/icons/treeMod3.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.actionPreferences.setIcon(icon1)
        self.actionExit = QAction(RelicMainWindow)
        self.actionExit.setObjectName(u"actionExit")
        icon2 = QIcon()
        icon2.addFile(u":/resources/close.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.actionExit.setIcon(icon2)
        self.actionAdministration_Mode = QAction(RelicMainWindow)
        self.actionAdministration_Mode.setObjectName(u"actionAdministration_Mode")
        self.actionAdministration_Mode.setCheckable(True)
        self.actionDocumentation = QAction(RelicMainWindow)
        self.actionDocumentation.setObjectName(u"actionDocumentation")
        self.actionDocumentation.setIcon(icon1)
        self.actionIngest = QAction(RelicMainWindow)
        self.actionIngest.setObjectName(u"actionIngest")
        icon3 = QIcon()
        icon3.addFile(u":/resources/icons/folder.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.actionIngest.setIcon(icon3)
        self.actionPortal = QAction(RelicMainWindow)
        self.actionPortal.setObjectName(u"actionPortal")
        self.actionPortal.setCheckable(True)
        self.actionPortal.setChecked(True)
        self.centralwidget = QWidget(RelicMainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(9, 9, 9, 9)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(9, 0, 9, 0)
        self.line_5 = QFrame(self.centralwidget)
        self.line_5.setObjectName(u"line_5")
        self.line_5.setFrameShape(QFrame.HLine)
        self.line_5.setFrameShadow(QFrame.Sunken)

        self.verticalLayout.addWidget(self.line_5)

        self.verticalSpacer_2 = QSpacerItem(2, 9, QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.documentationDock = QDockWidget(self.centralwidget)
        self.documentationDock.setObjectName(u"documentationDock")
        sizePolicy1 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.documentationDock.sizePolicy().hasHeightForWidth())
        self.documentationDock.setSizePolicy(sizePolicy1)
        palette = QPalette()
        brush = QBrush(QColor(200, 200, 200, 255))
        brush.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.WindowText, brush)
        brush1 = QBrush(QColor(68, 68, 68, 255))
        brush1.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.Button, brush1)
        palette.setBrush(QPalette.Active, QPalette.Text, brush)
        palette.setBrush(QPalette.Active, QPalette.ButtonText, brush)
        palette.setBrush(QPalette.Active, QPalette.Base, brush1)
        palette.setBrush(QPalette.Active, QPalette.Window, brush1)
        brush2 = QBrush(QColor(126, 126, 126, 255))
        brush2.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.Highlight, brush2)
        brush3 = QBrush(QColor(250, 250, 250, 255))
        brush3.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.HighlightedText, brush3)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.Active, QPalette.PlaceholderText, brush)
#endif
        palette.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        palette.setBrush(QPalette.Inactive, QPalette.Button, brush1)
        palette.setBrush(QPalette.Inactive, QPalette.Text, brush)
        palette.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
        palette.setBrush(QPalette.Inactive, QPalette.Base, brush1)
        palette.setBrush(QPalette.Inactive, QPalette.Window, brush1)
        palette.setBrush(QPalette.Inactive, QPalette.Highlight, brush2)
        palette.setBrush(QPalette.Inactive, QPalette.HighlightedText, brush3)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush)
#endif
        brush4 = QBrush(QColor(92, 92, 92, 255))
        brush4.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Disabled, QPalette.WindowText, brush4)
        brush5 = QBrush(QColor(43, 43, 43, 255))
        brush5.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Disabled, QPalette.Button, brush5)
        palette.setBrush(QPalette.Disabled, QPalette.Text, brush4)
        palette.setBrush(QPalette.Disabled, QPalette.ButtonText, brush4)
        palette.setBrush(QPalette.Disabled, QPalette.Base, brush5)
        palette.setBrush(QPalette.Disabled, QPalette.Window, brush5)
        palette.setBrush(QPalette.Disabled, QPalette.Highlight, brush2)
        palette.setBrush(QPalette.Disabled, QPalette.HighlightedText, brush3)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush4)
#endif
        self.documentationDock.setPalette(palette)
        self.documentationDock.setStyleSheet(u"QTextBrowser {\n"
"background-color: rgb()\n"
"}")
        self.documentationDock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.attrDockWidgetContents_3 = QWidget()
        self.attrDockWidgetContents_3.setObjectName(u"attrDockWidgetContents_3")
        self.attrDockWidgetContents_3.setMaximumSize(QSize(1024, 16777215))
        self.horizontalLayout_11 = QHBoxLayout(self.attrDockWidgetContents_3)
        self.horizontalLayout_11.setSpacing(6)
        self.horizontalLayout_11.setContentsMargins(9, 9, 9, 9)
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.documentationTextBrowser = QTextBrowser(self.attrDockWidgetContents_3)
        self.documentationTextBrowser.setObjectName(u"documentationTextBrowser")
        font = QFont()
        font.setPointSize(11)
        self.documentationTextBrowser.setFont(font)
        self.documentationTextBrowser.setStyleSheet(u"QTextBrowser {\n"
"padding: 8px 8px 8px 40px;\n"
"background-color: rgb(75, 75, 75);\n"
"}")
        self.documentationTextBrowser.setFrameShape(QFrame.NoFrame)

        self.horizontalLayout_11.addWidget(self.documentationTextBrowser)

        self.documentationDock.setWidget(self.attrDockWidgetContents_3)

        self.verticalLayout.addWidget(self.documentationDock)

        self.linksDock = QDockWidget(self.centralwidget)
        self.linksDock.setObjectName(u"linksDock")
        sizePolicy1.setHeightForWidth(self.linksDock.sizePolicy().hasHeightForWidth())
        self.linksDock.setSizePolicy(sizePolicy1)
        palette1 = QPalette()
        palette1.setBrush(QPalette.Active, QPalette.WindowText, brush)
        palette1.setBrush(QPalette.Active, QPalette.Button, brush1)
        palette1.setBrush(QPalette.Active, QPalette.Text, brush)
        palette1.setBrush(QPalette.Active, QPalette.ButtonText, brush)
        palette1.setBrush(QPalette.Active, QPalette.Base, brush1)
        palette1.setBrush(QPalette.Active, QPalette.Window, brush1)
        palette1.setBrush(QPalette.Active, QPalette.Highlight, brush2)
        palette1.setBrush(QPalette.Active, QPalette.HighlightedText, brush3)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette1.setBrush(QPalette.Active, QPalette.PlaceholderText, brush)
#endif
        palette1.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        palette1.setBrush(QPalette.Inactive, QPalette.Button, brush1)
        palette1.setBrush(QPalette.Inactive, QPalette.Text, brush)
        palette1.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
        palette1.setBrush(QPalette.Inactive, QPalette.Base, brush1)
        palette1.setBrush(QPalette.Inactive, QPalette.Window, brush1)
        palette1.setBrush(QPalette.Inactive, QPalette.Highlight, brush2)
        palette1.setBrush(QPalette.Inactive, QPalette.HighlightedText, brush3)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette1.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush)
#endif
        palette1.setBrush(QPalette.Disabled, QPalette.WindowText, brush4)
        palette1.setBrush(QPalette.Disabled, QPalette.Button, brush5)
        palette1.setBrush(QPalette.Disabled, QPalette.Text, brush4)
        palette1.setBrush(QPalette.Disabled, QPalette.ButtonText, brush4)
        palette1.setBrush(QPalette.Disabled, QPalette.Base, brush5)
        palette1.setBrush(QPalette.Disabled, QPalette.Window, brush5)
        palette1.setBrush(QPalette.Disabled, QPalette.Highlight, brush2)
        palette1.setBrush(QPalette.Disabled, QPalette.HighlightedText, brush3)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette1.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush4)
#endif
        self.linksDock.setPalette(palette1)
        self.linksDock.setStyleSheet(u"")
        self.linksDock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.attrDockWidgetContents_2 = QWidget()
        self.attrDockWidgetContents_2.setObjectName(u"attrDockWidgetContents_2")
        self.linksDock.setWidget(self.attrDockWidgetContents_2)

        self.verticalLayout.addWidget(self.linksDock)

        self.dockTitleFrame = QFrame(self.centralwidget)
        self.dockTitleFrame.setObjectName(u"dockTitleFrame")
        self.dockTitleFrame.setStyleSheet(u"QFrame{\n"
"    background-color: rgb(57, 57, 57);\n"
"   /* border: 1px solid rgb(43,43,43);*/\n"
"    border: 2px solid rgb(57,57,57);\n"
"\n"
"}")
        self.dockTitleFrame.setFrameShape(QFrame.StyledPanel)
        self.dockTitleFrame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_5 = QHBoxLayout(self.dockTitleFrame)
        self.horizontalLayout_5.setSpacing(9)
        self.horizontalLayout_5.setContentsMargins(9, 9, 9, 9)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.dockTitleWidgets = QFrame(self.dockTitleFrame)
        self.dockTitleWidgets.setObjectName(u"dockTitleWidgets")
        self.dockTitleWidgets.setStyleSheet(u"border: none;")
        self.dockTitleWidgets.setFrameShape(QFrame.StyledPanel)
        self.dockTitleWidgets.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_7 = QHBoxLayout(self.dockTitleWidgets)
        self.horizontalLayout_7.setSpacing(9)
        self.horizontalLayout_7.setContentsMargins(9, 9, 9, 9)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.toolButton = QToolButton(self.dockTitleWidgets)
        self.toolButton.setObjectName(u"toolButton")
        self.toolButton.setEnabled(False)
        self.toolButton.setStyleSheet(u"padding: -2px;\n"
"margin-left: 4px;")

        self.horizontalLayout_7.addWidget(self.toolButton)

        self.label_2 = QLabel(self.dockTitleWidgets)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setFont(font)
        self.label_2.setStyleSheet(u"border:none;")
        self.label_2.setFrameShape(QFrame.NoFrame)
        self.label_2.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_7.addWidget(self.label_2)

        self.filterFrame = QFrame(self.dockTitleWidgets)
        self.filterFrame.setObjectName(u"filterFrame")
        sizePolicy2 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.filterFrame.sizePolicy().hasHeightForWidth())
        self.filterFrame.setSizePolicy(sizePolicy2)
        self.filterFrame.setStyleSheet(u"QFrame {\n"
"	margin: 2px;\n"
"    border: 1px solid rgb(43, 43, 43);\n"
"    background-color: rgb(43, 43, 43);\n"
"    border-radius: 3px;\n"
"}\n"
"QFrame:hover {\n"
"    border: 1px solid rgb(150, 146, 137);\n"
"}")
        self.filterFrame.setFrameShape(QFrame.StyledPanel)
        self.filterFrame.setFrameShadow(QFrame.Plain)
        self.horizontalLayout_6 = QHBoxLayout(self.filterFrame)
        self.horizontalLayout_6.setSpacing(0)
        self.horizontalLayout_6.setContentsMargins(9, 9, 9, 9)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.filterButton = QPushButton(self.filterFrame)
        self.filterButton.setObjectName(u"filterButton")
        sizePolicy3 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.filterButton.sizePolicy().hasHeightForWidth())
        self.filterButton.setSizePolicy(sizePolicy3)
        self.filterButton.setStyleSheet(u"QPushButton {\n"
"    background-color: rgb(57, 57, 57);\n"
"    padding: 0px;\n"
"	border: none;\n"
"}\n"
"QPushButton:hover {\n"
"    background-color: rgb(108, 108, 108);\n"
"}\n"
"QPushButton:checked {\n"
"    background-color: rgb(43, 43, 43);\n"
"}")
        icon4 = QIcon()
        icon4.addFile(u":/resources/icons/searchLight.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.filterButton.setIcon(icon4)
        self.filterButton.setIconSize(QSize(18, 18))
        self.filterButton.setCheckable(True)
        self.filterButton.setChecked(True)
        self.filterButton.setFlat(False)

        self.horizontalLayout_6.addWidget(self.filterButton)

        self.filterBox = QLineEdit(self.filterFrame)
        self.filterBox.setObjectName(u"filterBox")
        sizePolicy4 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.filterBox.sizePolicy().hasHeightForWidth())
        self.filterBox.setSizePolicy(sizePolicy4)
        self.filterBox.setMinimumSize(QSize(0, 0))
        font1 = QFont()
        font1.setPointSize(8)
        self.filterBox.setFont(font1)
        self.filterBox.setStyleSheet(u"QLineEdit { padding: 0px;}\n"
"")
        self.filterBox.setFrame(False)
        self.filterBox.setClearButtonEnabled(True)

        self.horizontalLayout_6.addWidget(self.filterBox)


        self.horizontalLayout_7.addWidget(self.filterFrame)


        self.horizontalLayout_5.addWidget(self.dockTitleWidgets)

        self.horizontalSpacer_4 = QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_4)

        self.categoryExpandButton = QPushButton(self.dockTitleFrame)
        self.categoryExpandButton.setObjectName(u"categoryExpandButton")
        self.categoryExpandButton.setStyleSheet(u"QPushButton {\n"
"    padding: 0px;\n"
"    margin: 1px;\n"
"    background-color: rgb(57, 57, 57);\n"
"	border :none;\n"
"}\n"
"QPushButton:hover {\n"
"    background-color: rgb(92, 92, 92);\n"
"    color: rgb(250, 250, 250);\n"
"}\n"
"")
        icon5 = QIcon()
        icon5.addFile(u":/resources/icons/pageArrow.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon5.addFile(u":/resources/icons/pageArrowLeft.svg", QSize(), QIcon.Active, QIcon.On)
        self.categoryExpandButton.setIcon(icon5)
        self.categoryExpandButton.setIconSize(QSize(22, 22))
        self.categoryExpandButton.setCheckable(True)
        self.categoryExpandButton.setChecked(True)

        self.horizontalLayout_5.addWidget(self.categoryExpandButton)


        self.verticalLayout.addWidget(self.dockTitleFrame)

        self.attributeDockTitle = QFrame(self.centralwidget)
        self.attributeDockTitle.setObjectName(u"attributeDockTitle")
        self.attributeDockTitle.setStyleSheet(u"QFrame{\n"
"    background-color: rgb(57, 57, 57);\n"
"   /* border: 1px solid rgb(43,43,43);*/\n"
"    border: 2px solid rgb(57,57,57);\n"
"\n"
"}")
        self.attributeDockTitle.setFrameShape(QFrame.StyledPanel)
        self.attributeDockTitle.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_8 = QHBoxLayout(self.attributeDockTitle)
        self.horizontalLayout_8.setSpacing(9)
        self.horizontalLayout_8.setContentsMargins(9, 9, 9, 9)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.attrExpandButton = QPushButton(self.attributeDockTitle)
        self.attrExpandButton.setObjectName(u"attrExpandButton")
        self.attrExpandButton.setStyleSheet(u"QPushButton {\n"
"    padding: 0px;\n"
"    margin: 1px;\n"
"    background-color: rgb(57, 57, 57);\n"
"	border :none;\n"
"}\n"
"QPushButton:hover {\n"
"    background-color: rgb(92, 92, 92);\n"
"    color: rgb(250, 250, 250);\n"
"}\n"
"")
        icon6 = QIcon()
        icon6.addFile(u":/resources/icons/pageArrowLeft.svg", QSize(), QIcon.Normal, QIcon.Off)
        icon6.addFile(u":/resources/icons/pageArrow.svg", QSize(), QIcon.Active, QIcon.On)
        self.attrExpandButton.setIcon(icon6)
        self.attrExpandButton.setIconSize(QSize(22, 22))
        self.attrExpandButton.setCheckable(True)
        self.attrExpandButton.setChecked(True)

        self.horizontalLayout_8.addWidget(self.attrExpandButton)

        self.attributeDockTitleWidget = QFrame(self.attributeDockTitle)
        self.attributeDockTitleWidget.setObjectName(u"attributeDockTitleWidget")
        self.attributeDockTitleWidget.setStyleSheet(u"border: none;")
        self.attributeDockTitleWidget.setFrameShape(QFrame.StyledPanel)
        self.attributeDockTitleWidget.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_9 = QHBoxLayout(self.attributeDockTitleWidget)
        self.horizontalLayout_9.setSpacing(9)
        self.horizontalLayout_9.setContentsMargins(9, 9, 9, 9)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.horizontalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.label_3 = QLabel(self.attributeDockTitleWidget)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setFont(font)
        self.label_3.setStyleSheet(u"border:none;")
        self.label_3.setFrameShape(QFrame.NoFrame)
        self.label_3.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_9.addWidget(self.label_3)

        self.attrFilterFrame = QFrame(self.attributeDockTitleWidget)
        self.attrFilterFrame.setObjectName(u"attrFilterFrame")
        sizePolicy2.setHeightForWidth(self.attrFilterFrame.sizePolicy().hasHeightForWidth())
        self.attrFilterFrame.setSizePolicy(sizePolicy2)
        self.attrFilterFrame.setStyleSheet(u"QFrame {\n"
"	margin: 2px;\n"
"    border: 1px solid rgb(43, 43, 43);\n"
"    background-color: rgb(43, 43, 43);\n"
"    border-radius: 3px;\n"
"}\n"
"QFrame:hover {\n"
"    border: 1px solid rgb(150, 146, 137);\n"
"}")
        self.attrFilterFrame.setFrameShape(QFrame.StyledPanel)
        self.attrFilterFrame.setFrameShadow(QFrame.Plain)
        self.horizontalLayout_10 = QHBoxLayout(self.attrFilterFrame)
        self.horizontalLayout_10.setSpacing(0)
        self.horizontalLayout_10.setContentsMargins(9, 9, 9, 9)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalLayout_10.setContentsMargins(0, 0, 0, 0)
        self.attrFilterButotn = QPushButton(self.attrFilterFrame)
        self.attrFilterButotn.setObjectName(u"attrFilterButotn")
        sizePolicy3.setHeightForWidth(self.attrFilterButotn.sizePolicy().hasHeightForWidth())
        self.attrFilterButotn.setSizePolicy(sizePolicy3)
        self.attrFilterButotn.setStyleSheet(u"QPushButton {\n"
"    background-color: rgb(57, 57, 57);\n"
"    padding: 0px;\n"
"	border: none;\n"
"}\n"
"QPushButton:hover {\n"
"    background-color: rgb(108, 108, 108);\n"
"}\n"
"QPushButton:checked {\n"
"    background-color: rgb(43, 43, 43);\n"
"}")
        self.attrFilterButotn.setIcon(icon4)
        self.attrFilterButotn.setIconSize(QSize(18, 18))
        self.attrFilterButotn.setCheckable(True)
        self.attrFilterButotn.setChecked(True)
        self.attrFilterButotn.setFlat(False)

        self.horizontalLayout_10.addWidget(self.attrFilterButotn)

        self.attrFilterBox = QLineEdit(self.attrFilterFrame)
        self.attrFilterBox.setObjectName(u"attrFilterBox")
        sizePolicy4.setHeightForWidth(self.attrFilterBox.sizePolicy().hasHeightForWidth())
        self.attrFilterBox.setSizePolicy(sizePolicy4)
        self.attrFilterBox.setMinimumSize(QSize(0, 0))
        self.attrFilterBox.setFont(font1)
        self.attrFilterBox.setStyleSheet(u"QLineEdit { padding: 0px;}\n"
"")
        self.attrFilterBox.setFrame(False)
        self.attrFilterBox.setClearButtonEnabled(True)

        self.horizontalLayout_10.addWidget(self.attrFilterBox)


        self.horizontalLayout_9.addWidget(self.attrFilterFrame)

        self.horizontalSpacer_5 = QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer_5)

        self.toolButton_2 = QToolButton(self.attributeDockTitleWidget)
        self.toolButton_2.setObjectName(u"toolButton_2")
        self.toolButton_2.setEnabled(False)
        self.toolButton_2.setStyleSheet(u"padding: -2px;\n"
"margin-right: 4px;\n"
"border: none;")

        self.horizontalLayout_9.addWidget(self.toolButton_2)


        self.horizontalLayout_8.addWidget(self.attributeDockTitleWidget)

        self.horizontalSpacer_6 = QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.horizontalLayout_8.addItem(self.horizontalSpacer_6)


        self.verticalLayout.addWidget(self.attributeDockTitle)

        self.linkDockTitle = QFrame(self.centralwidget)
        self.linkDockTitle.setObjectName(u"linkDockTitle")
        self.linkDockTitle.setStyleSheet(u"QFrame{\n"
"    background-color: rgb(57, 57, 57);\n"
"   /* border: 1px solid rgb(43,43,43);*/\n"
"    border: 2px solid rgb(57,57,57);\n"
"\n"
"}")
        self.linkDockTitle.setFrameShape(QFrame.StyledPanel)
        self.linkDockTitle.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_14 = QHBoxLayout(self.linkDockTitle)
        self.horizontalLayout_14.setSpacing(9)
        self.horizontalLayout_14.setContentsMargins(9, 9, 9, 9)
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.horizontalLayout_14.setContentsMargins(0, 0, 0, 0)
        self.backButton = QToolButton(self.linkDockTitle)
        self.backButton.setObjectName(u"backButton")
        self.backButton.setStyleSheet(u"QToolButton {\n"
"    padding: 0px;\n"
"    margin: 0px;\n"
"    background-color: rgb(57, 57, 57);\n"
"	border :none;\n"
"}\n"
"QToolButton:hover {\n"
"    background-color: rgb(92, 92, 92);\n"
"    color: rgb(250, 250, 250);\n"
"}\n"
"")
        icon7 = QIcon()
        icon7.addFile(u":/resources/icons/backArrow.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.backButton.setIcon(icon7)
        self.backButton.setIconSize(QSize(22, 22))
        self.backButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.backButton.setArrowType(Qt.NoArrow)

        self.horizontalLayout_14.addWidget(self.backButton)

        self.linkDockTitleWidget = QFrame(self.linkDockTitle)
        self.linkDockTitleWidget.setObjectName(u"linkDockTitleWidget")
        self.linkDockTitleWidget.setStyleSheet(u"border: none;")
        self.linkDockTitleWidget.setFrameShape(QFrame.StyledPanel)
        self.linkDockTitleWidget.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_15 = QHBoxLayout(self.linkDockTitleWidget)
        self.horizontalLayout_15.setSpacing(9)
        self.horizontalLayout_15.setContentsMargins(9, 9, 9, 9)
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.horizontalLayout_15.setContentsMargins(0, 0, 0, 0)
        self.label_5 = QLabel(self.linkDockTitleWidget)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setFont(font)
        self.label_5.setStyleSheet(u"border:none;")
        self.label_5.setFrameShape(QFrame.NoFrame)
        self.label_5.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_15.addWidget(self.label_5)

        self.linkFilterFrame = QFrame(self.linkDockTitleWidget)
        self.linkFilterFrame.setObjectName(u"linkFilterFrame")
        sizePolicy2.setHeightForWidth(self.linkFilterFrame.sizePolicy().hasHeightForWidth())
        self.linkFilterFrame.setSizePolicy(sizePolicy2)
        self.linkFilterFrame.setStyleSheet(u"QFrame {\n"
"	margin: 2px;\n"
"    border: 1px solid rgb(43, 43, 43);\n"
"    background-color: rgb(43, 43, 43);\n"
"    border-radius: 3px;\n"
"}\n"
"QFrame:hover {\n"
"    border: 1px solid rgb(150, 146, 137);\n"
"}")
        self.linkFilterFrame.setFrameShape(QFrame.StyledPanel)
        self.linkFilterFrame.setFrameShadow(QFrame.Plain)
        self.horizontalLayout_16 = QHBoxLayout(self.linkFilterFrame)
        self.horizontalLayout_16.setSpacing(0)
        self.horizontalLayout_16.setContentsMargins(9, 9, 9, 9)
        self.horizontalLayout_16.setObjectName(u"horizontalLayout_16")
        self.horizontalLayout_16.setContentsMargins(0, 0, 0, 0)
        self.linkFilterButton = QPushButton(self.linkFilterFrame)
        self.linkFilterButton.setObjectName(u"linkFilterButton")
        sizePolicy3.setHeightForWidth(self.linkFilterButton.sizePolicy().hasHeightForWidth())
        self.linkFilterButton.setSizePolicy(sizePolicy3)
        self.linkFilterButton.setStyleSheet(u"QPushButton {\n"
"    background-color: rgb(57, 57, 57);\n"
"    padding: 0px;\n"
"	border: none;\n"
"}\n"
"QPushButton:hover {\n"
"    background-color: rgb(108, 108, 108);\n"
"}\n"
"QPushButton:checked {\n"
"    background-color: rgb(43, 43, 43);\n"
"}")
        self.linkFilterButton.setIcon(icon4)
        self.linkFilterButton.setIconSize(QSize(18, 18))
        self.linkFilterButton.setCheckable(True)
        self.linkFilterButton.setChecked(True)
        self.linkFilterButton.setFlat(False)

        self.horizontalLayout_16.addWidget(self.linkFilterButton)

        self.linkFilterBox = QLineEdit(self.linkFilterFrame)
        self.linkFilterBox.setObjectName(u"linkFilterBox")
        sizePolicy4.setHeightForWidth(self.linkFilterBox.sizePolicy().hasHeightForWidth())
        self.linkFilterBox.setSizePolicy(sizePolicy4)
        self.linkFilterBox.setMinimumSize(QSize(0, 0))
        self.linkFilterBox.setFont(font1)
        self.linkFilterBox.setStyleSheet(u"QLineEdit { padding: 0px;}\n"
"")
        self.linkFilterBox.setFrame(False)
        self.linkFilterBox.setClearButtonEnabled(True)

        self.horizontalLayout_16.addWidget(self.linkFilterBox)


        self.horizontalLayout_15.addWidget(self.linkFilterFrame)

        self.horizontalSpacer_7 = QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_15.addItem(self.horizontalSpacer_7)

        self.toolButton_4 = QToolButton(self.linkDockTitleWidget)
        self.toolButton_4.setObjectName(u"toolButton_4")
        self.toolButton_4.setEnabled(False)
        self.toolButton_4.setStyleSheet(u"padding: -2px;\n"
"margin-right: 4px;\n"
"border: none;")

        self.horizontalLayout_15.addWidget(self.toolButton_4)


        self.horizontalLayout_14.addWidget(self.linkDockTitleWidget)


        self.verticalLayout.addWidget(self.linkDockTitle)

        self.documentationDockTitle = QFrame(self.centralwidget)
        self.documentationDockTitle.setObjectName(u"documentationDockTitle")
        self.documentationDockTitle.setStyleSheet(u"QFrame{\n"
"    background-color: rgb(57, 57, 57);\n"
"   /* border: 1px solid rgb(43,43,43);*/\n"
"    border: 2px solid rgb(57,57,57);\n"
"\n"
"}")
        self.documentationDockTitle.setFrameShape(QFrame.StyledPanel)
        self.documentationDockTitle.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_17 = QHBoxLayout(self.documentationDockTitle)
        self.horizontalLayout_17.setSpacing(9)
        self.horizontalLayout_17.setContentsMargins(9, 9, 9, 9)
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.horizontalLayout_17.setContentsMargins(0, 0, 0, 0)
        self.documentationDockTitleWidget = QFrame(self.documentationDockTitle)
        self.documentationDockTitleWidget.setObjectName(u"documentationDockTitleWidget")
        self.documentationDockTitleWidget.setStyleSheet(u"border: none;")
        self.documentationDockTitleWidget.setFrameShape(QFrame.StyledPanel)
        self.documentationDockTitleWidget.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_18 = QHBoxLayout(self.documentationDockTitleWidget)
        self.horizontalLayout_18.setSpacing(9)
        self.horizontalLayout_18.setContentsMargins(9, 9, 9, 9)
        self.horizontalLayout_18.setObjectName(u"horizontalLayout_18")
        self.horizontalLayout_18.setContentsMargins(0, 0, 0, 0)
        self.toolButton_5 = QToolButton(self.documentationDockTitleWidget)
        self.toolButton_5.setObjectName(u"toolButton_5")
        self.toolButton_5.setEnabled(False)
        self.toolButton_5.setStyleSheet(u"padding: -2px;\n"
"margin-left: 4px;")

        self.horizontalLayout_18.addWidget(self.toolButton_5)

        self.documentationFilterFrame = QFrame(self.documentationDockTitleWidget)
        self.documentationFilterFrame.setObjectName(u"documentationFilterFrame")
        sizePolicy2.setHeightForWidth(self.documentationFilterFrame.sizePolicy().hasHeightForWidth())
        self.documentationFilterFrame.setSizePolicy(sizePolicy2)
        self.documentationFilterFrame.setStyleSheet(u"QFrame {\n"
"	margin: 2px;\n"
"    border: 1px solid rgb(43, 43, 43);\n"
"    background-color: rgb(43, 43, 43);\n"
"    border-radius: 3px;\n"
"}\n"
"QFrame:hover {\n"
"    border: 1px solid rgb(150, 146, 137);\n"
"}")
        self.documentationFilterFrame.setFrameShape(QFrame.StyledPanel)
        self.documentationFilterFrame.setFrameShadow(QFrame.Plain)
        self.horizontalLayout_19 = QHBoxLayout(self.documentationFilterFrame)
        self.horizontalLayout_19.setSpacing(0)
        self.horizontalLayout_19.setContentsMargins(9, 9, 9, 9)
        self.horizontalLayout_19.setObjectName(u"horizontalLayout_19")
        self.horizontalLayout_19.setContentsMargins(0, 0, 0, 0)
        self.documentationFilterButton = QPushButton(self.documentationFilterFrame)
        self.documentationFilterButton.setObjectName(u"documentationFilterButton")
        sizePolicy3.setHeightForWidth(self.documentationFilterButton.sizePolicy().hasHeightForWidth())
        self.documentationFilterButton.setSizePolicy(sizePolicy3)
        self.documentationFilterButton.setStyleSheet(u"QPushButton {\n"
"    background-color: rgb(57, 57, 57);\n"
"    padding: 0px;\n"
"	border: none;\n"
"}\n"
"QPushButton:hover {\n"
"    background-color: rgb(108, 108, 108);\n"
"}\n"
"QPushButton:checked {\n"
"    background-color: rgb(43, 43, 43);\n"
"}")
        self.documentationFilterButton.setIcon(icon4)
        self.documentationFilterButton.setIconSize(QSize(18, 18))
        self.documentationFilterButton.setCheckable(True)
        self.documentationFilterButton.setChecked(True)
        self.documentationFilterButton.setFlat(False)

        self.horizontalLayout_19.addWidget(self.documentationFilterButton)

        self.documentationFilterBox = QLineEdit(self.documentationFilterFrame)
        self.documentationFilterBox.setObjectName(u"documentationFilterBox")
        sizePolicy4.setHeightForWidth(self.documentationFilterBox.sizePolicy().hasHeightForWidth())
        self.documentationFilterBox.setSizePolicy(sizePolicy4)
        self.documentationFilterBox.setMinimumSize(QSize(0, 0))
        self.documentationFilterBox.setFont(font1)
        self.documentationFilterBox.setStyleSheet(u"QLineEdit { padding: 0px;}\n"
"")
        self.documentationFilterBox.setFrame(False)
        self.documentationFilterBox.setClearButtonEnabled(True)

        self.horizontalLayout_19.addWidget(self.documentationFilterBox)


        self.horizontalLayout_18.addWidget(self.documentationFilterFrame)

        self.horizontalSpacer_9 = QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_18.addItem(self.horizontalSpacer_9)

        self.label_6 = QLabel(self.documentationDockTitleWidget)
        self.label_6.setObjectName(u"label_6")
        font2 = QFont()
        font2.setPointSize(22)
        self.label_6.setFont(font2)
        self.label_6.setStyleSheet(u"border:none;")
        self.label_6.setFrameShape(QFrame.NoFrame)
        self.label_6.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_18.addWidget(self.label_6)

        self.horizontalSpacer_8 = QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_18.addItem(self.horizontalSpacer_8)

        self.backButton_2 = QToolButton(self.documentationDockTitleWidget)
        self.backButton_2.setObjectName(u"backButton_2")
        self.backButton_2.setStyleSheet(u"QToolButton {\n"
"    padding: 0px;\n"
"    margin: 0px;\n"
"    background-color: rgb(57, 57, 57);\n"
"	border :none;\n"
"}\n"
"QToolButton:hover {\n"
"    background-color: rgb(92, 92, 92);\n"
"    color: rgb(250, 250, 250);\n"
"}\n"
"")
        self.backButton_2.setIcon(icon2)
        self.backButton_2.setIconSize(QSize(22, 22))
        self.backButton_2.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.backButton_2.setArrowType(Qt.NoArrow)

        self.horizontalLayout_18.addWidget(self.backButton_2)


        self.horizontalLayout_17.addWidget(self.documentationDockTitleWidget)


        self.verticalLayout.addWidget(self.documentationDockTitle)

        self.line_4 = QFrame(self.centralwidget)
        self.line_4.setObjectName(u"line_4")
        self.line_4.setFrameShape(QFrame.HLine)
        self.line_4.setFrameShadow(QFrame.Sunken)

        self.verticalLayout.addWidget(self.line_4)

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

        self.line_6 = QFrame(self.centralwidget)
        self.line_6.setObjectName(u"line_6")
        self.line_6.setFrameShape(QFrame.VLine)
        self.line_6.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_3.addWidget(self.line_6)

        self.previewCheckBox = QCheckBox(self.centralwidget)
        self.previewCheckBox.setObjectName(u"previewCheckBox")
        icon8 = QIcon()
        icon8.addFile(u":/resources/icons/kohai.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.previewCheckBox.setIcon(icon8)

        self.horizontalLayout_3.addWidget(self.previewCheckBox)


        self.horizontalLayout_2.addLayout(self.horizontalLayout_3)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_3)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setSpacing(6)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(-1, -1, 3, -1)
        self.pageDownButton = QPushButton(self.centralwidget)
        self.pageDownButton.setObjectName(u"pageDownButton")
        self.pageDownButton.setStyleSheet(u"QPushButton {\n"
"    padding: 2px;\n"
"	border: none;\n"
"    background-color: rgb(68, 68, 68);\n"
"}\n"
"QPushButton:hover {\n"
"    background-color: rgb(92, 92, 92);\n"
"    color: rgb(250, 250, 250);\n"
"}")
        icon9 = QIcon()
        icon9.addFile(u":/resources/icons/pageArrowLeft.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pageDownButton.setIcon(icon9)
        self.pageDownButton.setIconSize(QSize(20, 20))

        self.horizontalLayout_4.addWidget(self.pageDownButton)

        self.pageSpinBox = QSpinBox(self.centralwidget)
        self.pageSpinBox.setObjectName(u"pageSpinBox")
        self.pageSpinBox.setStyleSheet(u"QAbstractSpinBox {\n"
"    padding: 1px;\n"
"    padding-left: 4px;\n"
"    margin: 1px;\n"
"    border: 1px solid rgb(43, 43, 43);\n"
"\n"
"}")
        self.pageSpinBox.setFrame(False)
        self.pageSpinBox.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.pageSpinBox.setMinimum(1)
        self.pageSpinBox.setMaximum(9999)
        self.pageSpinBox.setValue(1)

        self.horizontalLayout_4.addWidget(self.pageSpinBox)

        self.pageUpButton = QPushButton(self.centralwidget)
        self.pageUpButton.setObjectName(u"pageUpButton")
        self.pageUpButton.setStyleSheet(u"QPushButton {\n"
"    padding: 2px;\n"
"	border: none;\n"
"    background-color: rgb(68, 68, 68);\n"
"}\n"
"QPushButton:hover {\n"
"    background-color: rgb(92, 92, 92);\n"
"    color: rgb(250, 250, 250);\n"
"}")
        icon10 = QIcon()
        icon10.addFile(u":/resources/icons/pageArrow.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pageUpButton.setIcon(icon10)
        self.pageUpButton.setIconSize(QSize(20, 20))

        self.horizontalLayout_4.addWidget(self.pageUpButton)


        self.horizontalLayout_2.addLayout(self.horizontalLayout_4)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        RelicMainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(RelicMainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1117, 22))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuEdit = QMenu(self.menubar)
        self.menuEdit.setObjectName(u"menuEdit")
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName(u"menuHelp")
        self.menuView = QMenu(self.menubar)
        self.menuView.setObjectName(u"menuView")
        RelicMainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(RelicMainWindow)
        self.statusbar.setObjectName(u"statusbar")
        self.statusbar.setSizeGripEnabled(True)
        RelicMainWindow.setStatusBar(self.statusbar)
        self.categoryDock = QDockWidget(RelicMainWindow)
        self.categoryDock.setObjectName(u"categoryDock")
        self.categoryDock.setStyleSheet(u"")
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName(u"dockWidgetContents")
        self.verticalLayout_2 = QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setContentsMargins(9, 9, 9, 9)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.categoryScrollArea = QScrollArea(self.dockWidgetContents)
        self.categoryScrollArea.setObjectName(u"categoryScrollArea")
        self.categoryScrollArea.setWidgetResizable(True)
        self.categoryScrollAreaWidgetContents = QWidget()
        self.categoryScrollAreaWidgetContents.setObjectName(u"categoryScrollAreaWidgetContents")
        self.categoryScrollAreaWidgetContents.setGeometry(QRect(0, 0, 105, 557))
        self.categoryLayout = QVBoxLayout(self.categoryScrollAreaWidgetContents)
        self.categoryLayout.setSpacing(4)
        self.categoryLayout.setContentsMargins(9, 9, 9, 9)
        self.categoryLayout.setObjectName(u"categoryLayout")
        self.categoryLayout.setContentsMargins(4, 4, 4, 4)
        self.verticalSpacer = QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.MinimumExpanding)

        self.categoryLayout.addItem(self.verticalSpacer)

        self.categoryScrollArea.setWidget(self.categoryScrollAreaWidgetContents)

        self.verticalLayout_2.addWidget(self.categoryScrollArea)

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
        self.searchDockWidgetContents = QWidget()
        self.searchDockWidgetContents.setObjectName(u"searchDockWidgetContents")
        self.gridLayout = QGridLayout(self.searchDockWidgetContents)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(9, 9, 9, 9)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setHorizontalSpacing(0)
        self.gridLayout.setVerticalSpacing(2)
        self.gridLayout.setContentsMargins(6, 0, 6, 0)
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_2, 0, 4, 1, 1)

        self.line = QFrame(self.searchDockWidgetContents)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.gridLayout.addWidget(self.line, 1, 2, 1, 1)

        self.line_2 = QFrame(self.searchDockWidgetContents)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.HLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.gridLayout.addWidget(self.line_2, 1, 4, 1, 1)

        self.searchFrame = QFrame(self.searchDockWidgetContents)
        self.searchFrame.setObjectName(u"searchFrame")
        sizePolicy3.setHeightForWidth(self.searchFrame.sizePolicy().hasHeightForWidth())
        self.searchFrame.setSizePolicy(sizePolicy3)
        self.searchFrame.setStyleSheet(u"QFrame {\n"
"    border: 2px solid rgb(43, 43, 43);\n"
"    background-color: rgb(43, 43, 43);\n"
"    border-radius: 3px;\n"
"}\n"
"QFrame:hover {\n"
"    border: 2px solid rgb(150, 146, 137);\n"
"}")
        self.searchFrame.setFrameShape(QFrame.StyledPanel)
        self.searchFrame.setFrameShadow(QFrame.Plain)
        self.horizontalLayout = QHBoxLayout(self.searchFrame)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setContentsMargins(9, 9, 9, 9)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.searchButton = QPushButton(self.searchFrame)
        self.searchButton.setObjectName(u"searchButton")
        self.searchButton.setStyleSheet(u"QPushButton {\n"
"    background-color: rgb(43, 43, 43);\n"
"    padding: 2px;\n"
"	border: none;\n"
"}")
        self.searchButton.setIcon(icon4)
        self.searchButton.setIconSize(QSize(20, 20))
        self.searchButton.setFlat(False)

        self.horizontalLayout.addWidget(self.searchButton)

        self.searchBox = QLineEdit(self.searchFrame)
        self.searchBox.setObjectName(u"searchBox")
        sizePolicy5 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.searchBox.sizePolicy().hasHeightForWidth())
        self.searchBox.setSizePolicy(sizePolicy5)
        self.searchBox.setMinimumSize(QSize(256, 26))
        font3 = QFont()
        font3.setBold(True)
        self.searchBox.setFont(font3)
        self.searchBox.setStyleSheet(u"QLineEdit { padding: 0px;}\n"
"")
        self.searchBox.setFrame(False)
        self.searchBox.setClearButtonEnabled(True)

        self.horizontalLayout.addWidget(self.searchBox)


        self.gridLayout.addWidget(self.searchFrame, 0, 2, 1, 1)

        self.line_3 = QFrame(self.searchDockWidgetContents)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.HLine)
        self.line_3.setFrameShadow(QFrame.Sunken)

        self.gridLayout.addWidget(self.line_3, 1, 0, 1, 1)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 0, 0, 1, 1)

        self.searchDock.setWidget(self.searchDockWidgetContents)
        RelicMainWindow.addDockWidget(Qt.TopDockWidgetArea, self.searchDock)
        self.attributeDock = QDockWidget(RelicMainWindow)
        self.attributeDock.setObjectName(u"attributeDock")
        palette2 = QPalette()
        palette2.setBrush(QPalette.Active, QPalette.WindowText, brush)
        palette2.setBrush(QPalette.Active, QPalette.Button, brush1)
        palette2.setBrush(QPalette.Active, QPalette.Text, brush)
        palette2.setBrush(QPalette.Active, QPalette.ButtonText, brush)
        palette2.setBrush(QPalette.Active, QPalette.Base, brush1)
        palette2.setBrush(QPalette.Active, QPalette.Window, brush1)
        palette2.setBrush(QPalette.Active, QPalette.Highlight, brush2)
        palette2.setBrush(QPalette.Active, QPalette.HighlightedText, brush3)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette2.setBrush(QPalette.Active, QPalette.PlaceholderText, brush)
#endif
        palette2.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        palette2.setBrush(QPalette.Inactive, QPalette.Button, brush1)
        palette2.setBrush(QPalette.Inactive, QPalette.Text, brush)
        palette2.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
        palette2.setBrush(QPalette.Inactive, QPalette.Base, brush1)
        palette2.setBrush(QPalette.Inactive, QPalette.Window, brush1)
        palette2.setBrush(QPalette.Inactive, QPalette.Highlight, brush2)
        palette2.setBrush(QPalette.Inactive, QPalette.HighlightedText, brush3)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette2.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush)
#endif
        palette2.setBrush(QPalette.Disabled, QPalette.WindowText, brush4)
        palette2.setBrush(QPalette.Disabled, QPalette.Button, brush5)
        palette2.setBrush(QPalette.Disabled, QPalette.Text, brush4)
        palette2.setBrush(QPalette.Disabled, QPalette.ButtonText, brush4)
        palette2.setBrush(QPalette.Disabled, QPalette.Base, brush5)
        palette2.setBrush(QPalette.Disabled, QPalette.Window, brush5)
        palette2.setBrush(QPalette.Disabled, QPalette.Highlight, brush2)
        palette2.setBrush(QPalette.Disabled, QPalette.HighlightedText, brush3)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette2.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush4)
#endif
        self.attributeDock.setPalette(palette2)
        self.attributeDock.setStyleSheet(u"")
        self.attrDockWidgetContents = QWidget()
        self.attrDockWidgetContents.setObjectName(u"attrDockWidgetContents")
        self.attributeDock.setWidget(self.attrDockWidgetContents)
        RelicMainWindow.addDockWidget(Qt.RightDockWidgetArea, self.attributeDock)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.menuFile.addAction(self.actionIngest)
        self.menuFile.addAction(self.actionExit)
        self.menuEdit.addAction(self.actionAdministration_Mode)
        self.menuEdit.addAction(self.actionPreferences)
        self.menuHelp.addAction(self.actionDocumentation)
        self.menuView.addAction(self.actionPortal)

        self.retranslateUi(RelicMainWindow)
        self.pageDownButton.clicked.connect(self.pageSpinBox.stepDown)
        self.pageUpButton.clicked.connect(self.pageSpinBox.stepUp)
        self.filterButton.toggled.connect(self.filterBox.setVisible)
        self.categoryExpandButton.toggled.connect(self.dockTitleWidgets.setVisible)
        self.attrFilterButotn.toggled.connect(self.attrFilterBox.setVisible)
        self.attrExpandButton.toggled.connect(self.attributeDockTitleWidget.setVisible)
        self.actionPortal.toggled.connect(self.attrExpandButton.setChecked)
        self.actionPortal.toggled.connect(self.categoryExpandButton.setChecked)
        self.actionAdministration_Mode.toggled.connect(RelicMainWindow.toggleAdminMode)
        self.actionExit.triggered.connect(RelicMainWindow.close)

        QMetaObject.connectSlotsByName(RelicMainWindow)
    # setupUi

    def retranslateUi(self, RelicMainWindow):
        RelicMainWindow.setWindowTitle(QCoreApplication.translate("RelicMainWindow", u"Relic", None))
        self.actionPreferences.setText(QCoreApplication.translate("RelicMainWindow", u"Preferences", None))
        self.actionExit.setText(QCoreApplication.translate("RelicMainWindow", u"Exit", None))
        self.actionAdministration_Mode.setText(QCoreApplication.translate("RelicMainWindow", u"Administration Mode", None))
        self.actionDocumentation.setText(QCoreApplication.translate("RelicMainWindow", u"Documentation", None))
        self.actionIngest.setText(QCoreApplication.translate("RelicMainWindow", u"Ingest", None))
        self.actionPortal.setText(QCoreApplication.translate("RelicMainWindow", u"Portal", None))
#if QT_CONFIG(shortcut)
        self.actionPortal.setShortcut(QCoreApplication.translate("RelicMainWindow", u"Ctrl+Tab", None))
#endif // QT_CONFIG(shortcut)
        self.documentationDock.setWindowTitle(QCoreApplication.translate("RelicMainWindow", u"Docs", None))
        self.linksDock.setWindowTitle(QCoreApplication.translate("RelicMainWindow", u"Links", None))
        self.toolButton.setText("")
        self.label_2.setText(QCoreApplication.translate("RelicMainWindow", u"CATEGORIES", None))
        self.filterButton.setText("")
        self.filterBox.setPlaceholderText(QCoreApplication.translate("RelicMainWindow", u"Filter...", None))
        self.categoryExpandButton.setText("")
        self.attrExpandButton.setText("")
        self.label_3.setText(QCoreApplication.translate("RelicMainWindow", u"ATTRIBUTES", None))
        self.attrFilterButotn.setText("")
        self.attrFilterBox.setPlaceholderText(QCoreApplication.translate("RelicMainWindow", u"Filter...", None))
        self.toolButton_2.setText("")
        self.backButton.setText(QCoreApplication.translate("RelicMainWindow", u"Back", None))
        self.label_5.setText(QCoreApplication.translate("RelicMainWindow", u"LINKS", None))
        self.linkFilterButton.setText("")
        self.linkFilterBox.setPlaceholderText(QCoreApplication.translate("RelicMainWindow", u"Filter...", None))
        self.toolButton_4.setText("")
        self.toolButton_5.setText("")
        self.documentationFilterButton.setText("")
        self.documentationFilterBox.setPlaceholderText(QCoreApplication.translate("RelicMainWindow", u"Find...", None))
        self.label_6.setText(QCoreApplication.translate("RelicMainWindow", u"Autodesk Standard Surface", None))
        self.backButton_2.setText(QCoreApplication.translate("RelicMainWindow", u"Close", None))
        self.label.setText(QCoreApplication.translate("RelicMainWindow", u"Scale", None))
        self.previewCheckBox.setText(QCoreApplication.translate("RelicMainWindow", u"Preview On-Select", None))
        self.pageDownButton.setText("")
        self.pageSpinBox.setSuffix(QCoreApplication.translate("RelicMainWindow", u"/ 4", None))
        self.pageSpinBox.setPrefix(QCoreApplication.translate("RelicMainWindow", u"Page ", None))
        self.pageUpButton.setText("")
        self.menuFile.setTitle(QCoreApplication.translate("RelicMainWindow", u"File", None))
        self.menuEdit.setTitle(QCoreApplication.translate("RelicMainWindow", u"Edit", None))
        self.menuHelp.setTitle(QCoreApplication.translate("RelicMainWindow", u"Help", None))
        self.menuView.setTitle(QCoreApplication.translate("RelicMainWindow", u"View", None))
#if QT_CONFIG(statustip)
        self.statusbar.setStatusTip("")
#endif // QT_CONFIG(statustip)
        self.categoryDock.setWindowTitle(QCoreApplication.translate("RelicMainWindow", u"Categories", None))
        self.searchDock.setWindowTitle(QCoreApplication.translate("RelicMainWindow", u"Search", None))
        self.searchButton.setText("")
        self.searchBox.setPlaceholderText(QCoreApplication.translate("RelicMainWindow", u"Search...", None))
        self.attributeDock.setWindowTitle(QCoreApplication.translate("RelicMainWindow", u"Attributes", None))
    # retranslateUi

