import subprocess, sys
import oiio.OpenImageIO as oiio
import numpy as np

DEVNULL = subprocess.DEVNULL
CREATE_NO_WINDOW = 0x08000000

def getImageResolution(image_in):
    image_in = oiio.ImageInput.open(image_in)
    if not image_in:
        return None
    spec = image_in.spec()
    aspect = spec.get_float_attribute("PixelAspectRatio")
    return (spec.full_width, spec.full_height, spec.nchannels, aspect)


def read_file(image_in, subimage=(0,3)):
    image_in = oiio.ImageInput.open(image_in)
    if not image_in:
        return None, None
    spec = image_in.spec()
    display_r = oiio.get_roi_full(spec)
    data_r = spec.roi
    if isinstance(subimage, int):
        image_in.seek_subimage(subimage, 0)
        data = image_in.read_image(oiio.UNKNOWN)
    elif isinstance(subimage, tuple):
        start, end = subimage
        data = image_in.read_image(start, end + 1, oiio.UNKNOWN)
    # If display window is not the same as data window pad the pixels with zeros
    if spec.height < display_r.height or spec.width < display_r.width:
        display = np.zeros((display_r.height, display_r.width, data.shape[2]), dtype=data.dtype)
        display[data_r.ybegin:data_r.yend, data_r.xbegin:data_r.xend, :] = data
        data = display

    image_in.close()

    return data, spec


def generate_blank(
        xres,
        yres,
        channels=4,
        pixel_format=oiio.UINT8,
        value=(0, 0, 0, 0),
        xoffset=0,
        yoffset=0
    ):
    spec = oiio.ImageSpec(xres, yres, channels, pixel_format)
    spec.x = xoffset
    spec.y = yoffset
    b = oiio.ImageBuf(spec)
    oiio.ImageBufAlgo.fill(b, value)
    image = b.get_pixels(pixel_format)
    return image


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
    output = subprocess.check_output(cmd, creationflags=CREATE_NO_WINDOW).decode("utf-8").split('\r\n')
    return output[:3]
