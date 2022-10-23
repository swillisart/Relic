# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.3.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QGroupBox,
    QHBoxLayout, QLayout, QLineEdit, QPushButton,
    QSizePolicy, QSpacerItem, QToolButton, QVBoxLayout,
    QWidget)
import resources_rc

class Ui_ScreenCapture(object):
    def setupUi(self, ScreenCapture):
        if not ScreenCapture.objectName():
            ScreenCapture.setObjectName(u"ScreenCapture")
        ScreenCapture.resize(360, 127)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ScreenCapture.sizePolicy().hasHeightForWidth())
        ScreenCapture.setSizePolicy(sizePolicy)
        ScreenCapture.setMinimumSize(QSize(0, 0))
        icon = QIcon()
        icon.addFile(u":/resources/icons/capture.svg", QSize(), QIcon.Normal, QIcon.Off)
        ScreenCapture.setWindowIcon(icon)
        ScreenCapture.setWindowOpacity(1.000000000000000)
        ScreenCapture.setAutoFillBackground(False)
        ScreenCapture.setStyleSheet(u"QWidget#ScreenCapture[pinned='0'] {\n"
"	background-color: rgb(68, 68, 68);\n"
"}\n"
"QWidget#ScreenCapture[pinned='1'] {\n"
"	background-color: rgb(150, 68, 68);\n"
"}\n"
"QWidget {\n"
"	background-color: rgb(68, 68, 68);\n"
"    color: rgb(220, 220, 220);\n"
"    selection-background-color: rgb(126, 126, 126);\n"
"    selection-color: rgb(220, 220, 220);\n"
"    outline: 0;\n"
"}\n"
"QWidget:item {\n"
"    background-color: transparent;\n"
"}\n"
"QWidget:item:hover {\n"
"    background-color: rgb(150, 146, 137);\n"
"}\n"
"QWidget:item:selected {\n"
"    background-color: rgb(150, 146, 137);\n"
"}\n"
"QWidget:disabled {\n"
"    background-color: rgb(43, 43, 43);\n"
"    color: rgb(92, 92, 92);\n"
"}\n"
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
"  border-right: 1px sol"
                        "id rgb(150, 146, 137);\n"
"  border-bottom: 1px solid rgb(150, 146, 137);\n"
"}\n"
"QPushButton {\n"
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
"QMenu::"
                        "indicator {\n"
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
"    image: url(:style/checkbox_checked.svg);\n"
"}\n"
"QMenu::indicator:non-exclusive:unchecked {\n"
"    image: url(:style/checkbox.svg);\n"
"}\n"
"\n"
"QLineEdit:focus,\n"
"QTextEdit:focus {\n"
"    border: 2px solid rgb(150, 146, 137);\n"
"}\n"
"QLineEdit,\n"
"QAbstractSpinBox,\n"
"QTextEdit {\n"
"    background-color: rgb(43, 43, 43);\n"
"    border: 2px solid rgb(43, 43, 43);\n"
"    border-radius: 3px;\n"
"    color: rgb(200, 200, 200);\n"
"    padding: 1px;\n"
"    margin-top: 0px;\n"
"    padding-left: 0px;\n"
"}\n"
"interactiveSpinBox {\n"
"    padding: 1px;\n"
"    margin: 1px;\n"
"    border: 1px solid rgb(43, 43, 43);\n"
"\n"
"}\n"
"QTextEdit:disabled,\n"
"QAbstractS"
                        "pinBox:disabled,\n"
"QLineEdit:disabled {\n"
"    background-color: rgb(43, 43, 43);\n"
"    color: #787878;\n"
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
"    border-radius: 4"
                        "px;\n"
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
"    margin: 0px 3px 0px "
                        "0px;\n"
"    border-image: url(:style/stylesheet-branch-closed.png);\n"
"    height: 10px;\n"
"    width: 6px;\n"
"    subcontrol-position: right;\n"
"    subcontrol-origin: margin;\n"
"}\n"
"QScrollBar::sub-line:horizontal:hover,\n"
"QScrollBar::sub-line:horizontal:on,\n"
"QScrollBar::sub-line:horizontal {\n"
"    margin: 0px 0px 0px 3px;\n"
"    border-image: url(:style/stylesheet-branch-closedleft.png);\n"
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
"    border-image: url(:style/stylesheet-branch-open"
                        "up.png);\n"
"    height: 6px;\n"
"    width: 10px;\n"
"    subcontrol-position: top;\n"
"    subcontrol-origin: margin;\n"
"}\n"
"QScrollBar::add-line:vertical {\n"
"    margin: 0px 0px 3px 0px;\n"
"    border-image: url(:style/stylesheet-branch-open.png);\n"
"    height: 6px;\n"
"    width: 10px;\n"
"    subcontrol-position: bottom;\n"
"    subcontrol-origin: margin;\n"
"}\n"
"QScrollBar::sub-line:vertical:hover,\n"
"QScrollBar::sub-line:vertical:on {\n"
"    border-image: url(:style/stylesheet-branch-openup.png);\n"
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
"QTableCornerButton::section {\n"
"    background-color: "
                        "rgb(92, 92, 92);\n"
"	border: 1px rgb(43,43,43);\n"
"	border-radius: 0px;\n"
"}\n"
"QHeaderView {\n"
"	background-color: rgb(68, 68, 68);\n"
"	border: 0px transparent rgb(68,68,68);\n"
"    padding: 0px;\n"
"	margin: 1px;\n"
"	border-radius: 0px;\n"
"}\n"
"QHeaderView::section {\n"
"	background-color: rgb(92, 92, 92);\n"
"	color: rgb(200,200,200);\n"
"    border-bottom: 1px solid rgb(43,43,43);\n"
"    border-right: 1px solid rgb(43,43,43);\n"
"	border-radius: 0px;\n"
"	text-align: center;\n"
"}\n"
"QHeaderView::section:vertical,\n"
"QHeaderView::section:horizontal {\n"
"	padding-left: 6px;\n"
"    margin-top: -3px;\n"
"    margin-left: -3px;\n"
"}\n"
"QListView,\n"
"QTreeView,\n"
"QTableView,\n"
"QColumnView {\n"
"    border: none;\n"
"	alternate-background-color: rgb(75,75,75);\n"
"}\n"
"QListView::item,\n"
"QTreeView::item,\n"
"QTableView::item,\n"
"QColumnView::item {\n"
"    border-top: none;\n"
"    padding-right: 8px;\n"
"    padding-left: 1px;\n"
"    margin-top: 1px;\n"
"    margin-bottom: 1px;\n"
"  "
                        "  margin-left: 1px;\n"
"}\n"
"QTreeView::branch {\n"
"    border-top: 0px solid rgb(43, 43, 43);\n"
"    border-bottom: 0px solid rgb(43, 43, 43);\n"
"    padding: 4px;\n"
"    margin-top: 2px;\n"
"    margin-bottom: 2px;\n"
"}\n"
"QTreeView::branch:has-siblings:!adjoins-item {\n"
"    border-image: url(:style/stylesheet-vline.png);\n"
"}\n"
"QTreeView::branch:has-siblings:adjoins-item {\n"
"    border-image: url(:style/stylesheet-branch-more.png);\n"
"}\n"
"QTreeView::branch:!has-children:!has-siblings:adjoins-item {\n"
"    border-image: url(:style/stylesheet-branch-end.png);\n"
"}\n"
"QTreeView::branch:has-children:!has-siblings:closed,\n"
"QTreeView::branch:closed:has-children:has-siblings {\n"
"    image: url(:style/treeExpand.svg);\n"
"}\n"
"QTreeView::branch:open:has-children:!has-siblings,\n"
"QTreeView::branch:open:has-children:has-siblings  {\n"
"    image: url(:style/treeCollapse.svg);\n"
"}\n"
"\n"
"/* QCombobox -------------------------------------------------------------- */\n"
"QComboBox {\n"
" "
                        "   border: 0px;\n"
"    border-radius: 3px;\n"
"    background-color: rgb(92, 92, 92);\n"
"    padding-top: 2px;     /* This fix  #103, #111*/\n"
"    padding-bottom: 1px;  /* This fix  #103, #111*/\n"
"    padding-left: 4px;\n"
"    padding-right: 4px;\n"
"    min-width: 75px;\n"
"}\n"
"QComboBox[styling_mode=\"1\"]{\n"
"    margin: 0px;\n"
"    background-color: transparent;\n"
"    border-radius: 3px;\n"
"}\n"
"QComboBox[styling_mode=\"1\"]:hover {\n"
"    background-color: rgb(108, 108, 108);\n"
"    color: rgb(250, 250, 250);\n"
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
"QComboBox::down"
                        "-arrow:focus {\n"
"    image: url(:style/stylesheet-branch-open.png);\n"
"}\n"
"\n"
"\n"
"/* QCheckBox -------------------------------------------------------------- */\n"
"\n"
"\n"
"QCheckBox::indicator:checked:hover,\n"
"QTreeView::indicator:checked:hover,\n"
"QListView::indicator:checked:hover {\n"
"    image: url(:style/checkbox_checked_hover.svg);\n"
"}\n"
"QCheckBox::indicator:unchecked:hover,\n"
"QTreeView::indicator:unchecked:hover,\n"
"QListView::indicator:unchecked:hover {\n"
"    image: url(:style/checkbox_hover.svg);\n"
"}\n"
"QCheckBox::indicator {\n"
"    width: 14px;\n"
"    height: 14px;\n"
"}\n"
"QCheckBox::indicator:checked,\n"
"QTreeView::indicator:checked,\n"
"QListView::indicator:checked {\n"
"    image: url(:style/checkbox_checked.svg);\n"
"}\n"
"\n"
"QCheckBox::indicator:checked:hover,\n"
"QTreeView::indicator:checked:hover,\n"
"QListView::indicator:checked:hover {\n"
"    image: url(:style/checkbox_checked_hover.svg);\n"
"}\n"
"\n"
"QCheckBox::indicator:unchecked,\n"
"QTreeView::indicat"
                        "or:unchecked,\n"
"QListView::indicator:unchecked {\n"
"    color: rgb(43, 43, 43);\n"
"    image: url(:style/checkbox.svg);\n"
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
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"QGroupBox {\n"
"	background-color: rgb(68, 68, 68);\n"
"    color: rgb(225, 225, 225);\n"
"	border: 1px solid rgb(43, 43, 43);\n"
"	border-radius: 2px;\n"
"    padding-top: 14px;\n"
"}\n"
"QGroupBox:title { \n"
"    subcontrol-origin: padding;\n"
"    padding-left: 6px;\n"
"    padding-top: 3px;\n"
"    margin-top: -2px;\n"
"}\n"
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
"QTabWidget"
                        "::pane:selected {\n"
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
"    color: #787878;"
                        "\n"
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
"QTabBar::tab:bottom:!"
                        "selected:disabled {\n"
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
"    border-bottom: 3"
                        "px solid rgb(43, 43, 43);\n"
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
"    border-top-right-radius: 3px;\n"
"    border-top: 1px solid rgb(43, 43, 43);\n"
"}\n"
"\n"
"QRadioButton::indicator {\n"
"    width:                  8px;\n"
"    height:                 8px;\n"
"    border-radius:          6px;\n"
"}\n"
"QRadioButton::indicator:checked {\n"
"    background-color:       gray;\n"
"    border:                 2px solid rgb(43,43,43);\n"
"}\n"
"QRadioButton::indicator:unchecked {\n"
"    background-color:       rgb(43,43,43);\n"
"    "
                        "border:                 2px solid rgb(43,43,43);\n"
"}\n"
"QRadioButton:indicator:hover {\n"
"    border: 2px solid rgb(150, 146, 137);\n"
"}\n"
"\n"
"QAbstractSpinBox {\n"
"    padding: 1px;\n"
"    padding-left: 4px;\n"
"    margin: 1px;\n"
"    border: 1px solid rgb(43, 43, 43);\n"
"}\n"
"QToolBox {\n"
"	font-size: 11px;\n"
"	border: 0px;\n"
"	border-radius: 3px;\n"
"    border: 1px solid rgb(43,43,43);\n"
"}\n"
"\n"
"QToolBox::tab {\n"
"    border: 0px solid rgb(108, 108, 108);\n"
"    border-radius: 3px;\n"
"    background-color:rgb(92, 92, 92);\n"
"    margin: 0px;\n"
"    padding: 0px;\n"
"}\n"
"QToolBox::tab:selected {\n"
"    border-left: 2px solid rgb(150, 146, 137);\n"
"    background-color:rgb(108,108,108);\n"
"}\n"
"")
        self.actionTaskbar_Pin = QAction(ScreenCapture)
        self.actionTaskbar_Pin.setObjectName(u"actionTaskbar_Pin")
        self.verticalLayout = QVBoxLayout(ScreenCapture)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SetMinimumSize)
        self.verticalLayout.setContentsMargins(2, 2, 2, 2)
        self.historyGroupBox = QGroupBox(ScreenCapture)
        self.historyGroupBox.setObjectName(u"historyGroupBox")
        sizePolicy.setHeightForWidth(self.historyGroupBox.sizePolicy().hasHeightForWidth())
        self.historyGroupBox.setSizePolicy(sizePolicy)
        self.verticalLayout_5 = QVBoxLayout(self.historyGroupBox)
        self.verticalLayout_5.setSpacing(2)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setSizeConstraint(QLayout.SetMinimumSize)
        self.verticalLayout_5.setContentsMargins(6, 6, 6, 6)
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setSizeConstraint(QLayout.SetMinimumSize)
        self.horizontalLayout_3.setContentsMargins(2, 2, 2, 0)
        self.searchFrame = QFrame(self.historyGroupBox)
        self.searchFrame.setObjectName(u"searchFrame")
        sizePolicy1 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.searchFrame.sizePolicy().hasHeightForWidth())
        self.searchFrame.setSizePolicy(sizePolicy1)
        self.searchFrame.setStyleSheet(u"QFrame {\n"
"    border: 0px solid rgb(43, 43, 43);\n"
"    background-color: rgb(43, 43, 43);\n"
"    border-radius: 3px;\n"
"}")
        self.searchFrame.setFrameShape(QFrame.StyledPanel)
        self.searchFrame.setFrameShadow(QFrame.Plain)
        self.horizontalLayout_4 = QHBoxLayout(self.searchFrame)
        self.horizontalLayout_4.setSpacing(0)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.searchButton = QPushButton(self.searchFrame)
        self.searchButton.setObjectName(u"searchButton")
        self.searchButton.setStyleSheet(u"QPushButton {\n"
"    background-color: rgb(43, 43, 43);\n"
"    padding: 2px;\n"
"    margin-left: 1px;\n"
"	border-radius: 3px;\n"
"	border: 1px solid rgb(43, 43, 43);\n"
"}\n"
"QPushButton::hover {\n"
"    background-color: rgb(63, 63, 63);\n"
"    /*border: 1px solid rgb(150, 146, 137);*/\n"
"}")
        icon1 = QIcon()
        icon1.addFile(u":resources/app/searchLight.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.searchButton.setIcon(icon1)
        self.searchButton.setIconSize(QSize(18, 18))

        self.horizontalLayout_4.addWidget(self.searchButton)

        self.searchLine = QLineEdit(self.searchFrame)
        self.searchLine.setObjectName(u"searchLine")
        sizePolicy2 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.searchLine.sizePolicy().hasHeightForWidth())
        self.searchLine.setSizePolicy(sizePolicy2)
        self.searchLine.setMinimumSize(QSize(280, 26))
        font = QFont()
        font.setBold(False)
        self.searchLine.setFont(font)
        self.searchLine.setStyleSheet(u"QLineEdit { padding: 0px;}\n"
"QLineEdit:focus,\n"
"QTextEdit:focus {\n"
"    border: none;\n"
"}")
        self.searchLine.setFrame(False)
        self.searchLine.setClearButtonEnabled(True)

        self.horizontalLayout_4.addWidget(self.searchLine)


        self.horizontalLayout_3.addWidget(self.searchFrame)


        self.verticalLayout_5.addLayout(self.horizontalLayout_3)

        self.line_3 = QFrame(self.historyGroupBox)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setStyleSheet(u"margin: -0px 32px -0px 32px;")
        self.line_3.setFrameShape(QFrame.HLine)
        self.line_3.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_5.addWidget(self.line_3)

        self.verticalSpacer = QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.verticalLayout_5.addItem(self.verticalSpacer)


        self.verticalLayout.addWidget(self.historyGroupBox)

        self.buttonFrame = QFrame(ScreenCapture)
        self.buttonFrame.setObjectName(u"buttonFrame")
        sizePolicy1.setHeightForWidth(self.buttonFrame.sizePolicy().hasHeightForWidth())
        self.buttonFrame.setSizePolicy(sizePolicy1)
        self.buttonFrame.setStyleSheet(u"QFrame#buttonFrame {\n"
"border: 1px solid rgb(43, 43, 43);\n"
"border-radius: 2px;\n"
"padding: 1px;\n"
"}\n"
"QToolButton {\n"
"    padding: 0px;\n"
"    margin: 0px;\n"
"    border-radius: 3px;\n"
"    border: 1px solid rgb(68, 68, 68);\n"
"}\n"
"QToolButton:pressed {\n"
"    background-color: rgb(43, 43, 43);\n"
"    border: 1px solid rgb(150, 149, 147);\n"
"}\n"
"QToolButton:checked {\n"
"    background-color: rgb(140, 136, 127);\n"
"    border: 1px solid rgb(150, 146, 137);\n"
"    color: rgb(255, 255, 255);\n"
"}\n"
"QToolButton:hover {\n"
"    background-color: rgb(108, 108, 108);\n"
"    color: rgb(250, 250, 250);\n"
"}\n"
"\n"
"QToolButton::left-arrow,\n"
"QToolButton::left-arrow:on {\n"
"    border: 1px solid rgb(43, 43, 43);\n"
"    background-color: rgb(68, 68, 68);\n"
"    padding: 1px;\n"
"    margin: 2px;\n"
"    image: url(:/resources/checkbox.svg);\n"
"}\n"
"\n"
"QToolButton::down-arrow,\n"
"QToolButton::down-arrow:on {\n"
"    border: 1px solid rgb(150, 146, 137);\n"
"    background-color: r"
                        "gb(68, 68, 68);\n"
"    padding: 0px;\n"
"    margin: 2px;\n"
"    image: url(:/resources/checkbox_checked.svg);\n"
"}\n"
"\n"
"QToolButton::menu-button {\n"
"    border: none;\n"
"    /*\n"
"    border-top-right-radius: 6px;\n"
"    border-bottom-right-radius: 6px;\n"
"    width: 16px;\n"
"    */\n"
"    image: url(:/resources/icons/expander.png);\n"
"    subcontrol-position: right bottom;\n"
"    subcontrol-origin: padding;\n"
"}")
        self.buttonFrame.setFrameShape(QFrame.StyledPanel)
        self.buttonFrame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.buttonFrame)
        self.horizontalLayout_2.setSpacing(6)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(3, 3, 3, 3)
        self.captureButton = QToolButton(self.buttonFrame)
        self.captureButton.setObjectName(u"captureButton")
        icon2 = QIcon()
        icon2.addFile(u":/resources/icons/screenshot_20.png", QSize(), QIcon.Normal, QIcon.Off)
        self.captureButton.setIcon(icon2)
        self.captureButton.setIconSize(QSize(24, 24))
        self.captureButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        self.horizontalLayout_2.addWidget(self.captureButton)

        self.recordButton = QToolButton(self.buttonFrame)
        self.recordButton.setObjectName(u"recordButton")
        icon3 = QIcon()
        icon3.addFile(u":/resources/icons/rec.png", QSize(), QIcon.Normal, QIcon.Off)
        icon3.addFile(u":/resources/icons/stop.png", QSize(), QIcon.Active, QIcon.On)
        self.recordButton.setIcon(icon3)
        self.recordButton.setIconSize(QSize(24, 24))
        self.recordButton.setCheckable(True)
        self.recordButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        self.horizontalLayout_2.addWidget(self.recordButton)

        self.line_2 = QFrame(self.buttonFrame)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.VLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_2.addWidget(self.line_2)

        self.delayComboBox = QComboBox(self.buttonFrame)
        icon4 = QIcon()
        icon4.addFile(u":/resources/icons/timer.png", QSize(), QIcon.Normal, QIcon.Off)
        self.delayComboBox.addItem(icon4, "")
        self.delayComboBox.addItem(icon4, "")
        self.delayComboBox.addItem(icon4, "")
        self.delayComboBox.addItem(icon4, "")
        self.delayComboBox.setObjectName(u"delayComboBox")
        self.delayComboBox.setIconSize(QSize(24, 24))
        self.delayComboBox.setFrame(False)

        self.horizontalLayout_2.addWidget(self.delayComboBox)

        self.line = QFrame(self.buttonFrame)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.VLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_2.addWidget(self.line)

        self.expandButton = QToolButton(self.buttonFrame)
        self.expandButton.setObjectName(u"expandButton")
        icon5 = QIcon()
        icon5.addFile(u":/resources/icons/narrowLeft.png", QSize(), QIcon.Normal, QIcon.Off)
        icon5.addFile(u":/resources/icons/narrowDown.png", QSize(), QIcon.Active, QIcon.On)
        self.expandButton.setIcon(icon5)
        self.expandButton.setIconSize(QSize(24, 24))
        self.expandButton.setCheckable(True)
        self.expandButton.setChecked(True)
        self.expandButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.expandButton.setArrowType(Qt.NoArrow)

        self.horizontalLayout_2.addWidget(self.expandButton)


        self.verticalLayout.addWidget(self.buttonFrame)


        self.retranslateUi(ScreenCapture)

        QMetaObject.connectSlotsByName(ScreenCapture)
    # setupUi

    def retranslateUi(self, ScreenCapture):
        ScreenCapture.setWindowTitle(QCoreApplication.translate("ScreenCapture", u"Screen Capture", None))
        ScreenCapture.setProperty("styling_mode", QCoreApplication.translate("ScreenCapture", u"1", None))
        ScreenCapture.setProperty("pinned", QCoreApplication.translate("ScreenCapture", u"0", None))
        self.actionTaskbar_Pin.setText(QCoreApplication.translate("ScreenCapture", u"Taskbar Pin", None))
#if QT_CONFIG(tooltip)
        self.actionTaskbar_Pin.setToolTip(QCoreApplication.translate("ScreenCapture", u"Frameless focusless mode on taskbar activation.", None))
#endif // QT_CONFIG(tooltip)
        self.historyGroupBox.setTitle(QCoreApplication.translate("ScreenCapture", u"History", None))
        self.searchButton.setText("")
        self.searchLine.setPlaceholderText(QCoreApplication.translate("ScreenCapture", u"Search...", None))
#if QT_CONFIG(tooltip)
        self.captureButton.setToolTip(QCoreApplication.translate("ScreenCapture", u"Capture a single snapshot of a region.", None))
#endif // QT_CONFIG(tooltip)
        self.captureButton.setText(QCoreApplication.translate("ScreenCapture", u"Capture", None))
#if QT_CONFIG(tooltip)
        self.recordButton.setToolTip(QCoreApplication.translate("ScreenCapture", u"Captures a continuous recording of a defined region in the screen.\n"
"\n"
" Click again to stop.", None))
#endif // QT_CONFIG(tooltip)
        self.recordButton.setText(QCoreApplication.translate("ScreenCapture", u"Record", None))
        self.delayComboBox.setItemText(0, QCoreApplication.translate("ScreenCapture", u"Delay 0s         ", None))
        self.delayComboBox.setItemText(1, QCoreApplication.translate("ScreenCapture", u"Delay 1s", None))
        self.delayComboBox.setItemText(2, QCoreApplication.translate("ScreenCapture", u"Delay 3s", None))
        self.delayComboBox.setItemText(3, QCoreApplication.translate("ScreenCapture", u"Delay 5s", None))

#if QT_CONFIG(tooltip)
        self.delayComboBox.setToolTip(QCoreApplication.translate("ScreenCapture", u"Time Delay in seconds for snapshot or recording actions.", None))
#endif // QT_CONFIG(tooltip)
        self.delayComboBox.setCurrentText(QCoreApplication.translate("ScreenCapture", u"Delay 0s         ", None))
        self.delayComboBox.setProperty("styling_mode", QCoreApplication.translate("ScreenCapture", u"1", None))
#if QT_CONFIG(tooltip)
        self.expandButton.setToolTip(QCoreApplication.translate("ScreenCapture", u"Toggle list of capture history for viewing.", None))
#endif // QT_CONFIG(tooltip)
        self.expandButton.setText(QCoreApplication.translate("ScreenCapture", u"History", None))
    # retranslateUi

