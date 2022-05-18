import ctypes
import os
import subprocess
import sys
from datetime import datetime
import operator
import qtshared6.resources
from enum import IntEnum
# -- First-party --
from exif import EXIFTOOL
# -- Third-party --
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from qtshared6.delegates import ItemDispalyModes, AutoEnum, Statuses, BaseItemModel
from qtshared6.expandable_group import ExpandableGroup
from sequence_path.main import SequencePath as Path
from strand.client import StrandClient
from strand.server import StrandServer
from enum import Enum

# -- Module --
import resources
from history_view import (CaptureItem, HistoryTreeFilter, HistoryTreeView, Types,
                            scale_icon)
from file_io import AudioRecord, ShellCommand, video_to_gif
from ui.dialog import Ui_ScreenCapture

# -- Globals --
OUTPUT_PATH = "{}/Videos".format(os.getenv("USERPROFILE"))

NO_WINDOW = subprocess.CREATE_NO_WINDOW

class Delay(IntEnum):
    NONE = 0
    ONE = 1
    THREE = 2
    FIVE = 3

def get_preview_path(path):
    preview = (path.parent / 'previews' / path.stem)
    preview.ext = '.jpg'
    return preview

def makeThumbnail(pixmap):
    out_size = ItemDispalyModes.THUMBNAIL.thumb_size
    out_img = QImage(out_size, QImage.Format_RGBA8888)
    out_img.fill(QColor(68, 68, 68, 255))

    src_img = pixmap.toImage()
    alpha_img = src_img.scaled(out_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    painter = QPainter(out_img)
    painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
    painter.drawImage(0, 0, alpha_img)
    painter.end()
    return out_img


class ScreenOverlay(QDialog):

    clipped = Signal(QRect, QPixmap, QScreen)

    def __init__(self, screen):
        """A transparent tool dialog for selecting an area (QRect) on the screen.
        """
        super(ScreenOverlay, self).__init__()
        self.setMouseTracking(True)
        self.setCursor(Qt.CrossCursor)
        self.setScreen(screen)
        rect = screen.geometry()
        self.setGeometry(rect)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.X11BypassWindowManagerHint
            | Qt.Tool
        )
        # Dynamic Attributes
        self.origin_pos = QPoint(0,0)
        self.active_pos = QPoint(0,0)
        self.selection_rect = QRect()
        self.pad_point = QPoint(2, 2)
        self.screens_snapshot = screen.grabWindow(
            0, 0, 0, rect.width(), rect.height()
        )

    def paintEvent(self, event):
        """Draw frozen snapshot image over all screens / displays.

        Parameters
        ----------
        event : QEvent
            native Qt paint event
        """
        painter = QPainter(self)
        rect = event.rect()
        # Crosshair lines
        painter.drawPixmap(0, 0, self.screens_snapshot)
        pen = QPen(QColor(0, 0, 0, 200), 2, Qt.DotLine)
        self.drawCrosshairs(painter, rect + QMargins(2,2,0,0), pen)
        pen = QPen(QColor(255, 255, 255, 100), 2, Qt.DotLine)
        self.drawCrosshairs(painter, rect, pen)

        # Selected Region
        painter.setBrush(QColor(120, 165, 225, 25))
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.selection_rect)

    def mouseReleaseEvent(self, event):
        rect = self.selection_rect.normalized()
        scale = self.screen().devicePixelRatio()
        width = rect.width() * scale
        height = rect.height() * scale
        rect.setTopLeft(rect.topLeft() * scale)
        divisible_width = int(width) - (int(width) % 16)
        divisible_height = int(height) - (int(height) % 16)
        rect.setWidth(divisible_width)
        rect.setHeight(divisible_height)

        cropped = self.screens_snapshot.copy(rect)
        self.hide()
        self.clipped.emit(rect, cropped, self.screen())
        self.close()

    def drawCrosshairs(self, painter, rect, pen):
        """Draw cropping markers at origin and active cursor positions
        (The origin is created on mouseClick event)

        Parameters
        ----------
        painter : QPainter
            the painter to use
        rect : QRect
            The rectangle used to draw crosshairs on corners
        pen : QPen
            Styled pen for the markers.
        """
        # Painting at origin click position.
        active = self.active_pos
        origin = self.origin_pos
        painter.setPen(pen)
        painter.drawLine(
            rect.left(), origin.y(), rect.right(), origin.y()
        )
        painter.drawLine(
            origin.x(), rect.top(), origin.x(), rect.bottom()
        )

        # Painting at current / active mouse position.
        painter.drawLine(
            rect.left(), active.y(), rect.right(), active.y()
        )
        painter.drawLine(
            active.x(), rect.top(), active.x(), rect.bottom()
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.origin_pos = self.mapFromGlobal(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        self.active_pos = self.mapFromGlobal(event.globalPosition().toPoint())
        pos_compare = self.active_pos - self.origin_pos
        if all([event.buttons() == Qt.LeftButton,
            pos_compare.manhattanLength() >= 16
        ]):
            self.selection_rect = QRect(
                (self.origin_pos + self.pad_point),
                (self.active_pos - self.pad_point)
            )
        self.repaint()

class CaptureWindow(QWidget, Ui_ScreenCapture):

    onConvertedVideo = Signal(object)
    onConvertedGif = Signal(object)
    onConvertedWebp = Signal(object)

    class TreeActions(AutoEnum):
        view_item = {
            'obj': QAction(QIcon(':resources/icons/app_icon.ico'), 'View'),
            'key': 'space'}
        open_location = {
            'obj': QAction(QIcon(':resources/icons/folder.svg'), 'Open File Location'),
            'key': 'Ctrl+O'}
        rename_item = {
            'obj': QAction('Rename')}
        remove_item = {
            'obj': QAction('Delete'),
            'key': 'Del'}
        copy_to_clipboard = {
            'obj': QAction('Copy To Clipboard'),
            'key': 'ctrl+c'}

    class TrayActions(AutoEnum):
        taskbar_pin = {'obj': QAction('Taskbar Pin Toggle')}
        separator = {'obj': None}
        _close = {'obj': QAction('Exit')}

    def __init__(self, *args, **kwargs):
        super(CaptureWindow, self).__init__(*args, **kwargs)
        self.pinned = False
        self.setupUi(self)
        self.recording = False
        self.delay = 1000/30
        self.ffproc = None
        self.processing_item = False
        self.pool = QThreadPool.globalInstance()

        # -- System Tray --
        app_icon = QIcon(':/resources/icons/capture.svg')
        self.tray = QSystemTrayIcon(app_icon, self)
        self.tray.activated.connect(self.toggleVisibility)
        self.tray.show()
        tray_menu = QMenu(self)
        self.tray.setContextMenu(tray_menu)

        # -- Actions, Signals & Slots --
        for action in self.TrayActions:
            if isinstance(action.obj, QAction):
                self.defineAction(action)
                tray_menu.addAction(action.obj)
            else:
                tray_menu.addSeparator()


        gif_action = QAction('Convert To GIF')
        gif_action.triggered.connect(self.convert_to_gif)
        webp_action = QAction('Convert To WEBP')
        webp_action.triggered.connect(self.convert_to_webp)

        Types.Video.actions.extend([gif_action, webp_action])

        self.expandButton.clicked.connect(self.adjustSizes)
        self.captureButton.clicked.connect(self.delay_screenshot)
        self.recordButton.clicked.connect(self.perform_recording)
        self.onConvertedVideo.connect(self.item_processed)
        self.onConvertedGif.connect(self.gif_converted)
        self.onConvertedWebp.connect(self.webp_converted)

        self.item_model = BaseItemModel(0, 2)
        self.item_model.setHorizontalHeaderLabels(['Item', 'Date'])

        self.searchLine.textChanged.connect(self.searchChanged)

        model_root = self.item_model.invisibleRootItem()
        history_layout = self.historyGroupBox.layout()

        # Shared Tree actions
        for action in self.TreeActions:
            self.defineAction(action)

        for item_type in Types:
            tree = HistoryTreeView(self)
            proxy_model = HistoryTreeFilter(item_type)
            proxy_model.setDynamicSortFilter(True)
            proxy_model.setSourceModel(self.item_model)
            tree.setModel(proxy_model)
            
            for action in self.TreeActions:
                tree.addAction(action.obj)

            tree.doubleClicked.connect(self.openInViewer)
            tree.resizeColumnToContents(0)
            tree.sortByColumn(1, Qt.AscendingOrder)

            group = ExpandableGroup(tree, self.historyGroupBox)
            group.collapseExpand.connect(self.onGroupCollapse)
            group.iconButton.setIconSize(QSize(16,16))
            ExpandableGroup.BAR_HEIGHT -= 1
            group.styledLine.hide()
            group.styledLine_1.hide()
            group.iconButton.setIcon(QIcon(item_type.data))
            group.nameLabel.setText(item_type.name)

            history_layout.insertWidget(-2, group)
            header = tree.header()
            header.resizeSection(0, 200)
            header.resizeSection(1, 80)
            item_type.group = group

        self.captureItemsFromFolder(OUTPUT_PATH)

        try: os.mkdir(OUTPUT_PATH + '/previews')
        except: pass
        self.cursor_pix = scale_icon(QPixmap(':/resources/icons/cursor.png'))
        self.strand_client = StrandClient('peak')

    def taskbar_pin(self):
        if self.pinned:
            self.setWindowFlags(self.windowFlags() & ~Qt.FramelessWindowHint)
            self.show()
        else:
            self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.pinned = not self.pinned

    def changeEvent(self, event):
        if self.pinned:
            if event.type() == QEvent.ActivationChange:
                if not self.isActiveWindow():
                    self.hide()
        return super(CaptureWindow, self).changeEvent(event)

    @Slot()
    def adjustSizes(self, val):
        window = self.window()
        old_size = self.size()
        self.historyGroupBox.setVisible(val)
        self.adjustSize()
        new_size = self.size()
        diff = old_size - new_size
        diff_point = QPoint(diff.width(), diff.height())
        window.move(window.pos() + diff_point)

    @Slot()
    def onGroupCollapse(self, state):
        group = self.sender()
        if not state:
            self.historyGroupBox.hide()
            self.historyGroupBox.show()
        new_size = self.size() - QSize(0, group.height_store)
        self.resize(new_size)
        self.adjustSize()
        window = self.window()
        minus_bar = group.height_store - ExpandableGroup.BAR_HEIGHT
        if state:
            window.move(window.pos() - QPoint(0, minus_bar))
        else:
            window.move(window.pos() + QPoint(0, minus_bar))

    def getActiveSelectionModel(self):
        for item_type in Types:
            tree = item_type.group.content
            if tree.hasFocus():
                return item_type, tree.selectionModel()
            
    def defineAction(self, action):
        callback = getattr(self, action.name)
        action.obj.triggered.connect(callback)
        try:
            action.obj.setShortcut(QKeySequence(action.key))
        except: pass # no shortcut defined

    def captureItemsFromFolder(self, root):
        for in_file in Path(root):
            ext = in_file.ext
            for item_type in Types:
                if ext in item_type.ext:
                    mtime = datetime.fromtimestamp(in_file.datemodified)
                    if (datetime.now() - mtime).days >= 30:
                        archive = in_file.parent / 'old' / in_file.stem
                        in_file.moveTo(archive)
                    else:
                        self.appendItem(item_type, in_file)

    def appendItem(self, item_type, in_file):
        model_root = self.item_model.invisibleRootItem()
        mtime = datetime.fromtimestamp(in_file.datemodified)
        image = QPixmap(str(get_preview_path(in_file)))
        capture = CaptureItem(in_file)
        capture.date = mtime
        capture.thumbnail = image
        capture.type = item_type
        item = QStandardItem(capture.name)
        item.setData(capture, role=Qt.UserRole)
        self.change_count(operator.add, item_type, 1)
        date_item = QStandardItem(capture.date.strftime('%m/%d/%y %H:%M'))
        date_item.setData(capture.date, role=Qt.UserRole)
        model_root.appendRow([item, date_item])
        return item

    def change_count(self, operation, item_type, number):
        group = item_type.group
        count = group.countSpinBox.value()

        total = operation(count, number)
        group.countSpinBox.setValue(total)

    def closeEvent(self, event):
        self.hide()
        event.ignore()

    def _close(self):
        global EXIFTOOL
        del EXIFTOOL
        sys.exit()

    def searchChanged(self, text):
        regex = QRegularExpression(text, QRegularExpression.CaseInsensitiveOption)
        for item_type in Types:
            view_proxy_model = item_type.group.content.model()
            view_proxy_model.setFilterRegularExpression(regex)

    @Slot()
    def openInViewer(self, index):
        capture_obj = index.data(Qt.UserRole)
        if isinstance(capture_obj, CaptureItem):
            self.strand_client.sendPayload(str(capture_obj.path))
            if self.strand_client.errored:
                cmd = f'start peak://{capture_obj.path}'
                os.system(cmd)

    @staticmethod
    def renameFile(path, name):
        old = str(path)
        new = str(path.parent / (name + path.ext))
        os.rename(old, new)
        return new

    @Slot()
    def view_item(self, val):
        item_type, selection_model = self.getActiveSelectionModel()
        indices = selection_model.selectedIndexes()
        if not indices:
            return
        for index in indices:
            self.openInViewer(index)

    @Slot()
    def rename_item(self, val):
        item_type, selection_model = self.getActiveSelectionModel()
        indices = selection_model.selectedIndexes()
        if not indices:
            return
        items = [self.item_model.indexToItem(x).data(Qt.UserRole) for x in indices]
        filtered = [x for x in items if isinstance(x, CaptureItem)]
        obj = filtered[-1]
        self.pinned = not self.pinned # prevent popup focus from hiding pin
        new_name, ok = QInputDialog.getText(self, 'Rename',
                "New name:", QLineEdit.Normal,
                obj.path.name)
        if ok:
            old_preview_path = get_preview_path(obj.path)
            old_path = Path(str(obj.path))
            obj.path.name = new_name
            obj.name = new_name
            self.renameFile(old_path, new_name)
            preview_path = get_preview_path(obj.path)
            self.renameFile(old_preview_path, new_name)
        self.pinned = not self.pinned

    @Slot()
    def open_location(self, val):
        item_type, selection_model = self.getActiveSelectionModel()
        indices = selection_model.selectedIndexes()
        if not indices:
            return
        for index in reversed(indices):
            obj = index.data(Qt.UserRole)
            if isinstance(obj, CaptureItem):
                break
        winpath = str(obj.path).replace('/', '\\')
        cmd = f'explorer /select, "{winpath}"'
        os.system(cmd)

    @Slot()
    def remove_item(self, val):
        item_type, selection_model = self.getActiveSelectionModel()

        if not selection_model.hasSelection():
            return
        count = len(selection_model.selectedRows())
        self.pinned = not self.pinned # prevent popup focus from hiding pin

        message = QMessageBox.question(self,
                'Confirm', 'Are you sure?',
                buttons=QMessageBox.Yes | QMessageBox.No
                )

        if message == QMessageBox.RejectRole:
            return

        while indices := selection_model.selectedIndexes():
            index = indices[0]
            obj = index.data(Qt.UserRole)
            if not isinstance(obj, CaptureItem):
                selection_model.select(index, QItemSelectionModel.Deselect)
                continue

            item = self.item_model.indexToItem(index)
            item_parent = item.parent()
            if item_parent:
                item_parent.removeRow(item.index().row())
            else:
                self.item_model.removeRow(item.index().row())

            preview_path = get_preview_path(obj.path)
            # Don't delete animated icons. (they may still have a video)
            if obj.type != int(Types.Animated) and preview_path.exists():
                os.remove(str(preview_path))
            if obj.path.exists():
                os.remove(str(obj.path))

        self.change_count(operator.sub, item_type, count)
        self.pinned = not self.pinned

    def updateMovie(self, item, movie, val):
        item.setIcon(QIcon(movie.currentPixmap()))

    @Slot()
    def convert_to_webp(self, item):
        item_type, selection_model = self.getActiveSelectionModel()

        if not selection_model.hasSelection():
            return

        for index in selection_model.selectedIndexes():
            obj = index.data(Qt.UserRole)
            if not isinstance(obj, CaptureItem):
                continue
            out_path = obj.path.suffixed('', '.webp')
            cmd = [
                'ffmpeg',
                '-loglevel', 'error',
                '-i', str(obj.path),
                '-loop', '65535',
                str(out_path),
            ]
            item = self.appendItem(Types.Animated, obj.path)
            item.status = int(Statuses.Syncing)
            worker = ShellCommand(
                cmd, item, signal=self.onConvertedWebp)
            self.pool.start(worker)

    @Slot()
    def convert_to_gif(self, item):
        item_type, selection_model = self.getActiveSelectionModel()

        if not selection_model.hasSelection():
            return

        for index in selection_model.selectedIndexes():
            obj = index.data(Qt.UserRole)
            if not isinstance(obj, CaptureItem):
                continue
            item = self.appendItem(Types.Animated, obj.path)
            item.status = int(Statuses.Syncing)
            callback = lambda x: video_to_gif(x.data(Qt.UserRole).path)
            worker = ShellCommand(
                'echo .', item, signal=self.onConvertedGif, callback=callback)
            self.pool.start(worker)

    @Slot()
    def delay_screenshot(self):
        msg = 'Delaying the capture for {} seconds. /n/nSingle-Click to exit.'
        index = self.delayComboBox.currentIndex()
        seconds = Delay(index)
        self.deferred_snap = QTimer.singleShot(seconds*1000, self.perform_screenshot)

    def perform_screenshot(self, record=False):
        slot = self.startRecording if record else self.saveScreenshot
        self.hide()
        self.screens = []
        for screen in reversed(QGuiApplication.screens()):
            screen_overlay = ScreenOverlay(screen)
            screen_overlay.clipped.connect(slot)
            screen_overlay.show()
            self.screens.append(screen_overlay)

    @Slot()
    def perform_recording(self, state):
        if state:
            self.recording = True
            self.perform_screenshot(record=True)
        else:
            self.recording = False
            self.ffproc.stdin.close()
            if self.ffproc.wait() != 0:
                print('FFmpeg had errors')
            self.audio_recorder.stop()
            pid = self.ffproc.pid
            subprocess.call(
                f'taskkill /F /T /PID {pid}',
                creationflags=NO_WINDOW)
            # Combine audio with video and remove old files.
            self.out_file = self.out_video.suffixed('_c', ext='.mp4')

            audio_duration = EXIFTOOL.getFields(str(self.out_audio), ['-Duration#'], float)
            video_duration = EXIFTOOL.getFields(str(self.out_video), ['-Duration#'], float)

            post_cmd = [
                'ffmpeg',
                '-loglevel', 'error',
                '-y', # Always Overwrite
                '-i', f'{self.out_audio}',
                '-i', f'{self.out_video}',
                '-filter:v', 'setpts=PTS*{}'.format(audio_duration / video_duration),
                '-r', '24', # FPS
                str(self.out_file),
            ]
            item = self.appendItem(Types.Video, self.out_video)
            if not self.audio_recorder.input_device.isNull():
                item.status = int(Statuses.Syncing)
                self.processing_item = True
                worker = ShellCommand(
                    post_cmd, item, signal=self.onConvertedVideo)
                self.pool.start(worker)
            else:
                os.rename(str(self.out_video), self.out_file)
                os.rename(get_preview_path(self.out_video), get_preview_path(self.out_file))
                os.remove(str(self.out_audio))

    @Slot(object)
    def gif_converted(self, item):
        capture_item = item.data(Qt.UserRole)
        capture_item.status = int(Statuses.Local)
        capture_item.path = capture_item.path.suffixed('', ext='.gif')
        capture_item.name = capture_item.path.name

    @Slot(object)
    def webp_converted(self, item):
        capture_item = item.data(Qt.UserRole)
        capture_item.status = int(Statuses.Local)
        capture_item.path = capture_item.path.suffixed('', ext='.webp')
        capture_item.name = capture_item.path.name

    @Slot(object)
    def item_processed(self, item):
        item = item.data(Qt.UserRole)
        item.status = int(Statuses.Local)
        item.path = self.out_file
        item.name = self.out_file.name
        op = get_preview_path(self.out_video)
        np =  get_preview_path(self.out_file)
        os.rename(str(op), str(np))
        os.remove(str(self.out_audio))
        os.remove(str(self.out_video))
        self.processing_item = False

    def startRecording(self, rect, pixmap, screen):
        self.finishCapture()
        self.show()
        self.screen = screen
        scale = screen.devicePixelRatio()
        self.x = rect.x() / scale
        self.y = rect.y() / scale
        self.w = rect.width() / scale
        self.h = rect.height() / scale
        self.rect = QRect(self.x, self.y, self.w, self.h)
        self.out_video = new_capture_file(out_format='mp4')
        self.out_audio = self.out_video.parent / (self.out_video.name + '.wav')
        out_preview = get_preview_path(self.out_video)
        size = ItemDispalyModes.COMPACT.thumb_size
        out_img = makeThumbnail(pixmap)
        out_img.save(str(out_preview))
        self.audio_recorder = AudioRecord(self.out_audio)
        cmd = [
            'ffmpeg',
            #'-loglevel', 'error',
            '-y', # Always Overwrite
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-pix_fmt', 'rgb24',
            '-s', '{}x{}'.format(rect.width(), rect.height()),
            '-i', '-',
            '-r', '30', # FPS
            '-pix_fmt', 'yuv420p',
            '-preset', 'ultrafast',
            '-crf', '32',
            #'-vcodec', 'h264',
            #'-tune', 'zerolatency',
            str(self.out_video),
        ]

        self.ffproc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            #stdout=subprocess.DEVNULL,
            creationflags=NO_WINDOW,
        )
        self.capsnap = QTimer()
        self.capsnap.setInterval(self.delay)
        self.capsnap.setTimerType(Qt.PreciseTimer)
        self.capsnap.timeout.connect(self.execute)
        self.capsnap.start()

    @Slot()
    def execute(self):
        if not self.recording:
            self.capsnap.stop()
            return
        self.worker = CapScreen(self.rect, self.screen, self.ffproc, self.cursor_pix)
        self.pool.start(self.worker, priority=1)

    @Slot()
    def saveScreenshot(self, rect, pixmap, screen):
        path = new_capture_file()
        pixmap.save(str(path))
        icon_pixmap = makeThumbnail(pixmap)
        icon_pixmap.save(str(get_preview_path(path)))
        self.imageToClipboard(pixmap.toImage())
        self.finishCapture()
        item = self.appendItem(Types.Screenshot, path)
        index = self.item_model.indexFromItem(item)
        #self.openInViewer(index)
        self.show()

    def finishCapture(self):
        """cleans up widgets and resets state for new capture"""
        [x.close() for x in self.screens]

    @Slot()
    def toggleVisibility(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.grab()
            self.setVisible(not self.isVisible())
            self.activateWindow()
            self.raise_()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.setVisible(False)
            self.perform_screenshot()

    @staticmethod
    def imageToClipboard(image):
        clipboard = QApplication.clipboard()
        clipboard.setImage(image, QClipboard.Clipboard)

    def textToClipboard(self, text):
        mime_data = QMimeData()
        mime_data.setUrls([QUrl.fromLocalFile(text)])
        clipboard = QApplication.clipboard()
        clipboard.setMimeData(mime_data)

    def copy_to_clipboard(self):
        text_types = [int(Types.Animated), int(Types.Video)]
        item_type, selection_model = self.getActiveSelectionModel()
        if indices := selection_model.selectedIndexes():
            obj = indices[0].data(Qt.UserRole)
            if obj.type in text_types:
                self.textToClipboard(str(obj.path))
            else:
                img = QImage(str(obj.path))
                self.imageToClipboard(img)

class CapScreen(QRunnable):

    def __init__(self, rect, screen, ffproc, cursor_pix):
        super(CapScreen, self).__init__(None)
        self.ffproc = ffproc
        self.rect = rect
        self.screen = screen
        self.cursor_pixmap = cursor_pix
        self.cursor_pos = QCursor.pos()

    def run(self):
        rect = self.rect
        screen = self.screen
        x = rect.x()
        y = rect.y()
        w = rect.width()
        h = rect.height()
        pixmap = screen.grabWindow(0, x, y, w, h)
        # Draw cursor into our capture
        painter = QPainter(pixmap)
        painter.drawPixmap(self.cursor_pos.x()-x, self.cursor_pos.y()-y, self.cursor_pixmap)
        painter.end()
        image = pixmap.toImage().convertToFormat(QImage.Format_RGB888)
        try:
            self.ffproc.stdin.write(image.constBits())
        except ValueError:
            pass # write to closed file

def new_capture_file(out_format='png'):
    date = datetime.utcnow()
    result = Path("{dir}/{name}.{ext}".format(
        dir=OUTPUT_PATH,
        name=date.strftime("%y-%m-%d_%H-%M-%S"),
        ext=out_format,
    ))
    return result

def main(args):
    app = qApp or QApplication(sys.argv)
    window = CaptureWindow()
    window.setWindowIcon(QIcon(':resources/icons/capture.svg'))
    ctypes.windll.kernel32.SetConsoleTitleW('Capture')
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(u"resarts.relic-capture")
    app.processEvents()
    window.show()
    server = StrandServer('capture')
    server.incomingFile.connect(window.perform_screenshot)
    sys.exit(app.exec())

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Capture the screen')
    parser.add_argument('--screenshot', nargs='?', metavar='')
    parser.add_argument('--record', nargs='?', metavar='')
    args = parser.parse_args()

    # Define our Environment
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
    os.environ['PATH'] = os.environ['PATH'] + ';P:/Code/Relic'
    from strand.client import StrandClient
    client = StrandClient('capture')
    client.sendPayload('')
    if client.errored:
        import capture
        capture.app.main(sys.argv)
