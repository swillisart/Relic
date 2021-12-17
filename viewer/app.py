# -- Built-in --
import ctypes
import os
import sys
import time
import json
from functools import partial

# -- Third-party --
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
# -- First-Party -- 
from sequencePath import sequencePath as Path
from strand2.server import StrandServer
import relic_base

# -- Module --
import resources_rc
import viewer.resources
from viewer import io
from viewer.timeline import ClipA, Graph, timelineGLView
from viewer.ui import playerWidget
from viewer.ui.widgets import PaintDockWidget
from viewer.viewport import Viewport
from viewer import config

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
        self.exposure_control.setStatusTip('Exposure Control Value')

        self.gamma_control = InteractiveSpinBox(
            self, minimum=0.1, maximum=10000, decimals=3, default=1.0, speed=0.01)
        self.gamma_control.setStatusTip('Exposure Control Value')

        # Buttons
        icon_size = QSize(16, 16)
        exposure_icon = rasterizeSVG(':/resources/aperture.svg', icon_size).toImage()
        gamma_icon = QImage(':/resources/gammaCurve.png').scaled(
            icon_size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        ocio_icon = rasterizeSVG(':/resources/ocio.svg', icon_size).toImage()
        app_icon = rasterizeSVG(':/resources/icons/peak.svg', icon_size).toImage()
        self.icon_button = HoverTintButton(app_icon, size=icon_size)
        self.exposure_toggle = HoverTintButton(exposure_icon, size=icon_size)
        self.exposure_toggle.setStatusTip('Exposure. (Toggles exposure from current value to 0.0)')
        self.gamma_toggle = HoverTintButton(gamma_icon, size=icon_size)
        self.gamma_toggle.setStatusTip('Gamma (Toggles gamma to and from 1.0)')
        self.ocio_toggle = HoverTintButton(ocio_icon, size=icon_size)

        self.color_views = QComboBox(self)
        self.color_views.setStatusTip('OCIO Colorspace (View Transform)')
        self.exposure_toggle.clicked.connect(self.resetExposure)
        self.gamma_toggle.clicked.connect(self.resetGamma)
        self.zoom_ratios = QComboBox(self)
        self.zoom_ratios.setStatusTip('Zoom level (Percentage)')
        for item in config.ZOOM_RATIOS:
            self.zoom_ratios.addItem(f'{item} %', item)
        #self.zoom_ratios.setSizePolicy(
        #    QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred))
        self.zoom_ratios.setFixedWidth(18)

        self.left_layout.addWidget(self.icon_button)
        self.center_layout.addWidget(self.exposure_toggle)
        self.center_layout.addWidget(self.exposure_control)
        self.center_layout.addWidget(self.gamma_toggle)
        self.center_layout.addWidget(self.gamma_control)
        self.center_layout.addWidget(self.ocio_toggle)
        self.center_layout.addWidget(self.color_views)
        self.center_layout.addWidget(self.zoom_ratios)

        self.menubar = QMenuBar(self)
        self.menubar.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))

        self.left_layout.addWidget(self.menubar)
        self.menuFile = self.menubar.addMenu('File')
        #self.menuFile.setTearOffEnabled(True)

        for label in config.FILE_ACTIONS:
            action = QAction(label, self)
            # set class variable -> self.exitAction
            setattr(self, label.lower()+'Action', action) 
            self.menuFile.addAction(action)

    def resetGamma(self):
        value = self.gamma_control.value()
        if value == 1.0:
            value = float(config.PEAK_PREFS.gamma)
        else:
            config.PEAK_PREFS.gamma = value
            value = 1.0

        self.gamma_control.setValue(value)

    def resetExposure(self):
        value = self.exposure_control.value()
        if value == 0.0:
            value = float(config.PEAK_PREFS.exposure)
        else:
            config.PEAK_PREFS.exposure = value
            value = 0.0

        self.exposure_control.setValue(value)


class PlayerAppWindow(QMainWindow):
    def __init__(self, parent=None):
        super(PlayerAppWindow, self).__init__(parent)
        self.cache = {}
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint)
        self.setAcceptDrops(True)

        # widgets

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
        self.setCentralWidget(self.viewport)
        self.title_bar = ViewerTitleBar(self)
        self.timeline = timelineGLView(self)
        self.timelineFrame = QFrame(self)
        timeline_layout = QHBoxLayout()
        timeline_layout.addWidget(self.timeline)
        timeline_layout.setContentsMargins(4, 0, 4, 0)
        timeline_layout.setSpacing(2)
        self.timelineFrame.setLayout(timeline_layout)
        self.player = playerWidget(self, self.viewport, self.timeline)
        self.createDocks()

        # Status bar
        self.statusbar = QStatusBar(self)
        self.statusbar.setObjectName(u"statusbar")
        self.setStatusBar(self.statusbar)

        # Layouts
        self.thread = io.workers.loaderThread()
        self.qt_thread = io.workers.QuicktimeThread(self)
        self.meta_thread = io.workers.ExifWorker(self)
        self.meta_thread.metaLoaded.connect(self.movieDataRecieved)
        self.meta_thread.start()

        self.qt_thread.loadedImage.connect(self.loadFrameData)
        self.thread.loadedImage.connect(self.updateCache)
        self.worker = None

        # -- Signals / Slots --
        zoom_callback = lambda x: self.viewport.setZoom(config.ZOOM_RATIOS[x])
        self.title_bar.zoom_ratios.currentIndexChanged.connect(zoom_callback)
        self.title_bar.gamma_control.valueChanged.connect(self.viewport.setGamma)
        self.title_bar.exposure_control.valueChanged.connect(self.viewport.setExposure)
        self.title_bar.color_views.currentIndexChanged.connect(self.viewport.setColorspace)
        self.title_bar.exitAction.triggered.connect(self.close)
        self.title_bar.newAction.triggered.connect(self.newSession)

        self.viewport.colorConfigChanged.connect(self.title_bar.color_views.addItems)
        self.viewport.finishAnnotation.connect(self.saveAnnotation)
        self.viewport.zoomChanged.connect(self.setZoomValue)

        self.timeline.frameMapping.connect(self.loadFrames)
        self.timeline.frameJump.connect(self.playbackToggle)
        self.timeline.annotatedLoad.connect(self.viewAnnotated)
        self.timeline.mouseInteracted.connect(self.refreshViewport)
    
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

    def movieDataRecieved(self, clip, data):
        self.viewport.makeCurrent()
        clip.setMovieData(
            data.get('Duration'),
            data.get('ImageSize'),
            data.get('VideoFrameRate')
        )
        self.viewport.update()
        self.timeline.makeCurrent()
        self.timeline.graph.appendClip(clip, 0)
        if self.timeline.current_frame == clip.timeline_in:
            self.loadFrames(self.timeline.current_frame, clip)
            self.timeline.current_clip = clip
            self.timeline.frameGeometry()
        self.timeline.update()

    @Slot()
    def setZoomValue(self, percent):
        zoom_widget = self.title_bar.zoom_ratios
        zoom_widget.blockSignals(True)
        zoom_widget.setCurrentIndex(0)
        zoom_widget.blockSignals(False)
        zoom_widget.setItemData(0, f'{percent} %', Qt.DisplayRole)
        zoom_widget.setItemData(0, percent)
        config.ZOOM_RATIOS[0] = percent

    @Slot()
    def newSession(self):
        self.viewport.makeCurrent()
        self.viewport.image_plane = None
        if hasattr(self.timeline.current_clip, 'geometry'):
            self.timeline.current_clip.geometry.clear()
        self.timeline.makeCurrent()
        self.timeline.graph.clear()
        self.timeline.reset(ClipA())
        self.timeline.frameGeometry()

    def setShorctutMode(self, mode):
        for index in SHORTCUTS:
            is_mode = mode == index
            for shortcut in SHORTCUTS[index]:
                shortcut.setEnabled(is_mode)

    def closePaint(self):
        paint_mode = self.viewport.togglePaintContext(save=False)
        self.paint_dock.hide()
        self.setShorctutMode(PAINT) if paint_mode else self.setShorctutMode(VIEW)

    @Slot()
    def paintContext(self):
        paint_mode = self.viewport.togglePaintContext(save=True)
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
        if remove_path.exists:
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
        clip.geometry.no_annotation = False
        self.viewport.update()

    def fullscreen(self):
        self.showNormal() if self.isMaximized() else self.showMaximized()

    def theatreMode(self):
        if self.title_dock.isVisible():
            self.player_dock.hide()
            self.title_dock.hide()
            self.statusbar.hide()
            self.viewport.bgc = 0
            self.viewport.framebuffer.bgc = 0
        else:
            self.statusbar.show()
            self.player_dock.show()
            self.title_dock.show()
            self.viewport.framebuffer.bgc = 0.18

    def createDocks(self):
        self.setDockNestingEnabled(True)
        dock = PaintDockWidget()
        dock.colorChanged.connect(self.viewport.paint_engine.brush.setColor)
        dock.toolChanged.connect(self.viewport.setActiveTool)
        dock.onClosed.connect(self.closePaint)
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
        dock.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed))
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
        dock.setTitleBarWidget(self.player)
        dock.setWidget(self.timelineFrame)
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

    @Slot()
    def loadFrames(self, frame, clip):
        if not hasattr(clip, 'geometry'):
            return

        self.viewport.makeCurrent()
        self.viewport.image_plane = clip.geometry
        if not clip.geometry.no_annotation:
            clip.geometry.resetAnnotation()

        if clip.type == clip.MOVIE:
            local_frame = clip.mapToLocalFrame(frame)
            if local_frame is False:
                return
            is_next_frame = local_frame == (self.qt_thread.frame + 1)
            is_late = local_frame == (self.qt_thread.frame + 2)
            if clip is not self.qt_thread.clip or not is_next_frame and not is_late:
                self.timeline.controller.setFramerate(clip.framerate)
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
                time.sleep(0.05)
            self.cache = {}

            self.thread.load(frame, clip, self.timeline.graph)
            deferred_load = partial(self.loadFrame, frame)
            self.deferred_frame_load = QTimer.singleShot(600, deferred_load)
            return

        global_diff = frame - self.thread.frame
        if global_diff == frame:
            self.thread.load(frame, clip, self.timeline.graph)
        elif global_diff >= -50:
            gframe = frame + abs(global_diff)
            self.thread.load(gframe, clip, self.timeline.graph)
        self.viewport.update()

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
        data = event.mimeData()
        if data.hasUrls:
            if data.hasFormat('application/x-relic'):
                assets = data.text()
                for key, values in json.loads(assets).items():
                    constructor = relic_base.asset_classes.getCategoryConstructor(key)
                    for fields in values:
                        asset = constructor(**fields)
                        self.loadFile(asset.network_path, reset=False)
            else:
                event.setDropAction(Qt.CopyAction)
                event.accept()
                for url in data.urls():
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
        if clip.type == ClipA.MOVIE:
            self.meta_thread.addToQueue(clip)
        else:
            self.timeline.graph.appendClip(clip, 0)
        if reset or self.timeline.graph.nodes.count == 1:
            self.timeline.reset(clip)
            self.timeline.frameGeometry()
            self.loadFrames(offset, clip)
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
        self.meta_thread.stop()
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
    app.setEffectEnabled(Qt.UI_AnimateCombo, False)
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
