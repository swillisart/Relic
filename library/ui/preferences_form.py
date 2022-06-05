# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preferences_form.ui'
##
## Created by: Qt User Interface Compiler version 6.2.2
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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)
import resources_rc
import resources_rc

class Ui_PreferenceForm(object):
    def setupUi(self, PreferenceForm):
        if not PreferenceForm.objectName():
            PreferenceForm.setObjectName(u"PreferenceForm")
        PreferenceForm.resize(866, 420)
        PreferenceForm.setStyleSheet(u"PrefFrame {\n"
"    background-color: rgb(68, 68, 68);\n"
"    color: rgb(200, 200, 200);\n"
"    selection-background-color: rgb(126, 126, 126);\n"
"    selection-color: rgb(250, 250, 250);\n"
"    outline: 0;\n"
"}")
        self.verticalLayout_3 = QVBoxLayout(PreferenceForm)
        self.verticalLayout_3.setSpacing(6)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.PrefFrame = QFrame(PreferenceForm)
        self.PrefFrame.setObjectName(u"PrefFrame")
        self.PrefFrame.setStyleSheet(u"")
        self.PrefFrame.setFrameShape(QFrame.StyledPanel)
        self.PrefFrame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.PrefFrame)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.title_frame = QFrame(self.PrefFrame)
        self.title_frame.setObjectName(u"title_frame")
        self.title_frame.setFrameShape(QFrame.StyledPanel)
        self.title_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_3 = QHBoxLayout(self.title_frame)
        self.horizontalLayout_3.setSpacing(18)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(18, -1, 18, -1)
        self.titleLabel = QLabel(self.title_frame)
        self.titleLabel.setObjectName(u"titleLabel")
        font = QFont()
        font.setPointSize(12)
        font.setBold(False)
        self.titleLabel.setFont(font)
        self.titleLabel.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)

        self.horizontalLayout_3.addWidget(self.titleLabel)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)

        self.searchFrame = QFrame(self.title_frame)
        self.searchFrame.setObjectName(u"searchFrame")
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
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
        icon.addFile(u":/resources/general/searchLight.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.searchButton.setIcon(icon)
        self.searchButton.setIconSize(QSize(20, 20))
        self.searchButton.setFlat(False)

        self.horizontalLayout.addWidget(self.searchButton)

        self.searchBox = QLineEdit(self.searchFrame)
        self.searchBox.setObjectName(u"searchBox")
        sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.searchBox.sizePolicy().hasHeightForWidth())
        self.searchBox.setSizePolicy(sizePolicy1)
        self.searchBox.setMinimumSize(QSize(256, 26))
        font1 = QFont()
        font1.setBold(True)
        self.searchBox.setFont(font1)
        self.searchBox.setFrame(False)
        self.searchBox.setClearButtonEnabled(True)

        self.horizontalLayout.addWidget(self.searchBox)


        self.horizontalLayout_3.addWidget(self.searchFrame)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_2)


        self.verticalLayout_2.addWidget(self.title_frame)

        self.content_frame = QFrame(self.PrefFrame)
        self.content_frame.setObjectName(u"content_frame")
        self.content_frame.setStyleSheet(u"")
        self.content_frame.setFrameShape(QFrame.StyledPanel)
        self.content_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout = QVBoxLayout(self.content_frame)
        self.verticalLayout.setSpacing(3)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(3, 3, 3, 3)

        self.verticalLayout_2.addWidget(self.content_frame)

        self.buttons_frame = QFrame(self.PrefFrame)
        self.buttons_frame.setObjectName(u"buttons_frame")
        self.buttons_frame.setStyleSheet(u"QFrame {\n"
"    background-color: rgb(55, 55, 55);\n"
"}")
        self.buttons_frame.setFrameShape(QFrame.StyledPanel)
        self.buttons_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.buttons_frame)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(18, 6, 18, 6)
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setSpacing(9)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(6, 6, 6, 6)
        self.cancelButton = QPushButton(self.buttons_frame)
        self.cancelButton.setObjectName(u"cancelButton")

        self.horizontalLayout_4.addWidget(self.cancelButton)


        self.horizontalLayout_2.addLayout(self.horizontalLayout_4)


        self.verticalLayout_2.addWidget(self.buttons_frame)


        self.verticalLayout_3.addWidget(self.PrefFrame)


        self.retranslateUi(PreferenceForm)
        self.cancelButton.clicked.connect(PreferenceForm.close)

        QMetaObject.connectSlotsByName(PreferenceForm)
    # setupUi

    def retranslateUi(self, PreferenceForm):
        PreferenceForm.setWindowTitle(QCoreApplication.translate("PreferenceForm", u"Preferences", None))
        self.titleLabel.setText(QCoreApplication.translate("PreferenceForm", u"Preferences", None))
        self.searchButton.setText("")
        self.searchBox.setPlaceholderText(QCoreApplication.translate("PreferenceForm", u"Filter...", None))
        self.cancelButton.setText(QCoreApplication.translate("PreferenceForm", u"Close", None))
    # retranslateUi

