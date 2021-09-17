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
    return (spec.full_width, spec.full_height, aspect)


def read_file(image_in, subimage=(0,3)):
    image_in = oiio.ImageInput.open(image_in)
    if not image_in:
        return None, None
    spec = image_in.spec()
    if type(subimage) is int:
        image_in.seek_subimage(subimage, 0)
        data = image_in.read_image(oiio.UNKNOWN)

    if type(subimage) is tuple:
        start, end = subimage
        data = image_in.read_scanlines(
            spec.y, (spec.y + spec.height), spec.full_z, start, end + 1, oiio.UNKNOWN
        )
        #if start == end:
        #    data = np.stack((data,) / 3, -1)

    # If display window is not the same as data window pad the pixels with zeros
    if spec.height != spec.full_height or spec.width != spec.full_width:
        xpad = spec.x
        ypad = spec.y
        padded = np.zeros((spec.full_width, spec.full_height, 3), dtype=data.dtype)
        padded[ypad:data.shape[0]+ypad, xpad:data.shape[1]+xpad] = data
        data = padded
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
