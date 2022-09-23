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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QButtonGroup, QCheckBox,
    QDockWidget, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QMenu,
    QMenuBar, QPushButton, QRadioButton, QScrollArea,
    QSizePolicy, QSlider, QSpacerItem, QSpinBox,
    QStatusBar, QToolButton, QVBoxLayout, QWidget)
import resources_rc
import resources_rc

class Ui_RelicMainWindow(object):
    def setupUi(self, RelicMainWindow):
        if not RelicMainWindow.objectName():
            RelicMainWindow.setObjectName(u"RelicMainWindow")
        RelicMainWindow.resize(945, 540)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(RelicMainWindow.sizePolicy().hasHeightForWidth())
        RelicMainWindow.setSizePolicy(sizePolicy)
        icon = QIcon()
        icon.addFile(u":/resources/app/app_icon.svg", QSize(), QIcon.Normal, QIcon.Off)
        RelicMainWindow.setWindowIcon(icon)
        RelicMainWindow.setStyleSheet(u"")
        RelicMainWindow.setAnimated(True)
        RelicMainWindow.setDockNestingEnabled(True)
        self.actionPreferences = QAction(RelicMainWindow)
        self.actionPreferences.setObjectName(u"actionPreferences")
        self.actionExit = QAction(RelicMainWindow)
        self.actionExit.setObjectName(u"actionExit")
        icon1 = QIcon()
        icon1.addFile(u":/resources/style/close.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.actionExit.setIcon(icon1)
        self.actionAdministration_Mode = QAction(RelicMainWindow)
        self.actionAdministration_Mode.setObjectName(u"actionAdministration_Mode")
        self.actionAdministration_Mode.setCheckable(True)
        self.actionDocumentation = QAction(RelicMainWindow)
        self.actionDocumentation.setObjectName(u"actionDocumentation")
        self.actionIngest = QAction(RelicMainWindow)
        self.actionIngest.setObjectName(u"actionIngest")
        icon2 = QIcon()
        icon2.addFile(u":/resources/general/folder.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.actionIngest.setIcon(icon2)
        self.actionPortal = QAction(RelicMainWindow)
        self.actionPortal.setObjectName(u"actionPortal")
        self.actionPortal.setCheckable(True)
        self.actionPortal.setChecked(True)
        self.actionRecurseSubcategory = QAction(RelicMainWindow)
        self.actionRecurseSubcategory.setObjectName(u"actionRecurseSubcategory")
        self.actionRecurseSubcategory.setCheckable(True)
        self.actionRecurseSubcategory.setChecked(True)
        self.actionReconnect = QAction(RelicMainWindow)
        self.actionReconnect.setObjectName(u"actionReconnect")
        self.centralwidget = QWidget(RelicMainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(9, 9, 9, 9)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.line_5 = QFrame(self.centralwidget)
        self.line_5.setObjectName(u"line_5")
        self.line_5.setFrameShadow(QFrame.Raised)
        self.line_5.setFrameShape(QFrame.HLine)

        self.verticalLayout.addWidget(self.line_5)

        self.noSearchResultsPage = QFrame(self.centralwidget)
        self.noSearchResultsPage.setObjectName(u"noSearchResultsPage")
        self.noSearchResultsPage.setFrameShape(QFrame.StyledPanel)
        self.noSearchResultsPage.setFrameShadow(QFrame.Raised)
        self.verticalLayout_6 = QVBoxLayout(self.noSearchResultsPage)
        self.verticalLayout_6.setSpacing(6)
        self.verticalLayout_6.setContentsMargins(9, 9, 9, 9)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalSpacer_3 = QSpacerItem(20, 19, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_6.addItem(self.verticalSpacer_3)

        self.noResults = QFrame(self.noSearchResultsPage)
        self.noResults.setObjectName(u"noResults")
        self.noResults.setFrameShape(QFrame.StyledPanel)
        self.noResults.setFrameShadow(QFrame.Raised)
        self.verticalLayout_5 = QVBoxLayout(self.noResults)
        self.verticalLayout_5.setSpacing(6)
        self.verticalLayout_5.setContentsMargins(9, 9, 9, 9)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(18, 6, 18, 6)
        self.searchButton_2 = QPushButton(self.noResults)
        self.searchButton_2.setObjectName(u"searchButton_2")
        self.searchButton_2.setLayoutDirection(Qt.LeftToRight)
        self.searchButton_2.setStyleSheet(u"QPushButton {\n"
"	background-color: transparent;\n"
"    padding: 2px;\n"
"	border: none;\n"
"}")
        icon3 = QIcon()
        icon3.addFile(u":/resources/general/searchLight.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.searchButton_2.setIcon(icon3)
        self.searchButton_2.setIconSize(QSize(20, 20))
        self.searchButton_2.setFlat(False)

        self.verticalLayout_5.addWidget(self.searchButton_2)

        self.label = QLabel(self.noResults)
        self.label.setObjectName(u"label")
        font = QFont()
        font.setPointSize(14)
        self.label.setFont(font)
        self.label.setStyleSheet(u"color: rgb(182, 182, 182)")
        self.label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_5.addWidget(self.label)

        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setSpacing(9)
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.horizontalLayout_12.setContentsMargins(6, 6, 6, 6)
        self.horizontalSpacer_10 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_12.addItem(self.horizontalSpacer_10)

        self.clearSubcategoryButton = QPushButton(self.noResults)
        self.clearSubcategoryButton.setObjectName(u"clearSubcategoryButton")
        self.clearSubcategoryButton.setEnabled(True)
        self.clearSubcategoryButton.setStyleSheet(u"QPushButton {\n"
"    padding: 4px;\n"
"	border: 2px solid rgb(57,57,57);\n"
"	border-radius: 4px;\n"
"}")

        self.horizontalLayout_12.addWidget(self.clearSubcategoryButton)

        self.label_4 = QLabel(self.noResults)
        self.label_4.setObjectName(u"label_4")
        sizePolicy1 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy1)
        font1 = QFont()
        font1.setPointSize(9)
        self.label_4.setFont(font1)
        self.label_4.setStyleSheet(u"color: rgb(182, 182, 182)")
        self.label_4.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_12.addWidget(self.label_4)

        self.clearSearchButton = QPushButton(self.noResults)
        self.clearSearchButton.setObjectName(u"clearSearchButton")
        self.clearSearchButton.setEnabled(True)
        self.clearSearchButton.setStyleSheet(u"QPushButton {\n"
"    padding: 4px;\n"
"	border: 2px solid rgb(57,57,57);\n"
"	border-radius: 4px;\n"
"}")

        self.horizontalLayout_12.addWidget(self.clearSearchButton)

        self.horizontalSpacer_11 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_12.addItem(self.horizontalSpacer_11)


        self.verticalLayout_5.addLayout(self.horizontalLayout_12)


        self.verticalLayout_6.addWidget(self.noResults)

        self.verticalSpacer_2 = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_6.addItem(self.verticalSpacer_2)


        self.verticalLayout.addWidget(self.noSearchResultsPage)

        self.linksDock = QDockWidget(self.centralwidget)
        self.linksDock.setObjectName(u"linksDock")
        sizePolicy2 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.linksDock.sizePolicy().hasHeightForWidth())
        self.linksDock.setSizePolicy(sizePolicy2)
        palette = QPalette()
        brush = QBrush(QColor(200, 200, 200, 255))
        brush.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.WindowText, brush)
        brush1 = QBrush(QColor(32, 32, 32, 255))
        brush1.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.Button, brush1)
        palette.setBrush(QPalette.Active, QPalette.Text, brush)
        palette.setBrush(QPalette.Active, QPalette.ButtonText, brush)
        palette.setBrush(QPalette.Active, QPalette.Base, brush1)
        palette.setBrush(QPalette.Active, QPalette.Window, brush1)
        brush2 = QBrush(QColor(126, 126, 126, 255))
        brush2.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.Highlight, brush2)
        brush3 = QBrush(QColor(250, 250, 250, 255))
        brush3.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.HighlightedText, brush3)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.Active, QPalette.PlaceholderText, brush)
#endif
        palette.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        palette.setBrush(QPalette.Inactive, QPalette.Button, brush1)
        palette.setBrush(QPalette.Inactive, QPalette.Text, brush)
        palette.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
        palette.setBrush(QPalette.Inactive, QPalette.Base, brush1)
        palette.setBrush(QPalette.Inactive, QPalette.Window, brush1)
        palette.setBrush(QPalette.Inactive, QPalette.Highlight, brush2)
        palette.setBrush(QPalette.Inactive, QPalette.HighlightedText, brush3)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush)
#endif
        brush4 = QBrush(QColor(92, 92, 92, 255))
        brush4.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Disabled, QPalette.WindowText, brush4)
        brush5 = QBrush(QColor(43, 43, 43, 255))
        brush5.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Disabled, QPalette.Button, brush5)
        palette.setBrush(QPalette.Disabled, QPalette.Text, brush4)
        palette.setBrush(QPalette.Disabled, QPalette.ButtonText, brush4)
        palette.setBrush(QPalette.Disabled, QPalette.Base, brush5)
        palette.setBrush(QPalette.Disabled, QPalette.Window, brush5)
        palette.setBrush(QPalette.Disabled, QPalette.Highlight, brush2)
        palette.setBrush(QPalette.Disabled, QPalette.HighlightedText, brush3)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush4)
#endif
        self.linksDock.setPalette(palette)
        self.linksDock.setAutoFillBackground(True)
        self.linksDock.setStyleSheet(u"")
        self.linksDock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.attrDockWidgetContents_2 = QWidget()
        self.attrDockWidgetContents_2.setObjectName(u"attrDockWidgetContents_2")
        self.linksDock.setWidget(self.attrDockWidgetContents_2)

        self.verticalLayout.addWidget(self.linksDock)

        self.line_4 = QFrame(self.centralwidget)
        self.line_4.setObjectName(u"line_4")
        self.line_4.setFrameShape(QFrame.HLine)
        self.line_4.setFrameShadow(QFrame.Sunken)

        self.verticalLayout.addWidget(self.line_4)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setSpacing(6)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(9, 0, 0, 0)
        self.viewScaleLabel = QLabel(self.centralwidget)
        self.viewScaleLabel.setObjectName(u"viewScaleLabel")

        self.horizontalLayout_3.addWidget(self.viewScaleLabel)

        self.viewScaleSlider = QSlider(self.centralwidget)
        self.viewScaleSlider.setObjectName(u"viewScaleSlider")
        sizePolicy3 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.viewScaleSlider.sizePolicy().hasHeightForWidth())
        self.viewScaleSlider.setSizePolicy(sizePolicy3)
        self.viewScaleSlider.setMaximum(2)
        self.viewScaleSlider.setPageStep(1)
        self.viewScaleSlider.setValue(2)
        self.viewScaleSlider.setOrientation(Qt.Horizontal)
        self.viewScaleSlider.setTickPosition(QSlider.NoTicks)

        self.horizontalLayout_3.addWidget(self.viewScaleSlider)

        self.line_6 = QFrame(self.centralwidget)
        self.line_6.setObjectName(u"line_6")
        self.line_6.setFrameShape(QFrame.VLine)
        self.line_6.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_3.addWidget(self.line_6)

        self.previewCheckBox = QCheckBox(self.centralwidget)
        self.previewCheckBox.setObjectName(u"previewCheckBox")
        icon4 = QIcon()
        icon4.addFile(u":/resources/app/kohai.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.previewCheckBox.setIcon(icon4)

        self.horizontalLayout_3.addWidget(self.previewCheckBox)


        self.horizontalLayout_2.addLayout(self.horizontalLayout_3)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_3)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setSpacing(6)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(-1, -1, 3, -1)
        self.pageDownButton = QToolButton(self.centralwidget)
        self.pageDownButton.setObjectName(u"pageDownButton")
        icon5 = QIcon()
        icon5.addFile(u":/resources/general/pageArrowLeft.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pageDownButton.setIcon(icon5)
        self.pageDownButton.setIconSize(QSize(20, 20))

        self.horizontalLayout_4.addWidget(self.pageDownButton)

        self.pageSpinBox = QSpinBox(self.centralwidget)
        self.pageSpinBox.setObjectName(u"pageSpinBox")
        self.pageSpinBox.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.pageSpinBox.setMinimum(1)
        self.pageSpinBox.setMaximum(9999)
        self.pageSpinBox.setValue(1)

        self.horizontalLayout_4.addWidget(self.pageSpinBox)

        self.pageUpButton = QToolButton(self.centralwidget)
        self.pageUpButton.setObjectName(u"pageUpButton")
        icon6 = QIcon()
        icon6.addFile(u":/resources/general/pageArrow.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pageUpButton.setIcon(icon6)
        self.pageUpButton.setIconSize(QSize(20, 20))

        self.horizontalLayout_4.addWidget(self.pageUpButton)


        self.horizontalLayout_2.addLayout(self.horizontalLayout_4)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        RelicMainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(RelicMainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 945, 22))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuEdit = QMenu(self.menubar)
        self.menuEdit.setObjectName(u"menuEdit")
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName(u"menuHelp")
        self.menuView = QMenu(self.menubar)
        self.menuView.setObjectName(u"menuView")
        RelicMainWindow.setMenuBar(self.menubar)
        self.categoryDock = QDockWidget(RelicMainWindow)
        self.categoryDock.setObjectName(u"categoryDock")
        self.categoryDock.setAutoFillBackground(True)
        self.categoryDock.setFeatures(QDockWidget.DockWidgetFloatable|QDockWidget.DockWidgetMovable)
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName(u"dockWidgetContents")
        self.verticalLayout_2 = QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setContentsMargins(9, 9, 9, 9)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(1, 1, 1, 1)
        self.categoryScrollArea = QScrollArea(self.dockWidgetContents)
        self.categoryScrollArea.setObjectName(u"categoryScrollArea")
        self.categoryScrollArea.setStyleSheet(u"QTreeView {\n"
"    border: none;\n"
"	alternate-background-color: rgb(56,56,56);\n"
"    background-color: rgb(48, 48, 48);\n"
"}\n"
"QTreeView::item,\n"
"QTreeView::item:has-children {\n"
"    background-color: transparent;\n"
"    border: none;\n"
"    margin: 0px;\n"
"    margin-left: 1px;\n"
"    padding: 0px;\n"
"    padding-left: 1px;\n"
"}\n"
"QTreeView:item:hover {\n"
"        background-color: rgb(75, 75, 75);\n"
"        color: rgb(250, 250, 250);\n"
"}\n"
"QTreeView:item:selected {\n"
"        background-color: rgb(140, 136, 127);\n"
"        color: rgb(43, 43, 43);\n"
"    }\n"
"QTreeView::branch {\n"
"    border-top: 0px solid rgb(43, 43, 43);\n"
"    border-bottom: 0px solid rgb(43, 43, 43);\n"
"    padding: 4px;\n"
"    margin: 0px;\n"
"}\n"
"QTreeView::branch:has-siblings:!adjoins-item {\n"
"    border-image: url(:/resources/style/stylesheet-vline.png);\n"
"}\n"
"QTreeView::branch:has-siblings:adjoins-item {\n"
"    border-image: url(:/resources/style/stylesheet-branch-more.png);\n"
"}\n"
"QTr"
                        "eeView::branch:!has-children:!has-siblings:adjoins-item {\n"
"    border-image: url(:/resources/style/stylesheet-branch-end.png);\n"
"}\n"
"QTreeView::branch:!has-children:has-siblings:adjoins-item {\n"
"    border-image: url(:/resources/style/stylesheet-branch-more.png);\n"
"}\n"
"QTreeView::branch:has-children:!has-siblings:closed,\n"
"QTreeView::branch:closed:has-children:has-siblings {\n"
"    image: url(:/resources/style/treeExpand.svg);\n"
"    background-color: transparent;\n"
"}\n"
"QTreeView::branch:open:has-children:!has-siblings,\n"
"QTreeView::branch:open:has-children:has-siblings  {\n"
"    image: url(:/resources/style/treeCollapse.svg);\n"
"    background-color: transparent;\n"
"}")
        self.categoryScrollArea.setWidgetResizable(True)
        self.categoryScrollAreaWidgetContents = QWidget()
        self.categoryScrollAreaWidgetContents.setObjectName(u"categoryScrollAreaWidgetContents")
        self.categoryScrollAreaWidgetContents.setGeometry(QRect(0, 0, 124, 401))
        self.categoryDockLayout = QVBoxLayout(self.categoryScrollAreaWidgetContents)
        self.categoryDockLayout.setSpacing(0)
        self.categoryDockLayout.setContentsMargins(9, 9, 9, 9)
        self.categoryDockLayout.setObjectName(u"categoryDockLayout")
        self.categoryDockLayout.setContentsMargins(0, 0, 0, 0)
        self.subcategory_frame = QFrame(self.categoryScrollAreaWidgetContents)
        self.subcategory_frame.setObjectName(u"subcategory_frame")
        self.subcategory_frame.setFrameShape(QFrame.StyledPanel)
        self.subcategory_frame.setFrameShadow(QFrame.Raised)
        self.categoryLayout = QVBoxLayout(self.subcategory_frame)
        self.categoryLayout.setSpacing(2)
        self.categoryLayout.setContentsMargins(9, 9, 9, 9)
        self.categoryLayout.setObjectName(u"categoryLayout")
        self.categoryLayout.setContentsMargins(3, 3, 3, 3)
        self.verticalSpacer = QSpacerItem(116, 303, QSizePolicy.Minimum, QSizePolicy.MinimumExpanding)

        self.categoryLayout.addItem(self.verticalSpacer)


        self.categoryDockLayout.addWidget(self.subcategory_frame)

        self.categoryScrollArea.setWidget(self.categoryScrollAreaWidgetContents)

        self.verticalLayout_2.addWidget(self.categoryScrollArea)

        self.categoryDock.setWidget(self.dockWidgetContents)
        RelicMainWindow.addDockWidget(Qt.LeftDockWidgetArea, self.categoryDock)
        self.searchDock = QDockWidget(RelicMainWindow)
        self.searchDock.setObjectName(u"searchDock")
        self.searchDock.setStyleSheet(u"QDockWidget {\n"
"    background-color: rgb(68, 68, 68);\n"
"}\n"
"QDockWidget::title {\n"
"    border: 0px;\n"
"	padding: 0px;\n"
"	margin: 0px;\n"
"    width: 0px;\n"
"    height: 0px;\n"
"}\n"
"")
        self.searchDock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.searchDockWidgetContents = QWidget()
        self.searchDockWidgetContents.setObjectName(u"searchDockWidgetContents")
        self.gridLayout = QGridLayout(self.searchDockWidgetContents)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(9, 9, 9, 9)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setHorizontalSpacing(0)
        self.gridLayout.setVerticalSpacing(2)
        self.gridLayout.setContentsMargins(6, 0, 6, 0)
        self.line_2 = QFrame(self.searchDockWidgetContents)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.HLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.gridLayout.addWidget(self.line_2, 1, 5, 1, 1)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 0, 0, 1, 1)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setSpacing(3)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(6, 0, 6, 0)
        self.collectionRadioButton = QRadioButton(self.searchDockWidgetContents)
        self.buttonGroup = QButtonGroup(RelicMainWindow)
        self.buttonGroup.setObjectName(u"buttonGroup")
        self.buttonGroup.addButton(self.collectionRadioButton)
        self.collectionRadioButton.setObjectName(u"collectionRadioButton")
        self.collectionRadioButton.setMaximumSize(QSize(16777215, 16))
        icon7 = QIcon()
        icon7.addFile(u":/resources/asset_types/collection.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.collectionRadioButton.setIcon(icon7)
        self.collectionRadioButton.setChecked(True)

        self.verticalLayout_4.addWidget(self.collectionRadioButton)

        self.variationRadioButton = QRadioButton(self.searchDockWidgetContents)
        self.buttonGroup.addButton(self.variationRadioButton)
        self.variationRadioButton.setObjectName(u"variationRadioButton")
        sizePolicy4 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.variationRadioButton.sizePolicy().hasHeightForWidth())
        self.variationRadioButton.setSizePolicy(sizePolicy4)
        self.variationRadioButton.setMaximumSize(QSize(16777215, 16))
        self.variationRadioButton.setBaseSize(QSize(0, 0))
        icon8 = QIcon()
        icon8.addFile(u":/resources/asset_types/variant.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.variationRadioButton.setIcon(icon8)

        self.verticalLayout_4.addWidget(self.variationRadioButton)


        self.gridLayout.addLayout(self.verticalLayout_4, 0, 4, 1, 1)

        self.line_3 = QFrame(self.searchDockWidgetContents)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.HLine)
        self.line_3.setFrameShadow(QFrame.Sunken)

        self.gridLayout.addWidget(self.line_3, 1, 0, 1, 1)

        self.line_7 = QFrame(self.searchDockWidgetContents)
        self.line_7.setObjectName(u"line_7")
        self.line_7.setFrameShape(QFrame.HLine)
        self.line_7.setFrameShadow(QFrame.Sunken)

        self.gridLayout.addWidget(self.line_7, 1, 4, 1, 1)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_2, 0, 5, 1, 1)

        self.line = QFrame(self.searchDockWidgetContents)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.gridLayout.addWidget(self.line, 1, 2, 1, 1)

        self.searchFrame = QFrame(self.searchDockWidgetContents)
        self.searchFrame.setObjectName(u"searchFrame")
        sizePolicy3.setHeightForWidth(self.searchFrame.sizePolicy().hasHeightForWidth())
        self.searchFrame.setSizePolicy(sizePolicy3)
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
        self.horizontalLayout.setContentsMargins(9, 9, 9, 9)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.searchButton = QPushButton(self.searchFrame)
        self.searchButton.setObjectName(u"searchButton")
        self.searchButton.setStyleSheet(u"QPushButton {\n"
"    background-color: rgb(43, 43, 43);\n"
"    padding: 2px;\n"
"	border: none;\n"
"}")
        self.searchButton.setIcon(icon3)
        self.searchButton.setIconSize(QSize(20, 20))
        self.searchButton.setFlat(False)

        self.horizontalLayout.addWidget(self.searchButton)

        self.searchBox = QLineEdit(self.searchFrame)
        self.searchBox.setObjectName(u"searchBox")
        sizePolicy5 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.searchBox.sizePolicy().hasHeightForWidth())
        self.searchBox.setSizePolicy(sizePolicy5)
        self.searchBox.setMinimumSize(QSize(256, 26))
        font2 = QFont()
        font2.setBold(True)
        self.searchBox.setFont(font2)
        self.searchBox.setFrame(False)
        self.searchBox.setClearButtonEnabled(True)

        self.horizontalLayout.addWidget(self.searchBox)


        self.gridLayout.addWidget(self.searchFrame, 0, 2, 1, 1)

        self.searchDock.setWidget(self.searchDockWidgetContents)
        RelicMainWindow.addDockWidget(Qt.TopDockWidgetArea, self.searchDock)
        self.attributeDock = QDockWidget(RelicMainWindow)
        self.attributeDock.setObjectName(u"attributeDock")
        palette1 = QPalette()
        palette1.setBrush(QPalette.Active, QPalette.WindowText, brush)
        palette1.setBrush(QPalette.Active, QPalette.Button, brush1)
        palette1.setBrush(QPalette.Active, QPalette.Text, brush)
        palette1.setBrush(QPalette.Active, QPalette.ButtonText, brush)
        palette1.setBrush(QPalette.Active, QPalette.Base, brush1)
        palette1.setBrush(QPalette.Active, QPalette.Window, brush1)
        palette1.setBrush(QPalette.Active, QPalette.Highlight, brush2)
        palette1.setBrush(QPalette.Active, QPalette.HighlightedText, brush3)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette1.setBrush(QPalette.Active, QPalette.PlaceholderText, brush)
#endif
        palette1.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        palette1.setBrush(QPalette.Inactive, QPalette.Button, brush1)
        palette1.setBrush(QPalette.Inactive, QPalette.Text, brush)
        palette1.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
        palette1.setBrush(QPalette.Inactive, QPalette.Base, brush1)
        palette1.setBrush(QPalette.Inactive, QPalette.Window, brush1)
        palette1.setBrush(QPalette.Inactive, QPalette.Highlight, brush2)
        palette1.setBrush(QPalette.Inactive, QPalette.HighlightedText, brush3)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette1.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush)
#endif
        palette1.setBrush(QPalette.Disabled, QPalette.WindowText, brush4)
        palette1.setBrush(QPalette.Disabled, QPalette.Button, brush5)
        palette1.setBrush(QPalette.Disabled, QPalette.Text, brush4)
        palette1.setBrush(QPalette.Disabled, QPalette.ButtonText, brush4)
        palette1.setBrush(QPalette.Disabled, QPalette.Base, brush5)
        palette1.setBrush(QPalette.Disabled, QPalette.Window, brush5)
        palette1.setBrush(QPalette.Disabled, QPalette.Highlight, brush2)
        palette1.setBrush(QPalette.Disabled, QPalette.HighlightedText, brush3)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette1.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush4)
#endif
        self.attributeDock.setPalette(palette1)
        self.attributeDock.setFeatures(QDockWidget.DockWidgetFloatable|QDockWidget.DockWidgetMovable)
        self.attrDockWidgetContents = QWidget()
        self.attrDockWidgetContents.setObjectName(u"attrDockWidgetContents")
        self.verticalLayout_3 = QVBoxLayout(self.attrDockWidgetContents)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setContentsMargins(9, 9, 9, 9)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(1, 1, 1, 1)
        self.scrollArea = QScrollArea(self.attrDockWidgetContents)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setMinimumSize(QSize(355, 0))
        self.scrollArea.setAutoFillBackground(True)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 353, 401))
        self.attributesLayout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.attributesLayout.setSpacing(0)
        self.attributesLayout.setContentsMargins(9, 9, 9, 9)
        self.attributesLayout.setObjectName(u"attributesLayout")
        self.attributesLayout.setContentsMargins(0, 0, 0, 0)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout_3.addWidget(self.scrollArea)

        self.attributeDock.setWidget(self.attrDockWidgetContents)
        RelicMainWindow.addDockWidget(Qt.RightDockWidgetArea, self.attributeDock)
        self.statusbar = QStatusBar(RelicMainWindow)
        self.statusbar.setObjectName(u"statusbar")
        self.statusbar.setSizeGripEnabled(True)
        RelicMainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.menuFile.addAction(self.actionIngest)
        self.menuFile.addAction(self.actionExit)
        self.menuEdit.addAction(self.actionAdministration_Mode)
        self.menuEdit.addAction(self.actionPreferences)
        self.menuHelp.addAction(self.actionDocumentation)
        self.menuHelp.addAction(self.actionReconnect)
        self.menuView.addAction(self.actionPortal)
        self.menuView.addAction(self.actionRecurseSubcategory)

        self.retranslateUi(RelicMainWindow)
        self.actionAdministration_Mode.toggled.connect(RelicMainWindow.toggleAdminMode)
        self.actionExit.triggered.connect(RelicMainWindow.close)
        self.pageDownButton.clicked.connect(self.pageSpinBox.stepDown)
        self.pageUpButton.clicked.connect(self.pageSpinBox.stepUp)

        QMetaObject.connectSlotsByName(RelicMainWindow)
    # setupUi

    def retranslateUi(self, RelicMainWindow):
        RelicMainWindow.setWindowTitle(QCoreApplication.translate("RelicMainWindow", u"Relic", None))
        self.actionPreferences.setText(QCoreApplication.translate("RelicMainWindow", u"Preferences", None))
        self.actionExit.setText(QCoreApplication.translate("RelicMainWindow", u"Exit", None))
        self.actionAdministration_Mode.setText(QCoreApplication.translate("RelicMainWindow", u"Administration Mode", None))
        self.actionDocumentation.setText(QCoreApplication.translate("RelicMainWindow", u"Documentation", None))
        self.actionIngest.setText(QCoreApplication.translate("RelicMainWindow", u"Ingest", None))
        self.actionPortal.setText(QCoreApplication.translate("RelicMainWindow", u"Portal", None))
#if QT_CONFIG(statustip)
        self.actionPortal.setStatusTip(QCoreApplication.translate("RelicMainWindow", u"Collapse / Expand the Categories and Attributes panels.", None))
#endif // QT_CONFIG(statustip)
#if QT_CONFIG(shortcut)
        self.actionPortal.setShortcut(QCoreApplication.translate("RelicMainWindow", u"Ctrl+Tab", None))
#endif // QT_CONFIG(shortcut)
        self.actionRecurseSubcategory.setText(QCoreApplication.translate("RelicMainWindow", u"Recursive Subcategory Selection", None))
#if QT_CONFIG(tooltip)
        self.actionRecurseSubcategory.setToolTip(QCoreApplication.translate("RelicMainWindow", u"Use the selected Subcategories child-items in the active selection filter. (Enable Recursive Loading)", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.actionRecurseSubcategory.setStatusTip(QCoreApplication.translate("RelicMainWindow", u"Use the selected Subcategories child-items in the active selection filter. (Enable Recursive Loading)", None))
#endif // QT_CONFIG(statustip)
        self.actionReconnect.setText(QCoreApplication.translate("RelicMainWindow", u"Reconnect", None))
        self.searchButton_2.setText("")
        self.label.setText(QCoreApplication.translate("RelicMainWindow", u"Search Yielded No Results...", None))
        self.clearSubcategoryButton.setText(QCoreApplication.translate("RelicMainWindow", u"Clear Subcategory Selection", None))
        self.label_4.setText(QCoreApplication.translate("RelicMainWindow", u"OR", None))
        self.clearSearchButton.setText(QCoreApplication.translate("RelicMainWindow", u"Clear Search Keywords", None))
        self.linksDock.setWindowTitle(QCoreApplication.translate("RelicMainWindow", u"Links", None))
        self.viewScaleLabel.setText(QCoreApplication.translate("RelicMainWindow", u"Scale :", None))
        self.previewCheckBox.setText(QCoreApplication.translate("RelicMainWindow", u"Preview On-Select", None))
        self.pageSpinBox.setSuffix(QCoreApplication.translate("RelicMainWindow", u"/ 4", None))
        self.pageSpinBox.setPrefix(QCoreApplication.translate("RelicMainWindow", u"Page ", None))
        self.menuFile.setTitle(QCoreApplication.translate("RelicMainWindow", u"File", None))
        self.menuEdit.setTitle(QCoreApplication.translate("RelicMainWindow", u"Edit", None))
        self.menuHelp.setTitle(QCoreApplication.translate("RelicMainWindow", u"Help", None))
        self.menuView.setTitle(QCoreApplication.translate("RelicMainWindow", u"View", None))
        self.categoryDock.setWindowTitle(QCoreApplication.translate("RelicMainWindow", u"Categories", None))
        self.searchDock.setWindowTitle(QCoreApplication.translate("RelicMainWindow", u"Search", None))
        self.collectionRadioButton.setText(QCoreApplication.translate("RelicMainWindow", u"Collections", None))
        self.variationRadioButton.setText(QCoreApplication.translate("RelicMainWindow", u"Variations", None))
        self.searchButton.setText("")
        self.searchBox.setPlaceholderText(QCoreApplication.translate("RelicMainWindow", u"Search...", None))
        self.attributeDock.setWindowTitle(QCoreApplication.translate("RelicMainWindow", u"Attributes", None))
#if QT_CONFIG(statustip)
        self.statusbar.setStatusTip("")
#endif // QT_CONFIG(statustip)
    # retranslateUi

