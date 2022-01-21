import ctypes
import glob
import os
import subprocess
from functools import partial

import numpy as np
import oiio.OpenImageIO as oiio
from library.abstract_objects import ImageDimensions
from library.config import (DCC_EXT, MOVIE_EXT, RELIC_PREFS, TOOLS_EXT, RAW_EXT,
                            getAssetSourceLocation, log, logFunction)
from library.objectmodels import BaseFields, relic_asset, temp_asset
from PySide6.QtCore import (Property, QEvent, QFile, QItemSelectionModel,
                            QMargins, QMutex, QMutexLocker, QObject, QPoint,
                            QPropertyAnimation, QRect, QRegularExpression,
                            QSize, QSortFilterProxyModel, Qt, QTextStream,
                            QThread, QWaitCondition, Signal, Slot, QRunnable)
from PySide6.QtGui import (QAction, QColor, QCursor, QFont, QFontMetrics,
                           QIcon, QImage, QPainter, QPixmap,
                           QRegularExpressionValidator, QStandardItemModel, Qt)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QBoxLayout,
                               QDialog, QDockWidget, QFrame, QLabel, QLayout,
                               QLineEdit, QListView, QMenu, QScrollArea,
                               QStyledItemDelegate, QTreeView, QVBoxLayout,
                               QWidget)
from sequencePath import sequencePath as Path
from imagine import hdr, libraw
from imagine.colorchecker_detection import autoExpose
from imagine.exif import EXIFTOOL


INGEST_PATH = Path(os.getenv('userprofile')) / '.relic/ingest'

CREATE_NO_WINDOW = 0x08000000

TSIZE = ImageDimensions(288, 192)

PS_CMD = 'powershell -ExecutionPolicy bypass -command "{}"'

EXE_ICON_CMD = """Add-Type -AssemblyName System.Drawing;
$icon = [System.Drawing.Icon]::ExtractAssociatedIcon('{}');
$icon.ToBitmap().Save('{}')"""

def getMovInfo(fpath):
    fields = ['-Duration#', '-ImageSize', '-VideoFrameRate']
    mov_metadata = EXIFTOOL.getFields(str(fpath), fields, {})
    return mov_metadata

def getRawInfo(fpath):
    """
    Gets Exif metadata from Canon cameras raw .cr2.
    """
    fields = [
        '-CreateDate',
        '-CameraModelName',
        '-LensType',
        '-Orientation#',
        '-ShutterSpeed',
        '-Aperture',
        '-ISO',
        '-FocalLength',

        '-WhiteBalance',
        '-ColorTemperature',
        '-ExposureProgram',
        '-CanonFlashMode',
    ]
    result = EXIFTOOL.getFields(str(fpath), fields, {})
    return result

def generatePreviews(img_buf, path):
    """Makes Proxy & Icon previews from an OpenImageIO image buffer"""

    spec = img_buf.spec()
    size = ImageDimensions(spec.width, spec.height, channels=3)
    size.makeDivisble() # ensure divisible width for jpeg 16x16 blocks

    proxy_spec = oiio.ImageSpec(size.w, size.h, size.channels, oiio.UINT8)
    proxy_spec['compression'] = 'jpeg:75'
    proxy_buf = oiio.ImageBuf(proxy_spec)

    icon_spec = oiio.ImageSpec(TSIZE.w, TSIZE.h, 3, oiio.UINT8)
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
    icon_path = path.suffixed('_icon', ext='.jpg')
    proxy_path = path.suffixed('_proxy', ext='.jpg')
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
        #""">>> ['5.292', '912x899', '24']"""
        log.debug(str(in_img_path))
        mov_metadata = getMovInfo(in_img_path)
        log.debug(str(mov_metadata))
        duration = float(mov_metadata.get('Duration'))
        framerate = float(mov_metadata.get('VideoFrameRate'))
        pts = (((duration * framerate) * 24) / 100) / 24
        width, height = mov_metadata.get('ImageSize', '0x0').split('x')

        icon_path = out_img_path.suffixed('_icon', ext='.jpg')
        w, h = TSIZE.w, TSIZE.h
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
        if framelength == 1:
            return ConversionRouter.processHDR(in_img_path, out_img_path)
        a_input = oiio.ImageInput.open(frames[0])
        spec = a_input.spec()
        a_input.close()
        pts = ((framelength * 24) / 100) / 24
        w, h = TSIZE.w, TSIZE.h
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
            out_img = QImage(TSIZE.w, TSIZE.h, QImage.Format_RGB888)
            out_img.fill(QColor(65, 65, 65, 255))

            src_img = QImage(str(temp_path))
            scaled_img = src_img.scaled(TSIZE.w, TSIZE.h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            painter = QPainter(out_img)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            
            # calculate size offset image to center it.
            width_diff = int((TSIZE.w - scaled_img.width()) / 2)

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
    def processRAW(in_img_path, out_img_path):
        img_data = EXIFTOOL.getPreview(str(in_img_path))
        buf = hdr.bufFromArray(img_data)
        buf = oiio.ImageBufAlgo.channels(buf, (2, 1, 0, 3))
        ## Embed the Exif camera metadata into the metadata.
        raw_meta = getRawInfo(in_img_path)
        for key, value in raw_meta.items():
            buf.specmod().attribute(f'exif/{key}', value)

        jpeg_path = out_img_path.suffixed('_proxy', ext='.jpg')
        buf.write(str(jpeg_path))

        icon_spec = oiio.ImageSpec(TSIZE.w, TSIZE.h, 3, oiio.UINT8)
        icon_spec['compression'] = 'jpeg:40'
        icon_buf = oiio.ImageBuf(icon_spec)
        oiio.ImageBufAlgo.fit(icon_buf, buf, filtername='cubic', exact=True)
        # Composite icon image over constant grey
        bg = oiio.ImageBuf(icon_buf.spec())
        oiio.ImageBufAlgo.fill(bg, (0.247, 0.247, 0.247, 1.0))
        comp = oiio.ImageBufAlgo.over(icon_buf, bg)

        icon_path = out_img_path.suffixed('_icon', ext='.jpg')
        icon_buf.write(str(icon_path))

        asset = assetFromStill(buf.spec(), icon_path, in_img_path)
        in_img_path.copyTo(out_img_path)
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
    """Makes modifications in-place to the staged image data.
    Crops from an annotation, denoises raw, applies color from a detected matrix, 
    aligns the image rotation to the detected physical camera capture orientation,
    embeds exif data from source file and compresses exrs.

    Parameters
    ----------
    img_path : sequencePath
        
    temp_asset : temp_asset
        temporary asset object with custom processing fields for this function.

    """
    if not img_path.exists:
        temp_asset.path.copyTo(img_path)
        temp_asset.path = img_path

    is_raw = img_path.ext in RAW_EXT
    if is_raw:
        raw_path = str(img_path)
        img_data = libraw.decodeRaw(raw_path)
        img_buf = hdr.bufFromArray(img_data)
        img_path.ext = '.exr'
        temp_asset.path = img_path
    else:
        img_buf = oiio.ImageBuf(str(img_path))

    # Apply color changes before denoise.
    if temp_asset.colormatrix:
        img_buf = oiio.ImageBufAlgo.colormatrixtransform(img_buf, temp_asset.colormatrix)
    elif is_raw or temp_asset.aces:
        #img_buf = autoExpose(img_buf)
        img_buf = hdr.acesToCG(img_buf)
        temp_asset.aces = False

    # Denoise the full image before cropping.
    if temp_asset.denoise or int(RELIC_PREFS.denoise):
        denoise_path = img_path.suffixed('_dn', '.tif')
        img_buf = hdr.neatDenoise(img_buf, str(denoise_path))
        temp_asset.denoise = False

    # Crop using annotation BoundingBox
    annotated = img_path.parents(0) / 'annotations' / (img_path.name + '_proxy.1.png')
    if annotated.exists:
        img_buf = hdr.annotationCrop(img_buf, str(annotated))

    # Set the meta attributes and write the file.
    if is_raw:
        try:
            raw_meta = getRawInfo(raw_path)
            for key, value in raw_meta.items():
                img_buf.specmod().attribute(key, value)
        except Exception as exerr:
            print(exerr)

    img_buf.specmod().attribute('compression', 'dwaa:15')
    img_buf = oiio.ImageBufAlgo.reorient(img_buf)
    img_buf.write(str(img_path))
    spec = img_buf.spec()

    # generate new previews from modified image.
    formatted = oiio.ImageBuf(
        oiio.ImageSpec(spec.width, spec.height, 3, oiio.UINT8)
    )
    oiio.ImageBufAlgo.pow(formatted, img_buf, (0.454, 0.454, 0.454))
    icon_path = generatePreviews(formatted, img_path)
    temp_asset.resolution = '{}x{}x{}'.format(spec.full_width, spec.full_height, spec.nchannels)
    if is_raw: # Clean up
        del img_buf
        del img_data
        os.remove(raw_path)

    temp_asset.icon = QPixmap.fromImage(QImage(str(icon_path)))


def blendRawExposures(assets_by_file):
    primary_asset = list(assets_by_file.values())[0]
    primary_path = list(assets_by_file.keys())[0]
    out_file = primary_path.suffixed('', ext='.exr')
    hdr.blendExposures(assets_by_file.keys(), out_file, align=True)
    primary_asset.path = out_file
    primary_asset.aces = True

    raw_meta = getRawInfo(primary_path)
    img_buf = oiio.ImageBuf(str(out_file))
    for key, value in raw_meta.items():
        img_buf.specmod().attribute(key, value)
    [os.remove(str(x)) for x in assets_by_file.keys()]


class TaskRunnerSignals(QObject):
    completed = Signal(tuple)


class TaskRunner(QRunnable):
    
    def __init__(self, task, callback=None, signal=None):
        super(TaskRunner, self).__init__(signal)
        if signal:
            self.signal = TaskRunnerSignals()
        else:
            self.signal = None
        self.task = task
        self.callback = callback

    def run(self):
        result = self.task()
        if self.callback:
            self.callback(result)
        if self.signal and result:
            self.signal.completed.emit(result)


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

                if extra_files: # Add extra auxillary files to the packaged content.
                    for extra in extra_files:
                        subfolder = getAssetSourceLocation(extra)
                        filename = Path(extra).stem
                        new_path = out_path.parents(0) / subfolder / filename

                        files_map[Path(extra)] = new_path

                if in_path.ext in DCC_EXT:
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

                # Migrate the staged ingest files to their library location.
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

                # Calculate the final hash and size of the asset.
                item.filehash = out_path.parents(0).hash
                item.filesize = out_path.parents(0).size

                self.queue.pop(0)
                self.itemDone.emit(item)

            self.mutex.lock()
            self.condition.wait(self.mutex)
            self.mutex.unlock()
