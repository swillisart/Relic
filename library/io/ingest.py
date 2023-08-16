import os
import subprocess
from fractions import Fraction
from collections import deque
from functools import partial
from extra_types.properties import lazy_property

import traceback

import numpy as np
import oiio.OpenImageIO as oiio
from imagine import hdr, libraw
import av
from av.filter import Graph
from av import VideoFrame

#from imagine.colorchecker_detection import autoExpose
from imagine.exif import EXIFTOOL
from library.config import RELIC_PREFS, LOG
from library.io.util import ImageDimensions
from library.objectmodels import TempAsset # TODO: remove this dependency

from PySide6.QtCore import (Property, QDir, QDirIterator, QMutex, QMutexLocker,
                            QObject, QRunnable, Qt, QThread, QWaitCondition,
                            Signal, Slot)
from PySide6.QtGui import QColor, QImage, QPainter, Qt, QImageWriter, QImageReader
from relic.local import (INGEST_PATH, Extension, Category,
                        FileType, getAssetSourceLocation)

from relic.scheme import Class, AssetType
from relic.qt.role_model.delegates import ItemDispalyModes, IMAGE_CACHE

from sequence_path.main import SequencePath as Path

QImageReader.setAllocationLimit(0)
av.logging.set_level(av.logging.CRITICAL)

CREATE_NO_WINDOW = 0x08000000

THUMBNAIL_SIZE = ImageDimensions.fromQSize(ItemDispalyModes.THUMBNAIL.thumb_size) #(288, 192)

PS_CMD = 'powershell -ExecutionPolicy bypass -command "{}"'

EXE_ICON_CMD = """Add-Type -AssemblyName System.Drawing;
$icon = [System.Drawing.Icon]::ExtractAssociatedIcon('{}');
$icon.ToBitmap().Save('{}')"""


class FakeImageStream:
    def __init__(self, width, height, time_base):
        self.width =  width
        self.height = height
        self.time_base = time_base


class Encoder:
    __slots__ = ('container', 'stream', 'graph', 'time_base')
    FFMPEG_ARGS = {
        'pix_fmt': 'yuv422p',
        'crf': '26',
        'preset': 'medium',
        'tune': 'fastdecode',
    }
    def __init__(self, container, size, time_base, input_stream):
        self.container = container
        self.stream = self.createStream(container, size, time_base)
        self.graph = self.createScaleGraph(input_stream, size)
        self.time_base = time_base

    def createStream(self, container, size, time_base):
        video_stream = container.add_stream('h264', rate=24, options=Encoder.FFMPEG_ARGS)
        video_stream.width = size.w
        video_stream.height = size.h
        video_stream.time_base = time_base
        return video_stream

    def createScaleGraph(self, stream, dimensions):
        graph = Graph()
        w =  dimensions.w
        h = dimensions.h
        input_buffer = graph.add_buffer(
            width=stream.width, height=stream.height, format='yuv422p', time_base=stream.time_base,
        )
        scaler = f'w={w}:h={h}:force_original_aspect_ratio=decrease'
        padder = f'{w}:{h}:(ow-iw)/2:(oh-ih)/2'
        
        size_filter = graph.add('scale', scaler)
        pad_filter = graph.add('pad', padder)
        buffersink = graph.add('buffersink')

        input_buffer.link_to(size_filter)
        size_filter.link_to(pad_filter)
        pad_filter.link_to(buffersink)
        graph.configure()
        return graph


class VidOut:
    def __init__(self, path, input_stream):
        # Ensure 16x16 compatible format for h264 proxies
        proxy_size = ImageDimensions(input_stream.width, input_stream.height)
        proxy_size.makeDivisble(height=True)

        # Preview stream for thumbnail media is always 24fps.
        time_base = Fraction(1, 24)
        icon_container = av.open(str(path.suffixed('_icon', ext='.mp4')), "w")
        preview = Encoder(icon_container, THUMBNAIL_SIZE, time_base, input_stream)
        
        # Make the proxy stream as compressed
        proxy_container = av.open(str(path.suffixed('_proxy', ext='.mp4')), "w")
        proxy = Encoder(proxy_container, proxy_size, input_stream.time_base, input_stream)

        self.encodePreview = partial(VidOut.encodePreview,
            preview.container, preview.stream, preview.graph, preview.time_base)
        self.encodeProxy = partial(VidOut.encodeProxy,
            proxy.container, proxy.stream, proxy.graph)
        self.proxy = proxy
        self.preview = preview

    @staticmethod
    def encodePreview(container, stream, graph, time_base, frame_number, frame):
        graph.push(frame)
        icon_frame = graph.pull()
        icon_frame.time_base = time_base
        icon_frame.pts = frame_number / 10
        container.mux(stream.encode(icon_frame))
        return icon_frame

    @staticmethod
    def encodeProxy(container, stream, graph, frame):
        # Encode full-res proxy
        graph.push(frame)
        proxy_frame = graph.pull()
        container.mux(stream.encode(proxy_frame))
        return proxy_frame

    def __enter__(self):
        return self
        
    def __exit__(self, *exc):
        # close the input & output containers
        self.proxy.container.mux(self.proxy.stream.encode())
        self.proxy.container.close()
        self.preview.container.mux(self.preview.stream.encode())
        self.preview.container.close()
        return True

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


def tempAssetFromImage(in_path, out_path, src_img):
    icon_img = makeImagePreview(src_img)
    writeImagePreviews(src_img, icon_img, out_path)
    dimensions = ImageDimensions.fromQImage(src_img)
    temp_asset = TempAsset(
        name=in_path.stem,
        category=0,
        type=AssetType.COMPONENT.index,
        duration=0,
        resolution=str(dimensions),
        path=in_path,
        icon=icon_img,
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
    height_diff = int((h - resized.height()) / 2)

    painter.drawImage(width_diff, height_diff, resized)
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

class DefaultIcons(object):

    def create(self, resource_path):
        r = makeImagePreview(QImage(resource_path))
        IMAGE_CACHE.keep.append(r.cacheKey())
        return r 

    @lazy_property
    def raw(self):
        return self.create(':app/RedLogo.png')

    @lazy_property
    def document(self):
        return self.create(':resources/app/markdown_logo.png')


DEFAULT_ICONS = DefaultIcons()

# ----- Ingest Processors -----

def processTOOL(in_path, out_path, flag):
    if flag & FileType.EXE:
        # write to path to the executable inside as plain text.
        with open(str(out_path), 'w') as fp:
            fp.write(str(in_path))
        
        preview_img = thumbnailFromExe(in_path, out_path)
        in_path = out_path
    else:
        preview_img = QImage(':app/noicon.jpg')
    icon = preview_img
    icon.save(str(out_path.suffixed('_icon', ext='.jpg')))

    asset = TempAsset(
        name=in_path.stem,
        category=Category.SOFTWARE.index,
        type=AssetType.COMPONENT.index,
        duration=0,
        path=in_path,
        icon=icon,
    )
    asset.classification = flag.value
    return asset

def getDurationFramerate(stream):
    framerate = float(stream.rate)
    duration = stream.duration * float(stream.time_base)
    return duration, framerate

def generateProxy(in_path, out_path, modulus=10):
    input_container = av.open(str(in_path))
    input_stream = input_container.streams.video[0]
    input_stream.thread_type = "AUTO"

    duration, framerate = getDurationFramerate(input_stream)
    middle_frame = int((duration * framerate) / 2)

    # decode and encode streams
    with VidOut(out_path, input_stream) as vidout:
        for frame_number, frame in enumerate(input_container.decode(video=0)):
            # Only encode the preview every 10th frame to speed it up.
            if frame_number % modulus == 0:
                icon_frame = vidout.encodePreview(frame_number, frame)
            if frame_number == middle_frame:
                middle_pixels = icon_frame.to_rgb().to_ndarray()
            vidout.encodeProxy(frame)
    input_container.close()
    return duration, framerate, middle_pixels, input_stream


def processMOV(in_path, out_path, flag):
    duration, framerate, middle_pixels, stream = generateProxy(in_path, out_path)
    ih, iw, _ = middle_pixels.shape
    src_img = QImage(middle_pixels, iw, ih, QImage.Format_RGB888)
    icon_img = makeImagePreview(src_img)
    icon_img.save(str(out_path.suffixed('_icon', ext='.jpg')))
    asset = TempAsset(
        name=in_path.stem,
        category=0,
        type=AssetType.COMPONENT.index,
        duration=int(duration),
        framerate=int(framerate),
        resolution=f'{stream.width}x{stream.height}x3',
        path=in_path,
        icon=icon_img,
    )
    asset.classification = flag.value
    return asset

def processSEQ(in_path, out_path, flag):
    frames = sorted(in_path.frames)
    frame_count = len(frames)
    if frame_count == 1:
        return processHDR(in_path, out_path, flag)
    img_input = oiio.ImageInput.open(str(frames[0]))
    spec = img_input.spec()
    img_input.close()
    w, h, c = spec.full_width, spec.full_height, spec.nchannels

    # Ensure 16x16 compatible format for h264
    proxy_size = ImageDimensions(w, h)
    proxy_size.makeDivisble(height=True)

    middle_frame = int(frame_count / 2)

    input_stream = FakeImageStream(w, h, Fraction(1, 24))
    with VidOut(out_path, input_stream) as vidout:
        for frame_number, frame in enumerate(frames):
            buf = oiio.ImageBuf(str(frame))
            buf = oiio.ImageBufAlgo.colorconvert(buf, "Linear", "sRGB")

            # Exr's may have bounding box regions of interest.
            spec = buf.spec()
            r = spec.roi
            img_data = buf.get_pixels(format=oiio.UINT8)
            has_bbox = spec.height != spec.full_height or spec.width != spec.full_width
            if has_bbox:
                full_pixels = np.zeros((spec.full_height, spec.full_width, 3), dtype=np.uint8)
                full_pixels[r.ybegin:r.yend, r.xbegin:r.xend, :] = img_data[:, :, :3]
                array = full_pixels
            else:
                array = img_data[:, :, :3]

            # Write Icon from center of range
            if frame_number == middle_frame:
                ih, iw, _ = array.shape
                src_img = QImage(array, iw, ih, QImage.Format_RGB888)
                icon_img = makeImagePreview(src_img)
                icon_img.save(str(out_path.suffixed('_icon', ext='.jpg')))

            video_frame = VideoFrame.from_ndarray(array)
            # Only encode the preview every 10th frame to speed it up.
            if frame_number % 10 == 0:
                vidout.encodePreview(frame_number, video_frame)

            vidout.encodeProxy(video_frame)

    asset = TempAsset(
        name=in_path.stem,
        category=0,
        type=AssetType.COMPONENT.index,
        duration=int(frame_count/24),
        framerate=24,
        resolution=f'{w}x{h}x{c}',
        path=in_path,
        icon=icon_img,
    )
    asset.classification = flag.value
    return asset

def processRAW(in_path, out_path, flag):
    in_path.copyTo(out_path)
    in_path = out_path
    img_bytes = EXIFTOOL.getPreview(str(in_path))
    src_img = QImage()
    src_img.loadFromData(img_bytes)
    asset = tempAssetFromImage(in_path, out_path, src_img)
    asset.classification = flag.value
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
        type=AssetType.COMPONENT.index,
        duration=0,
        resolution=f'{w}x{h}x{c}',
        path=in_path,
        icon=icon_img,
    )
    return asset

def processFILM(in_path, out_path, flag):
    asset = TempAsset(
        name=in_path.stem,
        category=Category.ELEMENTS.index,
        type=AssetType.COMPONENT.index,
        duration=0,
        path=in_path,
    )
    asset.classification = Class.IMAGE.value
    return asset

def processDOC(in_path, out_path, flag):
    asset = TempAsset(
        name=in_path.stem,
        category=Category.REFERENCES.index,
        type=AssetType.REFERENCE.index,
        duration=0,
        path=in_path,
    )
    asset.classification = Class.DOCUMENT.flag
    asset.icon = DEFAULT_ICONS.document
    return asset

def processIMAGE(in_path, out_path, flag):
    if flag & (FileType.JPG | FileType.TIF | FileType.PNG | FileType.JPEG):
        # Assumes gamma correction has already been encoded into the file.
        asset = processLDR(in_path, out_path, flag)
    elif flag & (FileType.HDR | FileType.EXR):
        # Linear image will get a nice tonemapping applied to the previews.
        asset = processHDR(in_path, out_path, flag)
    asset.classification = flag.value
    return asset

def processLIGHT(in_path, out_path, flag):
    asset = TempAsset(
        name=in_path.stem,
        category=Category.LIGHTING.index,
        type=AssetType.COMPONENT.index,
        duration=0,
        path=in_path,
    )
    asset.classification = Class.IES.flag
    return asset


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
    elif is_raw:
        #img_buf = autoExpose(img_buf)
        print(f'converting {img_path} to ACEScg...')
        img_buf = hdr.acesToCG(img_buf)

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
    
    temp_asset.classification = FileType.EXR.value
    temp_asset.resolution = str(dimensions)
    temp_asset.icon = icon_img
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

    @staticmethod
    def copyOp(src, dst):
        src.copyTo(Path.cleanPath(dst))

    @staticmethod
    def moveOp(src, dst):
        src.moveTo(Path.cleanPath(dst))

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
        #TODO This function is too big and hard to read.
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
                try:
                    migrate_files(files_map)
                except:
                    print('failed to migrate files from mapping', files_map)
                # Calculate the final hash and size of the asset on network storage.
                item.filehash = out_path.parent.hash
                item.filesize = out_path.parent.size.kilobytes

                self.queue.popleft()
                self.itemDone.emit(item)

            self.mutex.lock()
            self.condition.wait(self.mutex)
            self.mutex.unlock()
