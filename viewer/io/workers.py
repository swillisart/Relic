import subprocess, os, json
import concurrent.futures
from functools import partial
from collections import deque

from PySide6.QtCore import (
    Signal, QMutex, QMutexLocker, QPoint, QSize, Qt, QThread, QWaitCondition,
    QRunnable, QThreadPool, QObject
)
import numpy as np
from .image import simpleRead
import time, random
import cv2

class QuicktimeSignals(QObject):
    frame_ready = Signal(int)
    finished = Signal()


class QuicktimeThread(QThread):
    
    BATCH_SIZE = 120

    def __init__(self, cache, parent=None):
        QThread.__init__(self, parent)
        self.mutex = QMutex()
        self.signals = QuicktimeSignals()
        self.cache = cache
        self.stopped = False
        self.path = None
        self.cap = None
        self.clip_frame = 0
        self.frame = 0

    @staticmethod
    def iterations():
        return range(0)

    def setFrame(self, clip_frame, frame):
        self.clip_frame = clip_frame
        self.frame = frame
        self.stopped = False

    def setClip(self, clip, clip_frame, frame):
        if self.cap:
            self.cap.release()
            self.cap = None
        self.path = str(clip.path)
        self.setFrame(clip_frame, frame)

    def stop(self):
        with QMutexLocker(self.mutex):
            self.stopped = True
            if self.cap:
                self.cap.release()
                self.cap = None
        self.wait(10)

    def start(self):
        self.stopped = False
        super(QuicktimeThread, self).start()

    def run(self):
        while True:
            with QMutexLocker(self.mutex):
                stop = self.stopped
                cache = self.cache
                cap = self.cap
                path = self.path
                clip_frame = self.clip_frame
                frame = self.frame
                if not cap and self.path:
                    cap = cv2.VideoCapture(path)
                    cap.set(cv2.CAP_PROP_POS_FRAMES, clip_frame - 1)

            if cap and not stop:
                #self.cap.set(cv2.CAP_PROP_POS_FRAMES, clip_frame - 1)
                for index in QuicktimeThread.iterations():
                    timeline_frame = frame + index
                    if timeline_frame in cache:
                        ret, data = cap.read()
                        if ret:
                            cache[timeline_frame] = data
                            self.signals.frame_ready.emit(timeline_frame)
                            self.msleep(1)
                self.signals.finished.emit()
                FrameThread.iterations = partial(range, 0)
                self.stopped = True
                self.cap = cap
            self.msleep(10)


class ExifWorker(QThread):

    metaLoaded = Signal(object, dict)

    def __init__(self, *args, **kwargs):
        super(ExifWorker, self).__init__(*args, **kwargs)
        self.mutex = QMutex()
        self.stopped = False
        self.proc = None
        self.queue = deque()

    def addToQueue(self, path):
        self.queue.append(path)

    def stop(self):
        with QMutexLocker(self.mutex):
            self.stopped = True
            if self.proc: # Kill the exiftool child process
                pid = self.proc.pid
                subprocess.call(f'taskkill /F /T /PID {pid}')
        self.wait(10)

    def start(self):
        self.stopped = False
        super(ExifWorker, self).start()

    def run(self):
        while True:
            with QMutexLocker(self.mutex):
                if self.stopped:
                    return
                if not self.queue:
                    self.msleep(10)
                    continue

                if not self.proc:
                    self.proc = subprocess.Popen(
                        'exiftool -stay_open True -@ -',
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                clip = self.queue.popleft()
                cmd_text = ['-j', # JSON
                    '-Duration#',
                    '-ImageSize',
                    '-VideoFrameRate',
                    '-SampleRate', # MXF framerate
                    '-DisplayHeight', # MXF
                    '-DisplayWidth', # MXF
                    str(clip.path),
                    '-execute\n']
                self.proc.stdin.write(bytes('\n'.join(cmd_text), encoding='utf-8'))
                self.proc.stdin.flush()
                output = b''
                while True:
                    line = self.proc.stdout.readline()
                    output += line
                    if output.endswith(b'y}\r\n'):
                        break
                data = json.loads(output.decode('utf-8').replace('{ready}', ''))[0]
                self.metaLoaded.emit(clip, data)


class FrameSignals(QObject):
    frame_ready = Signal(int)
    finished = Signal()


class FrameThread(QThread):

    BATCH_SIZE = 24

    def __init__(self, cache, parent=None):
        QThread.__init__(self, parent)
        # Instantiate signals and connect signals to the slots
        self.signals = FrameSignals()
        self.pool = concurrent.futures.ThreadPoolExecutor(4)
        self.cache = cache
        self.mutex = QMutex()

    @staticmethod
    def iterations():
        return range(0)

    @staticmethod
    def fastRead(index, cache=None, frame=None, clip_frame=None, path=None):
        timeline_frame = frame + index
        fp = path.padSequence(clip_frame + index)
        data = simpleRead(str(fp))
        #data = np.zeros(shape=(2160, 4096, 3), dtype=np.float16)
        if frame in cache: # Frame expected by GUI (Not old or obsolete)
            cache[timeline_frame] = data
            return timeline_frame
    
    def run(self):
        while True:
            counter = 0
            with QMutexLocker(self.mutex):
                cache = self.cache  
            func = partial(FrameThread.fastRead, cache=cache)
            for timeline_frame in self.pool.map(func, FrameThread.iterations()):
                if timeline_frame:
                    self.signals.frame_ready.emit(timeline_frame)
                counter += 1
                if counter == len(FrameThread.iterations()):
                    self.signals.finished.emit()
                    FrameThread.iterations = partial(range, 0)
                self.msleep(1)
            self.msleep(10)


class FrameCacheIOThread(QThread):

    def __init__(self, cache, parent=None):
        QThread.__init__(self, parent)
        self.mutex = QMutex()
        self.cache = cache
        self.queue = []

    def addToQueue(self, func):
        self.queue.append(func)

    @staticmethod
    def deleteCacheRange(_min, _max, cache):
        for x in range(_min, _max):
            try:
                del cache[x]
            except: pass

    def run(self):
        while True:
            with QMutexLocker(self.mutex):
                    queue = self.queue
                    cache = self.cache
            while queue:
                func = queue.pop(0)
                func(cache)
            self.msleep(100)
