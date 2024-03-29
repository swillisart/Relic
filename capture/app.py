import os
import sys
import json
from collections import deque
from fractions import Fraction
from datetime import datetime
from functools import partial, cached_property

# -- Third-party --
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtMultimedia import QAudioFormat, QMediaDevices, QAudioSource, QAudio

from relic.qt.role_model.delegates import ItemDispalyModes
from relic.qt.role_model.models import RoleModel, indexToItem
from relic.qt.role_model.views import RoleHeaderView
from relic.qt.expandable_group import ExpandableGroup
from relic.qt.widgets import SearchBox, AnnotationOverlay, GroupView, OptionBoxAction, LoadingOverlay

from intercom import Client
from sequence_path.main import SequencePath as Path
from qt_logger import registerLogConsoleMenu, attachLogger

import av
import numpy as np
from av.filter import Graph
from av import AudioFrame, VideoFrame
from PyGif.gifski import GifEncoder 
from d3dshot.d3dshot import D3DShot

# -- Module --
import resources
import capture.resources
from capture.config import LOG
from capture.history_view import (Types, CaptureItem, HistoryTreeView, TypesIndicator)
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
GIF_RATE = 15
# 24fps and 48000Hz (48000hz/24fps) = 2000 sample
# 25fps and 48000Hz: (48000hz/25fps) = 1920 sample

ExpandableGroup.ICON_SIZE = QSize(16, 16)
ExpandableGroup.HIDE_EMPTY = False

class HistoryItemModel(RoleModel):

    def supportedDropActions(self):
        return Qt.IgnoreAction | Qt.LinkAction | Qt.CopyAction


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


def videoToGif(obj, progress_callback=None):
    """Convert a video / movie to an animated GIF.
    """
    path = obj.path
    out_path = path.suffixed('', ext='.gif')
    in_container = av.open(str(path))
    in_stream = in_container.streams.video[0]
    in_stream.thread_type = "AUTO"
    width = in_stream.width
    height = in_stream.height
    length = in_stream.frames
    encoder = GifEncoder(str(out_path), width, height)
    solid_alpha = np.empty(shape=(height, width, 4), dtype=np.uint8)
    solid_alpha.fill(255)
    if not progress_callback:
        progress_callback = lambda x: None
    time_scale = 1/GIF_RATE
    pscale = 1/length * 100
    try:
        frame_count = 0
        frames = in_container.decode(video=0)
        for frame_number, frame in enumerate(frames):
            if frame_number % 2 == 0:
                array = frame.to_rgb().to_ndarray()
                solid_alpha[:, :, :3] = array
                timestamp = frame_count * time_scale
                encoder.add_frame(solid_alpha.tobytes(), frame_count, timestamp)
                frame_count += 1
                percent = (frame_number + 1) * pscale
                progress_callback(percent)
    except Exception as exerr:
        in_container.close()
        raise exerr
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


def createContainer(out_path: str, rect: QRect, has_audio: bool):
    # PyAv container and streams
    container = av.open(out_path, 'w')
    args = {
        'tune': 'zerolatency',
        'preset': 'ultrafast',
        'strict': 'unofficial',
        #'b:v': '3000',
        #'minrate:v': '3000',
        #'maxrate:v': '3000',
        #'probesize': '32M',
        #'bufsize': '166M',
        #'sc_threshold': '0',
        #'fflags': 'nobuffer',
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
    if has_audio:
        audio_stream = container.add_stream(
            codec_name='mp3', rate=AUDIO_RATE, layout='mono', format='s16'
        )
        audio_stream.thread_type = 'NONE'
        audio_stream.time_base = Fraction(1, AUDIO_RATE)
    return container


def makeThumbnail(image):
    out_size = ItemDispalyModes.THUMBNAIL.thumb_size
    out_img = QImage(out_size, QImage.Format_RGBA8888)
    out_img.fill(QColor(68, 68, 68, 255))

    alpha_img = image.scaled(out_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    painter = QPainter(out_img)
    painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
    painter.drawImage(0, 0, alpha_img)
    painter.end()
    return out_img


class EncodeImage(QRunnable):

    def __init__(self, container, array, audio, crop_graph, pts, screen, cursor_cache):
        super(EncodeImage, self).__init__()
        self.log = attachLogger(self)
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
        cursor_info, cursor_data = get_cursor_arrays(self.cursor_cache[self.screen.name()])
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
            msg = '%s cursor is likely intersecting or completely out of the capture boundary.'
            self.log.info(msg % exerr)
        return image

    def encodeAudio(self):
        if self.audio is None:
            return
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


class CircleQueue:
    __slots__ = ('mutex', 'queue', 'availibility', 'input_needs')

    def __init__(self):
        # Queues and the worker threads.
        self.queue = deque()
        # Circular semaphores and mutex for locking resources.
        self.mutex = QMutex()
        self.availibility = QSemaphore(0)
        self.input_needs = QSemaphore(1)

    def addToQueue(self, data):
        # __enter__
        self.input_needs.acquire()
        self.mutex.lock()
        # __call__
        self.queue.append(data)
        # __exit__
        self.mutex.unlock()
        self.availibility.release(1)


class CircularQueue(deque):
    # Circular Queues using a mutex and 2 semaphores for locking resources.
    __slots__ = ('mutex', 'availibility', 'input_needs')

    def __init__(self):
        self.mutex = QMutex()
        self.availibility = QSemaphore(0)
        self.input_needs = QSemaphore(1)

    def __enter__(self, *args):
        self.input_needs.acquire()
        self.mutex.lock()
        return self
    
    def __exit__(self, *args):
        self.mutex.unlock()
        self.availibility.release(1)
        return True

    def addToQueue(self, x):
        with self:
            super(CircularQueue, self).append(x)

    def next(self, thread):
        # try to acquire the next item in the queue of availability
        if not self.availibility.tryAcquire(1, 100):
            if thread.isInterruptionRequested():
                return False
            return None
        # Acquired availibility from queue in thread.objectName()
        self.mutex.lock()
        if thread.isInterruptionRequested():
            self.mutex.unlock()
            return False

        result = self.popleft()
    
        self.mutex.unlock()
        self.input_needs.release()
        return result


FRAME_QUEUE = CircleQueue()
JOB_QUEUE = CircularQueue()

def getAudioDevice():
    input_device = QMediaDevices.defaultAudioInput()
    if input_device.isNull():
        LOG.warning('No audio input device found, audio will not be recorded.')
        return None
    msg = ','.join(x.description() for x in QMediaDevices.audioInputs())
    LOG.info('Audio Input Devices Availible: [%s]' % msg)
    LOG.info('Initializing input device for audio source: %s' % (input_device.description()))
    audio_format = QAudioFormat()
    audio_format.setSampleRate(AUDIO_RATE)
    audio_format.setChannelCount(1) # 1 mono, 2 stereo
    audio_format.setSampleFormat(QAudioFormat.Int16)
    audio_input = QAudioSource(input_device, audio_format)
    return audio_input


class Interval(QObject):
    def __init__(self):
        QObject.__init__(self)
        self.audio_input = getAudioDevice()
        self.audio_input.stateChanged.connect(self.onStateChange)
        if self.audio_input is None:
            self.start = self._videoStart
            self.timerEvent = self._vTimerEvent
        else:
            self.start = self._audioStart
            self.timerEvent = self._avTimerEvent
        self.audio_data = None

    @Slot()
    def onStateChange(self, state):
        if state == QAudio.SuspendedState:
            self.killTimer(self.timer_id)
            self.audio_input.stop()

    def _videoStart(self):
        """Start the capture timer at 24fps in precise milisecond intervals"""
        self.startTimer(1000/VIDEO_RATE, Qt.PreciseTimer)

    def _audioStart(self):
        """Start the capture timer at 24fps in precise milisecond intervals"""
        self.io_device = self.audio_input.start()
        self.timer_id = self.startTimer(1000/VIDEO_RATE, Qt.PreciseTimer)

    def _avTimerEvent(self, event):
        audio_data = self.io_device.read(CHUNK_SIZE).data()
        FRAME_QUEUE.addToQueue(audio_data)

    def _vTimerEvent(self, event):
        FRAME_QUEUE.addToQueue(None)


class Recorder(QThread):
    
    started = Signal(object)
    stopped = Signal(object)

    def __init__(self, out_path, rect, screen, has_audio):
        #super(Recorder, self).__init__(parent)
        QThread.__init__(self)
        self.setObjectName('<Recording> Thread')
        FRAME_QUEUE.queue.clear()
        self.circle = FRAME_QUEUE
        self.log = attachLogger(self)
        self.rect = rect
        self.screen = screen
        self.out_path = out_path
        # Initialize Devices
        self.d3d = D3DShot()
        self.capture_func = self.d3d.screenshot

        # AV
        self.container = createContainer(out_path, rect, has_audio)
        self.crop_graph = createCropGraph(screen.geometry(), rect)

        self.log.debug('Initialized image encoding for screen : %s geometry: %s' % (screen.name(), str(screen.geometry())))

        # Create the embedded cursor cache for image injection.
        cursor_cache = {}
        all_screens = QGuiApplication.screens()
        for screen in reversed(all_screens):
            scale = screen.devicePixelRatio()
            cursor_size = int(32 * scale)
            cursor_cache[screen.name()] = build_cursor_data(cursor_size)

        def fmt(x):
            sz = x.size()
            scale = x.devicePixelRatio()
            return f'{int(sz.width()*scale)}x{int(sz.height()*scale)}'

        self.log.debug('Cached per-screen cursor bitmaps for screens: [%s]' % (
            ', '.join([f'{x.name()}: {fmt(x)}' for x in reversed(all_screens)])
        ))
        self.cursor_cache = cursor_cache
        self.encode_pool = QThreadPool()
        self.encode_pool.setMaxThreadCount(1)

    def start(self):
        self.pts = 0 # presentation time stamp
        self.container.start_encoding()
        QThread.start(self)
        self.log.debug('Starting Video and Audio capture.')
        self.log.debug(QThread.currentThread().objectName())

    def cleanup(self):
        container = self.container
        self.log.debug('Flushing streams and closing container.')
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

    def run(self):
        while True: # QWaitCondition
            circle = self.circle
            # try to acquire the next item in the queue of availability
            if not circle.availibility.tryAcquire(1, 100):
                if self.isInterruptionRequested():
                    self.cleanup()
                    return
                continue
            #print('Acquired availibility from queue %s' % currentThreadName())
            with QMutexLocker(circle.mutex):
                if self.isInterruptionRequested():
                    circle.mutex.unlock()
                    self.cleanup()
                    return
                queue = circle.queue
                if len(circle.queue) > 0:
                    data = queue.popleft()
                else:
                    data = None

            circle.input_needs.release()
            self.onFrameReady(data)
            self.msleep(10)

    def onFrameReady(self, audio_data):
        """Encode audio and video to container using the audio input device timing.
        """
        # video
        img_data = self.capture_func()
        #img_data = np.zeros((9216000,), dtype=np.uint8)
        self.pts += 1
        worker = EncodeImage(
            self.container, img_data, audio_data, self.crop_graph, self.pts, self.screen, self.cursor_cache)
        self.encode_pool.start(worker)


class Converter(QThread):
    
    progress = Signal(int)
    complete = Signal(object)

    def __init__(self):
        QThread.__init__(self)
        self.queue = JOB_QUEUE
        self.start()

    def run(self):
        while True: # QWaitCondition
            data = self.queue.next(self)
            if data is False:
                return # interruption was requested end the thread.
            elif data is not None:
                self.process(data)
            self.msleep(10)

    def process(self, index):
        obj = index.data(Qt.UserRole)
        new_path = videoToGif(obj, self.progress.emit)
        self.complete.emit(new_path)


class ScreenOverlay(QDialog):

    clipped = Signal(QRect, QImage, QScreen)

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
        ).toImage()

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
        painter.drawImage(0, 0, self.screens_snapshot)
        pen = QPen(QColor(0, 0, 0, 200), 2, Qt.DotLine)
        self.drawCrosshairs(painter, rect + QMargins(2,2,0,0), pen)
        pen = QPen(QColor(255, 255, 255, 100), 2, Qt.DotLine)
        self.drawCrosshairs(painter, rect, pen)

        # Selected Region
        painter.setBrush(QColor(120, 165, 225, 25))
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.selection_rect)

    def mouseReleaseEvent(self, event):
        super(ScreenOverlay, self).mouseReleaseEvent(event)
        self.clip()

    def clip(self):
        rect = self.selection_rect.normalized()
        scale = self.screen().devicePixelRatio()
        screen_rect = self.screen().geometry().normalized()

        if rect.width() < 8 and rect.height() < 8:
            rect = screen_rect
            rect.setTopLeft(QPoint(0,0))
        else:
            rect.setTopLeft(rect.topLeft() * scale)

        # Pad the rect to a multiple of 16. (optimization for h264 & jpeg)
        w = int(rect.width() * scale)
        h = int(rect.height() * scale)
        while w_mod := w % 16:
            w += w_mod
        while h_mod := h % 16:
            h += h_mod

        # Move the rect if the bounds are outside the screen.
        w_diff = (rect.x() + w) - (screen_rect.x() + screen_rect.width())
        h_diff = (rect.y() + h) - (screen_rect.y() + screen_rect.height())

        rect.setWidth(w)
        rect.setHeight(h)
        if w_diff > 0:
            rect.adjust(-w_diff, 0, -w_diff, 0)
        if h_diff > 0:
            rect.adjust(0, -h_diff, 0, -h_diff)

        # Crop the image and emit the clipped signal for further operations.
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


class TrayOverlay(AnnotationOverlay):

    def paintEvent(self, event):
        """ Draw a chip arrow pointing to the tray icon."""
        painter = QPainter(self)
        pen = QPen(QColor(232, 114, 109), 1, Qt.SolidLine)
        brush = QBrush(QColor(150, 70, 68), Qt.SolidPattern)
        painter.setPen(pen)
        painter.setBrush(brush)
        
        tray_rect = self.geometry()

        r = event.rect()
        baseline = r.height() - tray_rect.height() - 1
        #painter.drawLine(r.left(), baseline, r.right(), baseline)
        painter.setRenderHint(QPainter.Antialiasing, True)

        chip = self.mapFromGlobal(tray_rect.center() - QPoint(-1, (tray_rect.height() / 4) + 1))
        other = tray_rect.width() / 4 
        a = QPoint(chip.x() - other, baseline+1)
        b = QPoint(chip.x() + other, baseline+1)
        c = chip
        positions = [a, b, c]
        painter.drawPolygon(positions, Qt.OddEvenFill)


class LoadBarOverlay(LoadingOverlay):

    def __init__(self, *args, **kwargs):
        super(LoadBarOverlay, self).__init__(*args, **kwargs)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setFont(QFont('Arial', 8))
        self.progress_bar.setMaximumHeight(12)
        self.progress_bar.setMaximumWidth(128)
        self.layout.addWidget(self.progress_bar)

    def paintEvent(self, event):
        painter = QPainter(self)
        self.color.setAlpha(self._opaque)
        painter.setBrush(self.color)
        painter.setPen(Qt.NoPen)
        # Set layout to 5% of the parent widget size.
        rect = self.geometry()
        w = rect.width() * 0.01
        h = rect.height() * 0.01
        margins = QMargins(w, h, w, h)
        painter.drawRect(rect - margins)


class CaptureWindow(QWidget, Ui_ScreenCapture):

    onConvertedGif = Signal(object)
    stopRecording = Signal()

    def __init__(self, *args, **kwargs):
        super(CaptureWindow, self).__init__(*args, **kwargs)
        self.pinned = False
        self.setupUi(self)
        self.log = attachLogger(self)

        # -- System Tray --
        self.tray_icon = QIcon(':icons/capture.svg')
        self.tray_icon_hilight = QIcon(':icons/capture_hilight.svg')
        self.tray = QSystemTrayIcon(self.tray_icon, self)
        self.tray.activated.connect(self.toggleVisibility)
        self.tray.setToolTip(TRAY_TIP)
        self.tray.show()

        tray_menu = QMenu(self)
        registerLogConsoleMenu(tray_menu, parent=self)

        self.tray.setContextMenu(tray_menu)
        self.separator = QAction()
        self.separator.setSeparator(True)
        # -- Actions, Signals & Slots --
        tray_menu.addActions(self.tray_actions)

        gif_action = OptionBoxAction(self)
        gif_action.setShortcut(QKeySequence('Ctrl+G'))
        gif_action.setIcon(QIcon(':type/gif.png'))
        gif_action.setText('Convert to GIF')
        gif_action.main_triggered.connect(self.convertToGif)
        gif_action.option_triggered.connect(lambda : print('option box clicked'))

        Types.Video.actions.extend([gif_action])

        #temp_action = QAction('Add Description')
        #temp_action.triggered.connect(self.addDescription)
        #Types.Video.actions.extend([temp_action])

        self.expandButton.clicked.connect(self.adjustSizes)
        self.captureButton.clicked.connect(self.delayScreenshot)
        self.recordButton.clicked.connect(self.performRecording)
        self.pinButton.toggled.connect(self.taskbar_pin)

        self.item_model = HistoryItemModel()
        self.item_model.setColumnCount(2)

        history_layout = self.historyGroupBox.layout()

        self.group_view = GroupView(self.item_model, HistoryTreeView, ExpandableGroup, self)
        self.group_view.createGroups(TypesIndicator, 'type')

        self.searchLine = SearchBox(self)
        self.searchLine.editor.textChanged.connect(self.group_view.filterAll)
        history_layout.addWidget(self.searchLine)

        for tab in self.group_view.tabs:
            tab.collapseExpand.connect(self.onGroupChange)
            tab.styledLine.hide()

            tree = tab.content
            tree.addActions(self.tree_actions)
            tree.doubleClicked.connect(self.openInViewer)
            header = RoleHeaderView()
            header.setModel(self.item_model)
            header.createAttributeLabels(['title', 'date', 'size'], visible=['title', 'date'])
            tree.setHeader(header)
            tree.sortByColumn(1, Qt.DescendingOrder)
            header.resizeSection(0, 200)
            header.resizeSection(1, 80)

        history_layout.addWidget(self.group_view)

        self.captureItemsFromFolder(OUTPUT_PATH)

        try: os.mkdir(OUTPUT_PATH + '/previews')
        except: pass
        self.peak_client = Client('peak')
        QThread.currentThread().setObjectName('<Main> Thread')
        self.recorder = None

    def main(self, args):
        if args.get('screenshot'):
            self.performScreenshot()
        elif args.get('record'):
            self.recordButton.click()

    @Slot()
    def addDescription(self):
        """
        Create "MetaMod" class wrapper usage:
        with MetaMod(file_path) as src, dst:
            f.metadata['description'] = 'Artist note (description of work done / revisions made).'
            f.metadata['framerange'] = '1001-1025'
        """
        selection_model = self.getActiveSelectionModel()

        if not selection_model.hasSelection():
            return

        for index in selection_model.selectedIndexes():
            obj = index.data(Qt.UserRole)
            if not isinstance(obj, CaptureItem):
                continue

            container = av.open(str(obj.path))
            in_stream = container.streams.video[0]
            output = av.open(str(obj.path).replace(".mp4", ".mkv"), "w")

            output.metadata['description'] = 'Artist note (description of work done / revisions made).'
            output.metadata['framerange'] = '1001-1025'

            out_stream = output.add_stream(template=in_stream)
            for packet in container.demux(in_stream):
                if packet.dts is None:
                    continue
                packet.stream = out_stream
                output.mux(packet)

            output.close()
            container.close()


    @Slot(bool)
    def setGroupState(self, state):
        if state:
            [x.group.expandState() for x in Types]
        else:
            [x.group.collapseState() for x in Types]

    def setVerticalHandleState(self, state):
        [tab.verticalControl.setVisible(not state) for tab in self.group_view.tabs]

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
                    self.tray_overlay.close()
                elif not self.isActiveWindow():
                    self.tray.setIcon(self.tray_icon)
                    self.hide()
                    self.tray_overlay.close()
                else:
                    self.createTrayOverlay()
                    self.tray.setIcon(self.tray_icon_hilight)
        return super(CaptureWindow, self).changeEvent(event)

    @property
    def tray_overlay(self):
        try:
            return self._tray_overlay
        except AttributeError:
            return self.createTrayOverlay()

    def createTrayOverlay(self):
        self._tray_overlay = TrayOverlay(self.tray.geometry())
        self._tray_overlay.raise_()
        return self._tray_overlay

    def showEvent(self, event):
        super(CaptureWindow, self).showEvent(event)
        self.old_size = self.historyGroupBox.size()

    @Slot()
    def adjustSizes(self, val): 
        window = self.window()
        if not val:
            self.old_size = self.historyGroupBox.size()
        rect = self.geometry()
        self.historyGroupBox.setVisible(val)
        if not val:
            rect = rect - QMargins(0, self.old_size.height(), 0, 0)
        else:
            rect = rect + QMargins(0, self.old_size.height(), 0, 0)
        self.adjustSize()
        window.setGeometry(rect)

    @Slot()
    def onGroupChange(self, state):
        group = self.sender()
        geo = self.geometry()        
        adjustment = group.expand_height - group.bar_height
        if not state:
            self.historyGroupBox.hide()
            self.historyGroupBox.show()
            new_size = geo.size() - QSize(0, adjustment)
            new_pos = geo.topLeft() + QPoint(0, adjustment)
        else:
            new_size = geo.size() + QSize(0, adjustment)
            new_pos = geo.topLeft() - QPoint(0, adjustment)
        geo.setTopLeft(new_pos)
        geo.setSize(new_size)
        self.setGeometry(geo)
        window = self.window()

    def getActiveSelectionModel(self):
        for tab in self.group_view.tabs:
            tree = tab.content
            if tree.hasFocus():
                return tree.selectionModel()

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

        self.group_view.updateGroups()

    def appendItem(self, item_type, in_file):
        model_root = self.item_model.invisibleRootItem()
        image = QImage()
        image.load(str(getPreviewPath(in_file)))
        capture = CaptureItem(in_file)
        # side-load the image into the item parent class cache.
        capture.image = image
        capture.type = int(item_type)
        self.item_model.appendItemsFromData(capture, model_root)

    def closeEvent(self, event):
        self.hide()
        event.ignore()

    def _close(self):
        if hasattr(self, 'recorder') and self.recorder is not None:
            if self.recorder.isRunning():
                self.stopIt()
        sys.exit()

    @Slot()
    def openInViewer(self, index):
        capture_obj = index.data(Qt.UserRole)
        if isinstance(capture_obj, CaptureItem):
            self.peak_client.sendPayload(json.dumps({'path': str(capture_obj.path)}))
            if self.peak_client.errored:
                cmd = f'start peak://{capture_obj.path}'
                os.system(cmd)

    @staticmethod
    def renameFile(path, name):
        old = path
        new = path.parent / (name + path.ext)
        if os.path.exists(str(new)): # rename to avoid overwrite
            new = path.parent / (name + '1' + path.ext)
        os.rename(str(old), str(new))
        return new

    @Slot()
    def view_item(self):
        selection_model = self.getActiveSelectionModel()
        indices = selection_model.selectedIndexes()
        if not indices:
            return
        for index in indices:
            self.openInViewer(index)

    @Slot()
    def rename_item(self):
        selection_model = self.getActiveSelectionModel()
        proxy_model = selection_model.model()
        indices = [proxy_model.index(x.row(), 0) for x in selection_model.selectedIndexes()]
        if not indices:
            return
        index = indices[-1]
        obj = indexToItem(index).data(Qt.UserRole)

        pin_state = self.pinned
        self.pinned = False # prevent popup focus from hiding pin
        new_name, ok = QInputDialog.getText(self, 'Rename',
                "New name:", QLineEdit.Normal,
                obj.path.name)
        if ok:
            old_preview_path = getPreviewPath(obj.path)
            old_path = Path(str(obj.path))
            new_path = self.renameFile(old_path, new_name)
            preview_path = getPreviewPath(new_path)
            self.renameFile(old_preview_path, new_path.name)
            obj.path = new_path
            obj.title.text = new_name
        self.pinned = pin_state
        index.model().dataChanged.emit(index, index, [Qt.DisplayRole, Qt.UserRole]) # DisplayRole
        proxy_model.endResetModel()

    @Slot()
    def open_location(self):
        selection_model = self.getActiveSelectionModel()
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
        selection_model = self.getActiveSelectionModel()
        if not selection_model.hasSelection():
            return
        item_type = selection_model.selectedIndexes()[0].data(Qt.UserRole).type

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

            item = indexToItem(index)
            item_parent = item.parent()
            if item_parent:
                item_parent.removeRow(item.index().row())
            else:
                model.removeRow(item.index().row())

            preview_path = getPreviewPath(obj.path)
            if preview_path.exists():
                # If the preview is shared by another item dont delete it.
                has_shared_preview = False
                for shared_capture in shared_captures:
                    if shared_capture.name == obj.name:
                        has_shared_preview = True
                        break
                if not has_shared_preview:
                    os.remove(str(preview_path))
            if obj.path.exists():
                os.remove(str(obj.path))
            count += 1

        tab = self.group_view.tabs[item_type]
        tab.setCount(tab.count - count)
        self.pinned = pin_state

    @Slot()
    def convertToGif(self):
        selection_model = self.getActiveSelectionModel()
        if not selection_model.hasSelection():
            return
        msg = 'Converting to GIF...'
        bg = QColor(68, 68, 68)
        self.convert_overlay = LoadBarOverlay(self, text=msg, color=bg)
        self.convert_thread = Converter()
        self.convert_thread.complete.connect(self.onConversionCompleted)
        self.convert_thread.progress.connect(self.convert_overlay.progress_bar.setValue)
        for index in selection_model.selectedIndexes():
            obj = index.data(Qt.UserRole)
            if not isinstance(obj, CaptureItem):
                continue
            self.convert_thread.queue.addToQueue(index)

    @Slot(Path)
    def onConversionCompleted(self, path):
        self.appendItem(Types.Animated, path)
        self.group_view.updateGroups()
        self.convert_overlay.complete()
        thread = self.sender()
        thread.requestInterruption()
        thread.quit()
        thread.wait()
        thread.deleteLater()

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
    def performRecording(self, state=True):
        if state:
            self.performScreenshot(record=True)
        else:
            self.stopRecording.emit()
            self.appendItem(Types.Video, self.out_video)
        self.group_view.updateGroups()

    def startRecording(self, rect, pixmap, screen):
        self.finishCapture()
        self.show()
        self.out_video = newCaptureFile(out_format='mp4')
        # because D3DShot doesn't allow for restarting the device.
        self.log.debug('Restarting D3DShot')

        self.log.debug('Creating new Recorder')
        self.interval = Interval()
        has_audio = self.interval.audio_input is not None
        del self.recorder
        self.recorder = Recorder(str(self.out_video), rect, screen, has_audio)
        self.stopRecording.connect(self.stopIt)
        # set the direct 3d display from our chosen screen
        found = False
        dis = (len(self.recorder.d3d.displays), len(self.screens))
        self.log.debug('Mapping D3DShot displays (%d) to Qt screens (%d)' % dis) 
        for i, this_screen in enumerate(reversed(self.screens)):
            if screen == this_screen.screen():
                self.recorder.d3d.display = self.recorder.d3d.displays[i]
                found = True
                break

        if not found:
            self.log.error('Failed to find screen')
            return

        out_preview = getPreviewPath(self.out_video)
        size = ItemDispalyModes.COMPACT.thumb_size
        out_img = makeThumbnail(pixmap)
        out_img.save(str(out_preview))
        self.recorder.start()
        self.interval.start()
        self.log.debug('Threaded Recording started')

    def stopIt(self):
        self.log.debug('Stopping recording')
        self.recorder.requestInterruption()
        self.recorder.quit()
        self.recorder.wait()
        self.interval.audio_input.suspend()
        self.interval.deleteLater()

    @Slot()
    def saveScreenshot(self, rect, image, screen):
        path = newCaptureFile()
        image.save(str(path))
        icon_image = makeThumbnail(image)
        icon_image.save(str(getPreviewPath(path)))
        self.imageToClipboard(image)
        self.finishCapture()
        item = self.appendItem(Types.Screenshot, path)
        index = self.item_model.indexFromItem(item)
        self.group_view.updateGroups()
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
        selection_model = self.getActiveSelectionModel()
        if not selection_model:
            return
        if indices := selection_model.selectedIndexes():
            obj = indices[0].data(Qt.UserRole)
            if obj.type in text_types:
                self.textToClipboard(str(obj.path))
            else:
                img = QImage(str(obj.path))
                self.imageToClipboard(img)
