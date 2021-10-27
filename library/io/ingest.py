import ctypes
import glob
import os
import subprocess
import sys
import time
from functools import partial

import libraw
import numpy as np
import cv2
import oiio.OpenImageIO as oiio
from library.abstract_objects import ImageDimensions
from library.config import (DCC_EXT, MOVIE_EXT, RELIC_PREFS, TOOLS_EXT,
                            getAssetSourceLocation, log, logFunction)
from library.objectmodels import BaseFields, relic_asset, temp_asset
from PySide6.QtCore import (Property, QEvent, QFile, QItemSelectionModel,
                            QMargins, QMutex, QMutexLocker, QObject, QPoint,
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
from colorcheckerDetection import autoExpose

INGEST_PATH = Path(os.getenv('userprofile')) / '.relic/ingest'

CREATE_NO_WINDOW = 0x08000000

SIZE = ImageDimensions(288, 192)

PS_CMD = 'powershell -ExecutionPolicy bypass -command "{}"'

EXE_ICON_CMD = """Add-Type -AssemblyName System.Drawing;
$icon = [System.Drawing.Icon]::ExtractAssociatedIcon('{}');
$icon.ToBitmap().Save('{}')"""

NEAT_IMAGE_CMD = [
    'E:/OneDrive/Apps/Neat Image v8 Standalone/NeatImageCL.exe', '"{}"',
    '-sp',
    '-ow',
    '-e',
    '-b=M',
    '-s=',
]

def getMovInfo(fpath):
    """
    Gets Duration, Resolution and Framerate of supplied quicktime.

    Returns
    -------
    list (duration, resolution, framerate)

    EXAMPLE:
        >>> getMovInfo('dev/test.mov')
        >>> ['5.292', '912x899', '24']
    """
    cmd = 'exiftool -s3 -Duration# -ImageSize -VideoFrameRate "{}"'.format(fpath)
    output = subprocess.check_output(cmd, creationflags=CREATE_NO_WINDOW)
    result = output.decode("utf-8").split('\r\n')[:3]
    return result


def generatePreviews(img_buf, path):
    """Makes Proxy & Icon previews from an OpenImageIO image buffer"""

    spec = img_buf.spec()
    size = ImageDimensions(spec.width, spec.height, channels=3)
    size.makeDivisble() # ensure divisible width for jpeg 16x16 blocks

    proxy_spec = oiio.ImageSpec(size.w, size.h, size.channels, oiio.UINT8)
    proxy_spec['compression'] = 'jpeg:75'
    proxy_buf = oiio.ImageBuf(proxy_spec)

    icon_spec = oiio.ImageSpec(SIZE.w, SIZE.h, 3, oiio.UINT8)
    icon_spec['compression'] = 'jpeg:40'
    icon_buf = oiio.ImageBuf(icon_spec)

    oiio.ImageBufAlgo.resize(proxy_buf, img_buf, filtername='cubic')
    oiio.ImageBufAlgo.fit(icon_buf, proxy_buf, filtername='cubic', exact=True)

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


def assetFromStill(spec, icon_path, in_img_path):
    icon = QPixmap.fromImage(QImage(str(icon_path)))
    res = '{}x{}x{}'.format(spec.full_width, spec.full_height, spec.nchannels)
    asset = temp_asset(
        name=in_img_path.stem,
        category=0,
        type=0,
        duration=0,
        resolution=res,
        path=in_img_path,
        icon=icon,
    )
    return asset


class ConversionRouter(QObject):

    started = Signal(int)
    progress = Signal(object)
    finished = Signal()
    error = Signal(Exception)

    def __init__(self, function_map, parent=None):
        super(ConversionRouter, self).__init__(parent)
        self.function_map = function_map
        
        # Ensure our local ingest location exists
        self.ingest_path = INGEST_PATH

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
                    img_function = partial(getattr(self, 'processSEQ'), img, out_img_path)
                else:
                    img_function = partial(getattr(self, func), img, out_img_path)
                conversion_functions.append(img_function)

        if conversion_functions:
            self.started.emit(self.files_todo)
            for func in conversion_functions:
                try:
                    asset = func()
                    self.progress.emit(asset)
                except Exception as exerr:
                    print(exerr)
                    log.error('conversion error: %s' % exerr)
                    #self.error.emit(exerr)

    @staticmethod
    @logFunction('Making preview from (MOV)')
    def processMOV(in_img_path, out_img_path):
        duration, res, rate = getMovInfo(in_img_path)
        duration = float(duration)
        framerate = float(rate)
        pts = (((duration * framerate) * 24) / 100) / 24
        width, height = res.split('x')

        icon_path = out_img_path.suffixed('_icon', ext='.jpg')
        w, h = SIZE.w, SIZE.h
        FILTER_GRAPH_ICON = [
            f'setpts=PTS/{pts}',
            f'scale=w={w}:h={h}:force_original_aspect_ratio=decrease',
            f'pad={w}:{h}:(ow-iw)/2:(oh-ih)/2']

        ow = int(width) + (int(width) % 16)
        oh = int(height) - (int(height) % 16)

        FILTER_GRAPH_PROXY = [
            f'scale=w={ow}:h={oh}:force_original_aspect_ratio=decrease',
            f'pad={ow}:{oh}:(ow-iw)/2:(oh-ih)/2'
        ]

        cmd = [
            'ffmpeg',
            '-loglevel', 'error',
            '-y',
            '-i', str(in_img_path),
            '-pix_fmt', 'yuv422p',
            '-vcodec', 'h264',
            '-crf', '26',
            '-preset', 'medium',
            '-tune', 'fastdecode',
            '-movflags', '+faststart',
            '-vf', ','.join(FILTER_GRAPH_PROXY),
            str(out_img_path.suffixed('_proxy', ext='.mp4')),
            '-r', '24',
            '-vf', ','.join(FILTER_GRAPH_ICON),
            '-an',  # Flag to not try linking audio file
            '-pix_fmt', 'yuv422p',
            '-vcodec', 'h264',
            '-tune', 'fastdecode',
            '-movflags', '+faststart',
            str(out_img_path.suffixed('_icon', ext='.mp4')),
            '-vf', 'select=gte(n\,1),{}'.format(','.join(FILTER_GRAPH_ICON[1:])),
            '-vframes', '1',
            str(icon_path),
        ]
        subprocess.call(cmd, stdout=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW)

        spec = oiio.ImageSpec(int(width), int(height), 3, oiio.UINT8)
        asset = assetFromStill(spec, icon_path, in_img_path)
        asset.duration = int(duration)
        asset.framerate = framerate

        return asset

    @staticmethod
    def processFILM(in_path, out_path):
        asset = temp_asset(
            name=in_path.stem,
            category=0,
            type=0,
            duration=0,
            path=in_path,
        )
        return asset

    @staticmethod
    @logFunction('Making preview from (SEQ)')
    def processSEQ(in_img_path, out_img_path):
        frames = sorted(glob.glob(str(in_img_path.sequence_path)))
        framelength = len(frames)
        a_input = oiio.ImageInput.open(frames[0])
        spec = a_input.spec()
        a_input.close()
        pts = ((framelength * 24) / 100) / 24
        w, h = SIZE.w, SIZE.h
        width = spec.full_width
        height = spec.full_height 
        FILTER_GRAPH_ICON = [
            f'setpts=PTS/{pts}', 
            f'scale=w={w}:h={h}:force_original_aspect_ratio=decrease',
            f'pad={w}:{h}:(ow-iw)/2:(oh-ih)/2']

        ow = width + (width % 16)
        oh = height - (height % 16)

        FILTER_GRAPH_PROXY = [
            f'scale=w={ow}:h={oh}:force_original_aspect_ratio=decrease',
            f'pad={ow}:{oh}:(ow-iw)/2:(oh-ih)/2'
        ]

        command = [
            'ffmpeg',
            '-loglevel', 'error',
            '-y',
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-s', f'{width}x{height}',
            '-pix_fmt', 'rgb24',
            '-i', '-',  # Input comes from a pipe
            '-r', '24',  # fps
            '-an', # Flag to not try linking audio file
            '-pix_fmt', 'yuv422p',
            '-vcodec', 'h264',
            '-crf', '25',
            '-preset', 'medium',
            '-tune', 'fastdecode',
            '-movflags', '+faststart',
            '-vf', ','.join(FILTER_GRAPH_PROXY),
            str(out_img_path.suffixed('_proxy', ext='.mp4')),
            '-vf', ','.join(FILTER_GRAPH_ICON),
            '-an',  # Flag to not try linking audio file
            '-vcodec', 'h264',
            '-tune', 'fastdecode',
            '-movflags', '+faststart',
            str(out_img_path.suffixed('_icon', ext='.mp4'))
        ]

        pipe = subprocess.PIPE
        pr = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stdin=pipe,
            creationflags=CREATE_NO_WINDOW)

        i = 0
        while frames:
            frame = frames.pop(0)
            i += 1
            buf = oiio.ImageBuf(str(frame))
            spec = buf.spec()
            r = spec.roi

            buf = oiio.ImageBufAlgo.colorconvert(buf, "Linear", "sRGB")
            # Write Icon from center of range
            if i == int(framelength / 2):
                icon_path = generatePreviews(buf, out_img_path)
    
            data = buf.get_pixels(format=oiio.UINT8)

            if spec.height != spec.full_height or spec.width != spec.full_width:
                full_pixels = np.zeros((spec.full_height, spec.full_width, 3), dtype=np.uint8)
                full_pixels[r.ybegin:r.yend, r.xbegin:r.xend, :] = data[:, :, :3]
                data = full_pixels

            pr.stdin.write(data[:, :, :3].tobytes())
            pr.stdin.flush()

        pr.stdin.close()
        asset = assetFromStill(spec, icon_path, in_img_path)
        asset.duration = int(framelength/24)
        return asset

    @staticmethod
    @logFunction('Making preview from (HDR)')
    def processHDR(in_img_path, out_img_path):
        imgbuf = oiio.ImageBuf(str(in_img_path))
        if imgbuf.has_error:
            raise Exception
        spec = imgbuf.spec()
        formatted = oiio.ImageBuf(
            oiio.ImageSpec(spec.width, spec.height, 3, oiio.UINT8)
        )
        oiio.ImageBufAlgo.pow(formatted, imgbuf, (0.454, 0.454, 0.454))
        icon_path = generatePreviews(formatted, out_img_path)
        asset = assetFromStill(spec, icon_path, in_img_path)
        return asset

    @staticmethod
    @logFunction('Making preview from (TOOL)')
    def processTOOL(in_path, out_path):
        if in_path.ext == '.exe':
            temp_path = out_path.suffixed('', '.bmp')
            cmd = PS_CMD.format(EXE_ICON_CMD.format(in_path, temp_path))
            subprocess.call(cmd)
            out_img = QImage(SIZE.w, SIZE.h, QImage.Format_RGB888)
            out_img.fill(QColor(65, 65, 65, 255))

            src_img = QImage(str(temp_path))
            scaled_img = src_img.scaled(SIZE.w, SIZE.h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            painter = QPainter(out_img)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            
            # calculate size offset image to center it.
            width_diff = int((SIZE.w - scaled_img.width()) / 2)

            painter.drawImage(width_diff, 0, scaled_img)
            painter.end()
            icon = QPixmap.fromImage(out_img)
            out_icon = out_path.suffixed('_icon', ext='.jpg')
            icon.save(str(out_icon))

            with open(str(out_path), 'w') as fp:
                fp.write(str(in_path))

            in_path = out_path

        else:
            icon = QPixmap.fromImage(QImage(':resources/icons/noicon.jpg'))
            out_icon = out_path.suffixed('_icon', ext='.jpg')
            icon.save(str(out_icon))

        asset = temp_asset(
            name=in_path.stem,
            category=5,
            type=0,
            duration=0,
            path=in_path,
            icon=icon,
        )
        return asset

    @staticmethod
    @logFunction('Making preview from (RAW)')
    def processRAW(in_img_path, out_img_path, denoise=True):
        proc = libraw.LibRaw()

        # Read RAW data
        proc.open_file(str(in_img_path))
        proc.unpack()

        # Set libraw parameters
        proc.set_output_color(ctypes.c_int(6))
        proc.set_no_auto_bright(ctypes.c_int(1))

        proc.dcraw_process()

        raw_img_data = proc.imgdata.image
        img_data = raw_img_data[:, :, :-1] # remove alpha
        
        size = ImageDimensions.fromArray(img_data)
        # convert ACES2065-1 to ACEScg 
        spec = oiio.ImageSpec(size.w, size.h, size.channels, oiio.HALF)
        buf = oiio.ImageBuf(spec)
        buf.set_pixels(spec.roi, img_data)
        ACESCG_MATRIX = (
            1.4514393161,  -0.0765537734, 0.0083161484, 0,
            -0.2365107469,  1.1762296998, -0.0060324498, 0,
            -0.2149285693, -0.0996759264,  0.9977163014, 0,
            0,         0,         0,       1
        )
        buf = oiio.ImageBufAlgo.colormatrixtransform(buf, ACESCG_MATRIX)

        out_img_path.ext = '.exr' # Raw is always converted to exr.
        in_img_path.ext = '.exr' # Raw is always converted to exr.
        if denoise:
            denoise_path = out_img_path.suffixed('_dn', '.tif')
            tif_path = out_img_path.suffixed('_orig', '.tif')

            tifbuf = oiio.ImageBuf(
                oiio.ImageSpec(spec.width, spec.height, 3, oiio.UINT16)
            )
            offset = 0.01
            buf = oiio.ImageBufAlgo.add(buf, offset)
            oiio.ImageBufAlgo.pow(tifbuf, buf, (0.227, 0.227, 0.227))

            tifbuf.write(str(denoise_path))
            NEAT_IMAGE_CMD[1] = '"{}"'.format(str(denoise_path))
            subprocess.call(' '.join(NEAT_IMAGE_CMD), stdout=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW)

            denoise_buf = oiio.ImageBuf(str(denoise_path))
            denoise_buf = oiio.ImageBufAlgo.pow(denoise_buf, (4.4, 4.4, 4.4))
            tifbuf = oiio.ImageBufAlgo.pow(tifbuf, (4.4, 4.4, 4.4))

            dn = (denoise_buf.get_pixels(oiio.FLOAT) - offset)
            og = (tifbuf.get_pixels(oiio.FLOAT) - offset)

            noise = og - dn
            out_denoised = (buf.get_pixels() - offset) - noise
            buf.set_pixels(buf.spec().roi, out_denoised)
            #buf.specmod().attribute('compression', 'dwaa:15')
            os.remove(str(denoise_path))

        buf.write(str(out_img_path))

        formatted = oiio.ImageBuf(
            oiio.ImageSpec(spec.width, spec.height, 3, oiio.UINT8)
        )
        oiio.ImageBufAlgo.pow(formatted, buf, (0.454, 0.454, 0.454))
        icon_path = generatePreviews(formatted, out_img_path)
        asset = assetFromStill(spec, icon_path, in_img_path)

        return asset

    @staticmethod
    @logFunction('Making preview from (LDR)')
    def processLDR(in_img_path, out_img_path):
        #in_img_path.copyTo(out_img_path)
        imgbuf = oiio.ImageBuf(str(in_img_path))
        if imgbuf.has_error:
            raise Exception
        spec = imgbuf.spec()
        icon_path = generatePreviews(imgbuf, out_img_path)
        asset = assetFromStill(spec, icon_path, in_img_path)
        return asset


def applyImageModifications(img_path, temp_asset):
    img_buf = oiio.ImageBuf(str(img_path))
    spec = img_buf.spec()
    if temp_asset.colormatrix:
        img_buf = oiio.ImageBufAlgo.colormatrixtransform(img_buf, temp_asset.colormatrix)

    # Crop using annotation BoundingBox
    annotated = img_path.parents(0) / 'annotations' / (img_path.name + '_proxy.1.png')
    if annotated.exists:
        anno_buf = oiio.ImageBuf(str(annotated))
        anno_buf = oiio.ImageBufAlgo.pow(anno_buf, (2.2, 2.2, 2.2))

        alpha = anno_buf.get_pixels(oiio.UINT8)[:, :, 3]
        alpha = cv2.Canny(alpha, 2, 48)
        contours, _hierarchy = cv2.findContours(alpha, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        for i, cnt in enumerate(contours):
            x, y, w, h = cv2.boundingRect(cnt)
            img_buf = oiio.ImageBufAlgo.cut(img_buf, roi=oiio.ROI(x, (x + w), y, (y + h)))
            spec = img_buf.spec()
            break
        os.remove(str(annotated))
    elif not temp_asset.colormatrix:
        img_buf = autoExpose(img_buf)

    img_buf.specmod().attribute('compression', 'dwaa:15')
    img_buf.write(str(img_path))

    # generate new previews from modified image.
    formatted = oiio.ImageBuf(
        oiio.ImageSpec(spec.width, spec.height, 3, oiio.UINT8)
    )
    oiio.ImageBufAlgo.pow(formatted, img_buf, (0.454, 0.454, 0.454))
    icon_path = generatePreviews(formatted, img_path)
    temp_asset.icon = QPixmap.fromImage(QImage(str(icon_path)))


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
                temp_filename, item, extra_files = self.queue[0]
                ingest_path = self.ingest_path
                self.mutex.unlock()

                #log.debug(str('item'))
                in_path = item.path
                category = item.categoryName
                subcategory = item.subcategory.name
                item.path = Path(subcategory) / (item.name + in_path.ext)
                out_path = item.network_path

                files_map = {}

                temp_path = ingest_path / (temp_filename + in_path.ext)
                if temp_path.exists:
                    files_map[temp_path] = out_path
                else:
                    files_map[in_path] = out_path

                # Add extra auxillary files to the packaged content.
                if extra_files:
                    for extra in extra_files:
                        subfolder = getAssetSourceLocation(extra)
                        filename = Path(extra).stem
                        new_path = out_path.parents(0) / subfolder / filename

                        files_map[Path(extra)] = new_path

                if in_path.ext in ['.ma', '.mb']:
                    formats = [
                        ['', '.mtlx'],
                        ['_icon', '.jpg'],
                        ['_icon', '.mp4'],
                    ]
                    for pair in formats:
                        suffix, ext = pair
                        src = in_path.suffixed(suffix, ext)
                        if src.exists:
                            dst = out_path.suffixed(suffix, ext)
                            files_map[src] = dst
                elif in_path.ext in TOOLS_EXT:
                    in_icon = in_path.suffixed('_icon', ext='.jpg')
                    if in_icon.exists:
                        out_icon = out_path.suffixed('_icon', ext='.jpg')
                        files_map[in_icon] = out_icon
                elif in_path.sequence_path or in_path.ext in MOVIE_EXT:
                    in_proxy = temp_path.suffixed('_proxy', ext='.mp4')
                    in_icon = temp_path.suffixed('_icon', ext='.jpg')
                    out_icon = out_path.suffixed('_icon', ext='.jpg')
                    out_proxy = out_path.suffixed('_proxy', ext='.mp4')
                    # Movies have video icon preview's
                    in_icon_mov = temp_path.suffixed('_icon', ext='.mp4')
                    out_icon_mov = out_path.suffixed('_icon', ext='.mp4')
                    files_map[in_icon_mov] = out_icon_mov
                    files_map[in_icon] = out_icon
                    files_map[in_proxy] = out_proxy
                    # Set the path to include the frame expression
                    if in_path.sequence_path:
                        item.path = Path(subcategory) / (item.name + in_path.frame_expr + in_path.ext)
                else: # Only single-frame images have proxy jpegs.
                    in_proxy = temp_path.suffixed('_proxy', ext='.jpg')
                    out_proxy = out_path.suffixed('_proxy', ext='.jpg')

                    in_icon = temp_path.suffixed('_icon', ext='.jpg')
                    out_icon = out_path.suffixed('_icon', ext='.jpg')

                    files_map[in_icon] = out_icon
                    files_map[in_proxy] = out_proxy

                for src, dst in files_map.items():
                    src.checkSequence()
                    if src.sequence_path:
                        for seq_file in glob.glob(src.sequence_path):
                            frame = Path(seq_file).frame
                            src.frame = frame
                            dst.frame = frame
                            src.moveTo(dst)
                    else:
                        src.moveTo(dst)
                item.filehash = out_path.parents(0).hash
                item.filesize = out_path.parents(0).size
                # Clear the Id to allow for database creation
                self.queue.pop(0)
                self.itemDone.emit(item)

            self.mutex.lock()
            self.condition.wait(self.mutex)
            self.mutex.unlock()
