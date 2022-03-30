import subprocess
import os
from PySide6.QtMultimedia import (
    QAudioFormat,
    QMediaDevices,
    QAudioSource,
)
from PySide6.QtCore import QObject, QRunnable
CREATE_NO_WINDOW = 0x08000000

class AudioRecord(QObject):
    def __init__(self, audio_path):
        super(AudioRecord, self).__init__()
        self.input_device = QMediaDevices.defaultAudioInput()
        audio_format = QAudioFormat()
        audio_format.setSampleRate(44100)
        audio_format.setChannelCount(1) # 1 mono, 2 stereo
        audio_format.setSampleFormat(QAudioFormat.UInt8)

        self.cmd = [
            'ffmpeg',
            '-loglevel', 'error',
            '-y', # Always Overwrite
            '-r', '24', # FPS
            '-ar', '44100',
            '-ac', '1',
            '-f', 'u8',
            '-i', '-',
            str(audio_path),
        ]
        self.ffproc = subprocess.Popen(
            self.cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            creationflags=CREATE_NO_WINDOW,
        )

        if not self.input_device.isNull():
            self._audio_input = QAudioSource(self.input_device, audio_format, self)
            self._io_device = self._audio_input.start()
            self._io_device.readyRead.connect(self._readyRead)

    def stop(self):
        self.ffproc.stdin.close()
        if not self.input_device.isNull():
            self._audio_input.stop()

    def _readyRead(self):
        data = self._io_device.readAll()
        self.ffproc.stdin.write(data.data())


class ShellCommand(QRunnable):

    def __init__(self, cmd, obj, signal=None, callback=None):
        super(ShellCommand, self).__init__(signal)
        self.cmd = cmd
        self.obj = obj
        self.signal = signal
        self.callback = callback

    def run(self):
        subprocess.call(self.cmd, creationflags=CREATE_NO_WINDOW)
        if self.callback:
            self.callback(self.obj)
        if self.signal:
            self.signal.emit(self.obj)


def video_to_gif(path):
    out_path = path.suffixed('', ext='.gif')
    gif_palette = path.suffixed('_palette', ext='.png')
    cmd1 = [
        'ffmpeg',
        '-loglevel', 'error',
        '-i', str(path),
        '-vf', 'palettegen',
        str(gif_palette),
    ]
    cmd2 = [
        'ffmpeg',
        '-loglevel', 'error',
        '-i', str(path),
        '-i', str(gif_palette),
        '-filter_complex', 'fps=30,paletteuse',
        str(out_path),
    ]
    subprocess.call(cmd1, creationflags=CREATE_NO_WINDOW)
    subprocess.call(cmd2, creationflags=CREATE_NO_WINDOW)
    os.remove(str(gif_palette))

