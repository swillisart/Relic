# -- Built-in --
import ctypes
import os
import subprocess
import sys
import time
import timeit
from datetime import datetime
from functools import partial

from qtshared6.utils import loadStyleFromFile

# -- Third-party --
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from sequencePath import sequencePath as Path
# -- Module --
import capture.resources
from capture.ui.dialog import Ui_ScreenCapture
from capture.io import AudioRecord
from imagine.exif import EXIFTOOL

from strand.client import StrandClient
from strand.server import StrandServer

# -- Globals --
OUTPUT_PATH = "{}/Videos".format(os.getenv("USERPROFILE"))
PNG, MP4, WEBP, GIF = ['.png', '.mp4', '.webp', '.gif']
NO_WINDOW = subprocess.CREATE_NO_WINDOW
MOVIES = {}

def mouseMoveEvent(obj, event):
    if event.buttons() == Qt.LeftButton:
        if indices := obj.selectedIndexes():
            text = indices[0].data(role=Qt.UserRole)
            drag = QDrag(obj)
            mimeData = QMimeData()
            mimeData.setUrls([QUrl.fromLocalFile(text)])
            drag.setMimeData(mimeData)
            drag.exec(Qt.CopyAction)

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
        self.screens_snapshot = screencapRegion(self.getScreensRect())

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

    def __init__(self, *args, **kwargs):
        super(CaptureWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)

        # -- System Tray -- 
        app_icon = QIcon(':/resources/icons/capture.svg')
        self.tray = QSystemTrayIcon(app_icon, self)
        self.tray.activated.connect(self.toggleVisibility)
        self.tray.show()

        tray_menu = QMenu(self)
        close_action = tray_menu.addAction("Exit")
        close_action.triggered.connect(self._close)
        self.tray.setContextMenu(tray_menu)

        # -- Signals / Slots -- 
        self.expandButton.clicked.connect(self.adjustSize)
        self.videosListView.addAction(self.actionConvert_To_GIF)
        self.videosListView.addAction(self.actionConvert_To_WEBP)
        self.actionRename.triggered.connect(self.renameItem)
        self.actionOpen_File_Location.triggered.connect(self.exploreItem)
        self.actionDelete.triggered.connect(self.removeItem)
        self.actionConvert_To_WEBP.triggered.connect(self.convertToWEBP)
        self.actionConvert_To_GIF.triggered.connect(self.convertToGIF)
        self.captureButton.clicked.connect(self.delayScreenShot)
        self.recordButton.clicked.connect(self.performRecording)
        self.pool = QThreadPool.globalInstance()
        self.recording = False
        self.delay = 1000/30
        self.snap_model = QStandardItemModel()
        self.video_model = QStandardItemModel()
        self.gif_model = QStandardItemModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setDynamicSortFilter(True)
        self.proxy_model.setSourceModel(self.snap_model)
        self.searchLine.textChanged.connect(self.searchChanged)
        self.toolBox.currentChanged.connect(self.viewChanged)

        for view in [self.videosListView, self.screenshotListView, self.gifListView]:
            view.setModel(self.proxy_model)
            view.doubleClicked.connect(self.openInViewer)
            view.addAction(self.actionOpen_File_Location)
            view.addAction(self.actionRename)
            view.addAction(self.actionDelete)
            view.mouseMoveEvent = partial(mouseMoveEvent, view)

        self.video_icon = QPixmap(":resources/icons/video96.png").scaledToWidth(24, Qt.SmoothTransformation)
    
        for infile in Path(OUTPUT_PATH).path.iterdir():
            mtime = datetime.fromtimestamp(infile.stat().st_mtime)
            if (datetime.now() - mtime).days >= 90:
                in_path = Path(str(infile))
                archive = in_path.parents(0) / 'old' / in_path.stem
                in_path.moveTo(archive)
                continue
            if infile.suffix == PNG:
                self.appendToModel(str(infile), self.snap_model)
            elif infile.suffix == MP4:
                self.appendToModel(str(infile), self.video_model)
            elif infile.suffix == WEBP:
                self.appendToModel(str(infile), self.gif_model)
            elif infile.suffix == GIF:
                self.appendToModel(str(infile), self.gif_model)

        
        QShortcut(QKeySequence('ctrl+c'), self, self.copyToClipboard)

        try: os.mkdir(OUTPUT_PATH + '/previews') 
        except: pass
        self.cursor_pix = QPixmap(':/resources/icons/cursor.png').scaled(
            QSize(16, 16), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.strand_client = StrandClient('peak')

    def closeEvent(self, event):
        self.hide()
        event.ignore()

    def _close(self):
        sys.exit()

    def viewChanged(self, page_number):
        widget = self.toolBox.currentWidget()
        for child in widget.children():
            if child is self.videosListView:
                self.proxy_model.setSourceModel(self.video_model)
            elif child is self.screenshotListView:
                self.proxy_model.setSourceModel(self.snap_model)
            elif child is self.gifListView:
                self.proxy_model.setSourceModel(self.gif_model)
                
    def searchChanged(self, text):
        regex = QRegularExpression(text, QRegularExpression.CaseInsensitiveOption)
        self.proxy_model.setFilterRegularExpression(regex)

    def getActiveViewSelection(self):
        result = []
        widget = self.toolBox.currentWidget()
        for child in widget.children():
            if isinstance(child, QListView):
                if indices := child.selectedIndexes():
                    index = indices[0]
                    model = index.model()
                    source_model = model.sourceModel()
                    item = source_model.itemFromIndex(model.mapToSource(index))
                    return item
    
        return result

    @Slot()
    def openInViewer(self, index):
        path = Path(index.data(role=Qt.UserRole))
        self.strand_client.sendPayload(str(path))
        if self.strand_client.errored:
            cmd = f'start peak://{path}'
            os.system(cmd)

    @staticmethod
    def renameFile(path, name):
        old = str(path)
        new = str(path.parents(0) / (name + path.ext))
        os.rename(old, new)
        return new

    @Slot()
    def renameItem(self, val):
        item = self.getActiveViewSelection()
        path = Path(item.data(role=Qt.UserRole))
                
        text, ok = QInputDialog.getText(self, 'Rename',
                "New name:", QLineEdit.Normal,
                path.name)
        if ok:
            item.setText(text)
            new_path = self.renameFile(path, text)
            item.setData(new_path, Qt.UserRole)
            preview_path = path.parents(0) / 'previews' / (path.name + '.jpg')
            self.renameFile(preview_path, text)

    @Slot()
    def exploreItem(self, val):
        item = self.getActiveViewSelection()
        path = Path(item.data(role=Qt.UserRole))
        winpath = str(path).replace('/', '\\')
        cmd = 'explorer /select, "{}"'.format(winpath)
        subprocess.Popen(cmd)

    @Slot()
    def removeItem(self, val):
        item = self.getActiveViewSelection()
        path = Path(item.data(role=Qt.UserRole))

        message = QMessageBox(QMessageBox.Warning,
                'Confirm', 'Are you sure?',
                QMessageBox.NoButton, self)
        message.addButton('Yes', QMessageBox.AcceptRole)
        message.addButton('No', QMessageBox.RejectRole)

        if message.exec() == QMessageBox.AcceptRole:
            preview_path = path.parents(0) / 'previews' / (path.name + '.jpg')
            item.model().removeRow(item.index().row())
            if path.ext in ['.webp', '.gif']:
                premov = MOVIES.pop(str(path))
                premov.stop()
                premov.deleteLater()
            else:
                os.remove(str(preview_path))
            delete_func = partial(os.remove, str(path))
            self.timed_delete = QTimer.singleShot(600, delete_func)
            

    def updateMovie(self, item, movie, val):
        item.setIcon(QIcon(movie.currentPixmap()))

    def appendToModel(self, in_path, model, sort=False):
        path = Path(in_path)
        bg = QPixmap(str(path.parents(0) / 'previews' / (path.name + '.jpg')))
        
        set_movie = False
        if in_path.endswith('.mp4'):
            icon = QIcon(self.overlayImage(bg, self.video_icon))
        elif in_path.endswith('.webp') or in_path.endswith('.gif'):
            set_movie = True
            icon = bg
        else:
            icon = bg

        item = QStandardItem(icon, path.name)
        item.setData(str(path), Qt.UserRole)
        model.appendRow(item)
        if set_movie:
            movie = QMovie(in_path, parent=self)
            MOVIES[str(in_path)] = movie
            movie.start()
            func = partial(self.updateMovie, item, movie)
            movie.frameChanged.connect(func)
        if sort:
            model.sort(0, order=Qt.DescendingOrder)
        return item

    @Slot()
    def convertToWEBP(self, item):
        for index in self.videosListView.selectedIndexes():
            path = index.data(role=Qt.UserRole)
            out_path = path.replace('.mp4', '.webp')
            cmd = [
                'ffmpeg',
                '-loglevel', 'error',
                '-i', path,
                '-loop', '65535',
                out_path,
            ]
            subprocess.call(cmd, creationflags=NO_WINDOW)
            self.appendToModel(out_path, self.gif_model, sort=True)        

    @Slot()
    def convertToGIF(self, item):
        for index in self.videosListView.selectedIndexes():
            path = Path(index.data(role=Qt.UserRole))
            out_path = str(path).replace('.mp4', '.gif')
            gif_filter = path.parents(0) / '{}_palette.png'.format(path.name)
            cmd1 = [
                'ffmpeg',
                '-loglevel', 'error',
                '-i', str(path),
                '-vf', 'palettegen',
                str(gif_filter),
            ]
            cmd2 = [
                'ffmpeg',
                '-loglevel', 'error',
                '-i', str(path),
                '-i', str(gif_filter),
                '-filter_complex', 'fps=30,paletteuse',
                '{}/{}.gif'.format(path.parents(0), path.name),
            ]
            subprocess.call(cmd1)#, creationflags=NO_WINDOW)
            subprocess.call(cmd2)#, creationflags=NO_WINDOW)
            self.appendToModel(str(out_path), self.gif_model, sort=True)
            os.remove(str(gif_filter))

    @Slot()
    def delayScreenShot(self):
        msg = 'Delaying the capture for {} seconds. /n/nSingle-Click to exit.'
        delay = int(self.delayComboBox.currentText().replace('s', ''))
        self.deferred_snap = QTimer.singleShot(delay*1000, self.performScreenshot)

    def performScreenshot(self):
        self.hide()
        screen_overlay = ScreenOverlay()
        screen_overlay.clipped.connect(self.saveScreenshot)
        screen_overlay.exec()
    
    @Slot()
    def performRecording(self, state):
        if state:
            self.recording = True
            self.hide()
            screen_overlay = ScreenOverlay()
            screen_overlay.clipped.connect(self.startRecording)
            screen_overlay.exec()
        else:
            self.recording = False
            self.ffproc.stdin.close()
            self.audio_recorder.stop()
            # Combine audio with video and remove old files.
            out_file = str(self.out_video).replace('.mp4', '_.mp4')

            audio_duration = EXIFTOOL.getFields(str(self.out_audio), ['-Duration#'], float)
            video_duration = EXIFTOOL.getFields(str(self.out_video), ['-Duration#'], float)

            self.post_cmd = [
                'ffmpeg',
                '-loglevel', 'error',
                '-y', # Always Overwrite
                '-i', '{}'.format(self.out_audio),
                '-i', '{}'.format(self.out_video),
                #'-c:v', 'copy',
                #'-c:a', 'aac',
                #'-filter:a', 'atempo=1.0',#{}'.format(a_duration / v_duration),
                '-filter:v', 'setpts=PTS*{}'.format(audio_duration / video_duration),
                #'-map', '[v]',
                #'-map', '1:a',
                '-r', '24', # FPS
                #'-shortest',
                out_file,
            ]
            subprocess.call(self.post_cmd, creationflags=NO_WINDOW)
            os.remove(str(self.out_audio))
            os.remove(str(self.out_video))
            self.appendToModel(out_file, self.video_model, sort=True)

    def startRecording(self, rect, pixmap):
        self.show()
        self.rect = rect
        self.x = rect.x()
        self.y = rect.y()
        self.w = rect.width()
        self.h = rect.height()
        self.out_video = newCaptureFile(out_format='mp4')
        self.out_audio = self.out_video.parents(0) / (self.out_video.name + '.wav')
        out_icon = self.out_video.parents(0) / 'previews' / (self.out_video.name + '_.jpg')
        icon_pixmap = pixmap.scaled(QSize(96, 96), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon_pixmap.save(str(out_icon))
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
            #creationflags=NO_WINDOW,
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
        path = newCaptureFile()
        pixmap.save(str(path))
        icon_pixmap = pixmap.scaled(QSize(96, 96), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        out_icon = path.parents(0) / 'previews' / (path.name + '.jpg')
        icon_pixmap.save(str(out_icon))
        self.imageToClipboard(pixmap.toImage())
        item = self.appendToModel(str(path), self.snap_model, sort=True)
        index = self.snap_model.indexFromItem(item) 
        self.openInViewer(index)
        self.show()

    @Slot()
    def toggleVisibility(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.grab()
            self.setVisible(not self.isVisible())
            self.activateWindow()
            self.raise_()

    @staticmethod
    def overlayImage(image, over):
        result = QPixmap(image.width(), image.height())
        result.fill(Qt.transparent)
        pb = QPainter(result)
        pb.drawPixmap(0, 0, image)
        x = (image.width() / 2) - (over.width() / 2)
        y = (image.height() / 2) - (over.height() / 2)
        pb.drawPixmap(x, y, over)
        return result

    @staticmethod
    def imageToClipboard(image):
        clipboard = QApplication.clipboard()
        clipboard.setImage(image, QClipboard.Clipboard)
    
    def textToClipboard(self, text):
        mime_data = QMimeData()
        mime_data.setUrls([QUrl.fromLocalFile(text)])
        clipboard = QApplication.clipboard()
        clipboard.setMimeData(mime_data)

    def copyToClipboard(self):
        for child in self.toolBox.currentWidget().children():
            if child.objectName() in ['videosListView', 'gifListView']:
                if indices := child.selectedIndexes():
                    text = indices[0].data(role=Qt.UserRole)
                    self.textToClipboard(text)
            elif isinstance(child, QListView):
                if indices := child.selectedIndexes():
                    img = QImage(indices[0].data(role=Qt.UserRole))
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
        self.ffproc.stdin.write(image.constBits())


def newCaptureFile(out_format='png'):
    date = datetime.utcnow()
    result = Path("{dir}/{name}.{ext}".format(
        dir=OUTPUT_PATH,
        name=date.strftime("%y-%m-%d_%H-%M-%S"),
        ext=out_format,
    ))
    return result

def screencapRegion(rect):
    """Performs a screen capture on the specified rectangle.
    """
    divisible_width = int(rect.width()) - (int(rect.width()) % 16)
    screen = QGuiApplication.primaryScreen()
    return screen.grabWindow(
        0, rect.x(), rect.y(), divisible_width, rect.height()
    )

def main(args):
    app = QApplication(sys.argv)
    window = CaptureWindow()
    window.setWindowIcon(QIcon(':resources/icons/capture.svg'))
    loadStyleFromFile(window, ':style.qss')
    ctypes.windll.kernel32.SetConsoleTitleW("Peak-Capture")
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(u"resarts.relic-peak-capture")
    app.processEvents()
    window.show()
    server = StrandServer('capture')
    server.incomingFile.connect(window.performScreenshot)
    ret = app.exec()
    sys.exit(ret)


if __name__ == "__main__":
    main(sys.argv)
