# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.2.2
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QGroupBox,
    QHBoxLayout, QLineEdit, QListView, QSizePolicy,
    QToolBox, QToolButton, QVBoxLayout, QWidget)
import resources_rc

class Ui_ScreenCapture(object):
    def setupUi(self, ScreenCapture):
        if not ScreenCapture.objectName():
            ScreenCapture.setObjectName(u"ScreenCapture")
        ScreenCapture.resize(217, 384)
        icon = QIcon()
        icon.addFile(u":/resources/icons/app_icon.svg", QSize(), QIcon.Normal, QIcon.Off)
        ScreenCapture.setWindowIcon(icon)
        ScreenCapture.setStyleSheet(u"")
        self.actionOpen_File_Location = QAction(ScreenCapture)
        self.actionOpen_File_Location.setObjectName(u"actionOpen_File_Location")
        icon1 = QIcon()
        icon1.addFile(u":/resources/icons/folder.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.actionOpen_File_Location.setIcon(icon1)
        self.actionConvert_To_GIF = QAction(ScreenCapture)
        self.actionConvert_To_GIF.setObjectName(u"actionConvert_To_GIF")
        icon2 = QIcon()
        icon2.addFile(u":/resources/icons/gif.png", QSize(), QIcon.Normal, QIcon.Off)
        self.actionConvert_To_GIF.setIcon(icon2)
        self.actionRename = QAction(ScreenCapture)
        self.actionRename.setObjectName(u"actionRename")
        self.actionDelete = QAction(ScreenCapture)
        self.actionDelete.setObjectName(u"actionDelete")
        self.actionConvert_To_WEBP = QAction(ScreenCapture)
        self.actionConvert_To_WEBP.setObjectName(u"actionConvert_To_WEBP")
        self.verticalLayout = QVBoxLayout(ScreenCapture)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(6, 6, 6, 6)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.captureButton = QToolButton(ScreenCapture)
        self.captureButton.setObjectName(u"captureButton")
        icon3 = QIcon()
        icon3.addFile(u":/resources/icons/snapshot.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.captureButton.setIcon(icon3)
        self.captureButton.setIconSize(QSize(24, 24))
        self.captureButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        self.horizontalLayout.addWidget(self.captureButton)

        self.recordButton = QToolButton(ScreenCapture)
        self.recordButton.setObjectName(u"recordButton")
        icon4 = QIcon()
        icon4.addFile(u":/resources/icons/rec.png", QSize(), QIcon.Normal, QIcon.Off)
        icon4.addFile(u":/resources/icons/stop.png", QSize(), QIcon.Active, QIcon.On)
        self.recordButton.setIcon(icon4)
        self.recordButton.setIconSize(QSize(24, 24))
        self.recordButton.setCheckable(True)
        self.recordButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        self.horizontalLayout.addWidget(self.recordButton)

        self.delayComboBox = QComboBox(ScreenCapture)
        icon5 = QIcon()
        icon5.addFile(u":/resources/icons/timer.png", QSize(), QIcon.Normal, QIcon.Off)
        self.delayComboBox.addItem(icon5, "")
        self.delayComboBox.addItem(icon5, "")
        self.delayComboBox.addItem(icon5, "")
        self.delayComboBox.addItem(icon5, "")
        self.delayComboBox.setObjectName(u"delayComboBox")
        self.delayComboBox.setIconSize(QSize(16, 16))

        self.horizontalLayout.addWidget(self.delayComboBox)

        self.expandButton = QToolButton(ScreenCapture)
        self.expandButton.setObjectName(u"expandButton")
        icon6 = QIcon()
        icon6.addFile(u":/resources/icons/narrowLeft.png", QSize(), QIcon.Normal, QIcon.Off)
        icon6.addFile(u":/resources/icons/narrowDown.png", QSize(), QIcon.Active, QIcon.On)
        self.expandButton.setIcon(icon6)
        self.expandButton.setCheckable(True)
        self.expandButton.setChecked(True)
        self.expandButton.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.expandButton.setArrowType(Qt.NoArrow)

        self.horizontalLayout.addWidget(self.expandButton)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.historyGroupBox = QGroupBox(ScreenCapture)
        self.historyGroupBox.setObjectName(u"historyGroupBox")
        self.verticalLayout_5 = QVBoxLayout(self.historyGroupBox)
        self.verticalLayout_5.setSpacing(6)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(6, 6, 6, 6)
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(3)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(3, 3, 3, 3)
        self.searchButton = QToolButton(self.historyGroupBox)
        self.searchButton.setObjectName(u"searchButton")
        icon7 = QIcon()
        icon7.addFile(u":/resources/icons/search.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.searchButton.setIcon(icon7)
        self.searchButton.setIconSize(QSize(20, 20))

        self.horizontalLayout_2.addWidget(self.searchButton)

        self.searchLine = QLineEdit(self.historyGroupBox)
        self.searchLine.setObjectName(u"searchLine")
        self.searchLine.setClearButtonEnabled(True)

        self.horizontalLayout_2.addWidget(self.searchLine)


        self.verticalLayout_5.addLayout(self.horizontalLayout_2)

        self.toolBox = QToolBox(self.historyGroupBox)
        self.toolBox.setObjectName(u"toolBox")
        self.page = QWidget()
        self.page.setObjectName(u"page")
        self.page.setGeometry(QRect(0, 0, 191, 168))
        self.verticalLayout_2 = QVBoxLayout(self.page)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.screenshotListView = QListView(self.page)
        self.screenshotListView.setObjectName(u"screenshotListView")
        self.screenshotListView.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.screenshotListView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.screenshotListView.setDragEnabled(True)
        self.screenshotListView.setDragDropMode(QAbstractItemView.DragOnly)
        self.screenshotListView.setAlternatingRowColors(False)
        self.screenshotListView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.screenshotListView.setIconSize(QSize(128, 128))
        self.screenshotListView.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.screenshotListView.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.screenshotListView.setFlow(QListView.LeftToRight)
        self.screenshotListView.setProperty("isWrapping", True)
        self.screenshotListView.setResizeMode(QListView.Adjust)
        self.screenshotListView.setLayoutMode(QListView.Batched)
        self.screenshotListView.setSpacing(6)
        self.screenshotListView.setViewMode(QListView.ListMode)
        self.screenshotListView.setUniformItemSizes(True)
        self.screenshotListView.setSelectionRectVisible(True)

        self.verticalLayout_2.addWidget(self.screenshotListView)

        self.toolBox.addItem(self.page, icon3, u"Screenshots")
        self.page_2 = QWidget()
        self.page_2.setObjectName(u"page_2")
        self.page_2.setGeometry(QRect(0, 0, 191, 168))
        self.verticalLayout_3 = QVBoxLayout(self.page_2)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.videosListView = QListView(self.page_2)
        self.videosListView.setObjectName(u"videosListView")
        self.videosListView.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.videosListView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.videosListView.setDragEnabled(True)
        self.videosListView.setDragDropMode(QAbstractItemView.DragDrop)
        self.videosListView.setAlternatingRowColors(False)
        self.videosListView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.videosListView.setIconSize(QSize(128, 128))
        self.videosListView.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.videosListView.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.videosListView.setFlow(QListView.LeftToRight)
        self.videosListView.setProperty("isWrapping", True)
        self.videosListView.setResizeMode(QListView.Adjust)
        self.videosListView.setLayoutMode(QListView.Batched)
        self.videosListView.setSpacing(6)
        self.videosListView.setViewMode(QListView.ListMode)
        self.videosListView.setUniformItemSizes(True)
        self.videosListView.setSelectionRectVisible(True)

        self.verticalLayout_3.addWidget(self.videosListView)

        icon8 = QIcon()
        icon8.addFile(u":/resources/icons/video96.png", QSize(), QIcon.Normal, QIcon.Off)
        self.toolBox.addItem(self.page_2, icon8, u"Videos")
        self.page_3 = QWidget()
        self.page_3.setObjectName(u"page_3")
        self.page_3.setGeometry(QRect(0, 0, 191, 168))
        self.verticalLayout_4 = QVBoxLayout(self.page_3)
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.gifListView = QListView(self.page_3)
        self.gifListView.setObjectName(u"gifListView")
        self.gifListView.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.gifListView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.gifListView.setDragEnabled(True)
        self.gifListView.setDragDropMode(QAbstractItemView.DragOnly)
        self.gifListView.setAlternatingRowColors(False)
        self.gifListView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.gifListView.setIconSize(QSize(128, 128))
        self.gifListView.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.gifListView.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.gifListView.setFlow(QListView.LeftToRight)
        self.gifListView.setProperty("isWrapping", True)
        self.gifListView.setResizeMode(QListView.Adjust)
        self.gifListView.setLayoutMode(QListView.Batched)
        self.gifListView.setSpacing(6)
        self.gifListView.setViewMode(QListView.ListMode)
        self.gifListView.setUniformItemSizes(True)
        self.gifListView.setSelectionRectVisible(True)

        self.verticalLayout_4.addWidget(self.gifListView)

        self.toolBox.addItem(self.page_3, icon2, u"Animated")

        self.verticalLayout_5.addWidget(self.toolBox)


        self.verticalLayout.addWidget(self.historyGroupBox)


        self.retranslateUi(ScreenCapture)
        self.expandButton.toggled.connect(self.historyGroupBox.setVisible)

        self.toolBox.setCurrentIndex(1)
        self.toolBox.layout().setSpacing(2)


        QMetaObject.connectSlotsByName(ScreenCapture)
    # setupUi

    def retranslateUi(self, ScreenCapture):
        ScreenCapture.setWindowTitle(QCoreApplication.translate("ScreenCapture", u"Screen Capture", None))
        self.actionOpen_File_Location.setText(QCoreApplication.translate("ScreenCapture", u"Open File Location", None))
#if QT_CONFIG(tooltip)
        self.actionOpen_File_Location.setToolTip(QCoreApplication.translate("ScreenCapture", u"Opens the on-disk file location in explorer.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(shortcut)
        self.actionOpen_File_Location.setShortcut(QCoreApplication.translate("ScreenCapture", u"Ctrl+O", None))
#endif // QT_CONFIG(shortcut)
        self.actionConvert_To_GIF.setText(QCoreApplication.translate("ScreenCapture", u"Convert To GIF", None))
#if QT_CONFIG(tooltip)
        self.actionConvert_To_GIF.setToolTip(QCoreApplication.translate("ScreenCapture", u"Converts this video to an animated GIF.", None))
#endif // QT_CONFIG(tooltip)
        self.actionRename.setText(QCoreApplication.translate("ScreenCapture", u"Rename", None))
        self.actionDelete.setText(QCoreApplication.translate("ScreenCapture", u"Delete", None))
#if QT_CONFIG(tooltip)
        self.actionDelete.setToolTip(QCoreApplication.translate("ScreenCapture", u"Delete item and the associated files on disk.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(shortcut)
        self.actionDelete.setShortcut(QCoreApplication.translate("ScreenCapture", u"Del", None))
#endif // QT_CONFIG(shortcut)
        self.actionConvert_To_WEBP.setText(QCoreApplication.translate("ScreenCapture", u"Convert To WEBP", None))
#if QT_CONFIG(tooltip)
        self.actionConvert_To_WEBP.setToolTip(QCoreApplication.translate("ScreenCapture", u"Converts this video to an animated WebP.", None))
#endif // QT_CONFIG(tooltip)
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
        self.delayComboBox.setItemText(0, QCoreApplication.translate("ScreenCapture", u"0s", None))
        self.delayComboBox.setItemText(1, QCoreApplication.translate("ScreenCapture", u"1s", None))
        self.delayComboBox.setItemText(2, QCoreApplication.translate("ScreenCapture", u"3s", None))
        self.delayComboBox.setItemText(3, QCoreApplication.translate("ScreenCapture", u"5s", None))

#if QT_CONFIG(tooltip)
        self.delayComboBox.setToolTip(QCoreApplication.translate("ScreenCapture", u"Time Delay in seconds for snapshot or recording actions.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.expandButton.setToolTip(QCoreApplication.translate("ScreenCapture", u"Toggle list of capture history for viewing.", None))
#endif // QT_CONFIG(tooltip)
        self.expandButton.setText(QCoreApplication.translate("ScreenCapture", u"...", None))
        self.historyGroupBox.setTitle(QCoreApplication.translate("ScreenCapture", u"History", None))
        self.searchButton.setText(QCoreApplication.translate("ScreenCapture", u"...", None))
        self.searchLine.setPlaceholderText(QCoreApplication.translate("ScreenCapture", u"Filter...", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page), QCoreApplication.translate("ScreenCapture", u"Screenshots", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page_2), QCoreApplication.translate("ScreenCapture", u"Videos", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page_3), QCoreApplication.translate("ScreenCapture", u"Animated", None))
    # retranslateUi

