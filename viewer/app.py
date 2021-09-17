# -- Built-in --
import ctypes
import os
import sys
import time
from functools import partial

import numpy as np
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtOpenGL import *
from PySide2.QtWidgets import *
#from qtshared2.styleWatcher import StylesheetWatcher
from qtshared2.utils import loadStyleFromFile
from qtshared2.svg import rasterizeSVG
from qtshared2.widgets import (CompactTitleBar, HoverTintButton,
                              InteractiveSpinBox)
# -- Third-party --
from sequencePath import sequencePath as Path
from strand2.server import StrandServer

# -- Module --
import resources_rc
import viewer.resources
from viewer import io
from viewer.timeline import ClipA, Graph, timelineGLView
from viewer.ui import playerWidget
from viewer.ui.widgets import PaintDockWidget
from viewer.viewport import Viewport
from viewer.config import PEAK_PREFS

# Interaction modes
VIEW = 0
PAINT = 1

SHORTCUTS = {
    VIEW: [],
    PAINT: [],
}

SHORTCUT_MODE = VIEW

class ViewerTitleBar(CompactTitleBar):
    def __init__(self, *args, **kwargs):
        super(ViewerTitleBar, self).__init__(*args, **kwargs)
        self.makeWindowButtons()
        self.exposure_control = InteractiveSpinBox(
            self, minimum=-10000, maximum=10000, decimals=3, default=0.0, speed=0.1)
        self.gamma_control = InteractiveSpinBox(
            self, minimum=0.1, maximum=10000, decimals=3, default=1.0, speed=0.01)

        title_label = QLabel('Viewer')
        # Buttons
        icon_size = QSize(16, 16)
        exposure_icon = rasterizeSVG(':/resources/aperture.svg', icon_size).toImage()
        gamma_icon = rasterizeSVG(':/resources/gamma.svg', icon_size).toImage()
        ocio_icon = rasterizeSVG(':/resources/ocio.svg', icon_size).toImage()
        app_icon = rasterizeSVG(':/resources/icons/peak.svg', icon_size).toImage()
        self.icon_button = HoverTintButton(app_icon, size=icon_size)
        self.exposure_toggle = HoverTintButton(exposure_icon, size=icon_size)
        self.gamma_toggle = HoverTintButton(gamma_icon, size=icon_size)
        self.ocio_toggle = HoverTintButton(ocio_icon, size=icon_size)

        self.color_views = QComboBox(self)
        self.exposure_toggle.clicked.connect(self.resetExposure)
        self.gamma_toggle.clicked.connect(self.resetGamma)

        self.left_layout.addWidget(self.icon_button)
        self.left_layout.addWidget(title_label)
        self.center_layout.addWidget(self.exposure_toggle)
        self.center_layout.addWidget(self.exposure_control)
        self.center_layout.addWidget(self.gamma_toggle)
        self.center_layout.addWidget(self.gamma_control)
        self.center_layout.addWidget(self.ocio_toggle)
        self.center_layout.addWidget(self.color_views)

    def resetGamma(self):
        value = self.gamma_control.value()
        if value == 1.0:
            value = float(PEAK_PREFS.gamma)
        else:
            PEAK_PREFS.gamma = value
            value = 1.0

        self.gamma_control.setValue(value)

    def resetExposure(self):
        value = self.exposure_control.value()
        if value == 0.0:
            value = float(PEAK_PREFS.exposure)
        else:
            PEAK_PREFS.exposure = value
            value = 0.0

        self.exposure_control.setValue(value)


class PlayerAppWindow(QMainWindow):
    def __init__(self, parent=None):
        super(PlayerAppWindow, self).__init__(parent)
        self.cache = {}
        self.title_bar = ViewerTitleBar(self)
        self.setWindowFlags(Qt.CustomizeWindowHint)
        self.setAcceptDrops(True)

        # System Tray 
        app_icon = QIcon(':/resources/icons/peak.svg')
        self.tray = QSystemTrayIcon(app_icon, self)
        self.tray.activated.connect(self.toggleVisibility)
        self.tray.show()

        tray_menu = QMenu(self)
        close_action = tray_menu.addAction("Exit")
        close_action.triggered.connect(self.close)
        self.tray.setContextMenu(tray_menu)


        self.viewport = Viewport(self)
        self.timeline = timelineGLView()
        self.timeline.frameMapping.connect(self.loadFrames)
        self.timeline.frameJump.connect(self.playbackToggle)
        self.timeline.annotatedLoad.connect(self.viewAnnotated)
        self.timeline.mouseInteracted.connect(self.refreshViewport)
        self.setCentralWidget(self.viewport)
        self.createDocks()

        self.thread = io.workers.loaderThread()
        self.qt_thread = io.workers.QuicktimeThread(self)
        self.qt_thread.loadedImage.connect(self.loadFrameData)
        self.thread.loadedImage.connect(self.updateCache)
        self.worker = None

        # -- Signals / Slots --
        self.title_bar.gamma_control.valueChanged.connect(self.viewport.setGamma)
        self.title_bar.exposure_control.valueChanged.connect(self.viewport.setExposure)
        self.title_bar.color_views.currentIndexChanged.connect(self.viewport.setColorspace)
        self.viewport.colorConfigChanged.connect(self.title_bar.color_views.addItems)
        self.viewport.finishAnnotation.connect(self.saveAnnotation)

        # -- Shortcuts --
        channel_call = self.viewport.setColorChannel
        shuffle_red = partial(channel_call, 'r')
        shuffle_green = partial(channel_call, 'g')
        shuffle_blue = partial(channel_call, 'b')

        QShortcut(QKeySequence('alt+v'), self, self.playbackToggle)
        QShortcut(QKeySequence('ctrl+f'), self, self.fullscreen)
        SHORTCUTS[VIEW].append(QShortcut(QKeySequence('space'), self, self.playbackToggle))
        SHORTCUTS[VIEW].append(QShortcut(QKeySequence('r'), self, shuffle_red))
        SHORTCUTS[VIEW].append(QShortcut(QKeySequence('g'), self, shuffle_green))
        SHORTCUTS[VIEW].append(QShortcut(QKeySequence('b'), self, shuffle_blue))
        SHORTCUTS[VIEW].append(QShortcut(QKeySequence('p'), self, self.paintContext))

        QShortcut(QKeySequence('right'), self, self.timeline.controller.oneFrameForward)
        QShortcut(QKeySequence('left'), self, self.timeline.controller.oneFrameBackward)
        QShortcut(QKeySequence('ctrl+left'), self, self.timeline.controller.stepBackward)
        QShortcut(QKeySequence('ctrl+right'), self, self.timeline.controller.stepForward)
        QShortcut(QKeySequence('`'), self, self.theatreMode)

        self.viewport.setColorConfig()
        #self.loadFile('E:/OneDrive/Documents/Scripts/standalone_apps/peak/tests/SteinsGateChickenTenders.mp4', reset=False)
        #self.loadFile("P:\Photos\ingesttest_data\DJI00067\DJI00067.mp4", reset=False)

    def setShorctutMode(self, mode):
        for index in SHORTCUTS:
            is_mode = mode == index
            for shortcut in SHORTCUTS[index]:
                shortcut.setEnabled(is_mode)

    @Slot()
    def paintContext(self):
        paint_mode = self.viewport.togglePaintContext()
        self.paint_dock.setVisible(paint_mode)
        self.setShorctutMode(PAINT) if paint_mode else self.setShorctutMode(VIEW)

    @Slot()
    def clearAnnotation(self):
        self.viewport.paint_engine.clear()
        self.viewport.makeCurrent()
        self.viewport.image_plane.resetAnnotation()

        clip = self.timeline.current_clip
        frame = clip.mapToLocalFrame(self.timeline.current_frame)
        for i, x in enumerate(clip.annotations):
            if x == frame:
                clip.annotations.pop(i)
        folder = clip.annotation_folder
        remove_path = clip.annotated(frame)
        os.remove(str(remove_path))
        self.timeline.makeCurrent()
        self.timeline.updateNodeGlyphs()

    @Slot()
    def saveAnnotation(self, image):
        self.viewport.paint_engine.clear()
        clip = self.timeline.current_clip
        frame = clip.mapToLocalFrame(self.timeline.current_frame)
        clip.annotations.append(frame)
        folder = clip.annotation_folder
        save_path = clip.annotated(frame)
        if not folder.exists:
            folder.path.mkdir()
        image.save(str(save_path))
        self.timeline.makeCurrent()
        self.timeline.updateNodeGlyphs()

    @Slot()
    def viewAnnotated(self, frame, clip):
        self.viewport.makeCurrent()
        annotation_img = clip.loadAnnotation(frame)
        clip.geometry.setAnnotation(annotation_img)
        self.viewport.update()

    def fullscreen(self):
        self.showNormal() if self.isMaximized() else self.showMaximized()

    def theatreMode(self):
        if self.title_dock.isVisible():
            self.player_dock.hide()
            self.title_dock.hide()
            self.viewport.bgc = 0
            self.viewport.framebuffer.bgc = 0
        else:
            self.player_dock.show()
            self.title_dock.show()
            self.viewport.framebuffer.bgc = 0.18

    def createDocks(self):
        self.setDockNestingEnabled(True)
        dock = PaintDockWidget()
        dock.colorChanged.connect(self.viewport.paint_engine.brush.setColor)
        dock.toolChanged.connect(self.viewport.setActiveTool)
        dock.saveButton.clicked.connect(self.paintContext)
        dock.clearButton.clicked.connect(self.clearAnnotation)
        dock.shapeTypeCombobox.currentIndexChanged.connect(self.viewport.setShapeType)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)
        dock.setFloating(True)
        dock.hide()
        self.paint_dock = dock

        dock = QDockWidget('Titlebar')
        empty_widget = QFrame(self)
        empty_widget.setFrameShadow(QFrame.Raised)
        empty_widget.setFrameShape(QFrame.HLine)
        empty_widget.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed))
        empty_widget.setFixedHeight(1)
        dock.setWidget(empty_widget)
        dock.layout().setContentsMargins(0,0,0,0)
        dock.layout().setSpacing(0)
        dock.setAllowedAreas(Qt.TopDockWidgetArea)
        dock.setTitleBarWidget(self.title_bar)
        self.title_dock = dock

        self.addDockWidget(Qt.TopDockWidgetArea, dock)

        dock = QDockWidget('Timeline')
        dock.setAllowedAreas(Qt.BottomDockWidgetArea)
        dock.setFeatures(dock.features() | QDockWidget.DockWidgetVerticalTitleBar)
        self.player = playerWidget(self, self.viewport, self.timeline)
        dock.setTitleBarWidget(self.player)
        dock.setWidget(self.timeline)
        self.player_dock = dock

        self.addDockWidget(Qt.BottomDockWidgetArea, dock)


    @Slot()
    def playbackToggle(self, stop=False):
        if stop and self.timeline.controller.state() != 2:
            return
        if self.timeline.controller.state() == 2:
            self.player.play.setChecked(False)
        else:
            self.player.play.setChecked(True)
        self.timeline.controller.play()
        self.viewport.makeCurrent()
        if self.viewport.image_plane:
            self.viewport.image_plane.resetAnnotation()


    @Slot()
    def loadFrames(self, frame, clip, graph):
        if not hasattr(clip, 'geometry'):
            return

        self.viewport.makeCurrent()
        self.viewport.image_plane = clip.geometry

        if clip.type == clip.MOVIE:
            local_frame = clip.mapToLocalFrame(frame)
            if local_frame is False:
                return
            is_next_frame = local_frame == (self.qt_thread.frame + 1)
            if clip is not self.qt_thread.clip or not is_next_frame:
                self.playbackToggle()
                self.qt_thread.stop()
                self.qt_thread.setupRead(clip, local_frame)
                self.qt_thread.start()
                self.playbackToggle()
            else:
                self.qt_thread.frame = local_frame
                self.qt_thread.start()
            return

        self.loadFrame(frame)
        if self.notInCache(frame):
            if clip.mapToLocalFrame(frame) is False:
                return
            self.thread.pool.clear()
            while self.thread.pool.activeThreadCount() != 0:
                QApplication.processEvents()
                time.sleep(0.1)
            self.cache = {}

            self.thread.load(frame, clip, graph)
            deferred_load = partial(self.loadFrame, frame)
            self.deferred_frame_load = QTimer.singleShot(600, deferred_load)
            return

        global_diff = frame - self.thread.frame
        if global_diff == frame:
            self.thread.load(frame, clip, graph)
        
        elif global_diff >= -50:
            gframe = frame + abs(global_diff)
            self.thread.load(gframe, clip, graph)

    def notInCache(self, frame):
        cached_frames = self.cache.keys()
        if cached_frames:
            if frame < min(cached_frames) or frame > (max(cached_frames) + 1):
                return True

    def loadFrameData(self, frame_array):
        self.viewport.makeCurrent()
        self.viewport.image_plane.updateTexture(frame_array)
        self.viewport.update()

    def loadFrame(self, frame):
        mapped = self.cache.get(frame)
        if isinstance(mapped, np.ndarray):
            self.loadFrameData(mapped)

    @Slot()
    def updateCache(self, frame, image):
        self.cache[frame] = image
        frames = self.cache.keys()
        left = min(frames)
        right = max(frames)

        if len(frames) >= 125:
            self.cache.pop(left)
            left = min(self.cache.keys())
        self.timeline.updateCacheSize(left, right)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def refreshViewport(self, value):
        self.viewport.makeCurrent()
        self.viewport.update()

    def dropEvent(self, event):
        self.viewport.makeCurrent()
        if event.mimeData().hasUrls:
            event.setDropAction(Qt.CopyAction)
            event.accept()
            for url in event.mimeData().urls():
                self.loadFile(url.toLocalFile(), reset=False)
        else:
            event.ignore()

    def loadFile(self, path, reset=True):
        # Bring focus to the window
        self.grab()
        self.setVisible(True)
        self.activateWindow()
        self.raise_()
        stripped = str(path).replace('peak://', '')
        file_path = Path(stripped, checksequence=True)
        # Resolve the sequence and set the timeline offset
        offset = 0
        if self.timeline.graph.nodes.count and not reset:
            offset = self.timeline.graph.clips[-1][-1].timeline_out + 1
        else:
            self.cache = {}
            self.viewport.makeCurrent()
            if hasattr(self.timeline.current_clip, 'geometry'):
                self.timeline.current_clip.geometry.clear()

            self.timeline.graph = Graph(shader=self.timeline.primitive_shader)

        self.viewport.makeCurrent()
        clip = ClipA(file_path, timeline_in=offset)
        self.timeline.makeCurrent()
        self.timeline.graph.appendClip(clip, 0)
        if reset: #or self.timeline.graph.nodes.count == 1:
            self.timeline.reset(clip)
            self.timeline.frameGeometry()
            self.loadFrames(offset, clip, self.timeline.graph)
            self.viewport.frameGeometry()
        else:
            self.timeline.updateNodeGlyphs()

    def hide(self):
        self.thread.stop()
        self.qt_thread.stop()
        self.thread.pool.clear()
        self.cache = {}
        #sequence = Sequence()
        #clip = ClipA()
        #sequence.appendClip(clip)
        #self.timeline.graph = [sequence]
        #self.timeline.reset(clip)
        super(PlayerAppWindow, self).hide()

    def closeEvent(self, event):
        self.thread.stop()
        self.qt_thread.stop()
        self.thread.pool.clear()
        super(PlayerAppWindow, self).closeEvent(event)

    @Slot()
    def toggleVisibility(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.grab()
            self.setVisible(not self.isVisible())
            self.activateWindow()
            self.raise_()


def main(args):
    app = QApplication(sys.argv)
    # Sets a 4x MSAA surface format to all QGLWidgets creatin in this application
    gl_format = QGLFormat()
    gl_format.setSamples(4)
    QGLFormat.setDefaultFormat(gl_format)

    # C Python Windowing
    ctypes.windll.kernel32.SetConsoleTitleW("Peak")
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(u"resarts.peak")
    app.processEvents()
    window = PlayerAppWindow()
    window.setWindowIcon(QIcon(':resources/icons/peak.svg'))
    loadStyleFromFile(window, ':style.qss')

    #watcher = StylesheetWatcher()
    #watcher.watch(window, 'P:/Code/Relic/viewer/style.qss')
    window.resize(1024, 512)
    window.show()
    server = StrandServer('peak')
    server.incomingFile.connect(window.loadFile)
    if args:
        if args.path:
            window.loadFile(args.path)
        if args.annotate:
            window.paint_dock.setFloating(False)
            window.paintContext()

    sys.exit(app.exec_())
