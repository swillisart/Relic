# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'list_view_filtered.ui'
##
## Created by: Qt User Interface Compiler version 6.3.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget)
import resources_rc
import resources_rc

class Ui_ListViewFiltered(object):
    def setupUi(self, ListViewFiltered):
        if not ListViewFiltered.objectName():
            ListViewFiltered.setObjectName(u"ListViewFiltered")
        ListViewFiltered.resize(278, 232)
        ListViewFiltered.setStyleSheet(u"QWidget#ListViewFiltered {\n"
"    border: 1px solid rgb(68, 68, 68);\n"
"    background-color: rgb(43, 43, 43);\n"
"\n"
"}\n"
"QWidget {\n"
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
"}"
                        "\n"
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
"    image: url(:/style/checkbox_checked.svg);\n"
"}\n"
"QMenu::indicator:non-exclusive:unchecked {\n"
"    image: url(:/style/checkbox.svg);\n"
"}\n"
"\n"
"QLineEdit,\n"
"QAbstractSpinBox,\n"
"QTextEdit {\n"
"    background-color: rgb(43, 43, 43);\n"
"/*\n"
"    border: 2px solid rgb(43, 43, 43);\n"
"    border-radius: "
                        "3px;\n"
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
"    bord"
                        "er-radius: 4px;\n"
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
"    background: #14506E;\n"
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
"    margin: "
                        "0px 3px 0px 0px;\n"
"    border-image: url(:/style/stylesheet-branch-closed.png);\n"
"    height: 10px;\n"
"    width: 6px;\n"
"    subcontrol-position: right;\n"
"    subcontrol-origin: margin;\n"
"}\n"
"QScrollBar::sub-line:horizontal:hover,\n"
"QScrollBar::sub-line:horizontal:on,\n"
"QScrollBar::sub-line:horizontal {\n"
"    margin: 0px 0px 0px 3px;\n"
"    border-image: url(:/style/stylesheet-branch-closedleft.png);\n"
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
"    border-image: url(:/style/stylesh"
                        "eet-branch-openup.png);\n"
"    height: 6px;\n"
"    width: 10px;\n"
"    subcontrol-position: top;\n"
"    subcontrol-origin: margin;\n"
"}\n"
"QScrollBar::add-line:vertical {\n"
"    margin: 0px 0px 3px 0px;\n"
"    border-image: url(:/style/stylesheet-branch-open.png);\n"
"    height: 6px;\n"
"    width: 10px;\n"
"    subcontrol-position: bottom;\n"
"    subcontrol-origin: margin;\n"
"}\n"
"QScrollBar::sub-line:vertical:hover,\n"
"QScrollBar::sub-line:vertical:on {\n"
"    border-image: url(:/qss_icons/rc/up_arrow.png);\n"
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
""
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
"\n"
"\n"
"/* QCombobox -------------------------------------------------------------- */\n"
"QComboBox {\n"
"    border: 0px;\n"
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
"   "
                        " padding-right: 3px;\n"
"}\n"
"QComboBox::down-arrow,\n"
"QComboBox::down-arrow:on,\n"
"QComboBox::down-arrow:hover,\n"
"QComboBox::down-arrow:focus {\n"
"    image: url(:/style/stylesheet-branch-open.png);\n"
"}\n"
"")
        self.verticalLayout = QVBoxLayout(ListViewFiltered)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(2, 2, 2, 2)
        self.searchFrame = QFrame(ListViewFiltered)
        self.searchFrame.setObjectName(u"searchFrame")
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.searchFrame.sizePolicy().hasHeightForWidth())
        self.searchFrame.setSizePolicy(sizePolicy)
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
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.searchButton = QPushButton(self.searchFrame)
        self.searchButton.setObjectName(u"searchButton")
        self.searchButton.setStyleSheet(u"QPushButton {\n"
"    background-color: rgb(43, 43, 43);\n"
"    padding: 2px;\n"
"	border: none;\n"
"}")
        icon = QIcon()
        icon.addFile(u":/app/searchLight.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.searchButton.setIcon(icon)
        self.searchButton.setIconSize(QSize(18, 18))
        self.searchButton.setFlat(False)

        self.horizontalLayout.addWidget(self.searchButton)


        self.verticalLayout.addWidget(self.searchFrame)


        self.retranslateUi(ListViewFiltered)

        QMetaObject.connectSlotsByName(ListViewFiltered)
    # setupUi

    def retranslateUi(self, ListViewFiltered):
        ListViewFiltered.setWindowTitle(QCoreApplication.translate("ListViewFiltered", u"Form", None))
        self.searchButton.setText("")
    # retranslateUi

