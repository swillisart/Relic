import os
import sys
import time
from functools import partial
import glob
import libraw
import numpy as np
import oiio.OpenImageIO as oiio
from library.abstract_objects import ImageDimensions
from library.config import log, logFunction, MOVIE_EXT, relic_preferences
from library.objectmodels import BaseFields, relic_asset, temp_asset
from PySide6.QtCore import (Property, QEvent, QFile, QItemSelectionModel,
                            QMargins, QMutex, QObject, QPoint, QMutexLocker,
                            QPropertyAnimation, QRect, QRegularExpression,
                            QSize, QSortFilterProxyModel, Qt, QTextStream,
                            QThread, QWaitCondition, Signal, Slot)
from PySide6.QtGui import (QAction, QColor, QCursor, QFont, QFontMetrics,
                           QIcon, QImage, QPainter, QPixmap,
                           QRegularExpressionValidator, QStandardItemModel, Qt)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QBoxLayout,
                               QDialog, QDockWidget, QFrame, QLabel, QLayout,
                               QLineEdit, QListView, QMenu, QScrollArea,
                               QStyledItemDelegate, QTreeView, QVBoxLayout,
                               QWidget)
from sequencePath import sequencePath as Path


def generatePreviews(img_buf, path):
    """Makes Proxy & Icon previews from an OpenImageIO image buffer"""

    spec = img_buf.spec()
    size = ImageDimensions(spec.width, spec.height, channels=3)
    size.makeDivisble() # ensure divisible width for jpeg 16x16 blocks

    proxy_spec = oiio.ImageSpec(size.w, size.h, size.channels, oiio.UINT8)
    proxy_spec['compression'] = 'jpeg:75'
    proxy_buf = oiio.ImageBuf(proxy_spec)

    icon_spec = oiio.ImageSpec(384, 256, 3, oiio.UINT8)
    icon_spec['compression'] = 'jpeg:40'
    icon_buf = oiio.ImageBuf(icon_spec)

    oiio.ImageBufAlgo.resize(proxy_buf, img_buf, filtername='lanczos3')
    oiio.ImageBufAlgo.fit(icon_buf, proxy_buf, filtername='lanczos3', exact=True)

    # add alpha channel if none exists
    #if spec.nchannels <= 3:
    #    buf = oiio.ImageBufAlgo.channels(buf, ("R", "G", "B", 1.0),
    #                        ("R", "G", "B", "A"))

    # Composite icon image over constant grey
    bg = oiio.ImageBuf(icon_buf.spec())
    oiio.ImageBufAlgo.fill(bg, (0.247, 0.247, 0.247, 1.0))
    comp = oiio.ImageBufAlgo.over(icon_buf, bg)
    
    # Write to disk
    path.ext = '.jpg'
    icon_path = path.suffixed('_icon')
    proxy_path = path.suffixed('_proxy')
    icon_buf.write(str(icon_path))
    proxy_buf.write(str(proxy_path))
    return icon_path

class ConversionRouter(QObject):

    started = Signal(int)
    progress = Signal(object)
    finished = Signal()
    error = Signal(Exception)

    def __init__(self, function_map, parent=None):
        super(ConversionRouter, self).__init__(parent)
        self.function_map = function_map
        
        # Ensure our local ingest location exists
        self.ingest_path = Path(os.getenv('userprofile')) / '.relic/ingest'
        if not self.ingest_path.exists:
            self.ingest_path.path.mkdir(parents=True)

    def addToQueue(self, folders):
        if hasattr(self, 'queued_folders'):
            self.queued_folders = self.queued_folders + folders
            self.folder_queued_count += len(folders)
        else:
            self.folder_queued_count = len(folders)
            self.queued_folders = folders
            self.folders_done = 0
            self.files_todo = -1

    def run(self):
        while self.folders_done != self.folder_queued_count:
            item = self.queued_folders.pop(0)
            self.processDirectory(Path(item))
            self.folders_done += 1
        del self.queued_folders
        self.finished.emit()

    @logFunction('')
    def processDirectory(self, directory):
        conversion_functions = []
        sequences = []
        for img in directory:
            if img.path.is_dir():
                self.addToQueue([str(img)])
                continue

            if img.name in sequences:
                continue

            if func := self.function_map.get(img.ext):
                self.files_todo += 1
                out_img_path = Path(str(img))
                filename = 'unsorted{}{}'.format(self.files_todo, img.ext)
                out_img_path = self.ingest_path / filename
                img.checkSequence()
                if img.sequence_path:
                    sequences.append(img.name)
                img_function = partial(getattr(self, func), img, out_img_path)
                conversion_functions.append(img_function)

        if conversion_functions:
            self.started.emit(self.files_todo)
            for func in conversion_functions:
                try:
                    asset = func()
                    self.progress.emit(asset)
                except Exception as exerr:
                    #log.error(exerr)
                    self.error.emit(exerr)

    @staticmethod
    @logFunction('Making preview from (MOV)')
    def processMOV(in_img_path, movie_path):
        return None
        '''Creates Images / Video from (Quicktime)'''

        icon_out = output_path / 'unsorted{}_icon.jpg'.format(in_img_path)
        preview_out = output_path / 'unsorted{}_icon.mp4'.format(in_img_path)
        proxy_out = output_path / 'unsorted{}_proxy.mp4'.format(in_img_path)
        cmd = [
            "ffmpeg",
            "-loglevel", "error",
            "-y",
            "-i", str(movie_path),
            "-pix_fmt", "yuv422p",
            "-vcodec", "h264",
            "-crf", "28",
            "-preset", "slower",
            "-tune", "fastdecode",
            "-movflags", "+faststart",
            "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
            str(proxy_out),
            "-r", "24",
            "-vf", "setpts=PTS/{},scale=w=256:h=144:force_original_aspect_ratio=decrease,pad=256:144:(ow-iw)/2:(oh-ih)/2".format(pts),
            "-an",  # Flag to not try linking audio file
            "-pix_fmt", "yuv422p",
            "-vcodec", "h264",
            "-tune", "fastdecode",
            "-movflags", "+faststart",
            str(preview_out),
            "-vf", "select=gte(n\,1),scale=w=256:h=144:force_original_aspect_ratio=decrease,pad=256:144:(ow-iw)/2:(oh-ih)/2",
            "-vframes", "1",
            str(icon_out),
        ]
        subprocess.call(cmd, stdout=DEVNULL)
        icon_img = QImage(str(icon_out)).scaled(
            72, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon_pixmap = QPixmap.fromImage(icon_img)
        out_icon = QIcon()
        out_icon.addPixmap(icon_pixmap, QIcon.Normal)
        out_icon.addPixmap(icon_pixmap, QIcon.Selected)
        return out_icon

    @staticmethod
    @logFunction('Making preview from (SEQ)')
    def processSEQ(path, proxy_path, icon_path):
        return None
        frames = sorted(glob.glob(str(path)))
        framelength = len(frames)
        frame_data = []
        a_input = oiio.ImageInput.open(frames[0])
        spec = a_input.spec()
        a_input.close()
        pts = ((framelength * 24) / 100) / 24

        command = [
            "ffmpeg",
            "-loglevel", "error",
            "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", "{}x{}".format(spec.width, spec.height),
            "-pix_fmt", "rgb24",
            "-i", "-",  # Input comes from a pipe
            "-r", "24",  # fps
            "-an",  # Flag to not try linking audio file
            "-pix_fmt", "yuv422p",
            "-vcodec", "h264",
            "-crf", "30",
            "-preset", "medium",
            "-tune", "fastdecode",
            "-movflags", "+faststart",
            "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
            str(proxy_path),
            "-vf", "setpts=PTS/{},scale=w=256:h=144:force_original_aspect_ratio=decrease,pad=256:144:(ow-iw)/2:(oh-ih)/2".format(pts),
            "-vcodec", "h264",
            "-movflags", "+faststart",
            str(icon_path.parents(0) / (icon_path.name + '.mp4'))
        ]

        pipe = subprocess.PIPE
        pr = subprocess.Popen(
            command, stdout=DEVNULL, stdin=pipe
        )

        i = 0
        while True:
            if not frames: break
            frame = frames.pop(0)
            i += 1
            buf = oiio.ImageBuf(str(frame))
            spec = buf.spec()
            r = spec.roi
            if spec.nchannels >= 4:
                roi = oiio.ROI(r.xbegin, r.xend, r.ybegin, r.yend, 0, 1, 0, 4)
                alpha = True
            else:
                alpha = False

                roi = oiio.ROI(r.xbegin, r.xend, r.ybegin, r.yend, 0, 1, 0, 3)

            buf = oiio.ImageBufAlgo.colorconvert(buf, "Linear", "sRGB")
            data = buf.get_pixels(format=oiio.UINT8, roi=roi)

            # Write Icon
            if i == int(framelength / 2):
                generatePreviewsFile(frame, icon_path, gammaCorrect=True)

            if alpha:
                data = data[:, :, :-1]
            pr.stdin.write(data.tobytes())
            pr.stdin.flush()

        pr.stdin.close()
        return ('{}x{}'.format(spec.width, spec.height), framelength/24)

    @staticmethod
    @logFunction('Making preview from (HDR)')
    def processHDR(in_img_path, image_path):
        return None
        image = oiio.ImageBuf(str(image_path))
        spec = image.spec()
        formatted = oiio.ImageBuf(
            oiio.ImageSpec(spec.width, spec.height, 3, oiio.UINT8)
        )
        oiio.ImageBufAlgo.pow(formatted, image, (0.454, 0.454, 0.454))
        icon = generatePreviews(in_img_path, formatted)
        return icon

    @staticmethod
    @logFunction('Making preview from (RAW)')
    def processRAW(in_img_path, out_img_path):
        return None
        # For neat image if installed
        #subprocess.call('E:/OneDrive/Apps/Neat Image v8 Standalone/NeatImageCL.exe "{}" -sp -ow -e -b=M -s='.format(tif_path), stdout=DEVNULL)
        proc = LibRaw()

        # Read RAW data
        proc.open_file(str(in_img_path))
        proc.unpack()

        # Set libraw parameters
        proc.set_output_color(c_int(6))
        proc.set_no_auto_bright(c_int(1))

        proc.dcraw_process()

        raw_img_data = proc.imgdata.image
        img_data = raw_img_data[:, :, :-1] # remove alpha
        
        size = ImageDimensions.fromArray(img_data)
        # convert ACES2065-1 to ACEScg 
        spec = oiio.ImageSpec(size.w, size.h, size.channels, oiio.HALF)
        buf = oiio.ImageBuf(spec)
        buf.set_pixels(spec.roi, img_data)
        #img_pixels = buf.get_pixels(oiio.FLOAT)
        #img_pixels.reshape(size.w * size.h, size.channels)
        #aces_pixels = (flat_img @ libraw.ACESCG_MATRIX)
        #aces_pixels.reshape([size.h, size.w, size.channels])
        #buf.set_pixels(spec.roi, aces_pixels)
        out_img_path.ext = '.exr' # Raw is always converted to exr.
        buf.write(str(out_img_path))

        return #self.processHDR(in_img_path, exr_path)

    @staticmethod
    @logFunction('Making preview from (LDR)')
    def processLDR(in_img_path, out_img_path):
        #in_img_path.copyTo(out_img_path)
        imgbuf = oiio.ImageBuf(str(in_img_path))
        if imgbuf.has_error:
            raise Exception
        spec = imgbuf.spec()
        icon_path = generatePreviews(imgbuf, out_img_path)
        icon = QPixmap.fromImage(QImage(str(icon_path)))
        res = '{}x{}x{}'.format(spec.width, spec.height, spec.nchannels)
        asset = temp_asset(
            name=in_img_path.name,
            category=0,
            type=0,
            duration=0,
            resolution=res,
            path=in_img_path,
            icon=icon,
        )
        return asset


class IngestionThread(QThread):

    itemDone = Signal(object)

    def __init__(self, *args, **kwargs):
        super(IngestionThread, self).__init__(*args, **kwargs)
        self.mutex = QMutex()
        self.condition = QWaitCondition()
        self.ingest_path = Path(os.getenv('userprofile')) / '.relic/ingest'
        self.stopped = False
        self.queue = []

    def load(self, items):
        locker = QMutexLocker(self.mutex)
        self.queue.append(items)
        if not self.isRunning():
            self.start()
        else:
            self.stopped = False
            self.condition.wakeOne()

    def stop(self):
        with QMutexLocker(self.mutex):
            self.stopped = True
            self.condition.wakeOne()

        self.wait(20)

    def start(self):
        self.stopped = False
        super(IngestionThread, self).start()

    def run(self):
        while True:
            #self.mutex.lock()
            while self.queue:
                #self.mutex.unlock()
                if self.stopped:
                    return

                self.mutex.lock()
                file_id, item = self.queue.pop(0)
                ingest_path = self.ingest_path
                self.mutex.unlock()

                #log.debug(str('item'))
                in_path = item.path
                category = item.categoryName
                subcategory = item.subcategory.name
                item.path = Path(subcategory) / (item.name + in_path.ext)
                out_path = item.local_path

                files_map = {}
                #in_path.copyTo(out_path)

                temp_filename = 'unsorted' + file_id
                temp_path = ingest_path / temp_filename

                in_icon = temp_path.suffixed('_icon', ext='.jpg')
                out_icon = out_path.suffixed('_icon', ext='.jpg')

                files_map[in_icon] = out_icon
        
                if in_path.sequence_path or in_path.ext in MOVIE_EXT:
                    if in_path.sequence_path: # Map all sequences frames for copy
                        for seq_file in glob.glob(in_path.sequence_path):
                            frame = Path(seq_file).frame
                            in_path.frame = frame
                            out_path.frame = frame
                            files_map[in_path] = out_path
                    else: # Map Movie for copy
                        files_map[in_path] = out_path
                    in_proxy = temp_path.suffixed('_proxy', ext='.mp4')
                    out_proxy = out_path.suffixed('_proxy', ext='.mp4')

                    # Movies have video icon preview's
                    in_icon_mov = temp_path.suffixed('_icon', ext='.mp4')
                    out_icon_mov = out_path.suffixed('_icon', ext='.mp4')
                    files_map[in_icon_mov] = out_icon_mov

                else: # Only single-frame images have proxy jpegs.
                    files_map[in_path] = out_path
                    in_proxy = temp_path.suffixed('_proxy', ext='.jpg')
                    out_proxy = out_path.suffixed('_proxy', ext='.jpg')

                files_map[in_proxy] = out_proxy
                for src, dst in files_map.items():
                    src.copyTo(dst)
                item.filehash = out_path.parents(0).hash
                item.filesize = out_path.parents(0).size
                # Clear the Id to allow for database creation
                self.itemDone.emit(item)

            self.mutex.lock()
            self.condition.wait(self.mutex)
            self.mutex.unlock()
