# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.5.1
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
    QHBoxLayout, QLabel, QLayout, QSizePolicy,
    QSpacerItem, QToolButton, QVBoxLayout, QWidget)
import resources_rc

class Ui_ScreenCapture(object):
    def setupUi(self, ScreenCapture):
        if not ScreenCapture.objectName():
            ScreenCapture.setObjectName(u"ScreenCapture")
        ScreenCapture.resize(348, 97)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ScreenCapture.sizePolicy().hasHeightForWidth())
        ScreenCapture.setSizePolicy(sizePolicy)
        ScreenCapture.setMinimumSize(QSize(0, 0))
        icon = QIcon()
        icon.addFile(u":/icons/capture.svg", QSize(), QIcon.Normal, QIcon.Off)
        ScreenCapture.setWindowIcon(icon)
        ScreenCapture.setWindowOpacity(1.000000000000000)
        ScreenCapture.setAutoFillBackground(False)
        ScreenCapture.setStyleSheet(u"QWidget#ScreenCapture[pinned='0'] {\n"
"	background-color: rgb(68, 68, 68);\n"
"}\n"
"QWidget#ScreenCapture[pinned='1'] {\n"
"	background-color: rgb(150, 68, 68);\n"
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
        self.verticalLayout_5.setContentsMargins(6, 6, 6, 6)
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
        sizePolicy1 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.buttonFrame.sizePolicy().hasHeightForWidth())
        self.buttonFrame.setSizePolicy(sizePolicy1)
        self.buttonFrame.setFrameShape(QFrame.StyledPanel)
        self.buttonFrame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.buttonFrame)
        self.horizontalLayout_2.setSpacing(6)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(3, 3, 3, 3)
        self.captureButton = QToolButton(self.buttonFrame)
        self.captureButton.setObjectName(u"captureButton")
        icon1 = QIcon()
        icon1.addFile(u":/icons/screenshot_20.png", QSize(), QIcon.Normal, QIcon.Off)
        self.captureButton.setIcon(icon1)
        self.captureButton.setIconSize(QSize(24, 24))
        self.captureButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        self.horizontalLayout_2.addWidget(self.captureButton)

        self.recordButton = QToolButton(self.buttonFrame)
        self.recordButton.setObjectName(u"recordButton")
        icon2 = QIcon()
        icon2.addFile(u":/icons/rec.png", QSize(), QIcon.Normal, QIcon.Off)
        icon2.addFile(u":/icons/stop.png", QSize(), QIcon.Active, QIcon.On)
        self.recordButton.setIcon(icon2)
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
        icon3 = QIcon()
        icon3.addFile(u":/icons/timer.png", QSize(), QIcon.Normal, QIcon.Off)
        self.delayComboBox.addItem(icon3, "")
        self.delayComboBox.addItem(icon3, "")
        self.delayComboBox.addItem(icon3, "")
        self.delayComboBox.addItem(icon3, "")
        self.delayComboBox.setObjectName(u"delayComboBox")
        self.delayComboBox.setIconSize(QSize(22, 22))
        self.delayComboBox.setFrame(False)

        self.horizontalLayout_2.addWidget(self.delayComboBox)

        self.line = QFrame(self.buttonFrame)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.VLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_2.addWidget(self.line)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setSpacing(3)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.historyLabel = QLabel(self.buttonFrame)
        self.historyLabel.setObjectName(u"historyLabel")
        self.historyLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_4.addWidget(self.historyLabel)

        self.expandButton = QToolButton(self.buttonFrame)
        self.expandButton.setObjectName(u"expandButton")
        icon4 = QIcon()
        icon4.addFile(u":/icons/narrowUp.png", QSize(), QIcon.Normal, QIcon.Off)
        icon4.addFile(u":/icons/narrowDown.png", QSize(), QIcon.Active, QIcon.On)
        self.expandButton.setIcon(icon4)
        self.expandButton.setIconSize(QSize(16, 16))
        self.expandButton.setCheckable(True)
        self.expandButton.setChecked(True)
        self.expandButton.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.expandButton.setArrowType(Qt.NoArrow)

        self.horizontalLayout_4.addWidget(self.expandButton)


        self.verticalLayout_2.addLayout(self.horizontalLayout_4)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(3)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.pinLabel = QLabel(self.buttonFrame)
        self.pinLabel.setObjectName(u"pinLabel")
        font = QFont()
        font.setItalic(False)
        font.setStrikeOut(False)
        self.pinLabel.setFont(font)
        self.pinLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout.addWidget(self.pinLabel)

        self.pinButton = QToolButton(self.buttonFrame)
        self.pinButton.setObjectName(u"pinButton")
        icon5 = QIcon()
        icon5.addFile(u":/icons/expander.png", QSize(), QIcon.Normal, QIcon.Off)
        self.pinButton.setIcon(icon5)
        self.pinButton.setIconSize(QSize(16, 16))
        self.pinButton.setCheckable(True)
        self.pinButton.setChecked(True)
        self.pinButton.setToolButtonStyle(Qt.ToolButtonIconOnly)

        self.horizontalLayout.addWidget(self.pinButton)


        self.verticalLayout_2.addLayout(self.horizontalLayout)


        self.horizontalLayout_2.addLayout(self.verticalLayout_2)


        self.verticalLayout.addWidget(self.buttonFrame)


        self.retranslateUi(ScreenCapture)

        QMetaObject.connectSlotsByName(ScreenCapture)
    # setupUi

    def retranslateUi(self, ScreenCapture):
        ScreenCapture.setWindowTitle(QCoreApplication.translate("ScreenCapture", u"Screen Capture", None))
        ScreenCapture.setProperty("pinned", QCoreApplication.translate("ScreenCapture", u"0", None))
        self.actionTaskbar_Pin.setText(QCoreApplication.translate("ScreenCapture", u"Taskbar Pin", None))
#if QT_CONFIG(tooltip)
        self.actionTaskbar_Pin.setToolTip(QCoreApplication.translate("ScreenCapture", u"Frameless focusless mode on taskbar activation.", None))
#endif // QT_CONFIG(tooltip)
        self.historyGroupBox.setTitle(QCoreApplication.translate("ScreenCapture", u"History", None))
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
        self.historyLabel.setText(QCoreApplication.translate("ScreenCapture", u"History :", None))
#if QT_CONFIG(tooltip)
        self.expandButton.setToolTip(QCoreApplication.translate("ScreenCapture", u"Toggle list of capture history for viewing.", None))
#endif // QT_CONFIG(tooltip)
        self.expandButton.setText(QCoreApplication.translate("ScreenCapture", u"...", None))
        self.pinLabel.setText(QCoreApplication.translate("ScreenCapture", u"Pin :", None))
        self.pinButton.setText(QCoreApplication.translate("ScreenCapture", u"...", None))
    # retranslateUi

