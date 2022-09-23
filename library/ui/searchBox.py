# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'searchBox.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLineEdit,
    QSizePolicy, QSpacerItem, QToolButton, QWidget)
import resources_rc

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(183, 55)
        Form.setStyleSheet(u"QToolButton#filterBoxButton {\n"
"    background-color: rgb(57, 57, 57);\n"
"    padding: 0px;\n"
"	border: 0px;\n"
"	margin: 1px;\n"
"}\n"
"QToolButton#filterBoxButton:hover {\n"
"    background-color: rgb(108, 108, 108);\n"
"}\n"
"QToolButton#filterBoxButton:checked {\n"
"    background-color: rgb(43, 43, 43);\n"
"}\n"
"QFrame#filterBoxFrame {\n"
"    border: 1px solid rgb(43, 43, 43);\n"
"    background-color: rgb(43, 43, 43);\n"
"    border-radius: 2px;\n"
"}\n"
"QFrame#filterBoxFrame:hover {\n"
"    border: 1px solid rgb(150, 146, 137);\n"
"}\n"
"QLineEdit#filterBoxLine {\n"
"    border: 1px solid rgb(43, 43, 43);\n"
"    background-color: rgb(43, 43, 43);\n"
"    border-radius: 0px;\n"
"    color: rgb(200, 200, 200);\n"
"    padding: 0px;\n"
"}\n"
"QLineEdit#filterBoxLine:focus {\n"
"    border: 1px solid rgb(43, 43, 43);\n"
"    background-color: rgb(55, 55, 55);\n"
"}")
        self.horizontalLayout_2 = QHBoxLayout(Form)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.filterBoxFrame = QFrame(Form)
        self.filterBoxFrame.setObjectName(u"filterBoxFrame")
        self.filterBoxFrame.setMaximumSize(QSize(16777215, 20))
        self.horizontalLayout_8 = QHBoxLayout(self.filterBoxFrame)
        self.horizontalLayout_8.setSpacing(1)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.filterBoxButton = QToolButton(self.filterBoxFrame)
        self.filterBoxButton.setObjectName(u"filterBoxButton")
        self.filterBoxButton.setMinimumSize(QSize(18, 18))
        self.filterBoxButton.setMaximumSize(QSize(18, 18))
        icon = QIcon()
        icon.addFile(u":/resources/general/searchLight.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.filterBoxButton.setIcon(icon)
        self.filterBoxButton.setCheckable(True)

        self.horizontalLayout_8.addWidget(self.filterBoxButton)

        self.filterBoxLine = QLineEdit(self.filterBoxFrame)
        self.filterBoxLine.setObjectName(u"filterBoxLine")
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.filterBoxLine.sizePolicy().hasHeightForWidth())
        self.filterBoxLine.setSizePolicy(sizePolicy)
        self.filterBoxLine.setMinimumSize(QSize(0, 9))
        self.filterBoxLine.setMaximumSize(QSize(16777215, 18))
        font = QFont()
        font.setPointSize(8)
        self.filterBoxLine.setFont(font)
        self.filterBoxLine.setFrame(False)
        self.filterBoxLine.setClearButtonEnabled(True)

        self.horizontalLayout_8.addWidget(self.filterBoxLine)


        self.horizontalLayout_2.addWidget(self.filterBoxFrame)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)


        self.retranslateUi(Form)
        self.filterBoxButton.toggled.connect(self.filterBoxLine.setVisible)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.filterBoxButton.setText("")
        self.filterBoxLine.setPlaceholderText(QCoreApplication.translate("Form", u"Filter...", None))
    # retranslateUi

