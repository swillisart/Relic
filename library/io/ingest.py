import os
import subprocess
from collections import deque
from functools import partial
import traceback

import numpy as np
import oiio.OpenImageIO as oiio
from imagine import hdr, libraw
#from imagine.colorchecker_detection import autoExpose
from imagine.exif import EXIFTOOL
from library.config import RELIC_PREFS, log
from library.io.util import ImageDimensions
from PySide6.QtCore import (Property, QDir, QDirIterator, QMutex, QMutexLocker,
                            QObject, QRunnable, Qt, QThread, QWaitCondition,
                            Signal, Slot)
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap, Qt, QImageWriter 
from relic.local import (INGEST_PATH, Extension, TempAsset,
                        FileType, getAssetSourceLocation)
from relic.scheme import Class
from sequence_path.main import SequencePath as Path

CREATE_NO_WINDOW = 0x08000000

THUMBNAIL_SIZE = ImageDimensions(288, 192)

PS_CMD = 'powershell -ExecutionPolicy bypass -command "{}"'

EXE_ICON_CMD = """Add-Type -AssemblyName System.Drawing;
$icon = [System.Drawing.Icon]::ExtractAssociatedIcon('{}');
$icon.ToBitmap().Save('{}')"""

def getMovInfo(fpath):
    MOV_EXIF_META = ['-Duration#', '-ImageSize', '-VideoFrameRate']
    mov_metadata = EXIFTOOL.getFields(str(fpath), MOV_EXIF_META, {})
    return mov_metadata

def getRawInfo(fpath):
    """Gets Exif metadata from Canon cameras raw .cr2.
    """
    RAW_EXIF_META = [
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
    result = EXIFTOOL.getFields(str(fpath), RAW_EXIF_META, {})
    return result

def generatePreviews(path, img_buf=None):
    """Makes Proxy & Icon previews from an OpenImageIO image buffer"""
    if not img_buf:
        img_buf = oiio.ImageBuf(str(path))

    spec = img_buf.spec()
    size = ImageDimensions(spec.width, spec.height, channels=3)
    size.makeDivisble() # ensure divisible width for jpeg 16x16 blocks

    proxy_spec = oiio.ImageSpec(size.w, size.h, size.channels, oiio.UINT8)
    proxy_spec['compression'] = 'jpeg:70'
    proxy_buf = oiio.ImageBuf(proxy_spec)

    icon_spec = THUMBNAIL_SIZE.asSpec(oiio.UINT8)
    icon_spec['compression'] = 'jpeg:50'
    icon_buf = oiio.ImageBuf(icon_spec)

    oiio.ImageBufAlgo.resize(proxy_buf, img_buf, filtername='cubic')
    oiio.ImageBufAlgo.fit(icon_buf, proxy_buf, filtername='cubic', exact=True)


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

def assetFromStill(spec, icon_path, in_path):
    icon = QPixmap.fromImage(QImage(str(icon_path)))
    asset = TempAsset(
        name=in_path.stem,
        category=0,
        type=0,
        duration=0,
        resolution=str(ImageDimensions.fromSpec(spec)),
        path=in_path,
        icon=icon,
    )
    return asset

def tempAssetFromImage(in_path, out_path, src_img):
    icon_img = makeImagePreview(src_img)
    writeImagePreviews(src_img, icon_img, out_path)
    dimensions = ImageDimensions.fromQImage(src_img)
    temp_asset = TempAsset(
        name=in_path.stem,
        category=0,
        type=0,
        duration=0,
        resolution=str(dimensions),
        path=in_path,
        icon=QPixmap.fromImage(icon_img),
    )
    return temp_asset

def reassignExifMetadata(path, img_buf, prefix='exif/'):
    ## Embed the Exif camera metadata into the metadata.
    raw_meta = getRawInfo(path)

    spec_modifier = img_buf.specmod()
    for key, value in raw_meta.items():
        spec_modifier.attribute(f'{prefix}{key}', value)

def makeImagePreview(source_img):
    w = THUMBNAIL_SIZE.w
    h = THUMBNAIL_SIZE.h
    out_img = QImage(w, h, QImage.Format_RGB888)
    out_img.fill(QColor(65, 65, 65))

    painter = QPainter(out_img)
    painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
    # resize the image to the globally defined thumbnail size. 
    resized = source_img.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    # calculate size offset image to center it.
    width_diff = int((w - resized.width()) / 2)

    painter.drawImage(width_diff, 0, resized)
    painter.end()
    return out_img

def thumbnailFromExe(self, in_path, out_path):
    temp_path = out_path.suffixed('', '.bmp')
    cmd = PS_CMD.format(EXE_ICON_CMD.format(in_path, temp_path))
    subprocess.call(cmd, creationflags=CREATE_NO_WINDOW)

    src_img = QImage(str(temp_path))
    out_img = makeImagePreview(src_img)

    os.remove(str(temp_path))
    return out_img

def writeImagePreviews(proxy_img, icon_img, out_path):
    proxy_img.save(str(out_path.suffixed('_proxy', ext='.jpg')))
    icon_img.save(str(out_path.suffixed('_icon', ext='.jpg')))

# ----- Ingest Processors -----

def processTOOL(in_path, out_path, flag):
    if flag & FileType.EXE:
        # write to path to the executable inside as plain text.
        with open(str(out_path), 'w') as fp:
            fp.write(str(in_path))
        
        preview_img = thumbnailFromExe(in_path, out_path)
        in_path = out_path
    else:
        preview_img = QImage(':resources/icons/noicon.jpg')
    icon = QPixmap.fromImage(preview_img)
    icon.save(str(out_path.suffixed('_icon', ext='.jpg')))

    asset = TempAsset(
        name=in_path.stem,
        category=5,
        type=0,
        duration=0,
        path=in_path,
        icon=icon,
    )
    return asset

def processMOV(in_path, out_path):
    #""">>> ['5.292', '912x899', '24']"""
    log.debug(str(in_path))
    mov_metadata = getMovInfo(in_path)
    log.debug(str(mov_metadata))
    duration = float(mov_metadata.get('Duration'))
    framerate = float(mov_metadata.get('VideoFrameRate'))
    pts = (((duration * framerate) * 24) / 100) / 24
    width, height = mov_metadata.get('ImageSize', '0x0').split('x')

    icon_path = out_path.suffixed('_icon', ext='.jpg')
    w, h = THUMBNAIL_SIZE.w, THUMBNAIL_SIZE.h
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
        '-i', str(in_path),
        '-pix_fmt', 'yuv422p',
        '-vcodec', 'h264',
        '-crf', '26',
        '-preset', 'medium',
        '-tune', 'fastdecode',
        '-movflags', '+faststart',
        '-vf', ','.join(FILTER_GRAPH_PROXY),
        str(out_path.suffixed('_proxy', ext='.mp4')),
        '-r', '24',
        '-vf', ','.join(FILTER_GRAPH_ICON),
        '-an',  # Flag to not try linking audio file
        '-pix_fmt', 'yuv422p',
        '-vcodec', 'h264',
        '-tune', 'fastdecode',
        '-movflags', '+faststart',
        str(out_path.suffixed('_icon', ext='.mp4')),
        '-vf', 'select=gte(n\,1),{}'.format(','.join(FILTER_GRAPH_ICON[1:])),
        '-vframes', '1',
        str(icon_path),
    ]
    subprocess.call(cmd, stdout=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW)

    spec = oiio.ImageSpec(int(width), int(height), 3, oiio.UINT8)
    asset = assetFromStill(spec, icon_path, in_path)
    asset.duration = int(duration)
    asset.framerate = framerate

    return asset


def processSEQ(in_path, out_path, flag):
    frames = sorted(in_path.frames)
    frame_count = len(frames)
    if frame_count == 1:
        return processHDR(in_path, out_path, flag)
    a_input = oiio.ImageInput.open(frames[0])
    spec = a_input.spec()
    a_input.close()
    pts = ((frame_count * 24) / 100) / 24
    w, h = THUMBNAIL_SIZE.w, THUMBNAIL_SIZE.h
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
        str(out_path.suffixed('_proxy', ext='.mp4')),
        '-vf', ','.join(FILTER_GRAPH_ICON),
        '-an',  # Flag to not try linking audio file
        '-vcodec', 'h264',
        '-tune', 'fastdecode',
        '-movflags', '+faststart',
        str(out_path.suffixed('_icon', ext='.mp4'))
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
        if i == int(frame_count / 2):
            icon_path = generatePreviews(out_path, buf)

        data = buf.get_pixels(format=oiio.UINT8)

        if spec.height != spec.full_height or spec.width != spec.full_width:
            full_pixels = np.zeros((spec.full_height, spec.full_width, 3), dtype=np.uint8)
            full_pixels[r.ybegin:r.yend, r.xbegin:r.xend, :] = data[:, :, :3]
            data = full_pixels

        pr.stdin.write(data[:, :, :3].tobytes())
        pr.stdin.flush()

    pr.stdin.close()
    asset = assetFromStill(spec, icon_path, in_path)
    asset.duration = int(frame_count/24)
    return asset

def processRAW(in_path, out_path, flag):
    in_path.copyTo(out_path)
    in_path = out_path
    img_bytes = EXIFTOOL.getPreview(str(in_path))
    src_img = QImage()
    src_img.loadFromData(img_bytes)
    asset = tempAssetFromImage(in_path, out_path, src_img)
    setattr(asset, 'class', flag)
    return asset

def processLDR(in_path, out_path, flag):
    src_img = QImage(str(in_path))

    if flag & FileType.PNG: # convert PNG to TIF
        in_path = out_path.suffixed('', '.tif')
        writer = QImageWriter(str(in_path))
        writer.setCompression(1) # 0(none) 1(LZW)
        writer.write(src_img)
    asset = tempAssetFromImage(in_path, out_path, src_img)
    return asset

def processHDR(in_path, out_path, flag):
    src_buf = oiio.ImageBuf(str(in_path))
    if src_buf.has_error:
        raise Exception
    spec = src_buf.spec()
    w, h, c = spec.full_width, spec.full_height, spec.nchannels
    if flag & FileType.HDR: # convert HDR to EXR
        in_path = out_path.suffixed('', '.exr')
        src_buf.specmod().attribute('compression', 'dwaa:15')
        src_buf.write(str(in_path))

    img_buf = oiio.ImageBuf(oiio.ImageSpec(w, h, 3, oiio.UINT8))
    oiio.ImageBufAlgo.pow(img_buf, src_buf, (0.454, 0.454, 0.454))
    array = img_buf.get_pixels(format=oiio.UINT8)
    src_img = QImage(array, w, h, QImage.Format_RGB888)
    icon_img = makeImagePreview(src_img)
    writeImagePreviews(src_img, icon_img, out_path)
    asset = TempAsset(
        name=in_path.stem,
        category=0,
        type=0,
        duration=0,
        resolution=f'{w}x{h}x{c}',
        path=in_path,
        icon=QPixmap.fromImage(icon_img),
    )
    return asset

def processFILM(in_path, out_path, flag):
    asset = TempAsset(
        name=in_path.stem,
        category=0,
        type=0,
        duration=0,
        path=in_path,
    )
    setattr(asset, 'class', Class.IMAGE)
    return asset

def processIMAGE(in_path, out_path, flag):
    if flag & (FileType.JPG | FileType.TIF | FileType.PNG | FileType.JPEG):
        # Assumes gamma correction has already been encoded into the file.
        asset = processLDR(in_path, out_path, flag)
    elif flag & (FileType.HDR | FileType.EXR):
        # Linear image will get a nice tonemapping applied to the previews.
        asset = processHDR(in_path, out_path, flag)
    setattr(asset, 'class', flag)
    return asset

def processLIGHT(in_path, out_path, flag):
    return None


class ConversionRouter(QObject):

    started = Signal(int)
    error = Signal(int)
    progress = Signal(object)
    finished = Signal()

    def __init__(self, ingest_map, parent=None):
        super(ConversionRouter, self).__init__(parent)
        self.ingest_map = ingest_map
        self.ext_filters = [f'*{x}' for x in ingest_map.keys()]
        # Ensure our local ingest location exists
        self.ingest_path = INGEST_PATH
        self.queued_folders = deque()

    def addToQueue(self, folders):
        self.queued_folders.extend(folders)

    def run(self):
        import timeit
        start = timeit.default_timer()
        self.files_todo = 0
        queue = self.queued_folders
        while queue:
            self.processDirectory(queue.popleft())
        print('collection time:', round(timeit.default_timer() - start, 3))
        self.finished.emit()

    def processDirectory(self, directory):
        conversion_functions = []
        sequences = []
        ingest_path = self.ingest_path
        ingest_map = self.ingest_map
        it = QDirIterator(
            directory,
            self.ext_filters,
            QDir.Files, QDirIterator.Subdirectories
        )

        while it.hasNext():
            in_path = Path(it.next())
            if in_path.name in sequences:
                continue

            self.files_todo += 1
            ext = in_path.ext
            func, flag = ingest_map[ext]
            out_path = ingest_path / f'unsorted{self.files_todo}{ext}'
            
            if in_path.isSequence():
                sequences.append(in_path.name)
                func = processSEQ

            ingest_function = partial(func, in_path, out_path, flag)
            conversion_functions.append(ingest_function)

        progress_signal = self.progress
        if conversion_functions:
            self.started.emit(self.files_todo)
            for converter in conversion_functions:
                try:
                    asset = converter()
                    progress_signal.emit(asset)
                except Exception as exerr:
                    print(traceback.format_exc())
                    self.files_todo -= 1
                    self.error.emit(self.files_todo)


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
    if not img_path.exists():
        temp_asset.path.copyTo(img_path)
        temp_asset.path = img_path

    is_raw = img_path.ext in Extension.RAW
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
    annotated = img_path.parent / 'annotations' / (img_path.name + '_proxy.1.png')
    if annotated.exists():
        img_buf = hdr.annotationCrop(img_buf, str(annotated))

    # Set the meta attributes and write the file.
    if is_raw:
        try:
            reassignExifMetadata(raw_path, img_buf, prefix='')
        except Exception:
            print('metadata reassignment error: ', traceback.format_exc())

    img_buf.specmod().attribute('compression', 'dwaa:15')
    img_buf = oiio.ImageBufAlgo.reorient(img_buf)
    img_buf.write(str(img_path))
    spec = img_buf.spec()

    # generate new previews from modified image.
    formatted = oiio.ImageBuf(
        oiio.ImageSpec(spec.width, spec.height, 3, oiio.UINT8)
    )
    oiio.ImageBufAlgo.pow(formatted, img_buf, (0.454, 0.454, 0.454))

    array = formatted.get_pixels(format=oiio.UINT8)
    src_img = QImage(array, spec.width, spec.height, QImage.Format_RGB888)
    icon_img = makeImagePreview(src_img)
    writeImagePreviews(src_img, icon_img, temp_asset.path)
    dimensions = ImageDimensions.fromQImage(src_img)
    
    setattr(temp_asset, 'class', FileType.EXR)
    temp_asset.resolution = str(dimensions)
    temp_asset.icon = QPixmap.fromImage(icon_img)
    if is_raw: # Clean up
        del img_buf
        del img_data
        os.remove(raw_path)
    return temp_asset

def blendRawExposures(assets_by_file):
    primary_asset = list(assets_by_file.values())[0]
    primary_path = list(assets_by_file.keys())[0]
    out_file = primary_path.suffixed('', ext='.exr')
    hdr.blendExposures(assets_by_file.keys(), out_file, align=True)
    primary_asset.path = out_file
    primary_asset.aces = True
    img_buf = oiio.ImageBuf(str(out_file))
    raw_meta = reassignExifMetadata(primary_path, img_buf)
    [os.remove(str(x)) for x in assets_by_file.keys()]
    return primary_asset


class TaskRunnerSignals(QObject):
    completed = Signal(object)


class TaskRunner(QRunnable):
    def __init__(self, task, callback=None):
        super(TaskRunner, self).__init__()
        self.signals = TaskRunnerSignals()
        self.task = task
        self.callback = callback

    def run(self):
        result = self.task()
        if self.callback:
            self.callback(result)
        self.signals.completed.emit(result)


class IngestionThread(QThread):

    itemDone = Signal(object)

    def __init__(self, *args, **kwargs):
        super(IngestionThread, self).__init__(*args, **kwargs)
        self.mutex = QMutex()
        self.condition = QWaitCondition()
        self.ingest_path = INGEST_PATH
        self.ingest_path.mkdir(parents=True, exist_ok=True)
        self.stopped = False
        self.queue = deque()
        self.file_op = IngestionThread.moveOp

    @staticmethod
    def copyOp(src, dst):
        src.copyTo(dst)

    @staticmethod
    def moveOp(src, dst):
        src.moveTo(dst)

    @staticmethod
    def applyFileOperator(file_op, files_map):
        # Migrate the staged ingest files to their library location.
        for src, dst in files_map.items():
            if src.isSequence():
                for seq_file in src.frames:
                    frame = Path(seq_file).frame
                    src.frame = frame
                    dst.frame = frame
                    file_op(src, dst) # move or copy
            else:
                file_op(src, dst) # move or copy

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
            migrate_files = partial(IngestionThread.applyFileOperator, self.file_op)
            while self.queue:
                #self.mutex.unlock()
                if self.stopped:
                    return

                self.mutex.lock()
                temp_filename, item, extra_files = self.queue[0]
                ingest_path = self.ingest_path
                self.mutex.unlock()

                in_path = item.path
                #category = item.categoryName
                subcategory = item.subcategory.name
                item.path = Path(subcategory) / (item.name + in_path.ext)
                out_path = item.network_path

                files_map = {}

                temp_path = ingest_path / (temp_filename + in_path.ext)
                if temp_path.exists():
                    files_map[temp_path] = out_path
                else:
                    files_map[in_path] = out_path

                if extra_files: # Add extra auxillary files to the packaged content.
                    for extra in extra_files:
                        subfolder = getAssetSourceLocation(extra)
                        filename = Path(extra).stem
                        new_path = out_path.parent / subfolder / filename

                        files_map[Path(extra)] = new_path

                if in_path.ext in Extension.DCC:
                    formats = [
                        ['', '.mtlx'],
                        ['_icon', '.jpg'],
                        ['_icon', '.mp4'],
                    ]
                    for pair in formats:
                        suffix, ext = pair
                        src = in_path.suffixed(suffix, ext)
                        if src.exists():
                            dst = out_path.suffixed(suffix, ext)
                            files_map[src] = dst
                elif in_path.ext in Extension.TOOLS:
                    in_icon = in_path.suffixed('_icon', ext='.jpg')
                    if in_icon.exists():
                        files_map[in_icon] = out_path.suffixed('_icon', ext='.jpg')
                elif in_path.sequence_path or in_path.ext in Extension.MOVIE:
                    in_proxy = temp_path.suffixed('_proxy', ext='.mp4')
                    in_icon = temp_path.suffixed('_icon', ext='.jpg')
                    in_icon_mov = temp_path.suffixed('_icon', ext='.mp4')
                    # Movies have video icon preview's
                    files_map[in_icon_mov] = out_path.suffixed('_icon', ext='.mp4')
                    files_map[in_icon] = out_path.suffixed('_icon', ext='.jpg')
                    files_map[in_proxy] = out_path.suffixed('_proxy', ext='.mp4')
                    # Set the path to include the frame expression
                    if in_path.sequence_path:
                        item.path = Path(subcategory) / (item.name + in_path.frame_expr + in_path.ext)
                else: # Only single-frame images have proxy jpegs.
                    in_proxy = temp_path.suffixed('_proxy', ext='.jpg')
                    in_icon = temp_path.suffixed('_icon', ext='.jpg')

                    files_map[in_icon] = out_path.suffixed('_icon', ext='.jpg')
                    files_map[in_proxy] = out_path.suffixed('_proxy', ext='.jpg')

                migrate_files(files_map)

                # Calculate the final hash and size of the asset on network storage.
                item.filehash = out_path.parent.hash
                item.filesize = out_path.parent.size

                self.queue.popleft()
                self.itemDone.emit(item)

            self.mutex.lock()
            self.condition.wait(self.mutex)
            self.mutex.unlock()
