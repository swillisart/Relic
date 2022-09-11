# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'description.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QFrame, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QSpacerItem, QSplitter,
    QVBoxLayout, QWidget)

from library.widgets.description import (TextBrowser, TextEdit)
import resources_rc

class Ui_DescriptionDialog(object):
    def setupUi(self, DescriptionDialog):
        if not DescriptionDialog.objectName():
            DescriptionDialog.setObjectName(u"DescriptionDialog")
        DescriptionDialog.resize(607, 710)
        icon = QIcon()
        icon.addFile(u":/resources/general/markdown.png", QSize(), QIcon.Normal, QIcon.Off)
        DescriptionDialog.setWindowIcon(icon)
        self.verticalLayout = QVBoxLayout(DescriptionDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(-1, 3, -1, -1)
        self.descriptionDockTitle = QFrame(DescriptionDialog)
        self.descriptionDockTitle.setObjectName(u"descriptionDockTitle")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.descriptionDockTitle.sizePolicy().hasHeightForWidth())
        self.descriptionDockTitle.setSizePolicy(sizePolicy)
        self.descriptionDockTitle.setFrameShape(QFrame.StyledPanel)
        self.descriptionDockTitle.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_17 = QHBoxLayout(self.descriptionDockTitle)
        self.horizontalLayout_17.setSpacing(9)
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.horizontalLayout_17.setContentsMargins(3, 0, 3, 0)
        self.descriptionTitle = QLabel(self.descriptionDockTitle)
        self.descriptionTitle.setObjectName(u"descriptionTitle")
        font = QFont()
        font.setPointSize(12)
        self.descriptionTitle.setFont(font)
        self.descriptionTitle.setFrameShape(QFrame.NoFrame)
        self.descriptionTitle.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_17.addWidget(self.descriptionTitle)

        self.horizontalSpacer_9 = QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_17.addItem(self.horizontalSpacer_9)

        self.filterFrame_2 = QFrame(self.descriptionDockTitle)
        self.filterFrame_2.setObjectName(u"filterFrame_2")
        sizePolicy1 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.filterFrame_2.sizePolicy().hasHeightForWidth())
        self.filterFrame_2.setSizePolicy(sizePolicy1)
        self.filterFrame_2.setStyleSheet(u"QFrame#filterFrame_2 {\n"
"	margin: 2px;\n"
"    border: 1px solid rgb(43, 43, 43);\n"
"    background-color: rgb(43, 43, 43);\n"
"    border-radius: 3px;\n"
"}\n"
"QFrame#filterFrame_2:hover {\n"
"    border: 1px solid rgb(150, 146, 137);\n"
"}")
        self.filterFrame_2.setFrameShape(QFrame.StyledPanel)
        self.filterFrame_2.setFrameShadow(QFrame.Plain)
        self.horizontalLayout_11 = QHBoxLayout(self.filterFrame_2)
        self.horizontalLayout_11.setSpacing(0)
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.horizontalLayout_11.setContentsMargins(1, 0, 0, 0)
        self.filterButton_2 = QPushButton(self.filterFrame_2)
        self.filterButton_2.setObjectName(u"filterButton_2")
        sizePolicy2 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.filterButton_2.sizePolicy().hasHeightForWidth())
        self.filterButton_2.setSizePolicy(sizePolicy2)
        self.filterButton_2.setStyleSheet(u"QPushButton {\n"
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
        icon1 = QIcon()
        icon1.addFile(u":/resources/general/searchLight.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.filterButton_2.setIcon(icon1)
        self.filterButton_2.setIconSize(QSize(18, 18))
        self.filterButton_2.setCheckable(True)
        self.filterButton_2.setChecked(True)
        self.filterButton_2.setFlat(False)

        self.horizontalLayout_11.addWidget(self.filterButton_2)

        self.filter_box = QLineEdit(self.filterFrame_2)
        self.filter_box.setObjectName(u"filter_box")
        sizePolicy3 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.filter_box.sizePolicy().hasHeightForWidth())
        self.filter_box.setSizePolicy(sizePolicy3)
        self.filter_box.setMinimumSize(QSize(128, 0))
        font1 = QFont()
        font1.setPointSize(8)
        self.filter_box.setFont(font1)
        self.filter_box.setFrame(False)
        self.filter_box.setClearButtonEnabled(True)

        self.horizontalLayout_11.addWidget(self.filter_box)


        self.horizontalLayout_17.addWidget(self.filterFrame_2)

        self.found_results_label = QLabel(self.descriptionDockTitle)
        self.found_results_label.setObjectName(u"found_results_label")
        self.found_results_label.setStyleSheet(u"background-color: transparent;")

        self.horizontalLayout_17.addWidget(self.found_results_label)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_17.addItem(self.horizontalSpacer_6)


        self.verticalLayout.addWidget(self.descriptionDockTitle)

        self.splitter = QSplitter(DescriptionDialog)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.editor_frame = QFrame(self.splitter)
        self.editor_frame.setObjectName(u"editor_frame")
        self.editor_frame.setFrameShape(QFrame.StyledPanel)
        self.editor_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_7 = QVBoxLayout(self.editor_frame)
        self.verticalLayout_7.setSpacing(0)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.text_edit = TextEdit(self.editor_frame)
        self.text_edit.setObjectName(u"text_edit")

        self.verticalLayout_7.addWidget(self.text_edit)

        self.splitter.addWidget(self.editor_frame)
        self.text_browser = TextBrowser(self.splitter)
        self.text_browser.setObjectName(u"text_browser")
        self.text_browser.setStyleSheet(u"background-color: rgb(80,80,80);\n"
"padding-left: 24px;")
        self.text_browser.setOpenLinks(False)
        self.splitter.addWidget(self.text_browser)

        self.verticalLayout.addWidget(self.splitter)

        self.button_box = QDialogButtonBox(DescriptionDialog)
        self.button_box.setObjectName(u"button_box")
        self.button_box.setStandardButtons(QDialogButtonBox.Help|QDialogButtonBox.Reset|QDialogButtonBox.Save)
        self.button_box.setCenterButtons(False)

        self.verticalLayout.addWidget(self.button_box)


        self.retranslateUi(DescriptionDialog)

        QMetaObject.connectSlotsByName(DescriptionDialog)
    # setupUi

    def retranslateUi(self, DescriptionDialog):
        DescriptionDialog.setWindowTitle(QCoreApplication.translate("DescriptionDialog", u"Description ", None))
        self.descriptionTitle.setText(QCoreApplication.translate("DescriptionDialog", u"Description", None))
        self.filterButton_2.setText("")
        self.filter_box.setPlaceholderText(QCoreApplication.translate("DescriptionDialog", u"Find...", None))
        self.found_results_label.setText(QCoreApplication.translate("DescriptionDialog", u"1 / 2", None))
        self.text_edit.setPlaceholderText(QCoreApplication.translate("DescriptionDialog", u"Add description text (Markdown) here...", None))
    # retranslateUi

