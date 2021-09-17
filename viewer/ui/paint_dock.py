# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'paint_dock.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from ..gl.color_picker import ColorPickerGL

import resources_rc

class Ui_PaintDock(object):
    def setupUi(self, PaintDock):
        if not PaintDock.objectName():
            PaintDock.setObjectName(u"PaintDock")
        PaintDock.resize(196, 379)
        PaintDock.setFeatures(QDockWidget.DockWidgetFloatable|QDockWidget.DockWidgetMovable)
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName(u"dockWidgetContents")
        self.verticalLayout = QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout.setSpacing(3)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(3, 3, 3, 3)
        self.scrollArea = QScrollArea(self.dockWidgetContents)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 188, 314))
        self.verticalLayout_2 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setSpacing(9)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(4, 4, 4, 4)
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(3)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(3, 3, 3, 3)
        self.brushToolButton = QToolButton(self.scrollAreaWidgetContents)
        self.brushToolButton.setObjectName(u"brushToolButton")
        self.brushToolButton.setStyleSheet(u"")
        icon = QIcon()
        icon.addFile(u":/resources/brush_tool.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.brushToolButton.setIcon(icon)
        self.brushToolButton.setIconSize(QSize(32, 32))
        self.brushToolButton.setCheckable(True)
        self.brushToolButton.setChecked(True)
        self.brushToolButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.brushToolButton.setArrowType(Qt.NoArrow)

        self.horizontalLayout_2.addWidget(self.brushToolButton)

        self.shapeToolButton = QToolButton(self.scrollAreaWidgetContents)
        self.shapeToolButton.setObjectName(u"shapeToolButton")
        icon1 = QIcon()
        icon1.addFile(u":/resources/shape_tool.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.shapeToolButton.setIcon(icon1)
        self.shapeToolButton.setIconSize(QSize(32, 32))
        self.shapeToolButton.setCheckable(True)
        self.shapeToolButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        self.horizontalLayout_2.addWidget(self.shapeToolButton)

        self.textToolButton = QToolButton(self.scrollAreaWidgetContents)
        self.textToolButton.setObjectName(u"textToolButton")
        icon2 = QIcon()
        icon2.addFile(u":/resources/text_tool.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.textToolButton.setIcon(icon2)
        self.textToolButton.setIconSize(QSize(32, 32))
        self.textToolButton.setCheckable(True)
        self.textToolButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        self.horizontalLayout_2.addWidget(self.textToolButton)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)

        self.shapeFrame = QFrame(self.scrollAreaWidgetContents)
        self.shapeFrame.setObjectName(u"shapeFrame")
        self.shapeFrame.setFrameShape(QFrame.StyledPanel)
        self.shapeFrame.setFrameShadow(QFrame.Raised)
        self.gridLayout_2 = QGridLayout(self.shapeFrame)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.shapeTypeCombobox = QComboBox(self.shapeFrame)
        self.shapeTypeCombobox.addItem("")
        self.shapeTypeCombobox.addItem("")
        self.shapeTypeCombobox.addItem("")
        self.shapeTypeCombobox.addItem("")
        self.shapeTypeCombobox.setObjectName(u"shapeTypeCombobox")
        self.shapeTypeCombobox.setFrame(True)

        self.gridLayout_2.addWidget(self.shapeTypeCombobox, 0, 1, 1, 1)

        self.shapeTypeLabel = QLabel(self.shapeFrame)
        self.shapeTypeLabel.setObjectName(u"shapeTypeLabel")
        self.shapeTypeLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_2.addWidget(self.shapeTypeLabel, 0, 0, 1, 1)


        self.verticalLayout_2.addWidget(self.shapeFrame)

        self.toolBox = QToolBox(self.scrollAreaWidgetContents)
        self.toolBox.setObjectName(u"toolBox")
        self.page = QWidget()
        self.page.setObjectName(u"page")
        self.page.setGeometry(QRect(0, 0, 163, 161))
        self.verticalLayout_3 = QVBoxLayout(self.page)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.pickerFrame = QFrame(self.page)
        self.pickerFrame.setObjectName(u"pickerFrame")
        self.pickerFrame.setFrameShape(QFrame.StyledPanel)
        self.pickerFrame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_6 = QVBoxLayout(self.pickerFrame)
        self.verticalLayout_6.setSpacing(3)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(3)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.colorPaletteToolButton = QToolButton(self.pickerFrame)
        self.colorPaletteToolButton.setObjectName(u"colorPaletteToolButton")
        self.colorPaletteToolButton.setCheckable(True)

        self.horizontalLayout.addWidget(self.colorPaletteToolButton)

        self.colorWheelGLView = ColorPickerGL(self.pickerFrame)
        self.colorWheelGLView.setObjectName(u"colorWheelGLView")
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.colorWheelGLView.sizePolicy().hasHeightForWidth())
        self.colorWheelGLView.setSizePolicy(sizePolicy)
        self.colorWheelGLView.setMinimumSize(QSize(64, 64))

        self.horizontalLayout.addWidget(self.colorWheelGLView)

        self.colorPickerToolButton = QToolButton(self.pickerFrame)
        self.colorPickerToolButton.setObjectName(u"colorPickerToolButton")
        self.colorPickerToolButton.setCheckable(True)

        self.horizontalLayout.addWidget(self.colorPickerToolButton)


        self.verticalLayout_6.addLayout(self.horizontalLayout)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setHorizontalSpacing(4)
        self.gridLayout.setVerticalSpacing(0)
        self.gridLayout.setContentsMargins(3, 3, 3, 3)
        self.opacityLabel = QLabel(self.pickerFrame)
        self.opacityLabel.setObjectName(u"opacityLabel")

        self.gridLayout.addWidget(self.opacityLabel, 5, 0, 1, 1)

        self.valueControl = QDoubleSpinBox(self.pickerFrame)
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

        self.opacityControl = QDoubleSpinBox(self.pickerFrame)
        self.opacityControl.setObjectName(u"opacityControl")
        self.opacityControl.setFrame(False)
        self.opacityControl.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.opacityControl.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.opacityControl.setDecimals(3)
        self.opacityControl.setMaximum(1.000000000000000)
        self.opacityControl.setSingleStep(0.010000000000000)
        self.opacityControl.setValue(1.000000000000000)

        self.gridLayout.addWidget(self.opacityControl, 5, 2, 1, 1)

        self.valueLabel = QLabel(self.pickerFrame)
        self.valueLabel.setObjectName(u"valueLabel")

        self.gridLayout.addWidget(self.valueLabel, 4, 0, 1, 1)

        self.opacitySlider = QSlider(self.pickerFrame)
        self.opacitySlider.setObjectName(u"opacitySlider")
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

        self.valueSlider = QSlider(self.pickerFrame)
        self.valueSlider.setObjectName(u"valueSlider")
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

        self.saturationSlider = QSlider(self.pickerFrame)
        self.saturationSlider.setObjectName(u"saturationSlider")
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

        self.saturationLabel = QLabel(self.pickerFrame)
        self.saturationLabel.setObjectName(u"saturationLabel")

        self.gridLayout.addWidget(self.saturationLabel, 3, 0, 1, 1)

        self.saturationControl = QDoubleSpinBox(self.pickerFrame)
        self.saturationControl.setObjectName(u"saturationControl")
        self.saturationControl.setFrame(False)
        self.saturationControl.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.saturationControl.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.saturationControl.setDecimals(3)
        self.saturationControl.setMaximum(1.000000000000000)
        self.saturationControl.setSingleStep(0.010000000000000)
        self.saturationControl.setValue(1.000000000000000)

        self.gridLayout.addWidget(self.saturationControl, 3, 2, 1, 1)


        self.verticalLayout_6.addLayout(self.gridLayout)


        self.verticalLayout_3.addWidget(self.pickerFrame)

        self.toolBox.addItem(self.page, u"Color Picker")
        self.page_2 = QWidget()
        self.page_2.setObjectName(u"page_2")
        self.page_2.setGeometry(QRect(0, 0, 180, 134))
        self.page_2.setMaximumSize(QSize(16777215, 217))
        font = QFont()
        font.setPointSize(1)
        self.page_2.setFont(font)
        self.toolBox.addItem(self.page_2, u"")

        self.verticalLayout_2.addWidget(self.toolBox)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout.addWidget(self.scrollArea)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setSpacing(3)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(3, 3, 3, 3)
        self.saveButton = QPushButton(self.dockWidgetContents)
        self.saveButton.setObjectName(u"saveButton")

        self.horizontalLayout_4.addWidget(self.saveButton)

        self.clearButton = QPushButton(self.dockWidgetContents)
        self.clearButton.setObjectName(u"clearButton")

        self.horizontalLayout_4.addWidget(self.clearButton)


        self.verticalLayout.addLayout(self.horizontalLayout_4)

        PaintDock.setWidget(self.dockWidgetContents)

        self.retranslateUi(PaintDock)

        self.toolBox.setCurrentIndex(0)
        self.toolBox.layout().setSpacing(0)


        QMetaObject.connectSlotsByName(PaintDock)
    # setupUi

    def retranslateUi(self, PaintDock):
        PaintDock.setWindowTitle(QCoreApplication.translate("PaintDock", u"Annotate", None))
        self.brushToolButton.setText(QCoreApplication.translate("PaintDock", u"Brush", None))
        self.shapeToolButton.setText(QCoreApplication.translate("PaintDock", u"Shape", None))
        self.textToolButton.setText(QCoreApplication.translate("PaintDock", u"Text", None))
        self.shapeTypeCombobox.setItemText(0, QCoreApplication.translate("PaintDock", u"Rectangle", None))
        self.shapeTypeCombobox.setItemText(1, QCoreApplication.translate("PaintDock", u"Line", None))
        self.shapeTypeCombobox.setItemText(2, QCoreApplication.translate("PaintDock", u"Ellipse", None))
        self.shapeTypeCombobox.setItemText(3, QCoreApplication.translate("PaintDock", u"Circle", None))

        self.shapeTypeLabel.setText(QCoreApplication.translate("PaintDock", u"Type:", None))
        self.colorPaletteToolButton.setText("")
        self.colorPickerToolButton.setText("")
        self.opacityLabel.setText(QCoreApplication.translate("PaintDock", u"O:", None))
        self.valueControl.setPrefix("")
        self.opacityControl.setPrefix("")
        self.valueLabel.setText(QCoreApplication.translate("PaintDock", u"V:", None))
        self.saturationLabel.setText(QCoreApplication.translate("PaintDock", u"S:", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page), QCoreApplication.translate("PaintDock", u"Color Picker", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page_2), "")
        self.saveButton.setText(QCoreApplication.translate("PaintDock", u"Save", None))
        self.clearButton.setText(QCoreApplication.translate("PaintDock", u"Clear", None))
    # retranslateUi

