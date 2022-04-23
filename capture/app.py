# -- Built-in --
import ctypes
import os
import subprocess
import sys
from datetime import datetime
from functools import partial
import operator
import qtshared6.resources
# -- First-party --
from imagine.exif import EXIFTOOL
# -- Third-party --
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from qtshared6.delegates import ItemDispalyModes, AutoEnum, Statuses, BaseItemModel
from qtshared6.utils import polymorphicItem
from sequence_path.main import SequencePath as Path
from strand.client import StrandClient
from strand.server import StrandServer
from enum import Enum

# -- Module --
import capture.resources
from capture.history_view import (CaptureItem, HistoryTreeFilter, HistoryTreeView, Types,
                                  scale_icon)
from capture.io import AudioRecord, ShellCommand, video_to_gif
from capture.ui.dialog import Ui_ScreenCapture

# -- Globals --
OUTPUT_PATH = "{}/Videos".format(os.getenv("USERPROFILE"))

NO_WINDOW = subprocess.CREATE_NO_WINDOW

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

    clipped = Signal(QRect, QPixmap)

    def __init__(self, *args, **kwargs):
        """A transparent tool dialog for selecting an area (QRect) on the screen.
        """
        super(ScreenOverlay, self).__init__(*args, **kwargs)
        self.setMouseTracking(True)
        self.setCursor(Qt.CrossCursor)
        self.setGeometry(self.getScreensRect())
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
        self.screens_snapshot = screencap_region(self.getScreensRect())

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
        divisible_width = int(rect.width()) - (int(rect.width()) % 16)
        divisible_height = int(rect.height()) - (int(rect.height()) % 16)
        rect.setWidth(divisible_width)
        rect.setHeight(divisible_height)
        cropped = self.screens_snapshot.copy(rect)
        self.hide()
        self.clipped.emit(rect, cropped)
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
            self.origin_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        self.active_pos = event.globalPosition().toPoint()
        pos_compare = self.active_pos - self.origin_pos
        if all([event.buttons() == Qt.LeftButton,
            pos_compare.manhattanLength() >= 16
        ]):
            self.selection_rect = QRect(
                (self.origin_pos + self.pad_point),
                (self.active_pos - self.pad_point)
            )
        self.repaint()

    @staticmethod
    def getScreensRect():
        """Gets the combined QRect of all active screens from the desktop.

        Returns
        -------
        QRect
            unified screen geometry rectangle
        """
        screen = QGuiApplication.primaryScreen()
        return screen.virtualGeometry()

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
        _close = {
            'obj': QAction('Exit')}

    def __init__(self, *args, **kwargs):
        super(CaptureWindow, self).__init__(*args, **kwargs)
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
            self.defineAction(tray_menu, action)

        gif_action = QAction('Convert To GIF')
        gif_action.triggered.connect(self.convert_to_gif)
        webp_action = QAction('Convert To WEBP')
        webp_action.triggered.connect(self.convert_to_webp)

        Types.Video.actions.extend([gif_action, webp_action])

        self.expandButton.clicked.connect(self.adjustSize)
        self.captureButton.clicked.connect(self.delay_screenshot)
        self.recordButton.clicked.connect(self.perform_recording)
        self.onConvertedVideo.connect(self.item_processed)
        self.onConvertedGif.connect(self.gif_converted)
        self.onConvertedWebp.connect(self.webp_converted)

        self.item_model = BaseItemModel(0, 3)
        self.item_model.setHorizontalHeaderLabels(['Name', 'Date', 'Count'])

        model_root = self.item_model.invisibleRootItem()
        for item_type in Types:
            item = QStandardItem(QIcon(item_type.data), item_type.name)
            counter = QStandardItem()
            counter.setData('0', role=Qt.DisplayRole)
            counter.setData(0, role=Qt.UserRole)
            model_root.appendRow([item, QStandardItem(''), counter])
            item_type.item = item

        self.proxy_model = HistoryTreeFilter()
        self.proxy_model.setDynamicSortFilter(True)
        self.proxy_model.setSourceModel(self.item_model)
        self.searchLine.textChanged.connect(self.searchChanged)

        history_tree = HistoryTreeView(self)

        for action in self.TreeActions:
            self.defineAction(history_tree, action)

        history_tree.ACTIONS = self.TreeActions
        history_tree.setModel(self.proxy_model)
        history_tree.doubleClicked.connect(self.openInViewer)
        history_tree.resizeColumnToContents(0)
        history_tree.sortByColumn(1, Qt.AscendingOrder)

        self.historyGroupBox.layout().addWidget(history_tree)

        self.history_tree = history_tree

        self.captureItemsFromFolder(OUTPUT_PATH)

        try: os.mkdir(OUTPUT_PATH + '/previews')
        except: pass
        self.cursor_pix = scale_icon(QPixmap(':/resources/icons/cursor.png'))
        self.strand_client = StrandClient('peak')

        header = history_tree.header()
        header.resizeSection(0, 250)
        header.resizeSection(1, 80)

    def defineAction(self, widget, action):
        callback = getattr(self, action.name)
        action.obj.triggered.connect(callback)
        try:
            action.obj.setShortcut(QKeySequence(action.key))
        except: pass # no shortcut defined
        widget.addAction(action.obj)

    def captureItemsFromFolder(self, root):
        for in_file in Path(root):
            ext = in_file.ext
            for item_type in Types:
                if ext in item_type.ext:
                    mtime = datetime.fromtimestamp(in_file.datemodified)
                    if (datetime.now() - mtime).days >= 90:
                        archive = in_file.parent / 'old' / in_file.stem
                        in_file.moveTo(archive)
                    else:
                        self.appendItem(item_type, in_file)

    def appendItem(self, item_type, in_file):
        mtime = datetime.fromtimestamp(in_file.datemodified)
        image = QPixmap(str(get_preview_path(in_file)))
        capture = CaptureItem(in_file)
        capture.date = mtime
        capture.thumbnail = image
        capture.type = item_type.value
        item = polymorphicItem(fields=capture)
        
        self.change_count(operator.add, item_type, 1)

        date_item = QStandardItem(capture.date.strftime('%m/%d/%Y %H:%M'))
        date_item.setData(capture.date, role=Qt.UserRole)
        #date_item.setData(capture.date.strftime('%m/%d/%Y'), role=Qt.DisplayRole)

        item_type.item.appendRow([item, date_item])
        return item


    def change_count(self, operation, item_type, number):
        item_model = item_type.item.model()
        row = item_type.item.row()
        count_index = item_model.index(row, CaptureItem.Columns.count)
        count_item = item_model.itemFromIndex(count_index)

        total = operation(count_item.data(role=Qt.UserRole), number)
        count_item.setData(str(total), role=Qt.DisplayRole)
        count_item.setData(total, role=Qt.UserRole)

    def closeEvent(self, event):
        self.hide()
        event.ignore()

    def _close(self):
        global EXIFTOOL
        del EXIFTOOL
        sys.exit()

    def searchChanged(self, text):
        regex = QRegularExpression(text, QRegularExpression.CaseInsensitiveOption)
        self.proxy_model.setFilterRegularExpression(regex)

    @Slot()
    def openInViewer(self, index):
        capture_obj = index.data(polymorphicItem.Object)
        if capture_obj:
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
        indices = self.history_tree.selectedIndexes()
        if not indices:
            return
        for index in indices:
            self.openInViewer(index)

    @Slot()
    def rename_item(self, val):
        indices = self.history_tree.selectedIndexes()
        if not indices:
            return
        items = [self.indexToItem(x).data(polymorphicItem.Object) for x in indices]
        filtered = [x for x in items if x]
        obj = filtered[-1]
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

    @Slot()
    def open_location(self, val):
        indices = self.history_tree.selectedIndexes()
        if not indices:
            return
        for index in reversed(indices):
            obj = index.data(polymorphicItem.Object)
            if obj:
                break
        winpath = str(obj.path).replace('/', '\\')
        cmd = f'explorer /select, "{winpath}"'
        os.system(cmd)

    def indexToItem(self, index):
        remapped_index = self.proxy_model.mapToSource(index)
        item = self.item_model.itemFromIndex(remapped_index)
        return item

    @Slot()
    def remove_item(self, val):
        indices = self.history_tree.selectedIndexes()
        if not indices:
            return
        message = QMessageBox(QMessageBox.Warning,
                'Confirm', 'Are you sure?',
                QMessageBox.NoButton, self)
        message.addButton('Yes', QMessageBox.AcceptRole)
        message.addButton('No', QMessageBox.RejectRole)

        if message.exec() == QMessageBox.RejectRole:
            return

        selection_model = self.history_tree.selectionModel()
        while selection_model.selectedIndexes():
            index = selection_model.selectedIndexes()[0]
            obj = index.data(polymorphicItem.Object)
            if not obj:
                selection_model.select(index, QItemSelectionModel.Deselect)
                continue

            item = self.indexToItem(index)

            self.change_count(operator.sub, Types(item.type), 1)

            item.parent().removeRow(item.index().row())
    
            preview_path = get_preview_path(obj.path)
            # Don't delete animated icons. (they may still have a video)
            if obj.type != int(Types.Animated) and preview_path.exists():
                os.remove(str(preview_path))
            if obj.path.exists():
                os.remove(str(obj.path))

    def updateMovie(self, item, movie, val):
        item.setIcon(QIcon(movie.currentPixmap()))

    @Slot()
    def convert_to_webp(self, item):
        for index in self.history_tree.index_selection:
            obj = index.data(polymorphicItem.Object)
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
        for index in self.history_tree.index_selection:
            obj = index.data(polymorphicItem.Object)
            item = self.appendItem(Types.Animated, obj.path)
            item.status = int(Statuses.Syncing)
            callback = lambda x: video_to_gif(x.path)
            worker = ShellCommand(
                'echo .', item, signal=self.onConvertedGif, callback=callback)
            self.pool.start(worker)

    @Slot()
    def delay_screenshot(self):
        msg = 'Delaying the capture for {} seconds. /n/nSingle-Click to exit.'
        delay = int(self.delayComboBox.currentText().replace('s', ''))
        self.deferred_snap = QTimer.singleShot(delay*1000, self.perform_screenshot)

    def perform_screenshot(self):
        self.hide()
        screen_overlay = ScreenOverlay()
        screen_overlay.clipped.connect(self.saveScreenshot)
        screen_overlay.exec()

    @Slot()
    def perform_recording(self, state):
        if state:
            self.recording = True
            self.hide()
            screen_overlay = ScreenOverlay()
            screen_overlay.clipped.connect(self.startRecording)
            screen_overlay.exec()
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
            self.out_file = self.out_video.suffixed('_capture', ext='.mp4')

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
        item.status = int(Statuses.Local)
        item.path = item.path.suffixed('', ext='.gif')
        item.name = item.path.name

    @Slot(object)
    def webp_converted(self, item):
        item.status = int(Statuses.Local)
        item.path = item.path.suffixed('', ext='.webp')
        item.name = item.path.name

    @Slot(object)
    def item_processed(self, item):
        item.status = int(Statuses.Local)
        item.path = self.out_file
        item.name = self.out_file.name
        op = get_preview_path(self.out_video)
        np =  get_preview_path(self.out_file)
        os.rename(str(op), str(np))
        os.remove(str(self.out_audio))
        os.remove(str(self.out_video))
        self.processing_item = False

    def startRecording(self, rect, pixmap):
        self.show()
        self.rect = rect
        self.x = rect.x()
        self.y = rect.y()
        self.w = rect.width()
        self.h = rect.height()
        self.out_video = new_capture_file(out_format='mp4')
        self.out_audio = self.out_video.parent / (self.out_video.name + '.wav')
        out_preview = get_preview_path(self.out_video)
        size = ItemDispalyModes.COMPACT.thumb_size
        out_img = makeThumbnail(pixmap)
        out_img.save(str(out_preview))
        self.audio_recorder = AudioRecord(self.out_audio)
        divisible_width = int(rect.width()) - (int(rect.width()) % 16)
        cmd = [
            'ffmpeg',
            #'-loglevel', 'error',
            '-y', # Always Overwrite
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-pix_fmt', 'rgb24',
            '-s', '{}x{}'.format(divisible_width, self.h),
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
        self.worker = CapScreen(self.rect, self.ffproc, self.cursor_pix)
        self.pool.start(self.worker, priority=1)

    @Slot()
    def saveScreenshot(self, rect, pixmap):
        path = new_capture_file()
        pixmap.save(str(path))
        icon_pixmap = makeThumbnail(pixmap)
        icon_pixmap.save(str(get_preview_path(path)))
        self.imageToClipboard(pixmap.toImage())
        item = self.appendItem(Types.Screenshot, path)
        index = self.item_model.indexFromItem(item)
        #self.openInViewer(index)
        self.show()

    @Slot()
    def toggleVisibility(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.grab()
            self.setVisible(not self.isVisible())
            self.activateWindow()
            self.raise_()

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
        if indices := self.history_tree.selectedIndexes():
            obj = indices[0].data(polymorphicItem.Object)
            if obj.type in text_types:
                self.textToClipboard(str(obj.path))
            else:
                img = QImage(str(obj.path))
                self.imageToClipboard(img)


class CapScreen(QRunnable):

    def __init__(self, rect, ffproc, cursor_pix):
        super(CapScreen, self).__init__(None)
        self.ffproc = ffproc
        self.rect = rect
        self.cursor_pixmap = cursor_pix
        self.cursor_pos = QCursor.pos()

    def run(self):
        rect = self.rect
        x = rect.x()
        y = rect.y()
        w = rect.width()
        h = rect.height()
        screen = QGuiApplication.primaryScreen()
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

def screencap_region(rect):
    """Performs a screen capture on the specified rectangle.
    """
    divisible_width = int(rect.width()) - (int(rect.width()) % 16)
    screen = QGuiApplication.primaryScreen()
    return screen.grabWindow(
        0, rect.x(), rect.y(), divisible_width, rect.height()
    )

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
    main(sys.argv)
