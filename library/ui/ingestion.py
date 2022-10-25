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
from library.widgets.util import AssetNameListView
import resources_rc

class Ui_IngestForm(object):
    def setupUi(self, IngestForm):
        if not IngestForm.objectName():
            IngestForm.setObjectName(u"IngestForm")
        IngestForm.resize(866, 558)
        self.verticalLayout_3 = QVBoxLayout(IngestForm)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.frame_2 = QFrame(IngestForm)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.frame_2)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(-1, 0, -1, 0)
        self.ingestTabWidget = QTabWidget(self.frame_2)
        self.ingestTabWidget.setObjectName(u"ingestTabWidget")
        self.ingestTabWidget.setEnabled(True)
        self.ingestTabWidget.setStyleSheet(u"QTabBar,\n"
"QTabWidget,\n"
"QStackedWidget {background-color: rgb(72, 72, 72);}")
        self.collectTab = QWidget()
        self.collectTab.setObjectName(u"collectTab")
        self.collectTab.setStyleSheet(u"QFrame,\n"
"QWidget {background-color: rgb(72, 72, 72);}")
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
        self.gridLayout.setVerticalSpacing(6)
        self.gridLayout.setContentsMargins(9, 0, 9, 0)
        self.documentsLabel = QLabel(self.collectTab)
        self.documentsLabel.setObjectName(u"documentsLabel")
        font = QFont()
        font.setBold(True)
        self.documentsLabel.setFont(font)
        self.documentsLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.documentsLabel, 8, 0, 1, 1)

        self.texturesReferencesCheckBox = QCheckBox(self.collectTab)
        self.texturesReferencesCheckBox.setObjectName(u"texturesReferencesCheckBox")
        self.texturesReferencesCheckBox.setChecked(True)

        self.gridLayout.addWidget(self.texturesReferencesCheckBox, 3, 1, 1, 1)

        self.texturesReferencesLabel = QLabel(self.collectTab)
        self.texturesReferencesLabel.setObjectName(u"texturesReferencesLabel")
        self.texturesReferencesLabel.setFont(font)
        self.texturesReferencesLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.texturesReferencesLabel, 3, 0, 1, 1)

        self.rawLabel = QLabel(self.collectTab)
        self.rawLabel.setObjectName(u"rawLabel")
        self.rawLabel.setFont(font)
        self.rawLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.rawLabel, 4, 0, 1, 1)

        self.lightsLabel = QLabel(self.collectTab)
        self.lightsLabel.setObjectName(u"lightsLabel")
        self.lightsLabel.setFont(font)
        self.lightsLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.lightsLabel, 7, 0, 1, 1)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer_2, 10, 0, 1, 1)

        self.moviesCheckBox = QCheckBox(self.collectTab)
        self.moviesCheckBox.setObjectName(u"moviesCheckBox")

        self.gridLayout.addWidget(self.moviesCheckBox, 5, 1, 1, 1)

        self.lightsCheckBox = QCheckBox(self.collectTab)
        self.lightsCheckBox.setObjectName(u"lightsCheckBox")

        self.gridLayout.addWidget(self.lightsCheckBox, 7, 1, 1, 1)

        self.rawCheckBox = QCheckBox(self.collectTab)
        self.rawCheckBox.setObjectName(u"rawCheckBox")
        self.rawCheckBox.setEnabled(True)
        self.rawCheckBox.setChecked(False)

        self.gridLayout.addWidget(self.rawCheckBox, 4, 1, 1, 1)

        self.toolsLabel = QLabel(self.collectTab)
        self.toolsLabel.setObjectName(u"toolsLabel")
        self.toolsLabel.setFont(font)
        self.toolsLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.toolsLabel, 6, 0, 1, 1)

        self.title_line = QFrame(self.collectTab)
        self.title_line.setObjectName(u"title_line")
        self.title_line.setFrameShape(QFrame.HLine)
        self.title_line.setFrameShadow(QFrame.Sunken)

        self.gridLayout.addWidget(self.title_line, 1, 0, 1, 1)

        self.documentsCheckBox = QCheckBox(self.collectTab)
        self.documentsCheckBox.setObjectName(u"documentsCheckBox")

        self.gridLayout.addWidget(self.documentsCheckBox, 8, 1, 1, 1)

        self.moviesLabel = QLabel(self.collectTab)
        self.moviesLabel.setObjectName(u"moviesLabel")
        self.moviesLabel.setFont(font)
        self.moviesLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.moviesLabel, 5, 0, 1, 1)

        self.filteringTitleLabel = QLabel(self.collectTab)
        self.filteringTitleLabel.setObjectName(u"filteringTitleLabel")
        font1 = QFont()
        font1.setPointSize(10)
        font1.setBold(True)
        font1.setUnderline(False)
        font1.setKerning(True)
        self.filteringTitleLabel.setFont(font1)

        self.gridLayout.addWidget(self.filteringTitleLabel, 0, 0, 1, 1)

        self.toolsCheckBox = QCheckBox(self.collectTab)
        self.toolsCheckBox.setObjectName(u"toolsCheckBox")

        self.gridLayout.addWidget(self.toolsCheckBox, 6, 1, 1, 1)

        self.scenesCheckBox = QCheckBox(self.collectTab)
        self.scenesCheckBox.setObjectName(u"scenesCheckBox")

        self.gridLayout.addWidget(self.scenesCheckBox, 2, 1, 1, 1)

        self.scenesLabel = QLabel(self.collectTab)
        self.scenesLabel.setObjectName(u"scenesLabel")
        self.scenesLabel.setFont(font)
        self.scenesLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.scenesLabel, 2, 0, 1, 1)


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
        font2 = QFont()
        font2.setPointSize(9)
        font2.setBold(True)
        font2.setUnderline(False)
        font2.setKerning(True)
        self.label_7.setFont(font2)

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

        self.ingestTabWidget.addTab(self.collectTab, "")
        self.categorizeTab = QWidget()
        self.categorizeTab.setObjectName(u"categorizeTab")
        self.categorizeTab.setEnabled(False)
        font3 = QFont()
        font3.setUnderline(False)
        font3.setKerning(True)
        self.categorizeTab.setFont(font3)
        self.horizontalLayout = QHBoxLayout(self.categorizeTab)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(6, -1, 6, 6)
        self.collected_frame = QFrame(self.categorizeTab)
        self.collected_frame.setObjectName(u"collected_frame")
        self.collected_frame.setStyleSheet(u"QFrame#collected_subframe,\n"
"QFrame#collected_frame {background-color: rgb(72, 72, 72);}")
        self.collected_frame.setFrameShape(QFrame.StyledPanel)
        self.collected_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout = QVBoxLayout(self.collected_frame)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(-1, 0, -1, 0)
        self.collected_subframe = QFrame(self.collected_frame)
        self.collected_subframe.setObjectName(u"collected_subframe")
        self.collected_subframe.setFrameShape(QFrame.StyledPanel)
        self.collected_subframe.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_7 = QHBoxLayout(self.collected_subframe)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.loadingLabel = QLabel(self.collected_subframe)
        self.loadingLabel.setObjectName(u"loadingLabel")
        self.loadingLabel.setPixmap(QPixmap(u":/app/load_wheel_24.webp"))

        self.horizontalLayout_7.addWidget(self.loadingLabel)

        self.completedLabel = QLabel(self.collected_subframe)
        self.completedLabel.setObjectName(u"completedLabel")
        self.completedLabel.setPixmap(QPixmap(u":/app/check_green.png"))

        self.horizontalLayout_7.addWidget(self.completedLabel)

        self.collectedLabel = QLabel(self.collected_subframe)
        self.collectedLabel.setObjectName(u"collectedLabel")
        font4 = QFont()
        font4.setPointSize(12)
        font4.setBold(False)
        font4.setUnderline(False)
        font4.setKerning(True)
        self.collectedLabel.setFont(font4)

        self.horizontalLayout_7.addWidget(self.collectedLabel)

        self.horizontalSpacer_4 = QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_4)


        self.verticalLayout.addWidget(self.collected_subframe)

        self.line_2 = QFrame(self.collected_frame)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.HLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.verticalLayout.addWidget(self.line_2)

        self.collectedListView = AssetListView(self.collected_frame)
        self.collectedListView.setObjectName(u"collectedListView")
        self.collectedListView.setStyleSheet(u"QWidget#collectedListView {\n"
"background-color: rgb(72, 72, 72);\n"
"border: none;\n"
"}")
        self.collectedListView.setFrameShape(QFrame.NoFrame)
        self.collectedListView.setResizeMode(QListView.Adjust)
        self.collectedListView.setUniformItemSizes(True)
        self.collectedListView.setWordWrap(True)
        self.collectedListView.setSelectionRectVisible(True)

        self.verticalLayout.addWidget(self.collectedListView)


        self.horizontalLayout.addWidget(self.collected_frame)

        self.line = QFrame(self.categorizeTab)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.VLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout.addWidget(self.line)

        self.categorizeFrame = QFrame(self.categorizeTab)
        self.categorizeFrame.setObjectName(u"categorizeFrame")
        self.categorizeFrame.setFont(font3)
        self.categorizeFrame.setStyleSheet(u"QFrame#categorizeFrame {background-color: rgb(72, 72, 72);}\n"
"")
        self.categorizeFrame.setFrameShape(QFrame.StyledPanel)
        self.categorizeFrame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_5 = QVBoxLayout(self.categorizeFrame)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(6, 0, 6, 0)
        self.label_4 = QLabel(self.categorizeFrame)
        self.label_4.setObjectName(u"label_4")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy)
        self.label_4.setFont(font4)

        self.verticalLayout_5.addWidget(self.label_4)

        self.line_3 = QFrame(self.categorizeFrame)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.HLine)
        self.line_3.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_5.addWidget(self.line_3)

        self.label_5 = QLabel(self.categorizeFrame)
        self.label_5.setObjectName(u"label_5")
        font5 = QFont()
        font5.setPointSize(8)
        font5.setUnderline(False)
        font5.setKerning(True)
        self.label_5.setFont(font5)

        self.verticalLayout_5.addWidget(self.label_5)

        self.existingNamesList = AssetNameListView(self.categorizeFrame)
        self.existingNamesList.setObjectName(u"existingNamesList")
        self.existingNamesList.setFont(font3)

        self.verticalLayout_5.addWidget(self.existingNamesList)


        self.horizontalLayout.addWidget(self.categorizeFrame)

        self.line_5 = QFrame(self.categorizeTab)
        self.line_5.setObjectName(u"line_5")
        self.line_5.setFrameShape(QFrame.VLine)
        self.line_5.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout.addWidget(self.line_5)

        self.processed_frame = QFrame(self.categorizeTab)
        self.processed_frame.setObjectName(u"processed_frame")
        self.processed_frame.setStyleSheet(u"QFrame#processed_subframe,\n"
"QFrame#processed_frame {background-color: rgb(72, 72, 72);}\n"
"")
        self.processed_frame.setFrameShape(QFrame.StyledPanel)
        self.processed_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_6 = QVBoxLayout(self.processed_frame)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(-1, 0, -1, 0)
        self.processed_subframe = QFrame(self.processed_frame)
        self.processed_subframe.setObjectName(u"processed_subframe")
        self.processed_subframe.setFrameShape(QFrame.StyledPanel)
        self.processed_subframe.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_8 = QHBoxLayout(self.processed_subframe)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.processLoadingLabel = QLabel(self.processed_subframe)
        self.processLoadingLabel.setObjectName(u"processLoadingLabel")
        self.processLoadingLabel.setPixmap(QPixmap(u":/app/load_wheel_24.webp"))

        self.horizontalLayout_8.addWidget(self.processLoadingLabel)

        self.processCompleteLabel = QLabel(self.processed_subframe)
        self.processCompleteLabel.setObjectName(u"processCompleteLabel")
        self.processCompleteLabel.setPixmap(QPixmap(u":/app/check_green.png"))

        self.horizontalLayout_8.addWidget(self.processCompleteLabel)

        self.newAssetsLabel = QLabel(self.processed_subframe)
        self.newAssetsLabel.setObjectName(u"newAssetsLabel")
        self.newAssetsLabel.setFont(font4)

        self.horizontalLayout_8.addWidget(self.newAssetsLabel)

        self.horizontalSpacer_5 = QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_8.addItem(self.horizontalSpacer_5)


        self.verticalLayout_6.addWidget(self.processed_subframe)

        self.line_4 = QFrame(self.processed_frame)
        self.line_4.setObjectName(u"line_4")
        self.line_4.setFrameShape(QFrame.HLine)
        self.line_4.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_6.addWidget(self.line_4)

        self.newAssetListView = AssetListView(self.processed_frame)
        self.newAssetListView.setObjectName(u"newAssetListView")
        self.newAssetListView.setStyleSheet(u"QWidget#newAssetListView {\n"
"background-color: rgb(72, 72, 72);\n"
"border: none;\n"
"}")
        self.newAssetListView.setFrameShape(QFrame.NoFrame)
        self.newAssetListView.setResizeMode(QListView.Adjust)
        self.newAssetListView.setUniformItemSizes(True)
        self.newAssetListView.setWordWrap(True)
        self.newAssetListView.setSelectionRectVisible(True)

        self.verticalLayout_6.addWidget(self.newAssetListView)


        self.horizontalLayout.addWidget(self.processed_frame)

        self.ingestTabWidget.addTab(self.categorizeTab, "")

        self.verticalLayout_2.addWidget(self.ingestTabWidget)


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

        self.ingestTabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(IngestForm)
    # setupUi

    def retranslateUi(self, IngestForm):
        IngestForm.setWindowTitle(QCoreApplication.translate("IngestForm", u"Form", None))
        self.collectPathTextEdit.setPlaceholderText(QCoreApplication.translate("IngestForm", u"Insert paths or urls here...", None))
        self.documentsLabel.setText(QCoreApplication.translate("IngestForm", u"Documents :", None))
        self.texturesReferencesCheckBox.setText(QCoreApplication.translate("IngestForm", u" [ .tif, .jpg, .png ]", None))
        self.texturesReferencesLabel.setText(QCoreApplication.translate("IngestForm", u"Reference Images :", None))
        self.rawLabel.setText(QCoreApplication.translate("IngestForm", u"Camera Raw :", None))
        self.lightsLabel.setText(QCoreApplication.translate("IngestForm", u"Lights :", None))
        self.moviesCheckBox.setText(QCoreApplication.translate("IngestForm", u" [ .mov, .mp4, .mxf ]", None))
        self.lightsCheckBox.setText(QCoreApplication.translate("IngestForm", u" [ .ies ]", None))
        self.rawCheckBox.setText(QCoreApplication.translate("IngestForm", u" [ .cr2, .dng, .r3d ]", None))
        self.toolsLabel.setText(QCoreApplication.translate("IngestForm", u"Tools :", None))
        self.documentsCheckBox.setText(QCoreApplication.translate("IngestForm", u" [ .md ]", None))
        self.moviesLabel.setText(QCoreApplication.translate("IngestForm", u"Movies :", None))
        self.filteringTitleLabel.setText(QCoreApplication.translate("IngestForm", u"File Types Filtering", None))
        self.toolsCheckBox.setText(QCoreApplication.translate("IngestForm", u" [ .py, .exe, .nk ]", None))
        self.scenesCheckBox.setText(QCoreApplication.translate("IngestForm", u" [ .ma, .usd, .gltf ]", None))
        self.scenesLabel.setText(QCoreApplication.translate("IngestForm", u"Scenes :", None))
        self.label_7.setText(QCoreApplication.translate("IngestForm", u"Advanced", None))
        self.copyCheckBox.setText("")
        self.copyLabel.setText(QCoreApplication.translate("IngestForm", u"Copy Assets", None))
        self.texturesReferencesLabel_2.setText(QCoreApplication.translate("IngestForm", u"Categorize Using Parent Folder", None))
        self.texturesReferencesCheckBox_2.setText("")
        self.ingestTabWidget.setTabText(self.ingestTabWidget.indexOf(self.collectTab), QCoreApplication.translate("IngestForm", u"Collection", None))
        self.loadingLabel.setText("")
        self.completedLabel.setText("")
        self.collectedLabel.setText(QCoreApplication.translate("IngestForm", u"Collected : 0/0 ", None))
        self.label_4.setText(QCoreApplication.translate("IngestForm", u"Naming :", None))
        self.label_5.setText(QCoreApplication.translate("IngestForm", u" Provide a new name or re-use an existing name from the list below.", None))
        self.processLoadingLabel.setText("")
        self.processCompleteLabel.setText("")
        self.newAssetsLabel.setText(QCoreApplication.translate("IngestForm", u"Processed : 0/0", None))
        self.ingestTabWidget.setTabText(self.ingestTabWidget.indexOf(self.categorizeTab), QCoreApplication.translate("IngestForm", u"Ingestion", None))
        self.nextButton.setText(QCoreApplication.translate("IngestForm", u"Next", None))
        self.cancelButton.setText(QCoreApplication.translate("IngestForm", u"Cancel", None))
    # retranslateUi

