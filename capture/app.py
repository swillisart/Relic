import os
import sys
import operator
import timeit
import subprocess
from fractions import Fraction
from datetime import datetime
from functools import partial, cached_property
from enum import IntEnum
from collections import deque

# -- Third-party --
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtMultimedia import QAudioFormat, QMediaDevices, QAudioSource, QAudio
from relic.qt.delegates import ItemDispalyModes, BaseItemModel
from relic.qt.expandable_group import ExpandableGroup
from relic.qt.widgets import SearchBox

from intercom import Client
from sequence_path.main import SequencePath as Path
from extra_types.enums import DataAutoEnum

import av
import numpy as np
from av.filter import Graph
from av import AudioFrame, VideoFrame
from PyGif.gifski import GifEncoder
from d3dshot.d3dshot import D3DShot, Singleton

# -- Module --
import resources
import capture.resources
from capture.history_view import (CaptureItem, HistoryTreeFilter, HistoryTreeView, TypesIndicator)
from capture.ui.dialog import Ui_ScreenCapture
from capture.cursor import get_cursor_arrays, build_cursor_data
from capture.windowing import getForegroundWindow, isWindowOccluded

# -- Globals --
OUTPUT_PATH = "{}/Videos".format(os.getenv("USERPROFILE"))

TRAY_TIP = """Screen Capture :
- Right-click for options.
- Double-click to capture.
- Middle-click to record.
"""
DELAYS = (0, 1, 3, 5)
AUDIO_RATE = 48000
VIDEO_RATE = 25
CHUNK_SIZE = 3840
# 24fps and 48000Hz (48000hz/24fps) = 2000 sample
# 25fps and 48000Hz: (48000hz/25fps) = 1920 sample

# -- Functions --
def newCaptureFile(out_format='png'):
    date = datetime.utcnow()
    result = Path("{dir}/{name}.{ext}".format(
        dir=OUTPUT_PATH,
        name=date.strftime("%y-%m-%d_%H-%M-%S"),
        ext=out_format,
    ))
    return result


def getPreviewPath(path):
    preview = (path.parent / 'previews' / path.stem)
    preview.ext = '.jpg'
    return preview


def videoToGif(path):
    out_path = path.suffixed('', ext='.gif')
    in_container = av.open(str(path))
    in_stream = in_container.streams.video[0]
    in_stream.thread_type = "AUTO"
    width = in_stream.width
    height = in_stream.height
    encoder = GifEncoder(str(out_path), width, height)
    solid_alpha = np.empty(shape=(height, width, 4), dtype=np.uint8)
    solid_alpha.fill(255)
    try:
        frame_count = 0
        for frame_number, frame in enumerate(in_container.decode(video=0)):
            if frame_number % 2 == 0:
                array = frame.to_rgb().to_ndarray()
                solid_alpha[:, :, :3] = array
                timestamp = (frame_count+1)/15
                encoder.add_frame(solid_alpha.tobytes(), frame_count, timestamp)
                frame_count += 1
    except Exception as exerr:
        print(exerr)
        return None
    finally:
        in_container.close()

    return out_path


def createCropGraph(screen_geo, rect):
    graph = Graph()
    input_buffer = graph.add_buffer(
        width=screen_geo.width(), height=screen_geo.height(), format='bgra'
    )
    pos = rect.topLeft()
    crop_filter = graph.add(
        'crop',
        f'w={rect.width()}:h={rect.height()}:x={pos.x()}:y={pos.y()}'
    )
    last = graph.add('buffersink')
    input_buffer.link_to(crop_filter)
    crop_filter.link_to(last)
    graph.configure()
    return graph


def createContainer(out_path, rect):
    # PyAv container and streams
    container = av.open(out_path, 'w')
    args = {
        'tune': 'zerolatency',
        'preset': 'ultrafast',
        'b:v': '3000',
        'minrate:v': '3000',
        'maxrate:v': '3000',
        'probesize': '32M',
        'bufsize': '166M',
        'sc_threshold': '0',
        'fflags': 'nobuffer',
        'crf': '28',
    }
    # Video
    video_stream = container.add_stream('libx264', rate=VIDEO_RATE, options=args)
    video_stream.pix_fmt = 'yuv420p'
    video_stream.width = rect.width()
    video_stream.height = rect.height()
    video_stream.thread_type = 'NONE'
    video_stream.time_base = Fraction(1, 1000)
    # Audio 
    audio_stream = container.add_stream(
        codec_name='mp3', rate=AUDIO_RATE, layout='mono', format='s16'
    )
    audio_stream.thread_type = 'NONE'
    audio_stream.time_base = Fraction(1, AUDIO_RATE)
    return container


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


class EncodeImage(QRunnable):

    def __init__(self, container, array, audio, crop_graph, pts, screen, cursor_cache):
        super(EncodeImage, self).__init__()
        self.container = container
        self.array = array
        self.crop_graph = crop_graph
        self.pts = pts
        self.screen = screen
        self.cursor_cache = cursor_cache
        self.audio = audio

    def injectCursor(self):
        screen_geo = self.screen.geometry()
        width = screen_geo.width()
        height = screen_geo.height()
        image = np.reshape(self.array, (height, width, 4))

        # get the proper cursor and copy / paint into image.
        cursor, cursor_data = get_cursor_arrays(self.cursor_cache[self.screen.name()])
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
            # cursor intersecting or completely out of the capture boundary.
            #print('Cursor Error:', exerr)
            pass
        return image

    def encodeAudio(self):
        audio_stream = self.container.streams.audio[0]
        raw_signal = np.frombuffer(self.audio, np.int16)
        bf = raw_signal.reshape(1, raw_signal.shape[0])
        #bf = np.zeros((1, 1920), dtype=np.int16)
        audio_frame = AudioFrame.from_ndarray(bf, format='s16', layout='mono')
        audio_frame.sample_rate = AUDIO_RATE
        audio_frame.time_base = Fraction(1, AUDIO_RATE)
        audio_frame.pts = (1/VIDEO_RATE) * AUDIO_RATE * self.pts
        packets = audio_stream.encode(audio_frame)
        self.container.mux(packets)

    def run(self):
        # process
        image = self.injectCursor()
        video_frame = VideoFrame.from_ndarray(image, format='bgra')
        self.crop_graph.push(video_frame)
        frame = self.crop_graph.pull()
        frame.time_base = Fraction(1, VIDEO_RATE)
        frame.pts = self.pts
        # encode
        video_stream = self.container.streams.video[0]
        video_packets = video_stream.encode(frame)
        self.container.mux(video_packets)
        self.encodeAudio()


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


class Recorder(QObject):

    def __init__(self, parent=None):
        super(Recorder, self).__init__(parent)
        self.d3d = D3DShot()
        self.input_device = QMediaDevices.defaultAudioInput()
        audio_format = QAudioFormat()
        audio_format.setSampleRate(AUDIO_RATE)
        audio_format.setChannelCount(1) # 1 mono, 2 stereo
        audio_format.setSampleFormat(QAudioFormat.Int16)

        if not self.input_device.isNull():
            self._audio_input = QAudioSource(self.input_device, audio_format, self)

        cursor_cache = {}
        for screen in reversed(QGuiApplication.screens()):
            scale = screen.devicePixelRatio()
            cursor_size = int(32 * scale)
            cursor_cache[screen.name()] = build_cursor_data(cursor_size)
        self.cursor_cache = cursor_cache
        self.encode_pool = QThreadPool()
        self.encode_pool.setMaxThreadCount(1)

    def start(self, out_path, rect, screen):
        self.rect = rect
        self.screen = screen
        self.out_path = out_path
        br = rect.bottomRight()
        tl = rect.topLeft()
        self.capture_func = partial(self.d3d.screenshot, region=(tl.x(), tl.y(), br.x(), br.y()))
        self.container = createContainer(out_path, rect)

        self.crop_graph = createCropGraph(self.screen.geometry(), rect)

        if self.input_device.isNull():
            return
        self.container.start_encoding()

        # audio timer
        self.pts = 0
        self._io_device = self._audio_input.start()
        self._io_device.readyRead.connect(self.onFrameReady)

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
        # audio
        audio_data = self._io_device.read(CHUNK_SIZE).data()

        # video
        img_data = self.capture_func()
        #img_data = np.zeros((9216000,), dtype=np.uint8)
        screen = self.screen.screen()
        self.pts += 1
        worker = EncodeImage(
            self.container, img_data, audio_data, self.crop_graph, self.pts, screen, self.cursor_cache)
        self.encode_pool.start(worker)


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
        painter.setPen(pen)
        # Painting at cursors "origin" initial click position.
        origin = self.origin_pos
        painter.drawLine(rect.left(), origin.y(), rect.right(), origin.y())
        painter.drawLine(origin.x(), rect.top(), origin.x(), rect.bottom())

        # Painting at cursors current "active" movement position.
        active = self.active_pos
        painter.drawLine(rect.left(), active.y(), rect.right(), active.y())
        painter.drawLine(active.x(), rect.top(), active.x(), rect.bottom())

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
                (self.origin_pos),
                (self.active_pos)
            )
        self.repaint()


class TrayOverlay(QDialog):

    def __init__(self, *args, **kwargs):
        """A transparent tool dialog for annotating a hilight overly to the screen.
        """
        super(TrayOverlay, self).__init__(*args, **kwargs)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.X11BypassWindowManagerHint
            | Qt.ToolTip
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.tray = None

    def paintEvent(self, event):
        painter = QPainter(self)
        pen = QPen(QColor(232, 114, 109), 1, Qt.SolidLine)
        brush = QBrush(QColor(150, 70, 68), Qt.SolidPattern)
        painter.setPen(pen)
        painter.setBrush(brush)
        
        tray_rect = self.tray.geometry()

        r = event.rect()
        baseline = r.height() - tray_rect.height() - 1
        painter.drawLine(r.left(), baseline, r.right(), baseline)
        painter.setRenderHint(QPainter.Antialiasing, True)

        chip = self.mapFromGlobal(tray_rect.center() - QPoint(-1, (tray_rect.height() / 4) + 1))
        other = tray_rect.width() / 4 
        a = QPoint(chip.x() - other, baseline+1)
        b = QPoint(chip.x() + other, baseline+1)
        c = chip
        positions = [a, b, c]
        painter.drawPolygon(positions, Qt.OddEvenFill)


class CaptureWindow(QWidget, Ui_ScreenCapture):

    onConvertedGif = Signal(object)

    def __init__(self, *args, **kwargs):
        super(CaptureWindow, self).__init__(*args, **kwargs)
        self.pinned = False
        self.setupUi(self)
        # -- System Tray --
        self.tray_icon = QIcon(':icons/capture.svg')
        self.tray_icon_hilight = QIcon(':icons/capture_hilight.svg')
        self.tray = QSystemTrayIcon(self.tray_icon, self)
        self.tray.activated.connect(self.toggleVisibility)
        self.tray.setToolTip(TRAY_TIP)
        self.tray.show()

        tray_menu = QMenu(self)
        self.tray.setContextMenu(tray_menu)
        self.separator = QAction()
        self.separator.setSeparator(True)
        # -- Actions, Signals & Slots --
        tray_menu.addActions(self.tray_actions)

        gif_action = QAction('Convert To GIF')
        gif_action.triggered.connect(self.convertToGif)

        Types.Video.actions.extend([gif_action])

        self.expandButton.clicked.connect(self.adjustSizes)
        self.captureButton.clicked.connect(self.delayScreenshot)
        self.recordButton.clicked.connect(self.performRecording)
        self.pinButton.toggled.connect(self.taskbar_pin)

        self.item_model = BaseItemModel(0, 2)
        self.item_model.setHorizontalHeaderLabels(['Item', 'Date'])

        self.searchLine = SearchBox(self)
        self.searchLine.editor.textChanged.connect(self.searchChanged)

        model_root = self.item_model.invisibleRootItem()
        history_layout = self.historyGroupBox.layout()
        history_layout.insertWidget(0, self.searchLine)
        ExpandableGroup.BAR_HEIGHT -= 3
        for item_type in Types:
            tree = HistoryTreeView(self)
            header = tree.header()

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
            header.setSectionsMovable(True)
            header.setFirstSectionMovable(True)
            header.setContextMenuPolicy(Qt.CustomContextMenu)
            header.customContextMenuRequested.connect(self.onHeaderContextMenu)
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
        order_action = QAction('Column Headers', self, checkable=True, checked=True)
        order_action.toggled.connect(self.toggleOrderingState)

        self.group_actions = [
            QAction('Expand All Groups', self, triggered=lambda : self.setGroupState(True)),
            QAction('Collapse All Groups', self, triggered=lambda : self.setGroupState(False)), 
            order_action,
        ]
        self.header_menu = QMenu(self)
        for action in ('Date', 'User', 'Item'):
            checkbox = QCheckBox(action, self.header_menu)
            action = QWidgetAction(self.header_menu)
            action.setDefaultWidget(checkbox)
            self.header_menu.addAction(action)

    def onHeaderContextMenu(self):
        self.header_menu.exec(QCursor.pos())

    def onContextMenu(self):
        menu = QMenu(self)
        menu.addActions(self.group_actions)
        menu.exec(QCursor.pos())

    @Slot(bool)
    def toggleOrderingState(self, state):
        [x.group.content.setHeaderHidden(not state) for x in Types]

    @Slot(bool)
    def setGroupState(self, state):
        if state:
            [x.group.expandState() for x in Types]
        else:
            [x.group.collapseState() for x in Types]

    def setVerticalHandleState(self, state):
        [x.group.verticalControl.setVisible(not state) for x in Types]

    @cached_property
    def tree_actions(self):
        sep = QAction(self)
        sep.setSeparator(True)
        result = (
            QAction(QIcon(':resources/app/peak.svg'), 'View', self, shortcut='space', triggered=self.view_item),
            QAction(QIcon(':icons/folder.svg'), 'Open File Location', self, shortcut='ctrl+o', triggered=self.open_location),
            QAction('Copy To Clipboard', self, shortcut='ctrl+c', triggered=self.copyItemToClipboard),
            sep,
            QAction('Rename', self, triggered=self.rename_item),
            QAction('Delete', self, shortcut='Del', triggered=self.remove_item),
        )
        return result

    @cached_property
    def tray_actions(self):
        pin_action = QAction('Pinned To Taskbar', self, checkable=True, checked=True)
        pin_action.toggled.connect(self.taskbar_pin)
        self.pin_action = pin_action
        result = (
            self.pin_action,
            self.separator,
            QAction(QIcon(':/style/close.svg'), 'Exit', self, triggered=self._close),
        )
        return result

    @Slot()
    def taskbar_pin(self, state):
        if not state:
            self.setWindowFlags(self.windowFlags() & ~Qt.FramelessWindowHint)
            self.setProperty('pinned', '0')
            self.setVerticalHandleState(False)
            self.show()
            this_rect = self.frameGeometry() + QMargins(1, 1, 0, 0)
        else:
            self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
            self.setVerticalHandleState(True)
            self.setProperty('pinned', '1')
            this_rect = self.geometry()
        self.style().unpolish(self)
        self.style().polish(self)

        # Reposition the resized window to the tray icon
        self.update()
        tray_rect = self.tray.geometry()
        for screen in QGuiApplication.screens():
            screen_rect = screen.geometry()
            if screen_rect.contains(tray_rect):
                break
        distance_to_edge = screen_rect.width() - tray_rect.x()
        diff = this_rect.width() - distance_to_edge

        self.move(tray_rect.x() - diff, tray_rect.y() - this_rect.height())
        self.pinned = state

        if self.sender() is self.pinButton:
            self.pin_action.setChecked(state)
            if state:
                self.createTrayOverlay()
                self.tray.setIcon(self.tray_icon_hilight)
                self.show()
            else:
                self.tray.setIcon(self.tray_icon)

                self.tray_overlay.hide()
        else:
            self.pinButton.setChecked(state)

    def changeEvent(self, event):
        if self.pinned:
            if event.type() == QEvent.ActivationChange:
                if self.tray_overlay.isActiveWindow():
                    self.tray_overlay.hide()
                elif not self.isActiveWindow():
                    self.tray.setIcon(self.tray_icon)
                    self.hide()
                    self.tray_overlay.hide()
                else:
                    self.createTrayOverlay()
                    self.tray.setIcon(self.tray_icon_hilight)
        return super(CaptureWindow, self).changeEvent(event)

    @cached_property
    def tray_overlay(self):
        overlay = TrayOverlay()
        overlay.tray = self.tray
        return overlay

    def createTrayOverlay(self):
        tray_over = self.tray_overlay
        tray_rect = self.tray.geometry()
        tray_pad = QMargins(0, 0, 0, tray_rect.height())
        goemetry_with_tray = self.geometry() + tray_pad
        tray_over.setGeometry(goemetry_with_tray)
        tray_over.raise_()
        tray_over.show()

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
        image = QPixmap(str(getPreviewPath(in_file)))
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
        proxy_model = selection_model.model()
        indices = [proxy_model.index(x.row(), 0) for x in selection_model.selectedIndexes()]
        if not indices:
            return
        obj = self.item_model.indexToItem(indices[-1]).data(Qt.UserRole)
        pin_state = self.pinned
        self.pinned = False # prevent popup focus from hiding pin
        new_name, ok = QInputDialog.getText(self, 'Rename',
                "New name:", QLineEdit.Normal,
                obj.path.name)
        if ok:
            old_preview_path = getPreviewPath(obj.path)
            old_path = Path(str(obj.path))
            obj.path.name = new_name
            obj.name = new_name
            self.renameFile(old_path, new_name)
            preview_path = getPreviewPath(obj.path)
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
        pin_state = self.pinned # prevent popup focus from hiding pin
        self.pinned = False
        message = QMessageBox.question(self,
                'Confirm', 'Are you sure?',
                buttons=QMessageBox.Yes | QMessageBox.No
        )

        if message == QMessageBox.No:
            return

        model = self.item_model
        # Shared captures will re-use thumbnails across multiple items.
        # If removing an item with a shared preview dont delete its preview image.
        shared_captures = []
        for row in range(model.rowCount()):
            item = model.item(row)
            capture = item.data(Qt.UserRole)
            if capture.type not in (item_type, Types.Screenshot):
                shared_captures.append(capture)

        count = 0
        while indices := selection_model.selectedIndexes():
            index = indices[0]
            obj = index.data(Qt.UserRole)
            if not isinstance(obj, CaptureItem):
                selection_model.select(index, QItemSelectionModel.Deselect)
                continue

            item = model.indexToItem(index)
            item_parent = item.parent()
            if item_parent:
                item_parent.removeRow(item.index().row())
            else:
                model.removeRow(item.index().row())

            preview_path = getPreviewPath(obj.path)
            if preview_path.exists():
                # If the preview is shared by another item dont delete it.
                hase_shared_preview = False
                for shared_capture in shared_captures:
                    if shared_capture.name == obj.name:
                        hase_shared_preview = True
                        break
                if not hase_shared_preview:
                    os.remove(str(preview_path))
            if obj.path.exists():
                os.remove(str(obj.path))
            count += 1

        self.change_count(operator.sub, item_type, count)
        self.pinned = pin_state

    @Slot()
    def convertToGif(self):
        item_type, selection_model = self.getActiveSelectionModel()

        if not selection_model.hasSelection():
            return

        for index in selection_model.selectedIndexes():
            obj = index.data(Qt.UserRole)
            if not isinstance(obj, CaptureItem):
                continue
            new_path = videoToGif(obj.path)
            if new_path is None:
                return
            item = self.appendItem(Types.Animated, new_path)

    @Slot()
    def delayScreenshot(self):
        msg = 'Delaying the capture for {} seconds. /n/Click to cancel.'
        index = self.delayComboBox.currentIndex()
        seconds = DELAYS[index]
        self.deferred_snap = QTimer.singleShot(seconds*1000, self.performScreenshot)

    def performScreenshot(self, record=False):
        slot = self.startRecording if record else self.saveScreenshot
        self.hide()
        self.screens = []
        for screen in reversed(QGuiApplication.screens()):
            screen_overlay = ScreenOverlay(screen)
            screen_overlay.clipped.connect(slot)
            screen_overlay.show()
            self.screens.append(screen_overlay)

    @Slot()
    def performRecording(self, state):
        if state:
            self.performScreenshot(record=True)
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

        self.out_video = newCaptureFile(out_format='mp4')
        self.recorder.start(str(self.out_video), rect, screen)

        out_preview = getPreviewPath(self.out_video)
        size = ItemDispalyModes.COMPACT.thumb_size
        out_img = makeThumbnail(pixmap)
        out_img.save(str(out_preview))

    @Slot()
    def saveScreenshot(self, rect, pixmap, screen):
        path = newCaptureFile()
        pixmap.save(str(path))
        icon_pixmap = makeThumbnail(pixmap)
        icon_pixmap.save(str(getPreviewPath(path)))
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
        fg_hwnd = getForegroundWindow()
        this_hwnd = self.winId()
        reasons = QSystemTrayIcon.ActivationReason
        if reason == reasons.DoubleClick:
            self.setVisible(False)
            self.performScreenshot()
        elif reason == reasons.MiddleClick:
            self.setVisible(False)
            self.recordButton.click()

        if self.isVisible():
            if isWindowOccluded(this_hwnd):
                self.grab()
                self.activateWindow()
                self.raise_()
            else:
                self.hide()
        elif reason == reasons.Trigger:
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

    def copyItemToClipboard(self):
        text_types = [Types.Animated, Types.Video]
        item_type, selection_model = self.getActiveSelectionModel()
        if indices := selection_model.selectedIndexes():
            obj = indices[0].data(Qt.UserRole)
            if obj.type in text_types:
                self.textToClipboard(str(obj.path))
            else:
                img = QImage(str(obj.path))
                self.imageToClipboard(img)
