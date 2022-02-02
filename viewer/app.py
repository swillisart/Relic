# -- Built-in --
import ctypes
import os
import sys
import json
from functools import partial
from collections import defaultdict
from operator import itemgetter

# -- Third-party --
import numpy as np
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtOpenGL import *
from PySide6.QtWidgets import *
#from qtshared6.styleWatcher import StylesheetWatcher
from qtshared6.utils import loadStyleFromFile
from qtshared6.svg import rasterizeSVG
from qtshared6.widgets import (CompactTitleBar, HoverTintButton,
                              InteractiveSpinBox)
# -- First-Party -- 
from sequencePath import sequencePath as Path
from strand.server import StrandServer
#import relic_base

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
        self.setEasingCurve(QEasingCurve.Linear)
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
        new = self.frame * (1000 / (rate))
        self.setCurrentTime(new * duration_div)
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
        new_time = ((self.frame + self.fps) * self.millisec_fps)
        self.setCurrentTime(new_time)

    def stepBackward(self):
        new_time = ((self.frame - 1 - self.fps) * self.millisec_fps)
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
    CACHE = defaultdict(dict)
    SINGLE = 0
    STACK = 1
    SPLIT = 2

    def __init__(self, parent, timeline, viewport):
        QObject.__init__(self, parent)
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
        self._frameChanger = self.singleFrameChange
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
        self.cache_finished_callback = None
        self.cache_mode = FrameEngine.LOOK_AHEAD
        self.comp_mode = FrameEngine.SINGLE

    @property
    def cache_mode(self):
        return self._cache_mode

    @cache_mode.setter
    def cache_mode(self, value):
        self._cache_mode = value
        if value == FrameEngine.LOOK_AHEAD:
            self.timeline.setLookAheadCacheColor()
        elif value == FrameEngine.REGION:
            self.timeline.setRegionCacheColor()
        #if self.is_caching:

    @Slot(int)
    def onFrameJump(self, frame):
        if self.is_caching:
            cache = FrameEngine.CACHE
            all_frames = [item for items in [cache[i].keys() for i in cache] for item in items]
            if not frame in all_frames and not self.deferred_frame_jump:
                deferred_load = partial(self.onFrameJump, frame)
                self.deferred_frame_jump = QTimer.singleShot(600, deferred_load)
                return
        else:
            self.deferred_frame_jump = None

        if self.cache_mode == FrameEngine.LOOK_AHEAD:
            clip, clip_frame = self.timeline.getClipOnFrame(frame)
            self.timeline.current_clip = clip
            if isinstance(clip, MovClip):
                self.mov_thread.setClip(clip, clip_frame, frame)
        
        self.timeline_control.setFrame(frame)

    def setRegionCache(self):
        selection = self.timeline.graph.selected_clips
        self.timeline.updateClipTextures()
        if self.comp_mode == FrameEngine.STACK:
            self._frameChanger = self.multiFrameChange
        else:
            self._frameChanger = self.singleFrameChange

        if selection and self.cache_mode == FrameEngine.REGION:
            clip_size = sum([clip.geometry.num_bytes * clip.duration for clip in selection])
            if io.util.fitsInMemory(clip_size):
                head = min([clip.timeline_in for clip in selection])
                if selection[0].framerate != self.timeline_control.fps:
                    self.timeline_control.setFramerate(selection[0].framerate)
                self.timeline_control.setFrame(head)
                self.clearFrameCache(head, update=False)
                self.regionCaching(selection)
        else:
            self.clearFrameCache(self.timeline.current_frame, update=False)

    @Slot()
    def onCacheFinished(self):
        self.is_caching = False
        if self.cache_finished_callback:
            self.cache_finished_callback()

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

    def multiFrameChange(self, timeline_frame):
        viewport = self.viewport
        timeline = self.timeline
        data = timeline.newMultiFrame(timeline_frame)
        viewport.image_plane = None
        viewport.clips = []

        for clip in data:
            sequence_cache = FrameEngine.CACHE[clip.sequence]
            if isinstance(clip, ImageClip):
                img_data = sequence_cache.get(clip.label)
            else:
                img_data = sequence_cache.get(timeline_frame)
            if isinstance(img_data, np.ndarray):
                clip.geometry.texture.push(img_data)
                viewport.clips.append(clip)
                viewport.update()

        timeline.drawViewport()

    @Slot(int)
    def onFrameChange(self, frame):
        self._frameChanger(frame)

    def singleFrameChange(self, timeline_frame):
        viewport = self.viewport
        timeline = self.timeline
        clip, clip_frame = timeline.updatedFrame(timeline_frame)
        if not clip:
            return
        if isinstance(clip, ImageClip):
            img_data = FrameEngine.CACHE[clip.sequence].get(clip.label)
        else:
            img_data = FrameEngine.CACHE[clip.sequence].get(timeline_frame)
        update_framerate = False

        if not isinstance(img_data, np.ndarray):
            if not clip:
                self.timeline.drawViewport()
                return
            if (timeline_frame - 2) < self.minc or timeline_frame > (self.maxc + 2):
                if self.cache_mode == FrameEngine.LOOK_AHEAD:
                    self.clearFrameCache(timeline_frame, update=True)
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

            geo = clip.geometry
            viewport.image_plane = geo
            geo.texture.push(img_data)

            if not geo.no_annotation:
                if clip_frame not in clip.annotations:
                    geo.resetAnnotation()
            viewport.update()

        if timeline_frame == clip.timeline_in or update_framerate:
            if clip.framerate != self.timeline_control.fps:
                self.parent.playbackToggle()
                self.timeline_control.setFramerate(clip.framerate)
                self.timeline_control.setFrame(timeline_frame)
                self.parent.playbackToggle()

        self.timeline.drawViewport()


    def regionCaching(self, clips):
        if not clips:
            return
        head = min([clip.timeline_in for clip in clips])
        tail = max([clip.timeline_out for clip in clips])
        self.cache_end = tail
        self.is_caching = True
        while _clips := clips:
            clip = _clips.pop(0)
            cache = FrameEngine.CACHE[clip.sequence]
            [cache.update({x:None}) for x in range(head, tail + 1)]
            if isinstance(clip, MovClip):
                worker = io.workers.QuicktimeThread
                self.mov_thread.setClip(clip, clip.first, clip.timeline_in)
                worker.iterations = partial(range, clip.duration + 1)
                self.cache_finished_callback = partial(self.regionCaching, clips)
                return
            elif isinstance(clip, ImageClip):
                img_data = io.image.simpleRead(str(clip.path))
                cache = FrameEngine.CACHE[clip.sequence]
                cache[clip.label] = img_data
                self.is_caching = False
                self.updateCache(clip.timeline_out)
            else:
                worker = io.workers.FrameThread
                # Update the cache methods frame mappings
                worker.fastRead = partial(worker.fastRead,
                    sequence=clip.sequence,
                    frame=clip.timeline_in,
                    clip_frame=clip.first,
                    path=clip.path)
                worker.iterations = partial(range, clip.duration + 1)
                self.cache_finished_callback = partial(self.regionCaching, clips)
                return
        self.cache_finished_callback = None

    def startCaching(self, clip, clip_frame, timeline_frame, new_clip=False):
        # Don't re-queue if thread is already running
        if self.is_caching or self.cache_mode == FrameEngine.REGION:
            return

        self.is_caching = True

        if isinstance(clip, MovClip):
            worker = io.workers.QuicktimeThread
            if new_clip:
                self.mov_thread.setClip(clip, clip_frame, timeline_frame)
            else:
                self.mov_thread.setFrame(clip_frame, timeline_frame) # Debug impact
        elif isinstance(clip, SeqClip):
            worker = io.workers.FrameThread
            # Update the cache methods frame mappings
            worker.fastRead = partial(worker.fastRead,
                sequence=clip.sequence,
                frame=timeline_frame,
                clip_frame=clip_frame,
                path=clip.path)
        else:
            img_data = io.image.simpleRead(str(clip.path))
            cache = FrameEngine.CACHE[clip.sequence]
            cache[clip.label] = img_data
            [cache.update({x:None}) for x in range(timeline_frame, clip.timeline_out + 1)]
            self.cache_end = clip.timeline_out
            self.is_caching = False
            self.updateCache(clip.timeline_out)
            return

        cache_to = timeline_frame + worker.BATCH_SIZE
        if cache_to > clip.timeline_out:
            cache_to = clip.timeline_out
            cache_duration = (cache_to - timeline_frame)
        else:
            cache_duration = worker.BATCH_SIZE

        cache = FrameEngine.CACHE[clip.sequence]
        [cache.update({x:None}) for x in range(timeline_frame, cache_to + 1)]
        self.cache_end = cache_to
        worker.iterations = partial(range, cache_duration + 1)

    def removeTailFrames(self, amount):
        if self.cache_mode == FrameEngine.REGION:
            return
        self.cache_number = self.cache_number - amount
        new_min = self.minc + amount
        func = partial(io.workers.FrameCacheIOThread.deleteCacheRange, self.minc, new_min)
        self.frame_io_thread.addToQueue(func)
        self.minc = new_min

    def clearFrameCache(self, timeline_frame, update=False):
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
        self.zoom_ratios.setFixedWidth(18)

        self.view_modes = QComboBox(self)
        self.view_modes.setStatusTip('Viewport Composite Modes')
        for item in config.VIEW_MODES:
            self.view_modes.addItem(item)
        self.view_modes.setFixedWidth(85)

        self.left_layout.addWidget(self.icon_button)
        self.center_layout.addWidget(self.view_modes)
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

        self.viewport = Viewport()
        self.viewport.fileDropped.connect(self.onViewportDropped)
        viewport_container = QWidget.createWindowContainer(self.viewport)
    
        self.setCentralWidget(viewport_container)
        self.title_bar = ViewerTitleBar(self)
        self.timeline = timelineGLView()

        self.timeline.onContextMenu.connect(self.showTimelineContextMenu)
        self.timelineFrame = QFrame(self)
        timeline_layout = QHBoxLayout()
        timeline_container = QWidget.createWindowContainer(self.timeline)

        timeline_layout.addWidget(timeline_container)
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
        self.timeline.movieAdded.connect(self.mov_meta_thread.addToQueue)

        self.frame_engine = FrameEngine(self, self.timeline, self.viewport)
        self.player = playerWidget(self)
        self.createDocks()
        # -- Signals / Slots --
        zoom_callback = lambda x: self.viewport.setZoom(config.ZOOM_RATIOS[x])
        self.title_bar.zoom_ratios.currentIndexChanged.connect(zoom_callback)
        self.title_bar.gamma_control.valueChanged.connect(self.viewport.setGamma)
        self.title_bar.exposure_control.valueChanged.connect(self.viewport.setExposure)
        self.title_bar.color_views.currentIndexChanged.connect(self.viewport.setColorspace)
        self.title_bar.view_modes.currentIndexChanged.connect(self.onViewModeChange)
        self.title_bar.exitAction.triggered.connect(self.close)
        self.title_bar.newAction.triggered.connect(self.newSession)
        self.title_bar.exportAction.triggered.connect(self.exportSession)

        self.viewport.colorConfigChanged.connect(self.title_bar.color_views.addItems)
        self.viewport.finishAnnotation.connect(self.saveAnnotation)
        self.viewport.zoomChanged.connect(self.setZoomValue)

        self.timeline.frameJump.connect(self.playbackToggle)
        self.timeline.annotatedLoad.connect(self.viewAnnotated)
        self.timeline.mouseInteracted.connect(self.refreshViewport)
        self.timeline.clearCache.connect(self.clearCache)
        self.actionSetHandles = QAction('Set Handles', self)
        self.actionSetHandles.triggered.connect(self.getHandlesFromInput)

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
        SHORTCUTS[VIEW].append(QShortcut(QKeySequence('m'), self, self.cacheModeToggle))
        SHORTCUTS[VIEW].append(QShortcut(QKeySequence('c'), self, self.timeline.cut))

        play_control = self.frame_engine.timeline_control
        QShortcut(QKeySequence('right'), self, play_control.oneFrameForward)
        QShortcut(QKeySequence('left'), self, play_control.oneFrameBackward)
        QShortcut(QKeySequence('ctrl+left'), self, play_control.stepBackward)
        QShortcut(QKeySequence('ctrl+right'), self, play_control.stepForward)
        QShortcut(QKeySequence('ctrl+a'), self, self.timeline.selectAll)
        QShortcut(QKeySequence('`'), self, self.theatreMode)

        self.viewport.setColorConfig()

    def clearCache(self, frame):
        update = self.frame_engine.cache_mode == FrameEngine.STACK
        self.frame_engine.clearFrameCache(frame, update)

    @Slot(int)
    def onViewModeChange(self, index):
        selection = self.timeline.graph.selected_clips
        frame = self.timeline.current_frame
        if index == FrameEngine.SINGLE:
            self.frame_engine.cache_mode = FrameEngine.LOOK_AHEAD
            clip, local_frame = self.timeline.getClipOnFrame(frame)
            if local_frame:
                self.viewport.image_plane = clip.geometry

        elif index == FrameEngine.STACK:
            if len(selection) <= 1:
                self.timeline.selectClipsOnFrame(frame)
                selection = self.timeline.graph.selected_clips
            if len(selection) > 1:
                self.frame_engine.cache_mode = FrameEngine.REGION
            else:
                view_modes = self.title_bar.view_modes
                view_modes.blockSignals(True)
                view_modes.setCurrentIndex(FrameEngine.SINGLE)
                view_modes.blockSignals(False)
                return

        self.frame_engine.comp_mode = index
        self.clearCache(frame)
        self.frame_engine.setRegionCache()
    
        self.frame_engine.timeline_control.setFrame(frame)
        deferred_load = partial(self.frame_engine.onFrameChange, frame)
        self.deferred_frame_jump = QTimer.singleShot(150, deferred_load)
        self.viewport.frameGeometry()

    def showTimelineContextMenu(self, position):
        context_menu = QMenu(self)
        selection = self.timeline.graph.selected_clips
        if selection:
            context_menu.addAction(self.actionSetHandles)

        context_menu.exec(position)

    def getHandlesFromInput(self):
        value, ok = QInputDialog.getInt(self, 'Set Handles', 'Frames:')
        if not ok:
            return
        self.timeline.setHandles(value)

    @Slot()
    def cacheModeToggle(self):
        mode = not self.frame_engine.cache_mode
        if mode == FrameEngine.LOOK_AHEAD:
            message = 'Caching in Look Ahead mode.'
        elif mode == FrameEngine.REGION:
            message = 'Caching in Region mode.'
        self.frame_engine.cache_mode = mode
        self.frame_engine.setRegionCache()
        self.statusbar.showMessage(message, 1500)

    def movieDataRecieved(self, clip, data):
        try:
            print(clip.index)
        except:pass
        timeline = self.timeline
        if data.get('DisplayHeight'):
            data['ImageSize'] = '{}x{}'.format(data.get('DisplayWidth'), data.get('DisplayHeight'))
        clip.loadFile(
            data.get('Duration'),
            data.get('ImageSize'),
            data.get('VideoFrameRate') or data.get('SampleRate')
        )
        clip.start_timecode = float(data.get('StartTimecode', '0.0'))
        self.viewport.update()
        timeline.graph.appendClip(clip, 0)
        if timeline.current_frame in (clip.timeline_in, clip.timeline_in - 1):
            timeline.current_clip = clip
            self.frame_engine.onFrameChange(clip.timeline_in)
            timeline.update()
            timeline.frameGeometry()
        timeline.update()

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
    def exportSession(self):
        file_name, ok = QFileDialog.getSaveFileName(
            self, "Export", QDir.homePath(), "Image Files (*.edl *.piq *.mp4)")
        if not ok:
            return
        out_file = open(file_name, 'a')
        out_file.write(io.util.EDL_TITLE)
        index = 0
        for _, clip in self.timeline.graph.iterateSequences():
            index += 1
            tc_frame = clip.start_timecode * clip.framerate#clip.timecodeToFrame(clip.start_timecode)
            a = clip.frameToTimecode(clip.first + tc_frame)
            b = clip.frameToTimecode(clip.last + tc_frame)
            clip_name = clip.label.replace('_01P', '')
            out_str = io.util.EDL_CLIP.format(index, *a, *b, clip_name)
            out_file.write(out_str)

    @Slot()
    def newSession(self):
        self.frame_engine.clearFrameCache(-2, update=False)
        self.viewport.image_plane = None
        self.viewport.update()
        clip = SeqClip(timeline_in=0)
        clip.setBlankImage()
        self.timeline.reset(clip)
        self.timeline.frameGeometry()
        self.timeline.updateNodeGlyphs()
        self.frame_engine.onFrameChange(clip.timeline_in)

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
        self.timeline.updateNodeGlyphs()
        self.viewport.update()

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
        self.timeline.updateNodeGlyphs()

    @Slot()
    def viewAnnotated(self, frame, clip):
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
        timeline_control = self.frame_engine.timeline_control 
        if stop and timeline_control.state() != 2:
            return
        if timeline_control.state() == 2:
            self.player.play.setChecked(False)
        else:
            self.player.play.setChecked(True)
        timeline_control.play()

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
        self.viewport.update()

    @Slot()
    def refreshTimeline(self):
        self.timeline.update()

    @Slot(QMimeData, int)
    def onViewportDropped(self, data, add_mode):
        load = partial(self.addClipFromFile, add_mode=add_mode)
        if data.hasFormat('application/x-relic'):
            from library import objectmodels
            assets = data.text()
            for key, values in json.loads(assets).items():
                constructor = objectmodels.getCategoryConstructor(key)
                if key == 'uncategorized':
                    [load(constructor(**fields).path) for fields in values]
                else:
                    [load(constructor(**fields).network_path) for fields in values]
        else:
            for url in data.urls():
                load(url.toLocalFile())

    def addClipFromFile(self, file_path, add_mode=0):
        # Bring focus to the window
        self.grab()
        self.setVisible(True)
        self.activateWindow()
        self.raise_()
        # Define the clip position and add / insert it to the timeline.
        clip_position = self.timeline.defineClipPosition(add_mode)
        clip = self.timeline.addFileAsClip(
            file_path, int(clip_position.x), int(clip_position.y))

        # Finally update the viewport again
        self.frame_engine.onFrameChange(clip.timeline_in)
        callback = partial(self.frame_engine.timeline_control.setFrame, clip.timeline_in)
        deferred_frame = QTimer.singleShot(600, callback)

        self.viewport.frameGeometry()
        self.timeline.frameGeometry()

    def resetScene(self, reset=True):
        offset = 0
        # Now we modify the timeline
        clip = None # Need to provide and empty clip to reset into.
        if reset:
            self.frame_engine.clearFrameCache(offset, update=True)
            self.timeline.reset(clip)


    def hide(self):
        self.frame_engine.clearFrameCache(self.timeline.current_frame, update=True)
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
    gl_format = QSurfaceFormat()
    gl_format.setSamples(2)
    QSurfaceFormat.setDefaultFormat(gl_format)
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    # Sets a 4x MSAA surface format to all QGLWidgets creatin in this application

    # C Python Windowing
    ctypes.windll.kernel32.SetConsoleTitleW('Peak')
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(u"resarts.peak")
    app.setEffectEnabled(Qt.UI_AnimateCombo, False)
    window = PlayerAppWindow()
    window.setWindowIcon(QIcon(':resources/icons/peak.svg'))
    window.setWindowTitle('Peak')
    loadStyleFromFile(window, ':style.qss')

    #watcher = StylesheetWatcher()
    #watcher.watch(window, 'P:/Code/Relic/viewer/style.qss')
    window.resize(1024, 512)
    window.show()
    server = StrandServer('peak')
    server.incomingFile.connect(window.addClipFromFile)
    app.processEvents() # draw the initial ui before loading stuff
    if args and args.path:
        #for x in range(125):
        for file_path in args.path.replace('peak://', '').split(','):
            window.addClipFromFile(file_path)
        if args.annotate:
            window.paint_dock.setFloating(False)
            window.paintContext()

    sys.exit(app.exec_())
