import ctypes
import os
import sys
import operator
import subprocess

from datetime import datetime
from functools import partial, cached_property
from enum import IntEnum
from extra_types.enums import DataAutoEnum

# -- Third-party --
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtMultimedia import QAudioFormat, QMediaDevices, QAudioSource, QAudio
from relic.qt.delegates import ItemDispalyModes, BaseItemModel
from relic.qt.expandable_group import ExpandableGroup
from intercom import Client, Server
from sequence_path.main import SequencePath as Path

from d3dshot.d3dshot import D3DShot, Singleton
import av
from av.filter import Graph
from av import AudioFrame, VideoFrame
import numpy as np
from fractions import Fraction

# -- Module --
import resources
import capture.resources
from capture.history_view import (CaptureItem, HistoryTreeFilter, HistoryTreeView, TypesIndicator)
from capture.ui.dialog import Ui_ScreenCapture
from capture.cursor import get_cursor_arrays, build_cursor_data

# -- Globals --
OUTPUT_PATH = "{}/Videos".format(os.getenv("USERPROFILE"))


class CaptureType(object):
    __slots__ = ['ext', 'group', 'actions']
    def __init__(self, ext):
        self.ext = ext
        self.group = None
        self.actions = []

class Types(DataAutoEnum):
    Screenshot = CaptureType(['.png'])
    Video = CaptureType(['.mp4'])
    Animated = CaptureType(['.webp', '.gif'])

    def __getattr__(self, name):
        try:
            return self.__dict__[name]
        except:
            return getattr(self.__dict__['data'], name)

    def __setattr__(self, name, value):
        try:
            setattr(self.data, name, value)
        except:
            super().__setattr__(name, value)


def video_to_gif(path):
    out_path = path.suffixed('', ext='.gif')
    in_container = av.open(str(path))
    in_stream = in_container.streams.video[0]
    in_stream.thread_type = "AUTO"
    temp_path = str(path.suffixed('.%04d.', ext='png'))

    try:
        frame_count = 0
        for frame_number, frame in enumerate(in_container.decode(video=0)):
            if frame_number % 2 == 0:
                array = frame.to_rgb().to_ndarray()
                h, w, c = array.shape
                img = QImage(array, w, h, QImage.Format_RGB888)
                img.save(temp_path % frame_count)
                frame_count += 1
    except Exception as exerr:
        print(exerr)
    finally:
        in_container.close()

    png_frames = temp_path.replace('.%04d.', '.*.') 
    cmd = f'gifski -o {out_path} --fps 15 {png_frames}'
    subprocess.call(cmd)
    [os.remove(temp_path % i) for i in range(frame_count)]

    return out_path


class Delay(IntEnum):
    NONE = 0
    ONE = 1
    THREE = 2
    FIVE = 3

class Recorder(QObject):

    def __init__(self, parent=None):
        super(Recorder, self).__init__(parent)
        self.d3d = D3DShot()
        self.input_device = QMediaDevices.defaultAudioInput()
        audio_format = QAudioFormat()
        audio_format.setSampleRate(48000)
        audio_format.setChannelCount(1) # 1 mono, 2 stereo
        audio_format.setSampleFormat(QAudioFormat.Int16)

        if not self.input_device.isNull():
            self._audio_input = QAudioSource(self.input_device, audio_format, self)

        self.time_base = Fraction(1, 1000)
        cursor_cache = {}
        for screen in reversed(QGuiApplication.screens()):
            scale = screen.devicePixelRatio()
            cursor_size = int(32 * scale)
            cursor_cache[screen.name()] = build_cursor_data(cursor_size)
        self.cursor_cache = cursor_cache

    def createContainer(self, out_path):
        # PyAv container and streams
        container = av.open(out_path, "w")
        args = {'tune': 'zerolatency', 'bitrate': '6000', 'bufsize': '166', 'maxrate': '6000', 'crf': '28'}
        # Video
        video_stream = container.add_stream('libx264', rate=24, options=args)
        video_stream.pix_fmt = 'yuv420p'
        video_stream.width = self.rect.width()
        video_stream.height = self.rect.height()
        video_stream.thread_type = 'NONE'
        video_stream.codec_context.time_base = self.time_base
        # Audio
        audio_stream = container.add_stream(codec_name='mp3', rate=48000, layout='mono', format='s16')
        audio_stream.thread_type = 'NONE'
        audio_stream.codec_context.time_base = Fraction(1, 48000) #self.time_base
        return container

    def createCropGraph(self):
        graph = Graph()
        screen_width = self.screen.geometry().width()
        screen_height = self.screen.geometry().height()
        input_buffer = graph.add_buffer(
            width=screen_width, height=screen_height, format='bgra'
        )
        pos = self.rect.topLeft()
        crop_filter = graph.add("crop", 'w={}:h={}:x={}:y={}'.format(
            self.rect.width(), self.rect.height(), pos.x(), pos.y())
        )
        last = graph.add('buffersink')
        input_buffer.link_to(crop_filter)
        crop_filter.link_to(last)
        graph.configure()
        return graph

    def start(self, out_path, rect, screen):
        self.rect = rect
        self.screen = screen
        self.out_path = out_path
        br = rect.bottomRight()
        tl = rect.topLeft()
        self.capture_func = partial(self.d3d.screenshot, region=(tl.x(), tl.y(), br.x(), br.y()))
        self.container = self.createContainer(out_path)

        self.crop_graph = self.createCropGraph()

        if self.input_device.isNull():
            return
        self.container.start_encoding()
        self.later = 0

        # audio timer
        self._io_device = self._audio_input.start()
        self._io_device.readyRead.connect(self.onFrameReady)
        self.reference_time = QElapsedTimer()
        self.reference_time.start()

    def stop(self):
        if not self.input_device.isNull(): 
            self._audio_input.stop()

        deferred_cleanup = QTimer.singleShot(1*1000, self.cleanup)

    def cleanup(self):
        container = self.container
        # Flush streams
        try:
            while packet := container.streams.video[0].encode(None):
                container.mux(packet)
        except:
            pass
        try:
            while packet := container.streams.audio[0].encode(None):
                container.mux(packet)
        except:
            pass
        container.close()


    @Slot()
    def onFrameReady(self):
        pts = self.reference_time.elapsed()
        data = self._io_device.readAll()
        audio_data = data.data()
        container = self.container

        # video
        video_stream = container.streams.video[0]
        img_data = self.capture_func()
        screen = self.screen.screen()

        screen_geo = screen.geometry()
        width = screen_geo.width()
        height = screen_geo.height()
        image = np.reshape(img_data, (height, width, 4))

        # get the proper cursor and copy / paint into image.
        cursor, cursor_data = get_cursor_arrays(self.cursor_cache[screen.name()])
        try:
            if cursor_data is not None:
                color, mask = cursor_data
                top_left = screen_geo.topLeft()
                pos = QCursor.pos() - top_left
                x, y = pos.x(), pos.y()
                h, w, _ = color.shape
                #x, y = int(cursor.ptScreenPos.x), int(cursor.ptScreenPos.y) # global position
                slicer = np.s_[y:y+h, x:x+w, :3]
                np.copyto(image[slicer], color, where=mask)
        except ValueError as exerr:
            pass # cursor intersecting or completely out of the capture boundary.

        video_frame = VideoFrame.from_ndarray(image, format='bgra')

        self.crop_graph.push(video_frame)
        filtered_frame = self.crop_graph.pull()
        filtered_frame.pts = pts
        # muxing
        try:
            video_packet = video_stream.encode(filtered_frame)
            container.mux(video_packet)
        except Exception as exerr:
            print(exerr)

        # audio
        audio_stream = container.streams.audio[0]
        if data.size() == 0:
            return

        raw_signal = np.frombuffer(audio_data, np.int16)
        bf = raw_signal.reshape(1, raw_signal.shape[0])

        audio_frame = AudioFrame.from_ndarray(bf, format='s16', layout='mono')
        audio_frame.sample_rate = 48000
        filtered_frame.pts = pts
        try:
            audio_packet = audio_stream.encode(audio_frame)
            container.mux(audio_packet)
        except Exception as exerr:
            print(exerr)


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
        if rect.width() < 8 and rect.height() < 8:
            rect = self.screen().geometry().normalized()
            width = (rect.width() - 1)
            height = (rect.height() - 1)
            rect.setTopLeft(QPoint(1,1))
        else:
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

    onConvertedGif = Signal(object)

    def __init__(self, *args, **kwargs):
        super(CaptureWindow, self).__init__(*args, **kwargs)
        self.pinned = False
        self.setupUi(self)

        # -- System Tray --
        self.tray = QSystemTrayIcon(QIcon(':/resources/icons/capture.svg'), self)
        self.tray.activated.connect(self.toggleVisibility)
        self.tray.show()
        tray_menu = QMenu(self)
        self.tray.setContextMenu(tray_menu)
        self.separator = QAction()
        self.separator.setSeparator(True)
        # -- Actions, Signals & Slots --
        tray_menu.addActions(self.tray_actions)

        gif_action = QAction('Convert To GIF')
        gif_action.triggered.connect(self.convert_to_animated)

        Types.Video.actions.extend([gif_action])

        self.expandButton.clicked.connect(self.adjustSizes)
        self.captureButton.clicked.connect(self.delay_screenshot)
        self.recordButton.clicked.connect(self.perform_recording)

        self.item_model = BaseItemModel(0, 2)
        self.item_model.setHorizontalHeaderLabels(['Item', 'Date'])

        self.searchLine.textChanged.connect(self.searchChanged)

        model_root = self.item_model.invisibleRootItem()
        history_layout = self.historyGroupBox.layout()
        ExpandableGroup.BAR_HEIGHT -= 3
        for item_type in Types:
            tree = HistoryTreeView(self)
            proxy_model = HistoryTreeFilter(item_type)
            proxy_model.setDynamicSortFilter(True)
            proxy_model.setSourceModel(self.item_model)
            tree.setModel(proxy_model)
            
            tree.addActions(self.tree_actions)

            tree.doubleClicked.connect(self.openInViewer)
            tree.resizeColumnToContents(0)
            tree.sortByColumn(1, Qt.AscendingOrder)

            group = ExpandableGroup(tree, parent=self.historyGroupBox)
            group.collapseExpand.connect(self.onGroupCollapse)
            group.iconButton.setIconSize(QSize(18,18))
            group.styledLine.hide()
            group.styledLine_1.hide()
            item_icon = TypesIndicator(int(item_type))
            group.iconButton.setIcon(item_icon.data)
            group.nameLabel.setText(item_type.name)
            group.customContextMenu.connect(self.onContextMenu)

            history_layout.insertWidget(-2, group)
            header = tree.header()
            header.resizeSection(0, 200)
            header.resizeSection(1, 80)
            item_type.group = group
    
        spacer = QSpacerItem(100, 1, QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        history_layout.addItem(spacer)

        self.captureItemsFromFolder(OUTPUT_PATH)

        try: os.mkdir(OUTPUT_PATH + '/previews')
        except: pass
        self.intercom_client = Client('peak')
        self.recorder = Recorder()
        self.recording_thread = QThread(self)
        self.recorder.moveToThread(self.recording_thread)
        self.recording_thread.start()

        self.actions = [
            QAction('Expand All Tabs', self, triggered=lambda : self.setTabsState(True)),
            QAction('Collapse All Tabs', self, triggered=lambda : self.setTabsState(False)), 
            QAction('Enable Order', self, triggered=lambda : self.setOrderingState(True)), 
            QAction('Disable Order', self, triggered=lambda : self.setOrderingState(False)), 
        ]

    @Slot(bool)
    def setOrderingState(self, state):
        [x.group.content.setHeaderHidden(not state) for x in Types]

    @Slot(bool)
    def setTabsState(self, state):
        if state:
            [x.group.expandState() for x in Types]
        else:
            [x.group.collapseState() for x in Types]

    @Slot()
    def onContextMenu(self):
        context_menu = QMenu(self)
        [context_menu.addAction(action) for action in self.actions]
        context_menu.exec(QCursor.pos())

    @cached_property
    def tree_actions(self):
        result = [
            QAction(QIcon(':resources/icons/app_icon.ico'), 'View', self, shortcut='space', triggered=self.view_item),
            QAction(QIcon(':resources/icons/folder.svg'), 'Open File Location', self, shortcut='Ctrl+O', triggered=self.open_location),
            QAction('Copy To Clipboard', self, shortcut='ctrl+c', triggered=self.copy_to_clipboard),
            QAction('Rename', self, triggered=self.rename_item),
            QAction('Delete', self, shortcut='Del', triggered=self.remove_item),
        ]
        return result

    @cached_property
    def tray_actions(self):
        result = [
            QAction('Taskbar Pin Toggle', self, triggered=self.taskbar_pin),
            self.separator,
            QAction('Exit', self, triggered=self._close),
        ]
        return result

    def taskbar_pin(self):
        if self.pinned:
            self.setWindowFlags(self.windowFlags() & ~Qt.FramelessWindowHint)
            self.setProperty('pinned', '0')
            self.show()
        else:
            self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
            self.setProperty('pinned', '1')
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
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
        capture.icon = image
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
        total = operation(group.count, number)
        group.setCount(total)
        group.show()

    def closeEvent(self, event):
        self.hide()
        event.ignore()

    def _close(self):
        self.recording_thread.exit()
        sys.exit()

    def searchChanged(self, text):
        regex = QRegularExpression(text, QRegularExpression.CaseInsensitiveOption)
        for item_type in Types:
            group = item_type.group
            proxy_model = group.content.model()
            proxy_model.setFilterRegularExpression(regex)
            proxy_model.endResetModel()
            rows = proxy_model.rowCount()
            group.setCount(total=group.count, filtered=rows)
            group.show()

    @Slot()
    def openInViewer(self, index):
        capture_obj = index.data(Qt.UserRole)
        if isinstance(capture_obj, CaptureItem):
            self.intercom_client.sendPayload(str(capture_obj.path))
            if self.intercom_client.errored:
                cmd = f'start peak://{capture_obj.path}'
                os.system(cmd)

    @staticmethod
    def renameFile(path, name):
        old = str(path)
        new = str(path.parent / (name + path.ext))
        os.rename(old, new)
        return new

    @Slot()
    def view_item(self):
        item_type, selection_model = self.getActiveSelectionModel()
        indices = selection_model.selectedIndexes()
        if not indices:
            return
        for index in indices:
            self.openInViewer(index)

    @Slot()
    def rename_item(self):
        item_type, selection_model = self.getActiveSelectionModel()
        indices = selection_model.selectedIndexes()
        if not indices:
            return
        items = [self.item_model.indexToItem(x).data(Qt.UserRole) for x in indices]
        filtered = [x for x in items if isinstance(x, CaptureItem)]
        obj = filtered[-1]
        pin_state = self.pinned
        self.pinned = False # prevent popup focus from hiding pin
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
        self.pinned = pin_state

    @Slot()
    def open_location(self):
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
    def remove_item(self):
        item_type, selection_model = self.getActiveSelectionModel()

        if not selection_model.hasSelection():
            return
        count = len(selection_model.selectedRows())
        pin_state = self.pinned # prevent popup focus from hiding pin
        self.pinned = False
        message = QMessageBox.question(self,
                'Confirm', 'Are you sure?',
                buttons=QMessageBox.Yes | QMessageBox.No
                )

        if message == QMessageBox.NoRole:
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
        self.pinned = pin_state

    @Slot()
    def convert_to_animated(self):
        item_type, selection_model = self.getActiveSelectionModel()

        if not selection_model.hasSelection():
            return

        for index in selection_model.selectedIndexes():
            obj = index.data(Qt.UserRole)
            if not isinstance(obj, CaptureItem):
                continue
            new_path = video_to_gif(obj.path)
            item = self.appendItem(Types.Animated, new_path)

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
            self.perform_screenshot(record=True)
        else:
            self.recorder.stop()
            item = self.appendItem(Types.Video, self.out_video)


    def startRecording(self, rect, pixmap, screen):
        self.finishCapture()
        self.show()
        self.screen = screen
        self.rect = rect
        # because D3DShot doesn't allow for restarting the device.
        Singleton._instances = {}
        del self.recorder
        self.recorder = Recorder()
        self.recorder.moveToThread(self.recording_thread)

        # set the direct 3d display from our chosen screen
        for i, screen in enumerate(reversed(self.screens)):
            if self.screen == screen.screen():
                self.recorder.d3d.display = self.recorder.d3d.displays[i]

        self.out_video = new_capture_file(out_format='mp4')
        self.recorder.start(str(self.out_video), rect, screen)

        out_preview = get_preview_path(self.out_video)
        size = ItemDispalyModes.COMPACT.thumb_size
        out_img = makeThumbnail(pixmap)
        out_img.save(str(out_preview))


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
        text_types = [Types.Animated, Types.Video]
        item_type, selection_model = self.getActiveSelectionModel()
        if indices := selection_model.selectedIndexes():
            obj = indices[0].data(Qt.UserRole)
            if obj.type in text_types:
                self.textToClipboard(str(obj.path))
            else:
                img = QImage(str(obj.path))
                self.imageToClipboard(img)

def new_capture_file(out_format='png'):
    date = datetime.utcnow()
    result = Path("{dir}/{name}.{ext}".format(
        dir=OUTPUT_PATH,
        name=date.strftime("%y-%m-%d_%H-%M-%S"),
        ext=out_format,
    ))
    return result

def main(args):
    app = QApplication(args)
    window = CaptureWindow()
    window.setWindowIcon(QIcon(':resources/icons/capture.svg'))
    ctypes.windll.kernel32.SetConsoleTitleW('Capture')
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(u"resarts.relic-capture")
    app.processEvents()
    window.show()
    server = Server('capture')
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
    os.environ['PYAV_LOGGING'] = 'off'
    from intercom import Client
    client = Client('capture')
    client.sendPayload('')
    if client.errored:
        import capture
        capture.app.main(sys.argv)
