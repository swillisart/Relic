# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'description.ui'
##
## Created by: Qt User Interface Compiler version 6.5.1
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
    QFrame, QHBoxLayout, QLabel, QSizePolicy,
    QSpacerItem, QSplitter, QTextEdit, QVBoxLayout,
    QWidget)

from library.widgets.description import (TextBrowser, TextEdit)
import resources_rc

class Ui_DescriptionDialog(object):
    def setupUi(self, DescriptionDialog):
        if not DescriptionDialog.objectName():
            DescriptionDialog.setObjectName(u"DescriptionDialog")
        DescriptionDialog.resize(800, 900)
        icon = QIcon()
        icon.addFile(u":/resources/style/markdown.png", QSize(), QIcon.Normal, QIcon.Off)
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

        self.filter_layout = QHBoxLayout()
        self.filter_layout.setObjectName(u"filter_layout")
        self.filter_layout.setContentsMargins(3, 3, 3, 3)
        self.found_results_label = QLabel(self.descriptionDockTitle)
        self.found_results_label.setObjectName(u"found_results_label")

        self.filter_layout.addWidget(self.found_results_label)


        self.horizontalLayout_17.addLayout(self.filter_layout)

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
        self.text_edit.setMinimumSize(QSize(260, 0))
        font1 = QFont()
        font1.setPointSize(10)
        self.text_edit.setFont(font1)
        self.text_edit.setLineWrapMode(QTextEdit.FixedPixelWidth)
        self.text_edit.setLineWrapColumnOrWidth(720)
        self.text_edit.setCursorWidth(4)

        self.verticalLayout_7.addWidget(self.text_edit)

        self.splitter.addWidget(self.editor_frame)
        self.text_browser = TextBrowser(self.splitter)
        self.text_browser.setObjectName(u"text_browser")
        self.text_browser.setMinimumSize(QSize(260, 0))
        self.text_browser.setFont(font1)
        self.text_browser.setLineWrapMode(QTextEdit.FixedPixelWidth)
        self.text_browser.setLineWrapColumnOrWidth(720)
        self.text_browser.setCursorWidth(4)
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
        self.found_results_label.setText(QCoreApplication.translate("DescriptionDialog", u"1 / 2", None))
        self.text_edit.setPlaceholderText(QCoreApplication.translate("DescriptionDialog", u"Add description text (Markdown) here...", None))
    # retranslateUi

