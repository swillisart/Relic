from PySide2.QtCore import (
    Signal, QMutex, QMutexLocker, QPoint, QSize, Qt, QThread, QWaitCondition,
    QRunnable, QThreadPool, QObject
)
import numpy as np
from . import image
import time, random
import cv2

class QuicktimeThread(QThread):

    loadedImage = Signal(np.ndarray)

    def __init__(self, *args, **kwargs):
        super(QuicktimeThread, self).__init__(*args, **kwargs)
        self.mutex = QMutex()
        self.stopped = False
        self.clip = None
        self.cap = None
        self.frame = 1
        self.index = 1

    def setupRead(self, clip, start):
        self.clip = clip
        self.cap = cv2.VideoCapture(str(clip.path)) #, cv2.CAP_INTEL_MFX)    
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, start)
        self.frame = start
        self.index = start

    def stop(self):
        with QMutexLocker(self.mutex):
            self.stopped = True
            if self.cap:
                self.cap.release()
        self.wait(10)

    def start(self):
        self.stopped = False
        super(QuicktimeThread, self).start()

    def run(self):
        while True:
            with QMutexLocker(self.mutex):
                if self.stopped:
                    return
                if self.index <= self.frame:
                    ret, frame = self.cap.read()
                    if ret:
                        self.loadedImage.emit(frame)
                    self.index += 1
                else:
                    self.msleep(10)


class loaderThread(QThread):

    loadedImage = Signal(int, np.ndarray)

    def __init__(self, parent=None):
        super(loaderThread, self).__init__(parent)
        # Base Thread Logic using mutex
        self.mutex = QMutex()
        self.condition = QWaitCondition()
        self.abort = False
        self.pool = QThreadPool.globalInstance()
        self.pool.setMaxThreadCount(3)
        self.frame = 0
        self.chunk_size = 50

    def stop(self):
        self.mutex.lock()
        self.pool.clear()
        self.abort = True
        self.condition.wakeOne()
        self.mutex.unlock()
        self.wait(1000)

    def load(self, frame, clip, graph):
        locker = QMutexLocker(self.mutex)
        self.clip = clip
        self.graph = graph
        self.frame = int(frame)
        if not self.isRunning():
            self.start(QThread.HighPriority)
        else:
            self.condition.wakeOne()

    def run(self):
        while True:
            self.mutex.lock()
            self.mutex.unlock()

            if self.abort:
                return
            end_frame = self.frame + self.chunk_size
            switch = 0 # priority toggle to help thread priority
            for f in range(self.frame, end_frame):
                self.worker = ImageLoader(self.clip, self.graph, f, self.loadedImage)
                switch = not switch
                self.frame += 1
                self.pool.start(self.worker, priority=switch)

            self.mutex.lock()
            self.condition.wait(self.mutex)
            self.mutex.unlock()


class PixelLoader(QRunnable):
    
    def __init__(self, clip, graph, frame, signal):
        super(PixelLoader, self).__init__(signal)
        self.signal = signal
        self.clip = clip
        self.graph = graph
        self.frame = frame


class ImageLoader(PixelLoader):
    
    def __init__(self, *args, **kwargs):
        super(ImageLoader, self).__init__(*args, **kwargs)

    @staticmethod
    def readClipData(clip, frame):
        clip_frame = clip.mapToLocalFrame(frame)
        if not clip_frame:
            return None
        fp = clip.path.padSequence(clip_frame)
        data, spec = image.read_file(fp, subimage=(0, 2))
        return data

    def run(self):
        img_data = self.readClipData(self.clip, self.frame)
        if not isinstance(img_data, np.ndarray):
            # re-lookup looping over graph looking for next possible frame
            #for index, node in enumerate(self.graph[0].nodes):
            for sequence, clip in self.graph.iterateSequences():
                local_frame = clip.mapToLocalFrame(self.frame)
                if local_frame:
                    img_data = self.readClipData(clip, self.frame)
                    break
        if isinstance(img_data, np.ndarray):
            self.signal.emit(self.frame, img_data)
            time.sleep(random.uniform(0.001, 0.125))
