# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'color_picker.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_ColorPickerDock(object):
    def setupUi(self, ColorPickerDock):
        if not ColorPickerDock.objectName():
            ColorPickerDock.setObjectName(u"ColorPickerDock")
        ColorPickerDock.resize(173, 234)
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName(u"dockWidgetContents")
        self.verticalLayout = QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(3, 3, 3, 3)
        self.frame = QFrame(self.dockWidgetContents)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Sunken)
        self.verticalLayout_2 = QVBoxLayout(self.frame)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(3)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.colorPickerToolButton = QToolButton(self.frame)
        self.colorPickerToolButton.setObjectName(u"colorPickerToolButton")
        self.colorPickerToolButton.setCheckable(True)

        self.horizontalLayout.addWidget(self.colorPickerToolButton)

        self.colorPaletteToolButton = QToolButton(self.frame)
        self.colorPaletteToolButton.setObjectName(u"colorPaletteToolButton")
        self.colorPaletteToolButton.setCheckable(True)

        self.horizontalLayout.addWidget(self.colorPaletteToolButton)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setHorizontalSpacing(4)
        self.gridLayout.setVerticalSpacing(0)
        self.gridLayout.setContentsMargins(3, 3, 3, 3)
        self.opacityLabel = QLabel(self.frame)
        self.opacityLabel.setObjectName(u"opacityLabel")

        self.gridLayout.addWidget(self.opacityLabel, 5, 0, 1, 1)

        self.valueControl = QDoubleSpinBox(self.frame)
        self.valueControl.setObjectName(u"valueControl")
        self.valueControl.setFrame(False)
        self.valueControl.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.valueControl.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.valueControl.setDecimals(3)
        self.valueControl.setMinimum(0.000000000000000)
        self.valueControl.setMaximum(1.000000000000000)
        self.valueControl.setSingleStep(0.010000000000000)
        self.valueControl.setValue(1.000000000000000)

        self.gridLayout.addWidget(self.valueControl, 4, 2, 1, 1)

        self.opacityControl = QDoubleSpinBox(self.frame)
        self.opacityControl.setObjectName(u"opacityControl")
        self.opacityControl.setFrame(False)
        self.opacityControl.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.opacityControl.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.opacityControl.setDecimals(3)
        self.opacityControl.setMaximum(1.000000000000000)
        self.opacityControl.setSingleStep(0.010000000000000)
        self.opacityControl.setValue(1.000000000000000)

        self.gridLayout.addWidget(self.opacityControl, 5, 2, 1, 1)

        self.valueLabel = QLabel(self.frame)
        self.valueLabel.setObjectName(u"valueLabel")

        self.gridLayout.addWidget(self.valueLabel, 4, 0, 1, 1)

        self.opacitySlider = QSlider(self.frame)
        self.opacitySlider.setObjectName(u"opacitySlider")
        self.opacitySlider.setMouseTracking(True)
        self.opacitySlider.setStyleSheet(u"QSlider::groove:horizontal {\n"
"    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0, 0, 0, 0), stop:1 rgba(255, 255, 255, 255));\n"
"    padding-top: -6px;\n"
"    padding-bottom: -6px;\n"
"    margin-top: 5px;\n"
"    margin-bottom: 5px;\n"
"}\n"
"QSlider::handle:horizontal {\n"
"    background: rgb(0, 0, 0);\n"
"    border: 2px solid rgb(225, 225, 225);\n"
"    width: 2px;\n"
"	border-radius: 3px;\n"
"    padding-top: -6px;\n"
"    padding-bottom: -6px;\n"
"    margin-top: 5px;\n"
"    margin-bottom: 5px;\n"
"}")
        self.opacitySlider.setMaximum(1000)
        self.opacitySlider.setSingleStep(0)
        self.opacitySlider.setPageStep(0)
        self.opacitySlider.setValue(1000)
        self.opacitySlider.setOrientation(Qt.Horizontal)

        self.gridLayout.addWidget(self.opacitySlider, 5, 1, 1, 1)

        self.valueSlider = QSlider(self.frame)
        self.valueSlider.setObjectName(u"valueSlider")
        self.valueSlider.setMouseTracking(True)
        self.valueSlider.setStyleSheet(u"QSlider::groove:horizontal {\n"
"    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0, 0, 0, 255), stop:1 rgba(255, 255, 255, 255));\n"
"    padding-top: -6px;\n"
"    padding-bottom: -6px;\n"
"    margin-top: 5px;\n"
"    margin-bottom: 5px;\n"
"}\n"
"QSlider::handle:horizontal {\n"
"    background: rgb(0, 0, 0);\n"
"    border: 2px solid rgb(225, 225, 225);\n"
"    width: 2px;\n"
"	border-radius: 3px;\n"
"    padding-top: -6px;\n"
"    padding-bottom: -6px;\n"
"    margin-top: 5px;\n"
"    margin-bottom: 5px;\n"
"}\n"
"\n"
"")
        self.valueSlider.setMaximum(1000)
        self.valueSlider.setSingleStep(0)
        self.valueSlider.setPageStep(0)
        self.valueSlider.setValue(1000)
        self.valueSlider.setSliderPosition(1000)
        self.valueSlider.setOrientation(Qt.Horizontal)

        self.gridLayout.addWidget(self.valueSlider, 4, 1, 1, 1)

        self.saturationSlider = QSlider(self.frame)
        self.saturationSlider.setObjectName(u"saturationSlider")
        self.saturationSlider.setMouseTracking(True)
        self.saturationSlider.setStyleSheet(u"QSlider::groove:horizontal {\n"
"    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0, 0, 0, 255), stop:1 rgba(0, 255, 0, 255));\n"
"    padding-top: -6px;\n"
"    padding-bottom: -6px;\n"
"    margin-top: 5px;\n"
"    margin-bottom: 5px;\n"
"}\n"
"QSlider::handle:horizontal {\n"
"    background: rgb(0, 0, 0);\n"
"    border: 2px solid rgb(225, 225, 225);\n"
"    width: 2px;\n"
"	border-radius: 3px;\n"
"    padding-top: -6px;\n"
"    padding-bottom: -6px;\n"
"    margin-top: 5px;\n"
"    margin-bottom: 5px;\n"
"}\n"
"")
        self.saturationSlider.setMaximum(1000)
        self.saturationSlider.setSingleStep(0)
        self.saturationSlider.setPageStep(0)
        self.saturationSlider.setValue(1000)
        self.saturationSlider.setSliderPosition(1000)
        self.saturationSlider.setOrientation(Qt.Horizontal)

        self.gridLayout.addWidget(self.saturationSlider, 3, 1, 1, 1)

        self.saturationLabel = QLabel(self.frame)
        self.saturationLabel.setObjectName(u"saturationLabel")

        self.gridLayout.addWidget(self.saturationLabel, 3, 0, 1, 1)

        self.saturationControl = QDoubleSpinBox(self.frame)
        self.saturationControl.setObjectName(u"saturationControl")
        self.saturationControl.setFrame(False)
        self.saturationControl.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.saturationControl.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.saturationControl.setDecimals(3)
        self.saturationControl.setMaximum(1.000000000000000)
        self.saturationControl.setSingleStep(0.010000000000000)
        self.saturationControl.setValue(1.000000000000000)

        self.gridLayout.addWidget(self.saturationControl, 3, 2, 1, 1)


        self.verticalLayout_2.addLayout(self.gridLayout)


        self.verticalLayout.addWidget(self.frame)

        ColorPickerDock.setWidget(self.dockWidgetContents)

        self.retranslateUi(ColorPickerDock)

        QMetaObject.connectSlotsByName(ColorPickerDock)
    # setupUi

    def retranslateUi(self, ColorPickerDock):
        ColorPickerDock.setWindowTitle(QCoreApplication.translate("ColorPickerDock", u"Color Picker", None))
        self.colorPickerToolButton.setText("")
        self.colorPaletteToolButton.setText("")
        self.opacityLabel.setText(QCoreApplication.translate("ColorPickerDock", u"O:", None))
        self.valueControl.setPrefix("")
        self.opacityControl.setPrefix("")
        self.valueLabel.setText(QCoreApplication.translate("ColorPickerDock", u"V:", None))
        self.saturationLabel.setText(QCoreApplication.translate("ColorPickerDock", u"S:", None))
    # retranslateUi

