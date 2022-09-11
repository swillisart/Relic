# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ingestion.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QListView, QPlainTextEdit,
    QPushButton, QSizePolicy, QSpacerItem, QTabWidget,
    QVBoxLayout, QWidget)

from library.widgets.assets_alt import AssetListView
from library.widgets.metadataView import categoryWidget
from library.widgets.util import AssetNameListView
import resources_rc

class Ui_IngestForm(object):
    def setupUi(self, IngestForm):
        if not IngestForm.objectName():
            IngestForm.setObjectName(u"IngestForm")
        IngestForm.resize(866, 478)
        IngestForm.setStyleSheet(u"QWidget {\n"
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
"    background: rgb(43, 43"
                        ", 43);\n"
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
"    margin: 0px;\n"
"}\n"
"QSlider::groove:horizontal {\n"
"    height: 4px;\n"
"}\n"
"QSlider::groove:vertical {\n"
"    width: 4px;\n"
"}\n"
"QSlider::sub-page:vertical:disabled, \n"
"QSlider::sub-page:horizontal:disabled "
                        "{\n"
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
"    margin: 0px 3px 0px 0px;\n"
"    border-image: url(:/resources/style/stylesheet-branch-closed.png);\n"
"    height: 10px;\n"
"    width: 6px;\n"
"    subcontrol-position: right;\n"
"    subcontrol-origin: margin;\n"
"}\n"
"QScrollBar::sub-line:horizontal:hover,\n"
"QScrollBar::sub-line:horizontal:on,\n"
"QScrollBar::sub-line:horizontal {\n"
"    margin: 0px 0px 0px 3px;\n"
"    border-"
                        "image: url(:/resources/style/stylesheet-branch-closedleft.png);\n"
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
"    border-image: url(:/resources/style/stylesheet-branch-openup.png);\n"
"    height: 6px;\n"
"    width: 10px;\n"
"    subcontrol-position: top;\n"
"    subcontrol-origin: margin;\n"
"}\n"
"QScrollBar::add-line:vertical {\n"
"    margin: 0px 0px 3px 0px;\n"
"    border-image: url(:/resources/style/stylesheet-branch-open.png);\n"
"    height: 6px;\n"
"    width: 10px;\n"
"    subcontrol-positi"
                        "on: bottom;\n"
"    subcontrol-origin: margin;\n"
"}\n"
"QScrollBar::sub-line:vertical:hover,\n"
"QScrollBar::sub-line:vertical:on {\n"
"    border-image: url(:/resources/style/stylesheet-branch-openup.png);\n"
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
"QTreeVie"
                        "w::branch {\n"
"    border-top: 0px solid rgb(43, 43, 43);\n"
"    border-bottom: 0px solid rgb(43, 43, 43);\n"
"    padding: 4px; /*DO NOT CHANGE*/\n"
"    margin-top: 2px;\n"
"    margin-bottom: 2px;\n"
"}\n"
"QTreeView::branch:has-siblings:!adjoins-item {\n"
"    border-image: url(:/resources/style/stylesheet-vline.png);\n"
"}\n"
"QTreeView::branch:has-siblings:adjoins-item {\n"
"    border-image: url(:/resources/style/stylesheet-branch-more.png);\n"
"}\n"
"QTreeView::branch:!has-children:!has-siblings:adjoins-item {\n"
"    border-image: url(:/resources/style/stylesheet-branch-end.png);\n"
"}\n"
"QTreeView::branch:has-children:!has-siblings:closed,\n"
"QTreeView::branch:closed:has-children:has-siblings {\n"
"    image: url(:/resources/style/treeExpand.svg);\n"
"}\n"
"QTreeView::branch:open:has-children:!has-siblings,\n"
"QTreeView::branch:open:has-children:has-siblings  {\n"
"    image: url(:/resources/style/treeCollapse.svg);\n"
"}\n"
"\n"
"\n"
"/* QCombobox -----------------------------------------------"
                        "--------------- */\n"
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
"    padding-right: 3px;\n"
"    margin-left: 6px;\n"
"}\n"
"QComboBox::down-arrow,\n"
"QComboBox::down-arrow:on,\n"
"QComboBox::down-arrow:hover,\n"
"QComboBox::down-arrow:focus {\n"
"    image: url(:/resources/style/stylesheet-branch-open.png);\n"
"}\n"
"\n"
"\n"
"/* QCheckBox -------------------------------------------------------------- */\n"
"\n"
"\n"
"QCheckBox::indicator:che"
                        "cked:hover,\n"
"QTreeView::indicator:checked:hover,\n"
"QListView::indicator:checked:hover {\n"
"    image: url(:/resources/style/checkbox_checked_hover.svg);\n"
"}\n"
"QCheckBox::indicator:unchecked:hover,\n"
"QTreeView::indicator:unchecked:hover,\n"
"QListView::indicator:unchecked:hover {\n"
"    image: url(:/resources/style/checkbox_hover.svg);\n"
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
"}\n"
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
" "
                        "   background-color: rgb(68, 68, 68);\n"
"}\n"
"\n"
"/* QTabBar::tab - selected ----------------------------------------------- */\n"
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
""
                        "    margin-top: 2px;\n"
"    margin-bottom: 1px;\n"
"    padding-left: 10px; \n"
"    padding-right: 10px;\n"
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
"/"
                        "* QTabBar::tab - selected ----------------------------------------------- */\n"
"\n"
"QTabBar::tab {\n"
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
"    border"
                        "-left: 1px solid rgb(66, 118, 150);\n"
"    border-top-left-radius: 3px;\n"
"    border-top-right-radius: 3px;\n"
"    border-top: 1px solid rgb(43, 43, 43);\n"
"}")
        self.verticalLayout_3 = QVBoxLayout(IngestForm)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.frame_4 = QFrame(IngestForm)
        self.frame_4.setObjectName(u"frame_4")
        self.frame_4.setFrameShape(QFrame.StyledPanel)
        self.frame_4.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_3 = QHBoxLayout(self.frame_4)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(18, -1, 18, -1)
        self.titleLabel = QLabel(self.frame_4)
        self.titleLabel.setObjectName(u"titleLabel")
        font = QFont()
        font.setPointSize(12)
        font.setBold(False)
        self.titleLabel.setFont(font)

        self.horizontalLayout_3.addWidget(self.titleLabel)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_2)

        self.label_3 = QLabel(self.frame_4)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_3.addWidget(self.label_3)

        self.categoryComboBox = categoryWidget(self.frame_4)
        self.categoryComboBox.setObjectName(u"categoryComboBox")

        self.horizontalLayout_3.addWidget(self.categoryComboBox)


        self.verticalLayout_3.addWidget(self.frame_4)

        self.frame_2 = QFrame(IngestForm)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.frame_2)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(-1, 0, -1, 0)
        self.tabWidget = QTabWidget(self.frame_2)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setEnabled(True)
        self.tabWidget.setStyleSheet(u"QWidget {\n"
"    background-color: rgb(75, 75, 75);\n"
"}\n"
"QToolTip {\n"
"    background-color: #ffffff;\n"
"}")
        self.collectTab = QWidget()
        self.collectTab.setObjectName(u"collectTab")
        self.verticalLayout_4 = QVBoxLayout(self.collectTab)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.collectPathTextEdit = QPlainTextEdit(self.collectTab)
        self.collectPathTextEdit.setObjectName(u"collectPathTextEdit")
        self.collectPathTextEdit.setStyleSheet(u"border: 1px solid grey;")
        self.collectPathTextEdit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.collectPathTextEdit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.collectPathTextEdit.setLineWrapMode(QPlainTextEdit.NoWrap)

        self.verticalLayout_4.addWidget(self.collectPathTextEdit)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setSpacing(9)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(-1, 3, -1, 3)
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(9, 0, 9, 0)
        self.lightsCheckBox = QCheckBox(self.collectTab)
        self.lightsCheckBox.setObjectName(u"lightsCheckBox")

        self.gridLayout.addWidget(self.lightsCheckBox, 6, 1, 1, 1)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer_2, 8, 0, 1, 1)

        self.moviesLabel = QLabel(self.collectTab)
        self.moviesLabel.setObjectName(u"moviesLabel")
        self.moviesLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.moviesLabel, 4, 0, 1, 1)

        self.texturesReferencesLabel = QLabel(self.collectTab)
        self.texturesReferencesLabel.setObjectName(u"texturesReferencesLabel")
        self.texturesReferencesLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.texturesReferencesLabel, 2, 0, 1, 1)

        self.line_8 = QFrame(self.collectTab)
        self.line_8.setObjectName(u"line_8")
        self.line_8.setFrameShape(QFrame.HLine)
        self.line_8.setFrameShadow(QFrame.Sunken)

        self.gridLayout.addWidget(self.line_8, 1, 0, 1, 1)

        self.lightsLabel = QLabel(self.collectTab)
        self.lightsLabel.setObjectName(u"lightsLabel")
        self.lightsLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.lightsLabel, 6, 0, 1, 1)

        self.texturesReferencesCheckBox = QCheckBox(self.collectTab)
        self.texturesReferencesCheckBox.setObjectName(u"texturesReferencesCheckBox")
        self.texturesReferencesCheckBox.setChecked(True)

        self.gridLayout.addWidget(self.texturesReferencesCheckBox, 2, 1, 1, 1)

        self.toolsLabel = QLabel(self.collectTab)
        self.toolsLabel.setObjectName(u"toolsLabel")
        self.toolsLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.toolsLabel, 5, 0, 1, 1)

        self.label_2 = QLabel(self.collectTab)
        self.label_2.setObjectName(u"label_2")
        font1 = QFont()
        font1.setPointSize(10)
        self.label_2.setFont(font1)

        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 1)

        self.toolsCheckBox = QCheckBox(self.collectTab)
        self.toolsCheckBox.setObjectName(u"toolsCheckBox")

        self.gridLayout.addWidget(self.toolsCheckBox, 5, 1, 1, 1)

        self.moviesCheckBox = QCheckBox(self.collectTab)
        self.moviesCheckBox.setObjectName(u"moviesCheckBox")

        self.gridLayout.addWidget(self.moviesCheckBox, 4, 1, 1, 1)

        self.rawLabel = QLabel(self.collectTab)
        self.rawLabel.setObjectName(u"rawLabel")
        self.rawLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.rawLabel, 3, 0, 1, 1)

        self.rawCheckBox = QCheckBox(self.collectTab)
        self.rawCheckBox.setObjectName(u"rawCheckBox")
        self.rawCheckBox.setEnabled(True)
        self.rawCheckBox.setChecked(False)

        self.gridLayout.addWidget(self.rawCheckBox, 3, 1, 1, 1)


        self.horizontalLayout_6.addLayout(self.gridLayout)

        self.line_6 = QFrame(self.collectTab)
        self.line_6.setObjectName(u"line_6")
        self.line_6.setFrameShape(QFrame.VLine)
        self.line_6.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_6.addWidget(self.line_6)

        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(9, 0, 9, 0)
        self.label_7 = QLabel(self.collectTab)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setFont(font1)

        self.gridLayout_2.addWidget(self.label_7, 0, 0, 1, 1)

        self.copyCheckBox = QCheckBox(self.collectTab)
        self.copyCheckBox.setObjectName(u"copyCheckBox")

        self.gridLayout_2.addWidget(self.copyCheckBox, 3, 1, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout_2.addItem(self.verticalSpacer, 4, 0, 1, 1)

        self.copyLabel = QLabel(self.collectTab)
        self.copyLabel.setObjectName(u"copyLabel")

        self.gridLayout_2.addWidget(self.copyLabel, 3, 0, 1, 1)

        self.texturesReferencesLabel_2 = QLabel(self.collectTab)
        self.texturesReferencesLabel_2.setObjectName(u"texturesReferencesLabel_2")
        self.texturesReferencesLabel_2.setEnabled(False)
        self.texturesReferencesLabel_2.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_2.addWidget(self.texturesReferencesLabel_2, 2, 0, 1, 1)

        self.line_9 = QFrame(self.collectTab)
        self.line_9.setObjectName(u"line_9")
        self.line_9.setFrameShape(QFrame.HLine)
        self.line_9.setFrameShadow(QFrame.Sunken)

        self.gridLayout_2.addWidget(self.line_9, 1, 0, 1, 1)

        self.texturesReferencesCheckBox_2 = QCheckBox(self.collectTab)
        self.texturesReferencesCheckBox_2.setObjectName(u"texturesReferencesCheckBox_2")
        self.texturesReferencesCheckBox_2.setEnabled(False)

        self.gridLayout_2.addWidget(self.texturesReferencesCheckBox_2, 2, 1, 1, 1)


        self.horizontalLayout_6.addLayout(self.gridLayout_2)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_3)


        self.verticalLayout_4.addLayout(self.horizontalLayout_6)

        self.tabWidget.addTab(self.collectTab, "")
        self.categorizeTab = QWidget()
        self.categorizeTab.setObjectName(u"categorizeTab")
        self.categorizeTab.setEnabled(False)
        self.horizontalLayout = QHBoxLayout(self.categorizeTab)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.frame = QFrame(self.categorizeTab)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout = QVBoxLayout(self.frame)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(-1, 0, -1, 0)
        self.frame_5 = QFrame(self.frame)
        self.frame_5.setObjectName(u"frame_5")
        self.frame_5.setFrameShape(QFrame.StyledPanel)
        self.frame_5.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_7 = QHBoxLayout(self.frame_5)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.loadingLabel = QLabel(self.frame_5)
        self.loadingLabel.setObjectName(u"loadingLabel")
        self.loadingLabel.setPixmap(QPixmap(u":/resources/general/load_wheel_24.webp"))

        self.horizontalLayout_7.addWidget(self.loadingLabel)

        self.completedLabel = QLabel(self.frame_5)
        self.completedLabel.setObjectName(u"completedLabel")
        self.completedLabel.setPixmap(QPixmap(u":/resources/general/check_green.png"))

        self.horizontalLayout_7.addWidget(self.completedLabel)

        self.collectedLabel = QLabel(self.frame_5)
        self.collectedLabel.setObjectName(u"collectedLabel")
        self.collectedLabel.setFont(font)

        self.horizontalLayout_7.addWidget(self.collectedLabel)

        self.horizontalSpacer_4 = QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_4)


        self.verticalLayout.addWidget(self.frame_5)

        self.line_2 = QFrame(self.frame)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.HLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.verticalLayout.addWidget(self.line_2)

        self.collectedListView = AssetListView(self.frame)
        self.collectedListView.setObjectName(u"collectedListView")
        self.collectedListView.setResizeMode(QListView.Adjust)
        self.collectedListView.setUniformItemSizes(True)
        self.collectedListView.setWordWrap(True)
        self.collectedListView.setSelectionRectVisible(True)

        self.verticalLayout.addWidget(self.collectedListView)


        self.horizontalLayout.addWidget(self.frame)

        self.line = QFrame(self.categorizeTab)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.VLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout.addWidget(self.line)

        self.categorizeFrame = QFrame(self.categorizeTab)
        self.categorizeFrame.setObjectName(u"categorizeFrame")
        self.categorizeFrame.setFrameShape(QFrame.StyledPanel)
        self.categorizeFrame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_5 = QVBoxLayout(self.categorizeFrame)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(-1, 0, -1, 0)
        self.label_4 = QLabel(self.categorizeFrame)
        self.label_4.setObjectName(u"label_4")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy)
        self.label_4.setFont(font)

        self.verticalLayout_5.addWidget(self.label_4)

        self.line_3 = QFrame(self.categorizeFrame)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.HLine)
        self.line_3.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_5.addWidget(self.line_3)

        self.label_5 = QLabel(self.categorizeFrame)
        self.label_5.setObjectName(u"label_5")

        self.verticalLayout_5.addWidget(self.label_5)

        self.existingNamesList = AssetNameListView(self.categorizeFrame)
        self.existingNamesList.setObjectName(u"existingNamesList")

        self.verticalLayout_5.addWidget(self.existingNamesList)


        self.horizontalLayout.addWidget(self.categorizeFrame)

        self.line_5 = QFrame(self.categorizeTab)
        self.line_5.setObjectName(u"line_5")
        self.line_5.setFrameShape(QFrame.VLine)
        self.line_5.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout.addWidget(self.line_5)

        self.frame_6 = QFrame(self.categorizeTab)
        self.frame_6.setObjectName(u"frame_6")
        self.frame_6.setFrameShape(QFrame.StyledPanel)
        self.frame_6.setFrameShadow(QFrame.Raised)
        self.verticalLayout_6 = QVBoxLayout(self.frame_6)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(-1, 0, -1, 0)
        self.frame_7 = QFrame(self.frame_6)
        self.frame_7.setObjectName(u"frame_7")
        self.frame_7.setFrameShape(QFrame.StyledPanel)
        self.frame_7.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_8 = QHBoxLayout(self.frame_7)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.processLoadingLabel = QLabel(self.frame_7)
        self.processLoadingLabel.setObjectName(u"processLoadingLabel")
        self.processLoadingLabel.setPixmap(QPixmap(u":/resources/general/load_wheel_24.webp"))

        self.horizontalLayout_8.addWidget(self.processLoadingLabel)

        self.processCompleteLabel = QLabel(self.frame_7)
        self.processCompleteLabel.setObjectName(u"processCompleteLabel")
        self.processCompleteLabel.setPixmap(QPixmap(u":/resources/general/check_green.png"))

        self.horizontalLayout_8.addWidget(self.processCompleteLabel)

        self.newAssetsLabel = QLabel(self.frame_7)
        self.newAssetsLabel.setObjectName(u"newAssetsLabel")
        self.newAssetsLabel.setFont(font)

        self.horizontalLayout_8.addWidget(self.newAssetsLabel)

        self.horizontalSpacer_5 = QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_8.addItem(self.horizontalSpacer_5)


        self.verticalLayout_6.addWidget(self.frame_7)

        self.line_4 = QFrame(self.frame_6)
        self.line_4.setObjectName(u"line_4")
        self.line_4.setFrameShape(QFrame.HLine)
        self.line_4.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_6.addWidget(self.line_4)

        self.newAssetListView = AssetListView(self.frame_6)
        self.newAssetListView.setObjectName(u"newAssetListView")
        self.newAssetListView.setResizeMode(QListView.Adjust)
        self.newAssetListView.setUniformItemSizes(True)
        self.newAssetListView.setWordWrap(True)
        self.newAssetListView.setSelectionRectVisible(True)

        self.verticalLayout_6.addWidget(self.newAssetListView)


        self.horizontalLayout.addWidget(self.frame_6)

        self.tabWidget.addTab(self.categorizeTab, "")

        self.verticalLayout_2.addWidget(self.tabWidget)


        self.verticalLayout_3.addWidget(self.frame_2)

        self.frame_3 = QFrame(IngestForm)
        self.frame_3.setObjectName(u"frame_3")
        self.frame_3.setStyleSheet(u"QFrame {\n"
"    background-color: rgb(55, 55, 55);\n"
"}")
        self.frame_3.setFrameShape(QFrame.StyledPanel)
        self.frame_3.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.frame_3)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(18, 6, 18, 6)
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setSpacing(9)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(6, 6, 6, 6)
        self.nextButton = QPushButton(self.frame_3)
        self.nextButton.setObjectName(u"nextButton")
        self.nextButton.setEnabled(False)
        self.nextButton.setStyleSheet(u"")

        self.horizontalLayout_4.addWidget(self.nextButton)

        self.cancelButton = QPushButton(self.frame_3)
        self.cancelButton.setObjectName(u"cancelButton")

        self.horizontalLayout_4.addWidget(self.cancelButton)


        self.horizontalLayout_2.addLayout(self.horizontalLayout_4)


        self.verticalLayout_3.addWidget(self.frame_3)

#if QT_CONFIG(shortcut)
        self.texturesReferencesLabel.setBuddy(self.texturesReferencesCheckBox)
        self.texturesReferencesLabel_2.setBuddy(self.texturesReferencesCheckBox)
#endif // QT_CONFIG(shortcut)

        self.retranslateUi(IngestForm)
        self.cancelButton.clicked.connect(IngestForm.close)

        self.tabWidget.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(IngestForm)
    # setupUi

    def retranslateUi(self, IngestForm):
        IngestForm.setWindowTitle(QCoreApplication.translate("IngestForm", u"Form", None))
        self.titleLabel.setText(QCoreApplication.translate("IngestForm", u"Ingest Wizard", None))
        self.label_3.setText(QCoreApplication.translate("IngestForm", u"Category :", None))
        self.collectPathTextEdit.setPlaceholderText(QCoreApplication.translate("IngestForm", u"Insert paths or urls here...", None))
        self.lightsCheckBox.setText(QCoreApplication.translate("IngestForm", u" [ .ies ]", None))
        self.moviesLabel.setText(QCoreApplication.translate("IngestForm", u"Movies :", None))
        self.texturesReferencesLabel.setText(QCoreApplication.translate("IngestForm", u"Reference Images:", None))
        self.lightsLabel.setText(QCoreApplication.translate("IngestForm", u"Lights :", None))
        self.texturesReferencesCheckBox.setText(QCoreApplication.translate("IngestForm", u" [ .tif, .jpg, .png ]", None))
        self.toolsLabel.setText(QCoreApplication.translate("IngestForm", u"Tools :", None))
        self.label_2.setText(QCoreApplication.translate("IngestForm", u"File Types Filtering", None))
        self.toolsCheckBox.setText(QCoreApplication.translate("IngestForm", u" [ .py, .exe, .nk ]", None))
        self.moviesCheckBox.setText(QCoreApplication.translate("IngestForm", u" [ .mov, .mp4, .mxf ]", None))
        self.rawLabel.setText(QCoreApplication.translate("IngestForm", u"Camera Raw :", None))
        self.rawCheckBox.setText(QCoreApplication.translate("IngestForm", u" [ .cr2, .dng, .r3d ]", None))
        self.label_7.setText(QCoreApplication.translate("IngestForm", u"Advanced", None))
        self.copyCheckBox.setText("")
        self.copyLabel.setText(QCoreApplication.translate("IngestForm", u"Copy Assets", None))
        self.texturesReferencesLabel_2.setText(QCoreApplication.translate("IngestForm", u"Categorize Using Parent Folder", None))
        self.texturesReferencesCheckBox_2.setText("")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.collectTab), QCoreApplication.translate("IngestForm", u"1. Collect", None))
        self.loadingLabel.setText("")
        self.completedLabel.setText("")
        self.collectedLabel.setText(QCoreApplication.translate("IngestForm", u"Collected : 0/0 ", None))
        self.label_4.setText(QCoreApplication.translate("IngestForm", u"Naming :", None))
        self.label_5.setText(QCoreApplication.translate("IngestForm", u" Provide a new name or re-use an existing name from the list below.", None))
        self.processLoadingLabel.setText("")
        self.processCompleteLabel.setText("")
        self.newAssetsLabel.setText(QCoreApplication.translate("IngestForm", u"Processed : 0/0", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.categorizeTab), QCoreApplication.translate("IngestForm", u"2. Categorize", None))
        self.nextButton.setText(QCoreApplication.translate("IngestForm", u"Next", None))
        self.cancelButton.setText(QCoreApplication.translate("IngestForm", u"Cancel", None))
    # retranslateUi

