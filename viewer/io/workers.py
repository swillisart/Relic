import concurrent.futures
from functools import partial
from collections import deque, defaultdict

from PySide6.QtCore import (Signal, Slot, QMutex, QMutexLocker, Qt, QThread,
    QRunnable, QObject, QThreadPool
)
import av
import numpy as np
from .image import simpleRead
from sequence_path.main import Path

from viewer.config import log


def frame_to_timestamp(frame, stream):
    target_sec = frame / float(stream.rate)
    timestamp = int(target_sec / stream.time_base) + stream.start_time
    return timestamp

def timestamp_to_frame(timestamp, stream):
    frame = (timestamp - stream.start_time) * float(stream.time_base) * float(stream.rate)
    return int(frame)


class QuicktimeSignals(QObject):
    frame_ready = Signal(int)
    finished = Signal()


class FramesThread(QThread):

    def __init__(self, cache, parent=None):
        QThread.__init__(self, parent)
        self.mutex = QMutex()
        self.signals = QuicktimeSignals()
        self.cache = cache
        self.path = None
        self.container = None
        self.clip_frame = 0
        self.frame = 0
        self.sequence = 0
        self.iterations = 0 

    def setFrame(self, clip_frame, frame):
        self.clip_frame = clip_frame
        self.frame = frame

    def setClip(self, clip, clip_frame, frame):
        if self.container:
            self.container.close()
        self.path = str(clip.path)
        self.sequence = clip.sequence
        self.setFrame(clip_frame, frame)
        self.iterations = clip.duration + 1

    def run(self):
        while True:
            with QMutexLocker(self.mutex):
                iterations = self.iterations
                cache = self.cache[self.sequence]
                container = self.container
                path = self.path
                frame = self.frame
                if not container and path:
                    container = av.open(path)
            if container and iterations != 0:
                in_stream = container.streams.video[0]
                seek_timestamp = frame_to_timestamp(frame, in_stream)
                container.seek(seek_timestamp, stream=in_stream, any_frame=True)
                for index, image in enumerate(container.decode(video=0)):
                    rgb = image.to_rgb()
                    timeline_frame = frame + index
                    cache[timeline_frame] = rgb.to_ndarray()
                    self.signals.frame_ready.emit(timeline_frame)
                    self.msleep(1)
                    if index == iterations:
                        break

                self.signals.finished.emit()
                self.iterations = 0
                self.container = container
            self.msleep(10)


class FrameSignals(QObject):
    frame_ready = Signal(int)
    finished = Signal()


class FrameThread(QThread):

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
    def fastRead(index, cache=None, sequence=0, frame=0, clip_frame=0, path='',):
        timeline_frame = frame + index
        fp = path.padSequence(clip_frame + index)
        data = simpleRead(str(fp))
        #data = np.zeros(shape=(2160, 4096, 3), dtype=np.float16)
        if frame in cache[sequence]: # Frame expected by GUI (Not old or obsolete)
            cache[sequence][timeline_frame] = data
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

def fastRead(index, cache, sequence, frame, clip_frame, path):
    timeline_frame = frame + index
    fp = path.padSequence(clip_frame + index)
    data = simpleRead(str(fp))
    #if frame in cache[sequence]: # Frame expected by GUI (Not old or obsolete)
    #    cache[sequence][timeline_frame] = data
    return timeline_frame, data

class ReadImage(QObject):

    finished = Signal(int, object)

    def __init__(self, clip, index, cache):
        super(ReadImage, self).__init__()
        self.clip = clip
        self.cache = cache
        self.index = index

    def run(self):
        #msg = '%s in thread %s'
        #log.debug(msg % (self.__class__.__name__, str(QThread.currentThread().objectName())))
        frame, data = fastRead(
            self.index,
            self.cache,
            self.clip.sequence,
            self.clip.timeline_in,
            self.clip.first,
            self.clip.path
        )
        self.finished.emit(frame, data)
        QThread.currentThread().quit()

class CommandQueueThread(QObject):

    onFrameReady = Signal(int, object)

    def __init__(self, thread_count=4):
        super(CommandQueueThread, self).__init__()
        self.setObjectName('QueueThread')
        self.mutex = QMutex()
        self.queue = deque()
        self.pool = []
        for i in range(thread_count):
            thread = QThread()
            thread.setObjectName(f'Thread{i}')
            self.pool.append(thread)

    def addToQueue(self, command):
        with QMutexLocker(self.mutex):
            self.queue.append(command)

    @Slot(int, object)
    def printit(self, frame, data):
        #msg = 'signalling frame: %d in thread %s'
        #log.debug(msg % (frame, str(QThread.currentThread().objectName())))
        self.onFrameReady.emit(frame, data)

    def run(self):
        while True:
            args = False
            with QMutexLocker(self.mutex):
                if self.queue:
                    command, args = self.queue.popleft()

            if args:
                #msg = '%s in thread %s'
                #log.debug(msg % (self.__class__.__name__, str(QThread.currentThread().objectName())))
                if command is ReadImage:
                    for thread in self.pool:
                        if not thread.isRunning():
                            break
                    if thread.isRunning():
                        thread.wait()
                    
                    worker = command(*args)
                    worker.moveToThread(thread)
                    worker.finished.connect(self.printit, Qt.DirectConnection)
                    thread.started.connect(worker.run)
                    thread.start()
                else:
                    result = command.execute(*args)
                    self.onFrameReady.emit(result)



class Command(QObject): # Worker
    """Command object for funciton execution 
    data is updated by connecting to the emitted completion signal callback"""
    finished = Signal(int)

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__()

    def execute(self, *args, **kwargs):
        """ An execution function to reimplement in your class
        """
        msg = 'Command %s in thread %s'
        log.debug(msg % (self.__class__.__name__, str(QThread.currentThread().objectName())))


class MovData(Command):
    
    def execute(self, *args, **kwargs):
        """ An execution function to reimplement in your class
        """
        raise NotImplementedError


class FrameData(Command):
    
    def execute(self, frame: int, clip_frame: int, path: Path, cache: dict, sequence: int):
        timeline_frame = frame # + index
        fp = path.padSequence(clip_frame)
        data = simpleRead(str(fp))
        if frame in cache[sequence]: # Frame expected by GUI (Not old or obsolete)
            cache[sequence][timeline_frame] = data
            return timeline_frame


class DeleteCacheRange(Command):

    def execute(self, _min, _max, cache):
        framerange = range(_min, _max)
        for seq in cache:
            cache[seq].update({x: None for x in framerange})
