# -- Built-in --
import ctypes
import os
import sys
import timeit
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
from viewer.timeline import MovClip, SeqClip, ImageClip, Graph, timelineGLView
from viewer.ui import playerWidget
from viewer.ui.widgets import PaintDock, ColorPickerkDock, AnnotationDock
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

class timelineControl(QTimeLine):

    def __init__(self, *args, **kwargs):
        super(timelineControl, self).__init__(*args, **kwargs)
        self.end = 864000
        self.setFrameRange(1, self.end)
        self.fps = 24
        self.setFramerate()
        self.setLoopCount(0)
        self.setCurveShape(QTimeLine.LinearCurve)
        self.setUpdateInterval(0.25)

    @property
    def frame(self):
        return self.frameForTime(self.currentTime())

    @property
    def endTime(self):
        return (self.end - 1) * self.millisec_fps # millisec conversion

    @property
    def millisec_fps(self):
        return (1000 / self.fps)

    def setFramerate(self, rate=23.976):
        old_rate = self.fps
        self.fps = rate
        miliseconds_duration = self.end * (1000 / rate) # millisec conversion
        duration_div = miliseconds_duration / (self.end * (1000 / old_rate))
        self.setDuration(miliseconds_duration)
        # Block update signals to prevent recursive loop.
        self.blockSignals(True)
        new = (self.frame + 1) * (1000 / (rate))
        self.setCurrentTime( new * duration_div)
        self.blockSignals(False)

    def play(self):
        state = self.state()
        if state in [0, 1]:
            self.resume()
        if state == 2:
            self.stop()

    def jumpFirst(self):
        self.setFrame(0)

    def jumpLast(self):
        self.setCurrentTime(self.endTime)

    def stepForward(self):
        new_time = (((self.frame - 1) + self.fps) * self.millisec_fps)
        self.setCurrentTime(new_time)

    def stepBackward(self):
        new_time = ((self.frame - self.fps) * self.millisec_fps)
        self.setCurrentTime(new_time)

    def oneFrameForward(self):
        self.setCurrentTime(int(self.currentTime() + self.millisec_fps))

    def oneFrameBackward(self):
        self.setCurrentTime(int(self.currentTime() - self.millisec_fps))

    def setFrame(self, frame):
        new_time = (frame * self.millisec_fps)
        self.setCurrentTime(new_time)


class FrameEngine(QObject):

    LOOK_AHEAD = 0
    REGION = 1
    CACHE = {}

    def __init__(self, parent, timeline, viewport):
        QObject.__init__(self, parent)
        self.mode = FrameEngine.LOOK_AHEAD
        self.parent = parent
        self.thread = io.workers.FrameThread(FrameEngine.CACHE, self)
        self.thread.signals.frame_ready.connect(self.updateCache)
        self.thread.signals.finished.connect(self.onCacheFinished)
        self.thread.start(priority=QThread.LowPriority)
        self.mov_thread = io.workers.QuicktimeThread(FrameEngine.CACHE, self)
        self.mov_thread.signals.frame_ready.connect(self.updateCache)
        self.mov_thread.signals.finished.connect(self.onCacheFinished)
        self.mov_thread.start()
        self.frame_io_thread = io.workers.FrameCacheIOThread(FrameEngine.CACHE, self)
        self.frame_io_thread.start(priority=QThread.LowestPriority)
        self.timeline_control = timelineControl()
        self.timeline_control.frameChanged.connect(self.onFrameChange)
        self.timeline = timeline
        self.timeline.frameJump.connect(self.onFrameJump)
        self.viewport = viewport
        self.minc = 10000
        self.maxc = 0
        self.cache_number = 0
        self.is_caching = False
        self.cache_end = 0
        self.deferred_frame_jump = None

    @Slot(int)
    def onFrameJump(self, frame):
        if self.is_caching:
            if not frame in FrameEngine.CACHE and not self.deferred_frame_jump:
                deferred_load = partial(self.onFrameJump, frame)
                self.deferred_frame_jump = QTimer.singleShot(600, deferred_load)
                return
        else:
            self.deferred_frame_jump = None

        if self.mode == FrameEngine.LOOK_AHEAD:
            clip, clip_frame = self.timeline.getClipOnFrame(frame)
            self.timeline.current_clip = clip
            if isinstance(clip, MovClip):
                self.mov_thread.setClip(clip, clip_frame, frame)
        
        self.timeline_control.setFrame(frame)

    def setRegionCache(self):
        if self.timeline.selected_clips:
            clip = self.timeline.selected_clips[-1]
            clip_size = (clip.geometry.pixels.nbytes * clip.duration)
            if io.util.fitsInMemory(clip_size):
                self.mode = FrameEngine.REGION
                self.regionCaching(clip)
        else:
            self.mode = FrameEngine.LOOK_AHEAD

        return self.mode

    @Slot()
    def onCacheFinished(self):
        self.is_caching = False
        self.timeline.makeCurrent()
        self.timeline.drawViewport()

    @Slot(int)
    def updateCache(self, frame):
        sender = self.sender()
        if frame < self.minc:
            self.minc = frame
        elif frame > self.maxc:
            self.maxc = frame
        self.cache_number += 1

        self.timeline.updateCacheSize(self.minc, self.maxc)

        # clear tail frames past threshold seconds 
        if isinstance(sender, io.workers.QuicktimeSignals):
            if self.cache_number > 288:
                self.removeTailFrames(self.cache_number - 288)
        elif isinstance(sender, io.workers.FrameSignals):
            if self.cache_number > 120:
                self.removeTailFrames(self.cache_number - 144)

    @Slot(int)
    def onFrameChange(self, timeline_frame):
        viewport = self.viewport
        timeline = self.timeline
        clip, clip_frame = timeline.updatedFrame(timeline_frame)
        if not clip_frame:
            return

        if isinstance(clip, ImageClip):
            img_data = clip.geometry.pixels
        else:
            img_data = FrameEngine.CACHE.get(timeline_frame)

        update_framerate = False

        if not isinstance(img_data, np.ndarray):
            if self.timeline_control.state() == 2:
                self.parent.playbackToggle()

            if (timeline_frame - 2) < self.minc or timeline_frame > (self.maxc + 2):
                if self.mode == FrameEngine.LOOK_AHEAD:
                    self.clearFrameCache(timeline_frame)
            self.startCaching(clip, clip_frame, timeline_frame, new_clip=True)
            update_framerate = True
        else:
            if not self.is_caching: # Don't attempt frame queries while caching.
                look_ahead = timeline_frame + 24
                uncached_begin = self.cache_end + 1
                cache_end_ahead = look_ahead >= uncached_begin
                clip_end_ahead = clip.timeline_out <= look_ahead

                if cache_end_ahead and self.cache_end < clip.timeline_out:
                    clip_frame = clip.mapToLocalFrame(uncached_begin) # <- Optimize this as calculated instead
                    if clip_frame:
                        self.startCaching(clip, clip_frame, uncached_begin)
                elif clip_end_ahead:
                    next_clip, next_clip_frame = self.timeline.getClipOnFrame(look_ahead + 1)
                    if next_clip_frame and self.cache_end < next_clip.timeline_out:
                        self.startCaching(next_clip, next_clip.first, next_clip.timeline_in, new_clip=True)

            viewport.makeCurrent()
            geo = clip.geometry
            viewport.image_plane = geo 
            geo.updateTexture(img_data)

            if not geo.no_annotation:
                if clip_frame not in clip.annotations:
                    geo.resetAnnotation()
            viewport.update()

        if timeline_frame == clip.timeline_in or update_framerate:
            self.parent.playbackToggle()
            self.timeline_control.setFramerate(clip.framerate)
            self.parent.playbackToggle()

        self.timeline.makeCurrent()
        self.timeline.drawViewport()

    def regionCaching(self, clip):
        self.clearFrameCache(clip.timeline_in, update=False)
        self.is_caching = True

        if isinstance(clip, MovClip):
            worker = io.workers.QuicktimeThread
            self.mov_thread.setClip(clip, clip.first, clip.timeline_in)
        else:
            worker = io.workers.FrameThread
            # Update the cache methods frame mappings
            worker.fastRead = partial(worker.fastRead,
                frame=clip.timeline_in,
                clip_frame=clip.first,
                path=clip.path)
        cache = FrameEngine.CACHE
        [cache.update({x:None}) for x in range(clip.timeline_in, clip.timeline_out + 1)]
        self.cache_end = clip.timeline_out
        worker.iterations = partial(range, clip.duration + 1)

    def startCaching(self, clip, clip_frame, timeline_frame, new_clip=False):
        # Don't re-queue if thread is already running
        if self.is_caching or self.mode == FrameEngine.REGION:
            return

        self.is_caching = True

        if isinstance(clip, MovClip):
            worker = io.workers.QuicktimeThread
            if new_clip:
                self.mov_thread.setClip(clip, clip_frame, timeline_frame)
            else:
                self.mov_thread.setFrame(clip_frame, timeline_frame) # Debug impact
        else:
            worker = io.workers.FrameThread
            # Update the cache methods frame mappings
            worker.fastRead = partial(worker.fastRead,
                frame=timeline_frame,
                clip_frame=clip_frame,
                path=clip.path)

        cache_to = timeline_frame + worker.BATCH_SIZE
        if cache_to > clip.timeline_out:
            cache_to = clip.timeline_out
            cache_duration = (cache_to - timeline_frame)
        else:
            cache_duration = worker.BATCH_SIZE

        cache = FrameEngine.CACHE
        [cache.update({x:None}) for x in range(timeline_frame, cache_to + 1)]
        self.cache_end = cache_to
        worker.iterations = partial(range, cache_duration + 1)

    def removeTailFrames(self, amount):
        self.cache_number = self.cache_number - amount
        new_min = self.minc + amount
        func = partial(io.workers.FrameCacheIOThread.deleteCacheRange, self.minc, new_min)
        self.frame_io_thread.addToQueue(func)
        self.minc = new_min

    def clearFrameCache(self, timeline_frame, update=True):
        if self.is_caching:
            return
        FrameEngine.CACHE.clear()
        if update:
            deferred_load = partial(self.onFrameChange, timeline_frame)
            self.deferred_frame_load = QTimer.singleShot(600, deferred_load)
        self.minc = timeline_frame
        self.maxc = timeline_frame
        self.cache_number = 0
        self.timeline.updateCacheSize(self.minc, self.maxc)
        self.timeline.makeCurrent()
        self.timeline.drawViewport()


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
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint)
        self.setAcceptDrops(True)
        self.setDockNestingEnabled(True)
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

        # Status bar
        self.statusbar = QStatusBar(self)
        self.statusbar.setObjectName(u"statusbar")
        self.setStatusBar(self.statusbar)

        # Layouts
        self.mov_meta_thread = io.workers.ExifWorker(self)
        self.mov_meta_thread.metaLoaded.connect(self.movieDataRecieved)
        self.mov_meta_thread.start()

        self.frame_engine = FrameEngine(self, self.timeline, self.viewport)
        self.player = playerWidget(self)
        self.createDocks()
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
        SHORTCUTS[VIEW].append(QShortcut(QKeySequence('c'), self, self.cacheModeToggle))

        play_control = self.frame_engine.timeline_control
        QShortcut(QKeySequence('right'), self, play_control.oneFrameForward)
        QShortcut(QKeySequence('left'), self, play_control.oneFrameBackward)
        QShortcut(QKeySequence('ctrl+left'), self, play_control.stepBackward)
        QShortcut(QKeySequence('ctrl+right'), self, play_control.stepForward)
        QShortcut(QKeySequence('`'), self, self.theatreMode)

        self.viewport.setColorConfig()

    @Slot()
    def cacheModeToggle(self):
        mode = self.frame_engine.setRegionCache()
        if mode == FrameEngine.LOOK_AHEAD:
            message = 'Caching in Look Ahead mode.'
        elif mode == FrameEngine.REGION:
            message = 'Caching in Region mode.'
        self.statusbar.showMessage(message, 2000)

    def movieDataRecieved(self, clip, data):
        self.viewport.makeCurrent()
        if data.get('DisplayHeight'):
            data['ImageSize'] = '{}x{}'.format(data.get('DisplayWidth'), data.get('DisplayHeight'))
        clip.loadFile(
            data.get('Duration'),
            data.get('ImageSize'),
            data.get('VideoFrameRate') or data.get('SampleRate')
        )
        self.viewport.update()
        self.timeline.makeCurrent()
        self.timeline.graph.appendClip(clip, 0)
        if self.timeline.current_frame == clip.timeline_in:
            self.timeline.current_clip = clip
            self.frame_engine.onFrameChange(clip.timeline_in)
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
        self.viewport.update()
        self.timeline.makeCurrent()
        clip = SeqClip(timeline_in=0)
        clip.setBlankImage()
        self.timeline.reset(clip)
        self.timeline.frameGeometry()
        self.frame_engine.onFrameChange(clip.timeline_in)
        self.viewport.frameGeometry()

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
        paint_dock = PaintDock()
        paint_dock.onClosed.connect(self.closePaint)
        self.addDockWidget(Qt.LeftDockWidgetArea, paint_dock)
        paint_dock.hide()
        self.paint_dock = paint_dock

        dock = AnnotationDock()
        dock.toolChanged.connect(self.viewport.setActiveTool)
        dock.saveButton.clicked.connect(self.paintContext)
        dock.clearButton.clicked.connect(self.clearAnnotation)
        dock.shapeTypeCombobox.currentIndexChanged.connect(self.viewport.setShapeType)
        paint_dock.window.addDockWidget(Qt.LeftDockWidgetArea, dock)
        self.annotation_dock = dock

        dock = ColorPickerkDock()
        dock.colorChanged.connect(self.viewport.paint_engine.brush.setColor)
        paint_dock.window.addDockWidget(Qt.LeftDockWidgetArea, dock)
        dock.setFloating(False)
        self.color_picker_dock = dock

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
        if stop and self.frame_engine.timeline_control.state() != 2:
            return
        if self.frame_engine.timeline_control.state() == 2:
            self.player.play.setChecked(False)
        else:
            self.player.play.setChecked(True)
        self.frame_engine.timeline_control.play()
        self.viewport.makeCurrent()

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

    @Slot()
    def refreshViewport(self):
        self.viewport.makeCurrent()
        self.viewport.update()

    @Slot()
    def refreshTimeline(self):
        self.timeline.makeCurrent()
        self.timeline.update()

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
            try:
                offset = self.timeline.graph.clips[-1][-1].timeline_out
            except:
                pass

        self.viewport.makeCurrent() # Need this for clip image plane geometry creation

        if file_path.ext in io.MOVIE:
            clip = MovClip(file_path=file_path, timeline_in=offset)
            self.mov_meta_thread.addToQueue(clip)
        else:
            if file_path.sequence_path:
                clip = SeqClip(file_path=file_path, timeline_in=offset)
            else:
                clip = ImageClip(file_path=file_path, timeline_in=offset)

        # Now we modify the timeline
        self.timeline.makeCurrent()
        if reset or self.timeline.graph.nodes.count == 0:
            self.frame_engine.clearFrameCache(offset)
            self.timeline.reset(clip)

        self.timeline.graph.appendClip(clip, 0)
        self.timeline.updateNodeGlyphs()
        #self.timeline.frameGeometry()
        # Finally update the viewport again
        self.frame_engine.onFrameChange(clip.timeline_in)
        self.viewport.frameGeometry()

    def hide(self):
        self.frame_engine.clearFrameCache()
        super(PlayerAppWindow, self).hide()

    def closeEvent(self, event):
        self.frame_engine.thread.pool.shutdown()
        self.mov_meta_thread.stop()
        self.mov_meta_thread.quit()
        self.frame_engine.thread.quit()
        self.frame_engine.mov_thread.stop()
        self.frame_engine.mov_thread.quit()
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
